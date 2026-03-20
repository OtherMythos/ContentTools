from dataclasses import dataclass
from typing import List


@dataclass
class WordSegment:
    word: str
    start: float  #seconds from audio start
    end: float    #seconds from audio start


def transcribe(audio_path: str, model: str = "small") -> List[WordSegment]:
    """
    Transcribe audio with word-level timestamps.
    Tries mlx-whisper (Apple Silicon) first, falls back to openai-whisper.
    """
    try:
        return _transcribe_mlx(audio_path, model)
    except ImportError:
        pass
    return _transcribe_openai(audio_path, model)


def _transcribe_mlx(audio_path: str, model: str) -> List[WordSegment]:
    import mlx_whisper  # type: ignore

    print(f"[transcribe] Using mlx-whisper (model={model})")
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=f"mlx-community/whisper-{model}-mlx",
        word_timestamps=True,
    )
    return _extract_words(result)


def _transcribe_openai(audio_path: str, model: str) -> List[WordSegment]:
    import whisper  # type: ignore

    print(f"[transcribe] Using openai-whisper (model={model})")
    m = whisper.load_model(model)
    result = m.transcribe(audio_path, word_timestamps=True)
    return _extract_words(result)


def _extract_words(result: dict) -> List[WordSegment]:
    words: List[WordSegment] = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            text = w.get("word", "").strip()
            if not text:
                continue
            words.append(WordSegment(
                word=text,
                start=float(w["start"]),
                end=float(w["end"]),
            ))
    return words
