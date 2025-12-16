# Glossary

| Term | Definition |
|------|-----------|
| **CPS** | Characters Per Second — the number of visible characters divided by the cue duration. A key readability metric. |
| **Cue** | A single subtitle entry with start time, end time, and text content. Also called a "subtitle event" or "dialogue line". |
| **Track** | An ordered sequence of cues. A subtitle file typically contains one track. |
| **SRT** | SubRip Text — the most widely used subtitle format. Uses comma-separated milliseconds (`00:01:23,456`). |
| **VTT** | Web Video Text Tracks (WebVTT) — the HTML5 standard for web subtitles. Uses dots (`00:01:23.456`). |
| **ASS/SSA** | Advanced SubStation Alpha — a feature-rich format supporting styles, colours, and positioning. Common in anime fansubs. |
| **Timecode** | A time position in the format `HH:MM:SS,mmm` or `HH:MM:SS.mmm`. Internally stored as float seconds. |
| **Overlap** | When two cues have intersecting time ranges, meaning both would display simultaneously. |
| **Gap** | The silence between consecutive cues, measured in seconds. |
| **Speaker** | An optional attribution indicating who is speaking. Format varies: `JOHN:`, SSA `Name` field, etc. |
| **Style** | Formatting information for a cue — font, colour, size, position, alignment. Primarily used in ASS format. |
| **Conformance** | Adherence to an industry standard's subtitle guidelines (Netflix, broadcast, etc.). |
| **Preset** | A named set of conformance parameters (max CPS, line limits, timing constraints). |
| **Frame** | A single video frame. At 24fps, one frame = ~41.7ms. Timecodes can be snapped to frame boundaries. |
| **BOM** | Byte Order Mark — a Unicode character (`\ufeff`) sometimes found at the start of text files. subcue strips it automatically. |
| **WPS** | Words Per Second — an alternative readability metric to CPS. |
| **Dialogue** | A cue explicitly attributed to a speaker. Used for interview or multi-character content. |
| **Marker** | A non-subtitle time point, used for chapter boundaries or scene changes. |
| **Metadata** | File-level information: title, language, author, frame rate, encoding. |
| **Project** | A container for multiple tracks, useful for multi-language subtitle projects. |
| **Diagnostic** | An automated check that identifies issues (overlaps, high CPS, short duration, etc.). |
| **Health score** | A 0-100 quality rating based on the number and severity of diagnostics. |
| **Batch** | Processing multiple subtitle files in one operation. |
| **Query** | A composable, fluent API for filtering and sorting cues within a track. |
| **Segmentation** | Breaking a long text block into multiple timed cues that fit within display constraints. |
| **Normalisation** | Cleaning subtitle text: fixing encoding, standardising quotes/dashes, removing OCR artefacts. |
| **Deduplication** | Detecting and removing cues with identical or near-identical text. |
| **Reconciliation** | Comparing two versions of the same track and identifying differences. |
| **Word wrap** | Intelligently breaking subtitle text into lines that fit within a maximum character width. |
| **Interpolation** | Estimating values between known data points, used for timing smoothing and trend analysis. |
| **Binning** | Grouping numeric values into ranges (buckets) for distribution analysis. |
| **Timeline coverage** | The fraction of total video time that has subtitle text displayed. |
| **Density** | The number of cues or characters within a time interval. High density = busy subtitles. |
| **Snap to frame** | Aligning a timecode to the nearest video frame boundary for precise synchronisation. |
| **Scale** | Multiplying all timecodes by a factor, used for frame rate conversion (e.g. 25fps to 24fps). |
| **Shift** | Adding a constant offset to all timecodes, used to fix synchronisation issues. |
| **Plugin** | A registered handler function that extends subcue's functionality. |

## Abbreviations

| Abbr | Meaning |
|------|---------|
| CPS | Characters Per Second |
| WPS | Words Per Second |
| WPM | Words Per Minute |
| FPS | Frames Per Second |
| SRT | SubRip Text |
| VTT | Web Video Text Tracks |
| ASS | Advanced SubStation Alpha |
| SSA | SubStation Alpha |
| BOM | Byte Order Mark |
| CJK | Chinese, Japanese, Korean |
| RTL | Right-To-Left (writing direction) |
| WCAG | Web Content Accessibility Guidelines |
| a11y | Accessibility (a + 11 letters + y) |
| NFC | Unicode Normal Form Composed |
| NFKD | Unicode Normal Form Compatibility Decomposition |
| OCR | Optical Character Recognition |
| SDH | Subtitles for the Deaf and Hard of Hearing |
| CC | Closed Captions |
| HI | Hearing Impaired |
| TC | Timecode |
| ms | Milliseconds |
