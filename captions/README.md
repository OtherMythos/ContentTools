# Animated Captions Tool

Generates animated word-highlight captions for TikTok / short-form content in Final Cut Pro.

Each caption block shows all words at once, with the currently-spoken word highlighted in yellow and past/future words in white — the standard TikTok caption style.

## Requirements

- macOS with Final Cut Pro installed
- Python 3.10+
- ffmpeg (available via `brew install ffmpeg`)
- For best performance on Apple Silicon: `mlx-whisper` (falls back to `openai-whisper`)

## Install

```bash
cd captions/
pip install -r requirements.txt
```

> On Apple Silicon, `mlx-whisper` will be used automatically for fast on-device transcription via Metal/ANE. On Intel Macs it will fall back to `openai-whisper`.

## Workflow

1. **In Final Cut Pro**: generate captions from your audio (`Edit → Auto-generate Captions`). This defines the paragraph blocks for your captions. Export the project as FCPXML (`File → Export XML…`).
2. **Export your mixed audio** as a WAV or AIFF file from FCP (`File → Share → Export File`, Master File, audio only). This is what Whisper will transcribe for word-level timestamps.
3. **Run the tool**:

```bash
python captionsTool.py audio.wav \
    --xml /path/to/project.fcpxml \
    --output captions.fcpxml
```

4. **Import back into FCP**: `File → Import → XML…`, choose `captions.fcpxml`. A new event "Animated Captions" will appear in your library. Drag the "Animated Captions" project onto your timeline as a connected clip (position it above your primary storyline). The captions will be frame-accurately positioned.

## Options

```
python captionsTool.py --help

Arguments:
  AUDIO                    Path to audio file (WAV, AIFF, MP3, etc.)

Options:
  --xml PATH               FCPXML exported from FCP (provides caption text blocks).
                           If omitted, the fallback sentence-aware grouper is used.
  -o, --output PATH        Output FCPXML path [default: captions.fcpxml]
  --style PATH             JSON style file (see --dump-style)
  --audio-offset FLOAT     Shift Whisper timestamps by N seconds [default: 0.0]
  --model TEXT             Whisper model: tiny/base/small/medium/large [default: small]
  --list-title-uids        Print discovered Basic Title .moti paths and exit
  --dump-style PATH        Save default style JSON to PATH and exit
```

## Customising Look

Dump the default style JSON, edit it, and pass it back with `--style`:

```bash
python captionsTool.py --dump-style my_style.json
# edit my_style.json
python captionsTool.py audio.wav --xml project.fcpxml --style my_style.json -o captions.fcpxml
```

Key fields in the style JSON:

| Field | Default | Description |
|-------|---------|-------------|
| `font` | `"Helvetica Neue"` | Font family name |
| `fontSize` | `72.0` | Font size in points |
| `bold` | `true` | Bold text |
| `pastColour` | `"1 1 1 1"` | RGBA for already-spoken words (white) |
| `highlightColour` | `"1 0.85 0 1"` | RGBA for current word (yellow) |
| `futureColour` | `"1 1 1 0.5"` | RGBA for upcoming words (dim white) |
| `backgroundColour` | `"0 0 0 0.8"` | RGBA for text background pill |
| `position` | `"0 -800"` | Canvas XY position (0,0 = centre; negative Y = lower) |
| `connectedLane` | `2` | Lane number in FCP timeline |
| `lingerFrames` | `20` | Extra frames after last word in a block |
| `maxBlockWords` | `8` | Max words per block (fallback grouper only) |
| `whisperModel` | `"small"` | Whisper model size |

Colours are normalised RGBA: `"R G B A"` where each channel is 0–1. For example:
- White: `"1 1 1 1"`
- Yellow: `"1 0.85 0 1"`
- Semi-transparent black: `"0 0 0 0.8"`

## Notes

- **Title effect**: the tool automatically discovers the Basic Title `.moti` file installed by Final Cut Pro. If none is found (e.g. FCP is not installed on the machine running the script), it falls back to iTT `<caption>` elements which support the same per-word styling.
- **Audio offset**: if your exported audio starts at a different point than the project timeline, use `--audio-offset` to shift Whisper timestamps by that many seconds.
- **Accuracy**: the `small` Whisper model provides a good balance of speed and accuracy on Apple Silicon. For maximum accuracy use `--model medium` or `--model large`.
