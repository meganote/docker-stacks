from __future__ import annotations

import dataclasses
import functools
import re
from dataclasses import dataclass

from livekit import agents


@dataclass
class _TokenizerOptions:
    language: str
    min_sentence_len: int
    stream_context_len: int


class SentenceTokenizer(agents.tokenize.SentenceTokenizer):
    def __init__(
        self,
        *,
        language: str = "chinese",
        min_sentence_len: int = 5,
        stream_context_len: int = 5,
    ) -> None:
        super().__init__()
        self._config = _TokenizerOptions(
            language=language,
            min_sentence_len=min_sentence_len,
            stream_context_len=stream_context_len,
        )

    def tokenize(self, *, text: str, language: str | None = None) -> list[str]:
        return _split_sentences(text, min_sentence_len=self._config.min_sentence_len)

    def stream(
        self,
        *,
        language: str | None = None,
    ) -> agents.tokenize.SentenceStream:
        return agents.tokenize.BufferedTokenStream(
            tokenizer=functools.partial(
                _split_sentences,
                min_sentence_len=self._config.min_sentence_len,
            ),
            min_token_len=self._config.min_sentence_len,
            ctx_len=self._config.stream_context_len,
        )


class WordTokenizer(agents.tokenize.WordTokenizer):
    def __init__(self, *, ignore_punctuation: bool = True) -> None:
        self._ignore_punctuation = ignore_punctuation

    def tokenize(self, *, text: str, language: str | None = None) -> list[str]:
        return _split_words(text)

    def stream(self, *, language: str | None = None) -> agents.tokenizer.WordStream:
        return agents.tokenize.BufferedTokenStream(
            tokenizer=functools.partial(_split_words, ignore_punctuation=self._ignore_punctuation),
            min_token_len=1,
            ctx_len=1,  # ignore
        )


def _split_sentences(text: str, min_sentence_len: int = 20) -> list[str]:

    punc = r"(，|。|？|！|；|：|《|》|\,|\.|\?|\!|\;|\:|\<|\>)"

    # fmt: off
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(punc, "\\1<stop>", text)
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    if sentences and not sentences[-1]:
        sentences = sentences[:-1]
    # fmt: on

    new_sentences = []
    buff = ""
    for sentence in sentences:
        buff += " " + sentence
        if len(buff) > min_sentence_len:
            new_sentences.append(buff[1:])
            buff = ""

    if buff:
        new_sentences.append(buff[1:])

    return new_sentences


def _split_words(text: str, ignore_punctuation: bool = True) -> list[str]:
    # fmt: off
    punctuations = [".", ",", "!", "?", ";", ":", "'", '"', "(", ")", "[", "]", "{", "}", "<", ">",
                    "—", "，", "。", "？", "！", "；", "：","《","》"]
    # fmt: on

    if ignore_punctuation:
        for p in punctuations:
            # TODO(theomonnom): Ignore acronyms
            text = text.replace(p, "")

    words = text.split(" ")
    new_words = []
    for word in words:
        if not word:
            continue  # ignore empty
        new_words.append(word)

    return new_words
