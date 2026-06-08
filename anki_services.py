from typing import Any, Protocol

from anki.collection import Collection
from anki.models import FieldDict, NoteType
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

    def new_model(self, name: str) -> NoteType: ...

    def new_field(self, name: str) -> FieldDict: ...

    def add_field(self, model: NoteType, field: FieldDict) -> None: ...

    def new_template(self, name: str) -> Any: ...

    def add_template(self, model: NoteType, template: Any) -> None: ...

    def add_model(self, model: NoteType) -> NoteType: ...

    def media_dir(self) -> str: ...

    def checkpoint(self, name: str) -> None: ...

    def reset(self) -> None: ...

    def process_events(self) -> None: ...

    def progress_finish(self) -> None: ...

    def progress_timer(self, ms: int, callback, repeat: bool) -> None: ...


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
        return self._mw.col.models.fieldNames(model)

    def save_model(self, model: NoteType) -> None:
        self._mw.col.models.save(model)

    def get_note(self, nid: int) -> Note:
        return self._mw.col.getNote(nid)

    def new_model(self, name: str) -> NoteType:
        return self._mw.col.models.new(name)

    def new_field(self, name: str) -> FieldDict:
        return self._mw.col.models.newField(name)

    def add_field(self, model: NoteType, field: FieldDict) -> None:
        self._mw.col.models.addField(model, field)

    def new_template(self, name: str) -> Any:
        return self._mw.col.models.newTemplate(name)

    def add_template(self, model: NoteType, template: Any) -> None:
        self._mw.col.models.addTemplate(model, template)

    def add_model(self, model: NoteType) -> NoteType:
        self._mw.col.models.add(model)
        return model

    def media_dir(self) -> str:
        return self._mw.col.media.dir()

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
