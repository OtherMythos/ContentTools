"""
Generate a standalone FCPXML containing animated word-highlight caption titles.

Output structure:
  <fcpxml>
    <resources>
      <format />           — copied from source project
      <effect />           — Basic Title .moti reference
      <media />            — compound clip containing the gap + title clips
    </resources>
    <library>
      <event name="Animated Captions">
        <ref-clip />        — exposes the compound clip in the FCP event browser
      </event>
    </library>
  </fcpxml>

The compound clip (<media>) contains:
  <sequence>
    <spine>
      <gap duration="TOTAL">
        <!-- one <title> per word-reveal state, hanging as connected clips -->
        <title lane="1" offset="WORD_START" duration="WORD_DURATION">
          <adjust-transform position="X Y"/>
          <text>
            <text-style ref="ts_past">past words </text-style>
            <text-style ref="ts_cur">CURRENT</text-style>
            <text-style ref="ts_fut"> future words</text-style>
          </text>
          ...
        </title>
      </gap>
    </spine>
  </sequence>

Title effect UID:
  Uses FCP's built-in '...' prefix shorthand (same convention as other built-in
  effects exported by FCP itself, e.g. Directional transition).
  Override via style.titleEffectUID if needed.
"""

import glob
import uuid
from datetime import datetime
from typing import List, Optional
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

from style import CaptionStyle
from wordAligner import AlignedBlock
from fcpxmlParser import ProjectFormat
from transcribe import WordSegment


#FCP uses '...' as a shorthand prefix for its bundled effects base path.
#This matches exactly how FCP itself writes effect UIDs when exporting FCPXML,
#e.g. the Directional transition in the source: .../Transitions.localized/...
_BASIC_TITLE_UID = ".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"

#Search paths for --list-title-uids (informational only)
_BASIC_TITLE_GLOBS = [
    "/Applications/Final Cut Pro.app/Contents/PlugIns/MediaProviders/MotionEffect.fxp/Contents/Resources/PETemplates.localized/Titles.localized/**/*Basic Title.moti",
    "/Library/Application Support/ProApps/Effects/Titles.localized/**/*Basic Title*.moti",
]


def discover_title_uids() -> List[str]:
    """Return full filesystem paths to any Basic Title .moti files (informational)."""
    found: List[str] = []
    for pattern in _BASIC_TITLE_GLOBS:
        found.extend(glob.glob(pattern, recursive=True))
    return found


def _resolve_title_uid(style: CaptionStyle) -> str:
    """Return the effect UID to use; always succeeds — falls back to built-in shorthand."""
    if style.titleEffectUID:
        return style.titleEffectUID
    return _BASIC_TITLE_UID


def _ticks(seconds: float, tps: int = 3000) -> str:
    """Convert seconds to FCPXML rational time string using tps ticks/sec."""
    ticks = round(seconds * tps)
    return f"{ticks}/{tps}s"


def _make_id() -> str:
    return "ts_" + uuid.uuid4().hex[:8]


def generate(
    blocks: List[AlignedBlock],
    project_format: ProjectFormat,
    style: CaptionStyle,
    audio_duration: float,
    output_path: str,
) -> None:
    title_uid = _resolve_title_uid(style)
    tps = project_format.ticksPerSecond

    #frames/second from frameDuration "N/TPS s"
    parts = project_format.frameDuration.rstrip("s").split("/")
    frames_per_tick = int(parts[0]) if len(parts) == 2 else 100
    fps = tps / frames_per_tick  #e.g. 3000/100 = 30

    linger_seconds = style.lingerFrames / fps
    duration_str = _ticks(audio_duration, tps)
    compound_uid = str(uuid.uuid4()).upper()
    mod_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S +0000")

    print(f"[gen] Using title effect UID: {title_uid}")

    root = ET.Element("fcpxml", version="1.13")

    #---- resources ----
    resources = ET.SubElement(root, "resources")

    ET.SubElement(resources, "format",
        id="r1",
        frameDuration=project_format.frameDuration,
        width=str(project_format.width),
        height=str(project_format.height),
        colorSpace=project_format.colorSpace,
    )

    effect_id = "r_title"
    ET.SubElement(resources, "effect",
        id=effect_id,
        name="Basic Title",
        uid=title_uid,
    )

    #compound clip: <media> in resources, exposes as draggable clip in FCP browser
    media = ET.SubElement(resources, "media",
        id="r_compound",
        name="Animated Captions",
        uid=compound_uid,
        modDate=mod_date,
    )
    sequence = ET.SubElement(media, "sequence",
        format="r1",
        duration=duration_str,
        tcStart="0s",
        tcFormat="NDF",
        audioLayout="stereo",
        audioRate="48k",
    )
    spine = ET.SubElement(sequence, "spine")
    gap = ET.SubElement(spine, "gap",
        name="Gap",
        offset="0s",
        start="0s",
        duration=duration_str,
    )

    #emit one title element per word-reveal state per block
    for b_idx, block in enumerate(blocks):
        if not block.words:
            continue
        #cap linger so the last title of this block never overlaps the next block
        next_block_start: Optional[float] = None
        for nb in blocks[b_idx + 1:]:
            if nb.words:
                next_block_start = nb.words[0].start
                break
        _emit_block(gap, block, style, tps, linger_seconds, fps, effect_id, project_format.height, next_block_start)

    #---- library: event exposes the compound clip in the FCP browser ----
    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", name="Animated Captions")
    ET.SubElement(event, "ref-clip",
        ref="r_compound",
        offset="0s",
        duration=duration_str,
        name="Animated Captions",
    )

    #serialise with pretty-printing
    raw = ET.tostring(root, encoding="unicode")
    dom = minidom.parseString(raw)
    pretty = dom.toprettyxml(indent="  ", encoding=None)

    #minidom adds an extra xml declaration line; keep only the first one and add DOCTYPE
    lines = pretty.splitlines()
    output_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!DOCTYPE fcpxml>",
    ]
    for line in lines:
        if line.strip().startswith("<?xml"):
            continue
        output_lines.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"[gen] Written: {output_path}")


def _emit_block(
    parent: ET.Element,
    block: AlignedBlock,
    style: CaptionStyle,
    tps: int,
    linger_seconds: float,
    fps: float,
    effect_id: str,
    frame_height: int,
    next_block_start: Optional[float] = None,
) -> None:
    words = block.words
    n = len(words)

    for i, word in enumerate(words):
        #offset = absolute start of this word on the timeline
        offset_secs = word.start

        #duration = from this word's start to the next word's start (or end + linger)
        if i < n - 1:
            dur_secs = words[i + 1].start - word.start
        else:
            raw_end = word.end + linger_seconds
            #cap so the last title ends no later than the next block's first word
            if next_block_start is not None:
                raw_end = min(raw_end, next_block_start)
            dur_secs = raw_end - word.start

        #never produce zero/negative duration
        dur_secs = max(dur_secs, 1.0 / fps)

        _emit_title_clip(parent, words, i, offset_secs, dur_secs, style, tps, effect_id, frame_height)


def _build_text_runs(words: List[WordSegment], current_idx: int, style: CaptionStyle):
    """
    Returns (past_text, sep_before_current, current_text, future_text).
    A newline is inserted every style.wrapWords words; all other separators are spaces.
    Words are paged in windows of (maxLines * wrapWords); the window containing
    current_idx is shown and indices are renormalised to that window.
    """
    wrap_every = style.wrapWords

    #apply page-based windowing when maxLines is set
    if style.maxLines > 0:
        page_size = style.maxLines * wrap_every
        page = current_idx // page_size
        window_start = page * page_size
        words = words[window_start: window_start + page_size]
        current_idx = current_idx - window_start

    def sep(i: int) -> str:
        if i == 0:
            return ''
        return '\n' if (i % wrap_every == 0) else ' '

    past = ''.join(sep(i) + words[i].word.strip() for i in range(current_idx))
    sep_cur = sep(current_idx)
    current = words[current_idx].word.strip()
    future = ''.join(sep(i) + words[i].word.strip() for i in range(current_idx + 1, len(words)))
    return past, sep_cur, current, future


def _emit_title_clip(
    parent: ET.Element,
    words: List[WordSegment],
    idx: int,
    offset_secs: float,
    dur_secs: float,
    style: CaptionStyle,
    tps: int,
    effect_id: str,
    frame_height: int,
) -> None:
    past, sep_cur, current, future = _build_text_runs(words, idx, style)

    title = ET.SubElement(parent, "title",
        ref=effect_id,
        lane=str(style.connectedLane),
        offset=_ticks(offset_secs, tps),
        start="0s",
        duration=_ticks(dur_secs, tps),
        name=current,
    )

    #DTD-required order: param* → text* → text-style-def* → adjust-transform?

    #1. text content
    text_elem = ET.SubElement(title, "text")

    face_str = style.fontFace if style.fontFace else ("Bold" if style.bold else "Regular")

    id_past = _make_id()
    id_cur = _make_id()
    id_fut = _make_id()

    #past run (may be empty); trailing sep_cur provides the space/newline before current
    if past:
        ts_past = ET.SubElement(text_elem, "text-style", ref=id_past)
        ts_past.text = past + sep_cur
    elif sep_cur:
        #no past text but a separator precedes current (shouldn't occur in practice)
        current = sep_cur + current

    #current word
    ts_cur = ET.SubElement(text_elem, "text-style", ref=id_cur)
    ts_cur.text = current

    #future run (may be empty); future already starts with its own separator
    if future:
        ts_fut = ET.SubElement(text_elem, "text-style", ref=id_fut)
        ts_fut.text = future

    #2. style definitions
    if past:
        ddef = ET.SubElement(title, "text-style-def", id=id_past)
        ET.SubElement(ddef, "text-style",
            font=style.font,
            fontSize=str(style.fontSize),
            fontFace=face_str,
            fontColor=style.pastColour,
            backgroundColor=style.backgroundColour,
            strokeColor=style.outlineColour,
            strokeWidth=str(-style.outlineWidth) if style.outlineWidth else "0",
            alignment=style.alignment,
        )

    ddef_cur = ET.SubElement(title, "text-style-def", id=id_cur)
    ET.SubElement(ddef_cur, "text-style",
        font=style.font,
        fontSize=str(round(style.fontSize * style.highlightScale, 4)),
        fontFace=face_str,
        fontColor=style.highlightColour,
        backgroundColor=style.backgroundColour,
        strokeColor=style.outlineColour,
        strokeWidth=str(-style.outlineWidth) if style.outlineWidth else "0",
        alignment=style.alignment,
    )

    if future:
        ddef_fut = ET.SubElement(title, "text-style-def", id=id_fut)
        ET.SubElement(ddef_fut, "text-style",
            font=style.font,
            fontSize=str(style.fontSize),
            fontFace=face_str,
            fontColor=style.futureColour,
            backgroundColor=style.backgroundColour,
            strokeColor=style.outlineColour,
            strokeWidth=str(-style.outlineWidth) if style.outlineWidth else "0",
            alignment=style.alignment,
        )

    #3. position adjustment (must come after text-style-def per DTD)
    #skip entirely when position is 0 0 — FCP defaults to centre anyway
    px_vals = style.position.split()
    pct_x = float(px_vals[0]) / frame_height * 100
    pct_y = float(px_vals[1]) / frame_height * 100
    if pct_x != 0.0 or pct_y != 0.0:
        ET.SubElement(title, "adjust-transform", position=f"{pct_x:.4f} {pct_y:.4f}")


def _emit_caption_clip(
    parent: ET.Element,
    words: List[WordSegment],
    idx: int,
    offset_secs: float,
    dur_secs: float,
    style: CaptionStyle,
    tps: int,
) -> None:
    """
    Fallback: emit an iTT <caption> element with per-word text-style runs.
    Used when no Basic Title .moti is found.
    """
    past, current, future = _build_text_runs(words, idx, style)

    caption = ET.SubElement(parent, "caption",
        lane=str(style.connectedLane),
        offset=_ticks(offset_secs, tps),
        start="3600s",
        duration=_ticks(dur_secs, tps),
        name=current,
        role="iTT?captionFormat=ITT.en-US",
    )

    text_elem = ET.SubElement(caption, "text", placement="bottom")

    face_str = style.fontFace if style.fontFace else ("Bold" if style.bold else "Regular")
    id_past = _make_id()
    id_cur = _make_id()
    id_fut = _make_id()

    if past:
        ts = ET.SubElement(text_elem, "text-style", ref=id_past)
        ts.text = past + " "
    ts = ET.SubElement(text_elem, "text-style", ref=id_cur)
    ts.text = current
    if future:
        ts = ET.SubElement(text_elem, "text-style", ref=id_fut)
        ts.text = " " + future

    if past:
        ddef = ET.SubElement(caption, "text-style-def", id=id_past)
        ET.SubElement(ddef, "text-style",
            font=style.font,
            fontSize=str(style.fontSize),
            fontFace=face_str,
            fontColor=style.pastColour,
            backgroundColor=style.backgroundColour,
            strokeColor=style.outlineColour,
            strokeWidth=str(-style.outlineWidth) if style.outlineWidth else "0",
        )

    ddef_cur = ET.SubElement(caption, "text-style-def", id=id_cur)
    ET.SubElement(ddef_cur, "text-style",
        font=style.font,
        fontSize=str(style.fontSize),
        fontFace=face_str,
        fontColor=style.highlightColour,
        backgroundColor=style.backgroundColour,
        strokeColor=style.outlineColour,
        strokeWidth=str(-style.outlineWidth) if style.outlineWidth else "0",
    )

    if future:
        ddef_fut = ET.SubElement(caption, "text-style-def", id=id_fut)
        ET.SubElement(ddef_fut, "text-style",
            font=style.font,
            fontSize=str(style.fontSize),
            fontFace=face_str,
            fontColor=style.futureColour,
            backgroundColor=style.backgroundColour,
            strokeColor=style.outlineColour,
            strokeWidth=str(-style.outlineWidth) if style.outlineWidth else "0",
        )
