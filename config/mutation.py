"""ConfigMutation — deep module for config validation, transformation, persistence.

Provides ConfigMutation (Protocol) as the seam for config editing.
LiveConfigMutation is the production adapter. ModelCatalog replaces the leaky colArray global.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from .config import AddonConfig, parse_active_field

# ── Model discovery (replaces colArray global) ─────────────────


@dataclass(frozen=True)
class ModelInfo:
    card_types: list[str]
    fields: list[str]


class ModelCatalog(Protocol):
    def profile_names(self) -> Sequence[str]: ...
    def model_names(self, profile: str) -> Sequence[str]: ...
    def card_type_names(self, profile: str, model: str) -> Sequence[str]: ...
    def field_names(self, profile: str, model: str) -> Sequence[str]: ...


class LiveModelCatalog:
    """Opens collections for all profiles and caches note type / card type / field info.

    Mirrors the logic from main.py's loadAllProfileInformation.
    """

    def __init__(self, mw) -> None:
        from anki import Collection

        self._profiles: dict[str, dict[str, ModelInfo]] = {}
        for prof in mw.pm.profiles():
            try:
                if prof == mw.pm.name:
                    note_types = mw.col.models.all()
                else:
                    cpath = os.path.join(mw.pm.base, prof, "collection.anki2")
                    temp_col = Collection(cpath)
                    note_types = temp_col.models.all()
                    temp_col.close()
                model_dict: dict[str, ModelInfo] = {}
                for note in note_types:
                    model_dict[note["name"]] = ModelInfo(
                        card_types=[ct["name"] for ct in note["tmpls"]],
                        fields=[f["name"] for f in note["flds"]],
                    )
                self._profiles[prof] = model_dict
            except Exception:
                pass

    def profile_names(self) -> Sequence[str]:
        return list(self._profiles.keys())

    def model_names(self, profile: str) -> Sequence[str]:
        return list(self._profiles.get(profile, {}).keys())

    def card_type_names(self, profile: str, model: str) -> Sequence[str]:
        info = self._profiles.get(profile, {}).get(model)
        return info.card_types if info else []

    def field_names(self, profile: str, model: str) -> Sequence[str]:
        info = self._profiles.get(profile, {}).get(model)
        return info.fields if info else []


# ── ConfigDelta (typed partial config) ─────────────────────────

_KEY_MAP: dict[str, str] = {
    "profiles": "Profiles",
    "reading_type": "ReadingType",
    "bopomofo_tones_to_number": "BopomofoTonesToNumber",
    "hanzi_conversion": "hanziConversion",
    "reading_conversion": "readingConversion",
    "auto_css_js_generation": "AutoCssJsGeneration",
    "simplified_field": "SimplifiedField",
    "traditional_field": "TraditionalField",
    "simp_trad_field": "SimpTradField",
    "traditional_icons": "traditionalIcons",
    "font_size": "FontSize",
    "cantonese_tones": "CantoneseTones123456",
    "mandarin_tones": "MandarinTones12345",
    "use_file_references": "UseFileReferences",
    "active_fields": "ActiveFields",
}


@dataclass(frozen=True)
class ConfigDelta:
    profiles: list[str] | None = None
    reading_type: str | None = None
    bopomofo_tones_to_number: bool | None = None
    hanzi_conversion: str | None = None
    reading_conversion: str | None = None
    auto_css_js_generation: bool | None = None
    simplified_field: str | None = None
    traditional_field: str | None = None
    simp_trad_field: str | None = None
    traditional_icons: bool | None = None
    font_size: int | None = None
    use_file_references: bool | None = None
    cantonese_tones: tuple[str, ...] | None = None
    mandarin_tones: tuple[str, ...] | None = None
    active_fields: tuple[str, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for py_name, json_key in _KEY_MAP.items():
            val = getattr(self, py_name)
            if val is not None:
                d[json_key] = list(val) if isinstance(val, tuple) else val
        return d

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ConfigDelta:
        key_rev = {v: k for k, v in _KEY_MAP.items()}
        kw: dict[str, Any] = {}
        for json_key, val in raw.items():
            py_name = key_rev.get(json_key)
            if py_name is None:
                continue
            if isinstance(val, list):
                val = tuple(val)
            kw[py_name] = val
        return cls(**kw)


# ── Validation types ───────────────────────────────────────────


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str


class ConfigValidationError(ValueError):
    def __init__(self, errors: list[ValidationError]) -> None:
        self._errors = errors
        super().__init__("; ".join(e.message for e in errors))

    @property
    def errors(self) -> list[ValidationError]:
        return self._errors


# ── ConfigMutation (seam) ──────────────────────────────────────


class ConfigMutation(Protocol):
    def save_config(self, delta: ConfigDelta) -> AddonConfig:
        """Validate → merge → persist → return updated AddonConfig.
        Raises ConfigValidationError on invalid delta.
        """

    def validate(self, delta: ConfigDelta) -> list[ValidationError]:
        """Pre-flight validation; never persists."""


# ── Valid value sets ───────────────────────────────────────────

_VALID_READING_TYPES = frozenset({"pinyin", "bopomofo", "jyutping"})
_VALID_HANZI_CONVERSIONS = frozenset({"None", "Simplified", "Traditional"})
_VALID_READING_CONVERSIONS = frozenset({"None", "Pinyin", "Bopomofo"})


# ── Production adapter ─────────────────────────────────────────


class LiveConfigMutation:
    def __init__(
        self,
        anki_services: Any,
        addon_module_name: str,
        config: AddonConfig,
        defaults: dict[str, Any],
        model_catalog: ModelCatalog | None = None,
    ) -> None:
        self._anki = anki_services
        self._addon_module_name = addon_module_name
        self._config = config
        self._defaults = defaults
        self._catalog = model_catalog

    def validate(self, delta: ConfigDelta) -> list[ValidationError]:
        errors: list[ValidationError] = []
        self._validate_delta(delta, errors)
        return errors

    def save_config(self, delta: ConfigDelta) -> AddonConfig:
        errors = self.validate(delta)
        if errors:
            raise ConfigValidationError(errors)
        merged = dict(self._defaults)
        merged.update(self._config._raw)
        merged.update(delta.to_dict())
        self._anki.write_config(self._addon_module_name, merged)
        new_config = AddonConfig(_raw=merged)
        self._config = new_config
        return new_config

    def _validate_delta(self, delta: ConfigDelta, errors: list[ValidationError]) -> None:
        if delta.reading_type is not None and delta.reading_type not in _VALID_READING_TYPES:
            errors.append(
                ValidationError(
                    "reading_type",
                    f"invalid reading type: {delta.reading_type!r}; must be one of {sorted(_VALID_READING_TYPES)}",
                )
            )
        if delta.hanzi_conversion is not None and delta.hanzi_conversion not in _VALID_HANZI_CONVERSIONS:
            errors.append(
                ValidationError(
                    "hanzi_conversion",
                    f"must be one of {sorted(_VALID_HANZI_CONVERSIONS)}, got {delta.hanzi_conversion!r}",
                )
            )
        if delta.reading_conversion is not None and delta.reading_conversion not in _VALID_READING_CONVERSIONS:
            errors.append(
                ValidationError(
                    "reading_conversion",
                    f"must be one of {sorted(_VALID_READING_CONVERSIONS)}, got {delta.reading_conversion!r}",
                )
            )
        if delta.font_size is not None and not (1 <= delta.font_size <= 200):
            errors.append(
                ValidationError(
                    "font_size",
                    f"must be between 1 and 200, got {delta.font_size}",
                )
            )
        if delta.mandarin_tones is not None and len(delta.mandarin_tones) != 5:
            errors.append(
                ValidationError(
                    "mandarin_tones",
                    f"expected 5 colors, got {len(delta.mandarin_tones)}",
                )
            )
        if delta.cantonese_tones is not None and len(delta.cantonese_tones) != 6:
            errors.append(
                ValidationError(
                    "cantonese_tones",
                    f"expected 6 colors, got {len(delta.cantonese_tones)}",
                )
            )
        if delta.active_fields is not None:
            for i, raw in enumerate(delta.active_fields):
                try:
                    parsed = parse_active_field(raw)
                except ValueError as e:
                    errors.append(
                        ValidationError(
                            "active_fields",
                            f"active_fields[{i}]: {e}",
                        )
                    )
                    continue
                if self._catalog is not None:
                    self._validate_af_against_catalog(parsed, i, errors)

    def _validate_af_against_catalog(
        self,
        af: Any,
        i: int,
        errors: list[ValidationError],
    ) -> None:
        assert self._catalog is not None
        if af.profile != "all" and af.profile not in self._catalog.profile_names():
            errors.append(
                ValidationError(
                    "active_fields",
                    f"active_fields[{i}]: profile {af.profile!r} not found",
                )
            )
