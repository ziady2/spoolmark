"""Project model – multi-track container."""

from __future__ import annotations

from typing import Any

from .errors import NotFoundError
from .track import Track


class Project:
    __slots__ = ("name", "tracks", "fps", "created")

    def __init__(
        self,
        name: str = "Untitled",
        *,
        tracks: list[Track] | None = None,
        fps: float = 24.0,
        created: str = "",
    ) -> None:
        self.name = name.strip()
        self.tracks: list[Track] = list(tracks or [])
        self.fps = fps
        self.created = created.strip()

    def __repr__(self) -> str:
        return f"Project({self.name!r}, tracks={len(self.tracks)})"

    def __len__(self) -> int:
        return len(self.tracks)

    def add_track(self, track: Track) -> "Project":
        new = self.copy()
        new.tracks.append(track.copy())
        return new

    def remove_track(self, name: str) -> "Project":
        new_tracks = [t.copy() for t in self.tracks if t.name != name]
        if len(new_tracks) == len(self.tracks):
            raise NotFoundError("track", name)
        return Project(self.name, tracks=new_tracks, fps=self.fps, created=self.created)

    def get_track(self, name: str) -> Track:
        for t in self.tracks:
            if t.name == name:
                return t
        raise NotFoundError("track", name)

    def track_names(self) -> list[str]:
        return [t.name for t in self.tracks]

    def total_cues(self) -> int:
        return sum(len(t) for t in self.tracks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fps": self.fps,
            "created": self.created,
            "tracks": [t.to_dict() for t in self.tracks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        tracks = [Track.from_dict(d) for d in data.get("tracks", [])]
        return cls(
            name=str(data.get("name", "")),
            tracks=tracks,
            fps=float(data.get("fps", 24.0)),
            created=str(data.get("created", "")),
        )

    def copy(self) -> "Project":
        return Project(
            self.name, tracks=[t.copy() for t in self.tracks], fps=self.fps, created=self.created
        )

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fps": self.fps,
            "track_count": len(self.tracks),
            "total_cues": self.total_cues(),
        }
