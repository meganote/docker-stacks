import asyncio
import dataclasses
import io
import json
import os
import wave
import time
from contextlib import suppress
from dataclasses import dataclass
from typing import List, Optional, Union
from urllib.parse import urlencode

import aiohttp
from livekit import rtc
from livekit.agents import stt, utils
from livekit.agents.utils import AudioBuffer, merge_frames

from .log import logger
from .models import JtLanguages, JtModels


@dataclass
class STTOptions:
    language: JtLanguages | str | None
    detect_language: bool
    interim_results: bool
    punctuate: bool
    model: JtModels
    smart_format: bool
    no_delay: bool
    endpointing: int | None


class STT(stt.STT):
    def __init__(
        self,
        *,
        language: JtLanguages = "zh-CN",
        detect_language: bool = False,
        interim_results: bool = True,
        punctuate: bool = True,
        smart_format: bool = True,
        no_delay: bool = False,
        model: JtModels = "jt-multimodol",
        api_key: str | None = None,
        min_silence_duration: int = 0,
        http_session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__(streaming_supported=True)
        api_key = api_key or os.environ.get("JT_API_KEY")
        if api_key is None:
            raise ValueError("JT API key is required")
        self._api_key = api_key

        self._opts = STTOptions(
            language=language,
            detect_language=detect_language,
            interim_results=interim_results,
            punctuate=punctuate,
            model=model,
            smart_format=smart_format,
            no_delay=no_delay,
            endpointing=min_silence_duration,
        )
        self._session = http_session

    def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session:
            self._session = utils.http_session()

        return self._session

    async def recognize(
        self,
        *,
        buffer: AudioBuffer,
        language: JtLanguages | str | None = None,
    ) -> stt.SpeechEvent:
        config = self._sanitize_options(language=language)

        return prerecorded_transcription_to_speech_event(config.language, "")

    def stream(
        self,
        *,
        language: JtLanguages | str | None = None,
    ) -> "SpeechStream":
        config = self._sanitize_options(language=language)
        return SpeechStream(config, self._api_key, self._ensure_session())

    def _sanitize_options(
        self,
        *,
        language: str | None = None,
    ) -> STTOptions:
        config = dataclasses.replace(self._opts)
        config.language = language or config.language

        if config.detect_language:
            config.language = None

        return config


class SpeechStream(stt.SpeechStream):
    _KEEPALIVE_MSG: str = json.dumps({"type": "KeepAlive"})
    _INIT_MSG = {
        "chunk_size": [5, 10, 5],
        "wav_name": "wss",
        "is_speaking": True,
        "chunk_interval": 10,
        "itn": True,
        "mode": "2pass",
    }
    _CLOSE_MSG = {
        "chunk_size": [5, 10, 5],
        "wav_name": "wss",
        "is_speaking": False,
        "chunk_interval": 10,
        "mode": "2pass",
    }

    def __init__(
        self,
        opts: STTOptions,
        api_key: str,
        http_session: aiohttp.ClientSession,
        sample_rate: int = 16000,
        num_channels: int = 1,
        max_retry: int = 32,
    ) -> None:
        super().__init__()

        if opts.detect_language and opts.language is None:
            raise ValueError("language detection is not supported in streaming mode")

        self._opts = opts
        self._sample_rate = sample_rate
        self._num_channels = num_channels
        self._api_key = api_key
        self._speaking = False
        self._session = http_session
        self._queue = asyncio.Queue[Union[rtc.AudioFrame, str]]()
        self._event_queue = asyncio.Queue[Optional[stt.SpeechEvent]]()
        self._closed = False
        self._main_task = asyncio.create_task(self._run(max_retry))

        # keep a list of final transcripts to combine them inside the END_OF_SPEECH event
        self._final_events: List[stt.SpeechEvent] = []

    def push_frame(self, frame: rtc.AudioFrame) -> None:
        if self._closed:
            raise ValueError("cannot push frame to closed stream")

        self._queue.put_nowait(frame)

    async def aclose(self, *, wait: bool = True) -> None:
        self._closed = True
        self._queue.put_nowait(SpeechStream._CLOSE_MSG)

        if not wait:
            self._main_task.cancel()

        with suppress(asyncio.CancelledError):
            await self._main_task

        await self._session.close()

    async def _run(self, max_retry: int) -> None:
        """
        Run a single websocket connection to asr and make sure to reconnect
        when something went wrong.
        """

        try:
            retry_count = 0
            while not self._closed:
                try:
                    live_config = {
                        "model": self._opts.model,
                        "punctuate": self._opts.punctuate,
                        "smart_format": self._opts.smart_format,
                        "no_delay": self._opts.no_delay,
                        "interim_results": self._opts.interim_results,
                        "encoding": "linear16",
                        "sample_rate": self._sample_rate,
                        "vad_events": True,
                        "channels": self._num_channels,
                        "endpointing": self._opts.endpointing,
                    }

                    if self._opts.language:
                        live_config["language"] = self._opts.language

                    headers = {"Authorization": f"Token {self._api_key}"}
                    base_url = os.environ.get("ASR_BASE_URL")

                    url = f"ws://{base_url}/stream"
                    # logger.info(f"connection to asr: {url}")
                    ws = await self._session.ws_connect(url, headers=headers)
                    retry_count = 0  # connected successfully, reset the retry_count
                    logger.info(f"connected to asr: {url}")

                    await self._run_ws(ws)
                except Exception:
                    # Something went wrong, retry the connection
                    if retry_count >= max_retry:
                        logger.exception(f"failed to connect to asr after {max_retry} tries")
                        break

                    retry_delay = min(retry_count * 2, 10)  # max 10s
                    retry_count += 1  # increment after calculating the delay, the first retry should happen directly

                    logger.warning(f"asr connection failed, retrying in {retry_delay}s")
                    await asyncio.sleep(retry_delay)
        except Exception:
            logger.exception("asr task failed")
        finally:
            self._event_queue.put_nowait(None)

    async def _run_ws(self, ws: aiohttp.ClientWebSocketResponse) -> None:
        """
        This method can throw ws errors, these are handled inside the _run method
        """

        closing_ws = False

        async def keepalive_task():
            # if we want to keep the connection alive even if no audio is sent,
            # Deepgram expects a keepalive message.
            # https://developers.deepgram.com/reference/listen-live#stream-keepalive
            try:
                while True:
                    await ws.send_str(SpeechStream._KEEPALIVE_MSG)
                    await asyncio.sleep(5)
            except Exception:
                pass

        async def send_task():
            nonlocal closing_ws

            logger.debug(f"send init_msg: {SpeechStream._INIT_MSG}")
            await ws.send_json(SpeechStream._INIT_MSG)

            # forward inputs to deepgram
            # if we receive a close message, signal it to deepgram and break.
            # the recv task will then make sure to process the remaining audio and stop
            while True:
                data = await self._queue.get()
                self._queue.task_done()

                if isinstance(data, rtc.AudioFrame):
                    # TODO(theomonnom): The remix_and_resample method is low quality
                    # and should be replaced with a continuous resampling
                    frame = data.remix_and_resample(self._sample_rate, self._num_channels)
                    await ws.send_bytes(frame.data.tobytes())
                elif data == SpeechStream._CLOSE_MSG:
                    closing_ws = True
                    logger.debug(f"send close_msg: {data}")
                    await ws.send_json(data)  # tell asr we are done with inputs
                    break

        async def recv_task():
            nonlocal closing_ws

            while True:
                msg = await ws.receive()

                if msg.type in (
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    if closing_ws:  # close is expected, see SpeechStream.aclose
                        return

                    raise Exception(
                        "asr connection closed unexpectedly"
                    )  # this will trigger a reconnection, see the _run loop

                if msg.type != aiohttp.WSMsgType.TEXT:
                    logger.warning("unexpected asr message type %s", msg.type)
                    continue

                try:
                    # received a message from asr
                    data = json.loads(msg.data)
                    self._process_stream_event(data)
                except Exception:
                    logger.exception("failed to asr deepgram message")

        # async def detect_finish_task():
        #     try:
        #         while True:
        #             logger.debug(f"detect_finish_task {is_recent_speak} - {last_voice_time}")
        #             current_time = time.time()
        #             if (
        #                 is_recent_speak
        #                 and last_voice_time is not None
        #                 and (current_time - last_voice_time) > 2
        #             ):
        #                 is_recent_speak = False
        #                 await ws.send_json(SpeechStream._CLOSE_MSG)
        #             await asyncio.sleep(2)
        #     except Exception:
        #         pass

        await asyncio.gather(send_task(), recv_task())

    def _end_speech(self) -> None:
        if not self._speaking:
            logger.warning("trying to commit final events without being in the speaking state")
            return

        if len(self._final_events) == 0:
            return

        self._speaking = False

        # combine all final transcripts since the start of the speech
        sentence = ""
        confidence = 0.0
        for f in self._final_events:
            alt = f.alternatives[0]
            sentence += f"{alt.text.strip()} "
            confidence += alt.confidence

        sentence = sentence.rstrip()
        confidence /= len(self._final_events)  # avg. of confidence

        end_event = stt.SpeechEvent(
            type=stt.SpeechEventType.END_OF_SPEECH,
            alternatives=[
                stt.SpeechData(
                    language=str(self._opts.language),
                    start_time=self._final_events[0].alternatives[0].start_time,
                    end_time=self._final_events[-1].alternatives[0].end_time,
                    confidence=confidence,
                    text=sentence,
                )
            ],
        )
        self._event_queue.put_nowait(end_event)
        self._final_events = []

    def _process_stream_event(self, data: dict) -> None:
        assert self._opts.language is not None

        logger.debug(f"_process_stream_event: {data}")

        if data["mode"] == "2pass-offline":
            is_final_transcript = True
        else:
            is_final_transcript = False

        alts = live_transcription_to_speech_data(self._opts.language, data)
        # If, for some reason, we didn't get a SpeechStarted event but we got
        # a transcript with text, we should start speaking. It's rare but has
        # been observed.
        if len(alts) > 0 and alts[0].text:
            if not self._speaking:
                self._speaking = True
                start_event = stt.SpeechEvent(type=stt.SpeechEventType.START_OF_SPEECH)
                self._event_queue.put_nowait(start_event)

            if is_final_transcript:
                final_event = stt.SpeechEvent(
                    type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                    alternatives=alts,
                )
                self._final_events.append(final_event)
                self._event_queue.put_nowait(final_event)
            else:
                interim_event = stt.SpeechEvent(
                    type=stt.SpeechEventType.INTERIM_TRANSCRIPT,
                    alternatives=alts,
                )
                self._event_queue.put_nowait(interim_event)

            # if we receive an endpoint, only end the speech if
            # we either had a SpeechStarted event or we have a seen
            # a non-empty transcript
            if is_final_transcript and self._speaking:
                logger.debug("_end_speech")
                self._end_speech()

    async def __anext__(self) -> stt.SpeechEvent:
        evt = await self._event_queue.get()
        if evt is None:
            raise StopAsyncIteration

        return evt


def live_transcription_to_speech_data(
    language: str,
    data: dict,
) -> List[stt.SpeechData]:

    return [
        stt.SpeechData(
            language=language,
            start_time=0,
            end_time=0,
            confidence=0.0,
            text=data["text"],
        )
    ]


def prerecorded_transcription_to_speech_event(
    language: str | None,  # language should be None when 'detect_language' is enabled
    data: dict,
) -> stt.SpeechEvent:
    # Always zh
    detected_language = "zh"

    return stt.SpeechEvent(
        type=stt.SpeechEventType.FINAL_TRANSCRIPT,
        alternatives=[
            stt.SpeechData(
                language=language or detected_language,
                start_time=0,
                end_time=0,
                confidence=0.0,
                text="",
            )
        ],
    )
