from .llm import LLM, LLMStream
from .models import TTSEncoding, TTSModels
from .stt import STT, SpeechStream
from .tokenizer import SentenceTokenizer, WordTokenizer
from .tts import DEFAULT_VOICE, TTS, Voice, VoiceSettings
from .version import __version__

__all__ = [
    "STT",
    "SpeechStream",
    "TTS",
    "Voice",
    "VoiceSettings",
    "TTSEncoding",
    "TTSModels",
    "DEFAULT_VOICE",
    "LLM",
    "LLMStream",
    "SentenceTokenizer",
    "WordTokenizer",
    "__version__",
]


from livekit.agents import Plugin


class JtPlugin(Plugin):
    def __init__(self):
        super().__init__(__name__, __version__, __package__)

    def download_files(self):
        pass


Plugin.register_plugin(JtPlugin())
