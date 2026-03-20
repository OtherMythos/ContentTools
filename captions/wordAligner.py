"""
Align FCPXML caption text blocks to Whisper word-level timestamps.

Strategy:
  1. Normalise both caption text and Whisper words to lowercase, strip punctuation.
  2. For each caption block, find the best matching contiguous run of Whisper words
     using a forward greedy search with difflib fuzzy matching to handle transcription
     imperfections (homophones, missing punctuation, minor word-order differences).
  3. Consume matched words so that blocks are assigned non-overlapping, ordered spans.

Fallback (no FCPXML captions):
  Sentence-aware grouper: split Whisper words on sentence-ending punctuation, capping
  each group at maxBlockWords.
"""

import re
import difflib
from dataclasses import dataclass, field
from typing import List, Optional

from transcribe import WordSegment
from fcpxmlParser import CaptionBlock


@dataclass
class AlignedBlock:
    text: str                         #original caption text
    words: List[WordSegment] = field(default_factory=list)


def _normalise(text: str) -> str:
    """Lowercase and strip punctuation for comparison."""
    return re.sub(r"[^a-z0-9\s']", "", text.lower()).strip()


def _split_words(text: str) -> List[str]:
    return _normalise(text).split()


def align(
    caption_blocks: List[CaptionBlock],
    whisper_words: List[WordSegment],
) -> List[AlignedBlock]:
    """
    Align each caption block to a contiguous span of Whisper words.
    Returns AlignedBlock list in the same order as caption_blocks.
    """
    if not caption_blocks:
        return []
    if not whisper_words:
        return [AlignedBlock(text=b.text) for b in caption_blocks]

    aligned: List[AlignedBlock] = []
    pool_start = 0  #index into whisper_words consumed so far

    for block in caption_blocks:
        target_words = _split_words(block.text)
        n_target = len(target_words)

        if n_target == 0:
            aligned.append(AlignedBlock(text=block.text))
            continue

        best_score = -1.0
        best_start = pool_start
        best_end = min(pool_start + n_target, len(whisper_words))

        #search a window: allow up to 2× as many whisper words as target words
        #to absorb filler words, repetitions, etc.
        window_end = min(pool_start + n_target * 3, len(whisper_words))

        remaining = window_end - pool_start
        #outer range: ensure at least start_idx=pool_start is always tried
        outer_end = max(pool_start + 1, window_end - n_target + 1)
        for start_idx in range(pool_start, outer_end):
            available = window_end - start_idx
            if available <= 0:
                break
            #inner range: span from min(n_target, available) to allow partial
            #matches near end of audio where fewer words may remain
            min_span = min(n_target, available)
            max_span = min(n_target * 2, available)
            for span_len in range(min_span, max_span + 1):
                end_idx = start_idx + span_len
                candidate_words = [
                    _normalise(w.word)
                    for w in whisper_words[start_idx:end_idx]
                ]
                candidate_str = " ".join(candidate_words)
                target_str = " ".join(target_words)
                score = difflib.SequenceMatcher(
                    None, target_str, candidate_str
                ).ratio()
                if score > best_score:
                    best_score = score
                    best_start = start_idx
                    best_end = end_idx

        matched = whisper_words[best_start:best_end]
        aligned.append(AlignedBlock(text=block.text, words=list(matched)))
        pool_start = best_end

        print(
            f"[align] Block '{block.text[:40]}...' → "
            f"{len(matched)} words [{matched[0].start:.2f}s–{matched[-1].end:.2f}s] "
            f"(score={best_score:.2f})"
            if matched else
            f"[align] Block '{block.text[:40]}...' → NO MATCH"
        )

    return aligned


def fallback_group(
    whisper_words: List[WordSegment],
    max_block_words: int = 8,
) -> List[AlignedBlock]:
    """
    Sentence-aware grouper used when no FCPXML captions are available.
    Splits on sentence-ending punctuation, caps each group at max_block_words.
    """
    if not whisper_words:
        return []

    blocks: List[AlignedBlock] = []
    current: List[WordSegment] = []
    sentence_end_re = re.compile(r"[.?!,;]$")

    for word in whisper_words:
        current.append(word)
        is_sentence_end = bool(sentence_end_re.search(word.word.strip()))
        if is_sentence_end or len(current) >= max_block_words:
            text = " ".join(w.word.strip() for w in current)
            blocks.append(AlignedBlock(text=text, words=list(current)))
            current = []

    if current:
        text = " ".join(w.word.strip() for w in current)
        blocks.append(AlignedBlock(text=text, words=list(current)))

    return blocks
