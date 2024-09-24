import asyncio
import copy
import logging
from collections import deque
from enum import Enum
from typing import Annotated, List

from livekit import agents, rtc
from livekit.agents import JobContext, JobRequest, WorkerOptions, cli, llm, tokenize
from livekit.agents.llm import ChatContext, ChatMessage, ChatRole
from livekit.agents.voice_assistant import AssistantContext, VoiceAssistant
from livekit.plugins import nltk, silero
from plugins import jt

MAX_IMAGES = 3
NO_IMAGE_MESSAGE_GENERIC = (
    "I'm sorry, I don't have an image to process. Are you publishing your video?"
)


class Room(Enum):
    BEDROOM = "bedroom"
    LIVING_ROOM = "living room"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    OFFICE = "office"


class AssistantFnc(agents.llm.FunctionContext):
    @agents.llm.ai_callable(
        desc="Called when asked to evaluate something that would require vision capabilities."
    )
    async def image(
        self,
        user_msg: Annotated[
            str,
            agents.llm.TypeInfo(desc="The user message that triggered this function"),
        ],
    ):
        ctx = AssistantContext.get_current()
        ctx.store_metadata("user_msg", user_msg)

    @llm.ai_callable(desc="Turn on/off the lights in a room")
    async def toggle_light(
        self,
        room: Annotated[Room, llm.TypeInfo(desc="The specific room")],
        status: bool,
    ):
        logging.info("toggle_light %s %s", room, status)
        ctx = AssistantContext.get_current()
        key = "enabled_rooms" if status else "disabled_rooms"
        li = ctx.get_metadata(key, [])
        li.append(room)
        ctx.store_metadata(key, li)

    @llm.ai_callable(desc="User want the assistant to stop/pause speaking")
    def stop_speaking(self):
        pass  # do nothing


async def get_human_video_track(room: rtc.Room):
    track_future = asyncio.Future[rtc.RemoteVideoTrack]()

    def on_sub(track: rtc.Track, *_):
        if isinstance(track, rtc.RemoteVideoTrack):
            track_future.set_result(track)

    room.on("track_subscribed", on_sub)

    remote_video_tracks: List[rtc.RemoteVideoTrack] = []
    for _, p in room.participants.items():
        for _, t_pub in p.tracks.items():
            if t_pub.track is not None and isinstance(t_pub.track, rtc.RemoteVideoTrack):
                remote_video_tracks.append(t_pub.track)

    if len(remote_video_tracks) > 0:
        track_future.set_result(remote_video_tracks[0])

    video_track = await track_future
    room.off("track_subscribed", on_sub)
    return video_track


async def entrypoint(ctx: JobContext):
    sip = ctx.room.name.startswith("sip")

    fnc_ctx = AssistantFnc()

    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role=ChatRole.SYSTEM,
                text=(
                    "You are a funny bot created by LiveKit. Your interface with users will be voice. "
                    "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
                ),
            )
        ]
    )

    # gpt = openai.LLM(
    #     model="gpt-4o",
    # )
    cm = jt.LLM(model="qwen-v2")
    latest_image: rtc.VideoFrame | None = None
    img_msg_queue: deque[agents.llm.ChatMessage] = deque()
    assistant = VoiceAssistant(
        vad=silero.VAD(
            model_path="/root/.cache/torch/hub/snakers4-silero-vad-7a176cc/files/silero_vad.jit"
        ),
        stt=jt.STT(),
        llm=cm,
        tts=jt.TTS(),
        fnc_ctx=fnc_ctx,  # None if sip else AssistantFnc(),
        chat_ctx=initial_ctx,
        allow_interruptions=True,
        debug=True,
    )

    chat = rtc.ChatManager(ctx.room)

    async def _answer_from_text(text: str):
        # chat_ctx = copy.deepcopy(assistant.chat_context)
        # chat_ctx.messages.append(ChatMessage(role=ChatRole.USER, text=text))
        assistant.chat_context.messages.append(ChatMessage(role=ChatRole.USER, text=text))

        stream = await cm.chat(assistant.chat_context)
        await assistant.say(stream)

    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if not msg.message:
            return

        asyncio.create_task(_answer_from_text(msg.message))

    async def respond_to_image(user_msg: str):
        nonlocal latest_image, img_msg_queue, initial_ctx
        if not latest_image:
            await assistant.say(NO_IMAGE_MESSAGE_GENERIC)
            return

        initial_ctx.messages.append(
            agents.llm.ChatMessage(
                role=agents.llm.ChatRole.USER,
                text=user_msg,
                images=[agents.llm.ChatImage(image=latest_image)],
            )
        )
        img_msg_queue.append(initial_ctx.messages[-1])
        if len(img_msg_queue) >= MAX_IMAGES:
            msg = img_msg_queue.popleft()
            msg.images = []

        stream = await cm.chat(initial_ctx)
        await assistant.say(stream, allow_interruptions=True)

    @assistant.on("agent_speech_interrupted")
    def _agent_speech_interrupted(chat_ctx: llm.ChatContext, msg: llm.ChatMessage):
        msg.text += "... (user interrupted you)"

    @assistant.on("function_calls_finished")
    def _function_calls_done(ctx: AssistantContext):
        user_msg = ctx.get_metadata("user_msg")
        if not user_msg:
            return
        asyncio.ensure_future(respond_to_image(user_msg))

    assistant.start(ctx.room)

    await asyncio.sleep(0.5)
    await assistant.say(
        "Hey, how can I help you today?",
        allow_interruptions=True,
    )
    while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
        video_track = await get_human_video_track(ctx.room)
        async for event in rtc.VideoStream(video_track):
            latest_image = event.frame


async def request_fnc(req: JobRequest) -> None:
    logging.info("received request %s", req)
    await req.accept(entrypoint)


if __name__ == "__main__":
    option = WorkerOptions(request_fnc)
    option.host = "0.0.0.0"
    cli.run_app(option)
