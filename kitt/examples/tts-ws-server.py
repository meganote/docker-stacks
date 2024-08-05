import asyncio
import json
import os

import aiohttp
from websockets.server import serve


async def echo(websocket):
    base_url = os.getenv("TTS_BASE_URL", "http://ip:port")
    headers = {"Content-Type": "application/json"}
    async with aiohttp.ClientSession(base_url) as session:
        async for message in websocket:
            print(f"message: {message}")
            message_json = json.loads(message)
            async with session.post(
                "/jttts/TTS_Service", json=message_json, headers=headers
            ) as resp:
                data = await resp.text()
                json_data = json.loads(data)
                audio = json_data["Msg"]

            await websocket.send(audio)


async def main():
    async with serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever


asyncio.run(main())
