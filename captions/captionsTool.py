"""
captionsTool.py — Animated word-highlight caption generator for Final Cut Pro.

Usage:
  python captionsTool.py audio.wav --xml project.fcpxml --output captions.fcpxml
  python captionsTool.py audio.wav --output captions.fcpxml  (no XML = fallback grouper)
  python captionsTool.py --list-title-uids
  python captionsTool.py audio.wav --dump-style style.json   (save default style to edit)
"""

import sys
import os

#add this directory to path so sibling modules resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

import click

from style import CaptionStyle, load_style, save_style
from transcribe import transcribe
from fcpxmlParser import parse, CaptionBlock, ProjectFormat
from wordAligner import align, fallback_group
from fcpxmlGen import generate, discover_title_uids


def _get_audio_duration(audio_path: str) -> float:
    """Return duration in seconds via ffprobe/ffmpeg."""
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", audio_path],
            capture_output=True, text=True, check=True
        )
        import json
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            dur = stream.get("duration")
            if dur:
                return float(dur)
    except Exception:
        pass

    #ffmpeg stderr fallback (same as fc.py)
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", audio_path],
            stderr=subprocess.PIPE, text=True
        )
        for line in result.stderr.splitlines():
            if "Duration" in line:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = map(float, dur_str.split(":"))
                return h * 3600 + m * 60 + s
    except Exception:
        pass

    raise RuntimeError(f"Could not determine duration of {audio_path}")


@click.command()
@click.argument("audio", required=False, type=click.Path(exists=True))
@click.option("--xml", "fcpxml_path", default=None, type=click.Path(exists=True),
              help="Exported FCPXML from Final Cut Pro (provides caption text blocks).")
@click.option("--output", "-o", default="captions.fcpxml", show_default=True,
              help="Path for the generated output FCPXML.")
@click.option("--style", "style_path", default=None, type=click.Path(),
              help="JSON style file (see --dump-style to generate one).")
@click.option("--audio-offset", default=0.0, show_default=True,
              help="Shift all Whisper timestamps by this many seconds (e.g. if audio starts mid-project).")
@click.option("--model", "whisper_model", default=None,
              help="Whisper model size (tiny/base/small/medium/large). Overrides style file.")
@click.option("--list-title-uids", is_flag=True, default=False,
              help="Print discovered Basic Title .moti paths and exit.")
@click.option("--dump-style", "dump_style_path", default=None, type=click.Path(),
              help="Save default style JSON to PATH and exit.")
def main(audio, fcpxml_path, output, style_path, audio_offset, whisper_model,
         list_title_uids, dump_style_path):
    #---- utility exits ----
    if list_title_uids:
        from fcpxmlGen import _BASIC_TITLE_UID
        click.echo(f"Built-in UID (used by default): {_BASIC_TITLE_UID}")
        uids = discover_title_uids()
        if uids:
            click.echo("Discovered Basic Title .moti files on this machine:")
            for u in uids:
                click.echo(f"  {u}")
        else:
            click.echo("No .moti files found via filesystem search (built-in UID will still be used).")
        return

    if dump_style_path:
        save_style(CaptionStyle(), dump_style_path)
        click.echo(f"Default style written to: {dump_style_path}")
        return

    if not audio:
        raise click.UsageError("AUDIO argument is required unless using --list-title-uids or --dump-style.")

    #---- load style ----
    if style_path:
        style = load_style(style_path)
        click.echo(f"[tool] Loaded style from: {style_path}")
    else:
        style = CaptionStyle()

    if whisper_model:
        style.whisperModel = whisper_model

    #---- parse source FCPXML ----
    caption_blocks = []
    project_format = ProjectFormat()

    if fcpxml_path:
        click.echo(f"[tool] Parsing FCPXML: {fcpxml_path}")
        caption_blocks, project_format = parse(fcpxml_path)
        click.echo(f"[tool] Found {len(caption_blocks)} caption block(s) in FCPXML")

    #---- transcribe ----
    click.echo(f"[tool] Transcribing audio: {audio} (model={style.whisperModel})")
    whisper_words = transcribe(audio, model=style.whisperModel)

    if audio_offset != 0.0:
        from transcribe import WordSegment
        whisper_words = [
            WordSegment(word=w.word, start=w.start + audio_offset, end=w.end + audio_offset)
            for w in whisper_words
        ]
        click.echo(f"[tool] Applied audio offset: {audio_offset:+.2f}s")

    click.echo(f"[tool] Transcribed {len(whisper_words)} word(s)")

    #---- align / group ----
    if caption_blocks:
        click.echo("[tool] Aligning caption blocks to Whisper words...")
        aligned_blocks = align(caption_blocks, whisper_words)
    else:
        click.echo(f"[tool] No captions in FCPXML — using fallback grouper (max {style.maxBlockWords} words/block)")
        aligned_blocks = fallback_group(whisper_words, max_block_words=style.maxBlockWords)

    total_words = sum(len(b.words) for b in aligned_blocks)
    click.echo(f"[tool] Producing {len(aligned_blocks)} block(s), {total_words} aligned word(s)")

    #---- get audio duration for gap clip ----
    audio_duration = _get_audio_duration(audio)
    click.echo(f"[tool] Audio duration: {audio_duration:.3f}s")

    #---- generate FCPXML ----
    click.echo(f"[tool] Generating: {output}")
    generate(
        blocks=aligned_blocks,
        project_format=project_format,
        style=style,
        audio_duration=audio_duration,
        output_path=output,
    )

    click.echo("[tool] Done. Import the output FCPXML into Final Cut Pro and drag")
    click.echo("       the 'Animated Captions' project over your timeline as a connected clip.")


if __name__ == "__main__":
    main()
