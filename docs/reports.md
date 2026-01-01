# Reports Reference

| Module              | Main function          | Key columns                       |
|---------------------|------------------------|-----------------------------------|
| `report_timing`     | `timing_rows()`        | index, start, end, duration       |
| `report_cps`        | `cps_rows()`           | index, text, cps, status          |
| `report_overlap`    | `overlap_rows()`       | index_a, index_b, overlap_sec     |
| `report_gaps`       | `gap_rows()`           | index_a, index_b, gap_sec         |
| `report_words`      | `word_rows()`          | word, count, percentage           |
| `report_speakers`   | `speaker_rows()`       | speaker, cue_count, duration      |
| `report_duration`   | `duration_rows()`      | bucket, count, percentage         |
| `report_readspeed`  | `readspeed_rows()`     | index, cps, wps, conformant       |
| `report_sync`       | `sync_rows()`          | index, issue_type, detail         |
| `report_conformance`| `conformance_rows()`   | index, check, passed, detail      |
| `report_styles`     | `style_rows()`         | style, cue_count, percentage      |
| `report_density`    | `density_rows()`       | interval_start, cue_count, chars  |
