from typing import Any, Protocol

from anki.collection import Collection
from anki.models import NoteType
from anki.notes import Note


class AnkiServices(Protocol):
    @property
    def col(self) -> Collection: ...

    @property
    def profile_name(self) -> str: ...

    @property
    def addon_folder(self) -> str: ...

    def all_models(self) -> list[NoteType]: ...

    def model_by_name(self, name: str) -> NoteType | None: ...

    def field_names(self, model: NoteType) -> list[str]: ...

    def save_model(self, model: NoteType) -> None: ...

    def get_note(self, nid: int) -> Note: ...

    def checkpoint(self, name: str) -> None: ...

    def reset(self) -> None: ...

    def process_events(self) -> None: ...

    def progress_finish(self) -> None: ...

    def progress_timer(self, ms: int, callback, repeat: bool) -> None: ...

    def write_config(self, addon_module_name: str, config: dict[str, Any]) -> None: ...

    def config_defaults(self, addon_dir: str) -> dict[str, Any]: ...


class LiveAnkiServices:
    def __init__(self, mw):
        self._mw = mw

    @property
    def col(self) -> Collection:
        return self._mw.col

    @property
    def profile_name(self) -> str:
        return self._mw.pm.name

    @property
    def addon_folder(self) -> str:
        return self._mw.pm.addonFolder()

    def all_models(self) -> list[NoteType]:
        return self._mw.col.models.all()

    def model_by_name(self, name: str) -> NoteType | None:
        return self._mw.col.models.by_name(name)

    def field_names(self, model: NoteType) -> list[str]:
        return self._mw.col.models.field_names(model)

    def save_model(self, model: NoteType) -> None:
        self._mw.col.models.save(model)

    def get_note(self, nid: int) -> Note:
        return self._mw.col.get_note(nid)

    def checkpoint(self, name: str) -> None:
        self._mw.checkpoint(name)

    def reset(self) -> None:
        self._mw.reset()

    def process_events(self) -> None:
        self._mw.app.processEvents()

    def progress_finish(self) -> None:
        self._mw.progress.finish()

    def progress_timer(self, ms: int, callback, repeat: bool) -> None:
        self._mw.progress.timer(ms, callback, repeat)

    def write_config(self, addon_module_name: str, config: dict[str, Any]) -> None:
        self._mw.addonManager.writeConfig(addon_module_name, config)

    def config_defaults(self, addon_dir: str) -> dict[str, Any]:
        return self._mw.addonManager.addonConfigDefaults(addon_dir)
