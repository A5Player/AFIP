"""Atomic JSON repository for reusable AFIP profiles."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .models import CustomProfile

class ProfileRepository:
    def __init__(self, path: str | Path = "runtime/profiles/profiles.json") -> None:
        self.path = Path(path)

    def _read(self) -> dict[str, Any]:
        if not self.path.exists(): return {"active_profile_id": "", "profiles": {}, "history": {}}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return {"active_profile_id": str(data.get("active_profile_id", "")), "profiles": dict(data.get("profiles", {})), "history": dict(data.get("history", {}))}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        temp.replace(self.path)

    def list(self, include_archived: bool = False) -> tuple[CustomProfile, ...]:
        profiles = [CustomProfile.from_mapping(v, version=int(v.get("version", 1))) for v in self._read()["profiles"].values()]
        return tuple(sorted((p for p in profiles if include_archived or not p.archived), key=lambda p: (not p.active, p.profile_name.lower())))

    def get(self, profile_id: str) -> CustomProfile | None:
        raw = self._read()["profiles"].get(profile_id)
        return CustomProfile.from_mapping(raw, version=int(raw.get("version", 1))) if raw else None

    def save(self, profile: CustomProfile) -> CustomProfile:
        data = self._read(); previous = data["profiles"].get(profile.profile_id)
        version = int(previous.get("version", 0)) + 1 if previous else 1
        saved = CustomProfile.from_mapping({**profile.as_dict(), "version": version}, version=version)
        if previous: data["history"].setdefault(profile.profile_id, []).append(previous)
        if saved.active:
            for pid, raw in data["profiles"].items(): raw["active"] = pid == saved.profile_id
            data["active_profile_id"] = saved.profile_id
        data["profiles"][saved.profile_id] = saved.as_dict(); self._write(data); return saved

    def delete(self, profile_id: str) -> None:
        data = self._read(); raw = data["profiles"].pop(profile_id, None)
        if raw: data["history"].setdefault(profile_id, []).append(raw)
        if data["active_profile_id"] == profile_id: data["active_profile_id"] = ""
        self._write(data)

    def history(self, profile_id: str) -> tuple[dict[str, Any], ...]:
        return tuple(self._read()["history"].get(profile_id, []))
