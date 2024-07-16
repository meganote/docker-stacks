from .stt import STT, SpeechStream
from .tts import DEFAULT_VOICE, TTS, Voice, VoiceSettings
from .version import __version__

__all__ = [
    "STT",
    "TTS",
    "SpeechStream",
    "__version__",
]


from livekit.agents import Plugin


class JtPlugin(Plugin):
    def __init__(self):
        super().__init__(__name__, __version__, __package__)

    def download_files(self):
        pass


Plugin.register_plugin(JtPlugin())
