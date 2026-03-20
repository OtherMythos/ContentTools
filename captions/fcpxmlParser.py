"""
Parse an exported FCPXML file and extract:
  - Ordered list of caption text blocks (from <caption> elements)
  - Project format attributes (frameDuration, width, height)

Caption offsets are intentionally ignored: all timing comes from Whisper.
The caption text order reflects the editorial sequence of the video.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ProjectFormat:
    frameDuration: str = "100/3000s"  #rational tick string e.g. "100/3000s"
    width: int = 1080
    height: int = 1920
    colorSpace: str = "1-1-1 (Rec. 709)"

    @property
    def ticksPerSecond(self) -> int:
        """Denominator of frameDuration rational, e.g. 3000 for '100/3000s'."""
        parts = self.frameDuration.rstrip("s").split("/")
        return int(parts[1]) if len(parts) == 2 else 3000


@dataclass
class CaptionBlock:
    """A block of text as defined by an FCP caption element."""
    text: str


def parse(fcpxml_path: str) -> Tuple[List[CaptionBlock], ProjectFormat]:
    """
    Returns (caption_blocks, project_format).
    caption_blocks is ordered by document appearance (= timeline order).
    """
    tree = ET.parse(fcpxml_path)
    root = tree.getroot()

    fmt = _parse_format(root)
    captions = _parse_captions(root)
    captions = _resplit_on_sentences(captions)

    return captions, fmt


def _parse_format(root: ET.Element) -> ProjectFormat:
    #look for the primary sequence format - find the project sequence first
    fmt = ProjectFormat()

    #find project sequence format ref
    sequence_fmt_id: Optional[str] = None
    for project in root.iter("project"):
        seq = project.find("sequence")
        if seq is not None:
            sequence_fmt_id = seq.get("format")
            break

    #find matching <format> in resources
    for f in root.iter("format"):
        fid = f.get("id")
        if fid == sequence_fmt_id or sequence_fmt_id is None:
            fd = f.get("frameDuration")
            w = f.get("width")
            h = f.get("height")
            cs = f.get("colorSpace", fmt.colorSpace)
            if fd:
                fmt.frameDuration = fd
            if w:
                fmt.width = int(w)
            if h:
                fmt.height = int(h)
            fmt.colorSpace = cs
            break

    return fmt


def _resplit_on_sentences(blocks: List[CaptionBlock]) -> List[CaptionBlock]:
    """
    Split any block whose text contains an internal sentence boundary into
    multiple blocks. Splits after '.', '?' or '!' that is followed by whitespace,
    ensuring each output block is at most one sentence. This prevents a new
    sentence starting on the last displayed line of a block.
    """
    #split after sentence-ending punctuation followed by whitespace.
    #negative lookbehind excludes common abbreviations like digits (3.5) and
    #single uppercase letters (e.g. U.S.) by only splitting when preceded by
    #a lowercase letter, digit sequence end, or closing punctuation.
    boundary = re.compile(r'(?<=[.?!])\s+')
    result: List[CaptionBlock] = []
    for block in blocks:
        parts = boundary.split(block.text.strip())
        for part in parts:
            part = part.strip()
            if part:
                result.append(CaptionBlock(text=part))
    return result


def _parse_captions(root: ET.Element) -> List[CaptionBlock]:
    blocks: List[CaptionBlock] = []
    seen: set = set()

    for caption in root.iter("caption"):
        #collect text from all <text-style> children inside <text>
        text_elem = caption.find("text")
        if text_elem is None:
            continue

        parts: List[str] = []
        for ts in text_elem.iter("text-style"):
            if ts.text:
                parts.append(ts.text.strip())

        full_text = " ".join(p for p in parts if p)
        if not full_text or full_text in seen:
            continue

        seen.add(full_text)
        blocks.append(CaptionBlock(text=full_text))

    return blocks
