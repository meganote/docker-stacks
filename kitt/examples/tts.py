from livekit import rtc
import aiohttp
import asyncio
import wave
import json
import base64


async def main():
    sample_rate: int = 32000

    async with aiohttp.ClientSession("http://host:port") as session:
        body = {
            "customIndex": "jinya",
            "user_id": "jinya",
            "prompt_num": 5,
            "streaming_mode": True,
            "text": "您还可以使用我们的多功能在线工具将音频文件转换为 Base64。只需上传您的音频文件，我们的解码器就会快速将其转换为 Base64 格式。",
        }
        # body = {
        #     "text": "您还可以使用我们的多功能在线工具将音频文件转换为 Base64。只需上传您的音频文件，我们的解码器就会快速将其转换为 Base64 格式。"
        # }

        async with session.post("/jttts/Voice_Clone", json=body) as resp:
            # avoid very small frames. chunk by 10ms 16bits
            bytes_per_frame = (sample_rate // 100) * 2
            buf = bytearray()
            async for data, _ in resp.content.iter_chunks():
                buf.extend(data)

                while len(buf) >= bytes_per_frame:
                    frame_data = buf[:bytes_per_frame]
                    buf = buf[bytes_per_frame:]

                    data = rtc.AudioFrame(
                        data=frame_data,
                        sample_rate=sample_rate,
                        num_channels=1,
                        samples_per_channel=len(frame_data) // 2,
                    )
                    print(data)

            # send any remaining data
            if len(buf) > 0:
                data = rtc.AudioFrame(
                    data=buf,
                    sample_rate=sample_rate,
                    num_channels=1,
                    samples_per_channel=len(buf) // 2,
                )
                print(data)

            # data = await resp.text()
            # print(data)
            # json_data = json.loads(data)
            # audio = json_data["Msg"]
            # b64data = base64.b64decode(audio)
            # audio = rtc.AudioFrame(
            #     data=b64data,
            #     sample_rate=sample_rate,
            #     num_channels=1,
            #     samples_per_channel=len(b64data) // 2,  # 16-bit
            # )
            # print(audio)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
