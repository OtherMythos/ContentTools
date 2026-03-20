from dataclasses import dataclass, field, asdict
import json
from pathlib import Path


@dataclass
class CaptionStyle:
    #font used for all caption text
    font: str = "Falling Sky"
    fontSize: float = 36.0
    bold: bool = True
    #exact face name as the font defines it (e.g. "Regular", "Bold", "Condensed Bold").
    #if empty, falls back to "Bold" or "Regular" derived from the bold flag above.
    #custom/display fonts often only have "Regular" — set that here if FCP reverts to Helvetica.
    fontFace: str = "Regular"
    alignment: str = "center"

    #colour of words already spoken (past) in the block - white
    pastColour: str = "1 1 1 1"
    #colour of the currently active word - magenta
    highlightColour: str = "0.5647 0.3059 1.0 1"
    #font size multiplier for the active word (e.g. 1.2 = 20% bigger)
    highlightScale: float = 1.0
    #colour of words not yet spoken (future) in the block - dim white
    futureColour: str = "1 1 1 0.9"

    #text outline (stroke) — colour as RGBA string, width in points (0 = disabled).
    #stored as positive; written as negative so Core Text renders fill AND stroke.
    outlineColour: str = "0 0 0 1"
    outlineWidth: float = 2.0

    #semi-transparent black pill behind each title
    backgroundColour: str = "0 0 0 0.8"

    #position in pixels from canvas centre (0,0 = centre; positive Y = up).
    #FCP inspector shows these exact pixel values under Transform > Position.
    #Converted to adjust-transform percentages (of frame height) when writing FCPXML.
    #Leave as "0 0" to skip emitting adjust-transform (recommended — position the
    #compound clip on the timeline yourself instead).
    position: str = "0 0"

    #number of words per line before a line break is inserted
    wrapWords: int = 4

    #FCP Basic Title effect UID - discovered at runtime, this is the fallback path pattern
    #leave empty to force auto-discovery
    titleEffectUID: str = ""

    #connected lane in the output FCPXML gap clip
    connectedLane: int = 2

    #frames to linger after the last word in a block before cutting to next block
    lingerFrames: int = 20

    #max words per block when no FCPXML captions are present (fallback grouper)
    maxBlockWords: int = 8

    #whisper model size
    whisperModel: str = "small"


def load_style(path: str) -> CaptionStyle:
    with open(path, "r") as f:
        data = json.load(f)
    style = CaptionStyle()
    for k, v in data.items():
        if hasattr(style, k):
            setattr(style, k, v)
    return style


def save_style(style: CaptionStyle, path: str) -> None:
    with open(path, "w") as f:
        json.dump(asdict(style), f, indent=2)
