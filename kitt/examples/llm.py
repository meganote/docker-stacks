import time
import jwt
import asyncio

# from sdk import JiutianAI


def generate_token(apikey: str, exp_seconds: int):
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time())) + exp_seconds,
        "timestamp": int(round(time.time())),
    }
    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "typ": "JWT", "sign_type": "SIGN"},
    )


async def main():
    sample_rate: int = 32000
    API_KEY = ""

    jwt_token = "Bearer " + generate_token(API_KEY, 60)

    headers = {"Authorization": jwt_token}
    data = {
        "modelId": "jiutian-lan",
        "messages": [{"role": "user", "content": "Hello!"}],
        "temperature": 0.8,
        "top_p": 0.95,
        "stream": True,
    }

    # client = JiutianAI(api_key=API_KEY, disable_token_cache=False)
    # from openai import OpenAI
    # client = OpenAI(api_key=generate_token(API_KEY, 60))
    from jiutianai import JiutianAI

    client = JiutianAI()
    response = client.chat.completions.create(
        model="jiutian-lan",
        messages=[
            {"role": "user", "content": "Hello"},
        ],
        temperature=0.8,
        top_p=0.95,
        stream=True,
    )
    for chunk in response:
        print(chunk.choices[0].delta.content)

    # for chunk in response:
    #     print(chunk.choices[0].delta)

    # # use httpx
    # async with httpx.AsyncClient(timeout=10) as client:
    #     async with httpx_sse.aconnect_sse(
    #         client, "POST", url, json=data, headers=headers
    #     ) as event_source:
    #         async for sse in event_source.aiter_sse():
    #             print(sse)

    # # use aio
    # async with aiohttp.ClientSession("http://172.31.192.111:30443") as session:
    #     async with session.post(
    #         url="/largemodel/api/v2/chat/completions", headers=headers, json=data
    #     ) as resp:
    #         event_data = []
    #         while True:
    #             line = await resp.content.readline()
    #             if not line:
    #                 await resp.release()
    #                 raise StopAsyncIteration
    #             line = line.decode("utf-8").rstrip()
    #             print(f"line: {line}")
    #             # if line == "":
    #             #     break
    #             event_data.append(line)
    #         return "\n".join(event_data)
    #         print(event_data)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
