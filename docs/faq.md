# FAQ

**Q: Does subcue need any external dependencies?**
A: No. Everything uses the Python standard library only.

**Q: What subtitle formats are supported?**
A: SRT (SubRip), VTT (WebVTT), ASS/SSA (Advanced SubStation Alpha), JSON, and plain text.

**Q: What is CPS?**
A: Characters Per Second — the number of visible characters divided by the cue duration. A common guideline is max 20-25 CPS.

**Q: How do I shift all timecodes?**
A: Use `subcue shift 2.5 movie.srt` to shift by 2.5 seconds. Negative values shift earlier.

**Q: Can subcue merge multiple subtitle files?**
A: Yes — use `subcue merge file1.srt file2.srt` or the `merge` module programmatically.
