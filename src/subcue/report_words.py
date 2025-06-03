"""Word and character frequency analysis report.

Analyses word usage frequency across all cues and provides
per-cue character and word statistics.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List

from .math_utils import mean, median, round_to, safe_divide
from .track import Track

_WORD_RE = re.compile(r"[\w']+", re.UNICODE)


def word_frequency(track: Track, top_n: int = 50) -> List[dict]:
    """Return the most common words across all cues.

    Keys
    ----
    rank : int
        1-based rank by frequency.
    word : str
        The word (lowercased).
    count : int
        Number of occurrences.
    pct : float
        Percentage of total word count.
    cue_count : int
        Number of distinct cues containing this word.
    """
    counter: Counter[str] = Counter()
    cue_counts: Counter[str] = Counter()
    for cue in track.cues:
        words = _WORD_RE.findall(cue.plain_text.lower())
        counter.update(words)
        cue_counts.update(set(words))
    total = sum(counter.values()) or 1
    result: List[dict] = []
    for rank, (word, count) in enumerate(counter.most_common(top_n), start=1):
        result.append(
            {
                "rank": rank,
                "word": word,
                "count": count,
                "pct": round_to(count / total * 100),
                "cue_count": cue_counts[word],
            }
        )
    return result


def char_stats(track: Track) -> List[dict]:
    """Character and word counts per cue.

    Keys
    ----
    index : int
        Cue sequence number.
    char_count : int
        Number of characters in plain text.
    word_count : int
        Number of words.
    line_count : int
        Number of lines.
    chars_per_line : float
        Average characters per line.
    words_per_line : float
        Average words per line.
    longest_word : str
        Longest word in the cue.
    """
    result: List[dict] = []
    for cue in track.sorted_cues():
        words = _WORD_RE.findall(cue.plain_text)
        longest = max(words, key=len) if words else ""
        lc = cue.line_count if cue.line_count > 0 else 1
        result.append(
            {
                "index": cue.index,
                "char_count": cue.char_count,
                "word_count": cue.word_count,
                "line_count": cue.line_count,
                "chars_per_line": round_to(safe_divide(cue.char_count, lc)),
                "words_per_line": round_to(safe_divide(cue.word_count, lc)),
                "longest_word": longest,
            }
        )
    return result


def vocabulary_summary(track: Track) -> List[dict]:
    """High-level vocabulary statistics for the track.

    Keys
    ----
    track_name : str
        Name of the track.
    total_words : int
        Total word count across all cues.
    unique_words : int
        Number of distinct words.
    avg_words_per_cue : float
        Mean words per cue.
    median_words_per_cue : float
        Median words per cue.
    avg_chars_per_cue : float
        Mean characters per cue.
    median_chars_per_cue : float
        Median characters per cue.
    lexical_diversity : float
        Ratio of unique words to total words.
    """
    all_words: List[str] = []
    words_per_cue: List[float] = []
    chars_per_cue: List[float] = []
    for cue in track.cues:
        ws = _WORD_RE.findall(cue.plain_text.lower())
        all_words.extend(ws)
        words_per_cue.append(float(len(ws)))
        chars_per_cue.append(float(cue.char_count))
    total = len(all_words) or 1
    unique = len(set(all_words))
    return [
        {
            "track_name": track.name,
            "total_words": len(all_words),
            "unique_words": unique,
            "avg_words_per_cue": round_to(mean(words_per_cue)),
            "median_words_per_cue": round_to(median(words_per_cue)),
            "avg_chars_per_cue": round_to(mean(chars_per_cue)),
            "median_chars_per_cue": round_to(median(chars_per_cue)),
            "lexical_diversity": round_to(safe_divide(unique, total)),
        }
    ]
