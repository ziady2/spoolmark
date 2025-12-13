# Subtitle Formats

## SRT (SubRip)

```srt
1
00:00:01,000 --> 00:00:04,000
Hello, world!

2
00:00:05,500 --> 00:00:08,200
This is the second subtitle.
```

## VTT (WebVTT)

```vtt
WEBVTT

1
00:00:01.000 --> 00:00:04.000
Hello, world!

2
00:00:05.500 --> 00:00:08.200
This is the second subtitle.
```

## ASS (Advanced SubStation Alpha)

```ass
[Script Info]
Title: Example
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Hello, world!
```

## TXT (subcue line format)

Each non-comment line contains a start time, an end time, and text. The final
separator before the text is optional, but including `|` is recommended.

```text
00:00:01.000 --> 00:00:04.000 | Hello, world!
00:00:05.500 --> 00:00:08.200 | This is the second subtitle.
```

Blank lines and lines beginning with `#` are ignored.

## JSON

```json
{
  "name": "Track",
  "cues": [
    {"index": 1, "start": 1.0, "end": 4.0, "text": "Hello, world!"},
    {"index": 2, "start": 5.5, "end": 8.2, "text": "Second subtitle."}
  ]
}
```
