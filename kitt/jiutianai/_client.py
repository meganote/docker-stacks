import os
import jwt
import time
from typing import Optional
from typing_extensions import override

from openai import OpenAI, AsyncOpenAI


class JiutianAI(OpenAI):
    jwt_exp_seconds: int | None

    def __init__(self) -> None:
        self.jwt_exp_seconds = 60

        super().__init__()

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        jwt_exp_seconds = self.jwt_exp_seconds
        jwt_token = _get_jwt_token(api_key, jwt_exp_seconds)
        return {"Authorization": f"Bearer {jwt_token}"}


class AsyncJiutianAI(AsyncOpenAI):
    jwt_exp_seconds: int | None

    def __init__(self) -> None:
        self.jwt_exp_seconds = 60

        super().__init__()

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        jwt_exp_seconds = self.jwt_exp_seconds
        jwt_token = _get_jwt_token(api_key, jwt_exp_seconds)
        return {"Authorization": f"Bearer {jwt_token}"}


def _get_jwt_token(api_key, exp_seconds: int):
    try:
        id, secret = api_key.split(".")
    except Exception as e:
        raise Exception("invalid api_key", e)

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


Client = JiutianAI

AsyncClient = AsyncJiutianAI
