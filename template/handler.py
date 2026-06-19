import os
import re
from os.path import join

from .._infra import show_info
from ..config.config import parse_active_field
from .injector import TemplateInjector

_MEDIA_PREFIX = "_thai_reading_"
_BUNDLE_FILENAME = "_thai_reading_bundle.js"


class ThaiCssJsHandler:
    def __init__(self, mw, anki_services, path, config):
        self.mw = mw
        self.anki = anki_services
        self.path = path
        self.config = config
        self.injector = TemplateInjector(join(path, "js"))
        self.wrapperDict: dict = {}
        self._current_media_files: list[str] = []

    def updateWrapperDict(self):
        self.wrapperDict, _wrapperCheck = self.getWrapperDict()

    def get_alt_reading_type(self, note_type_name, field_name):
        if note_type_name in self.wrapperDict:
            for entries in self.wrapperDict[note_type_name]:
                if entries[1] == field_name and entries[4] != "default":
                    return entries[4]
        return False

    def noteCardFieldExists(self, data):
        models = self.anki.all_models()
        error = ""
        note = False
        card = False
        field = False
        side = False
        if data[5] in ["both", "front", "back"]:
            side = True
        for model in models:
            if model["name"] == data[2] and not note:
                note = True
                if data[3].lower() == "all":
                    card = True
                else:
                    for t in model["tmpls"]:
                        if t["name"] == data[3] and not card:
                            card = True
                for fld in model["flds"]:
                    if fld["name"] == data[4] and not field:
                        field = True
        if not note:
            return (
                False,
                'The "' + data[2] + '" note type does not exist in this profile, if this note type exists '
                "in another profile consider setting its profile setting to the appropriate profile "
                "in the Active Fields settings menu.",
            )

        if not card:
            error += 'The "' + data[3] + '" card type does not exist.\n'
        if not field:
            error += 'The "' + data[4] + '" field does not exist.\n'
        if not side:
            error += 'The last value must be "front", "back", or "both", it cannot be "' + data[5] + '"'

        if error == "":
            return True, False
        return False, error

    def fieldConflictCheck(self, item, array, dType):
        conflicts = []
        for value in array:
            valAr = value[0]
            valDType = value[1]
            if valAr == item:
                conflicts.append('In "' + valDType + '": ' + ";".join(valAr))
                conflicts.append('In "' + dType + '": ' + ";".join(item))
                return False, conflicts
            elif (
                valAr[2] == item[2]
                and (valAr[3].lower() == "all" or item[3].lower() == "all" or valAr[3] == item[3])
                and valAr[4] == item[4]
                and (valAr[5] == "both" or item[5] == "both")
            ):
                conflicts.append('In "' + valDType + '": ' + ";".join(valAr))
                conflicts.append('In "' + dType + '": ' + ";".join(item))
                return False, conflicts
        return True, True

    def getWrapperDict(self):
        wrapperDict = {}
        self.anki.all_models()
        syntaxErrors = ""
        notFoundErrors = ""
        fieldConflictErrors = ""
        alreadyIncluded = []
        for item in self.config.active_fields:
            try:
                parsed = parse_active_field(item)
            except ValueError as e:
                syntaxErrors += "\n" + str(e) + "\n"
                continue
            if self.anki.profile_name != parsed.profile and "all" != parsed.profile.lower():
                continue
            dataArray = [
                parsed.display_type,
                parsed.profile,
                parsed.note_type,
                parsed.card_type,
                parsed.field,
                parsed.side,
                parsed.reading_type,
            ]
            if dataArray[2] != "noteTypeName" and dataArray[3] != "cardTypeName" and dataArray[4] != "fieldName":
                success, errorMsg = self.noteCardFieldExists(dataArray)
                if success:
                    conflictFree, conflicts = self.fieldConflictCheck(dataArray, alreadyIncluded, dataArray[0])
                    if conflictFree:
                        if dataArray[2] not in wrapperDict:
                            alreadyIncluded.append([dataArray, dataArray[0]])
                            wrapperDict[dataArray[2]] = [
                                [dataArray[3], dataArray[4], dataArray[5], dataArray[0], dataArray[6]]
                            ]
                        else:
                            if [
                                dataArray[3],
                                dataArray[4],
                                dataArray[5],
                                dataArray[0],
                                dataArray[6],
                            ] not in wrapperDict[dataArray[2]]:
                                alreadyIncluded.append([dataArray, dataArray[0]])
                                wrapperDict[dataArray[2]].append(
                                    [dataArray[3], dataArray[4], dataArray[5], dataArray[0], dataArray[6]]
                                )
                    else:
                        fieldConflictErrors += (
                            "A conflict was found in this field pair:\n\n" + "\n".join(conflicts) + "\n\n"
                        )
                else:
                    notFoundErrors += (
                        '"' + item + '" in "ActiveFields" has the following error(s):\n' + errorMsg + "\n\n"
                    )

        if syntaxErrors != "":
            show_info(
                "The following entries have incorrect syntax:\n"
                "Please make sure the format is as follows:\n"
                '"displayType;profileName;noteTypeName;cardTypeName;fieldName;side(;ReadingType)".\n' + syntaxErrors,
                level="err",
            )
            return (wrapperDict, False)
        if notFoundErrors != "":
            show_info(
                'The following entries in "ActiveFields" could not be found:\n\n' + notFoundErrors,
                level="err",
            )
            return (wrapperDict, False)
        if fieldConflictErrors != "":
            show_info(
                "You have entries that point to the same field and the same side. "
                "Please make sure that a field and side combination does not conflict.\n\n" + fieldConflictErrors,
                level="err",
            )
            return (wrapperDict, False)
        return (wrapperDict, True)

    def refreshConfig(self, config=None):
        if config is not None:
            self.config = config

    def checkProfile(self):
        if self.anki.profile_name in self.config.profiles or (
            "all" in self.config.profiles or "All" in self.config.profiles
        ):
            return True
        return False

    def fieldExists(self, field):
        models = self.anki.all_models()
        for model in models:
            for fld in model["flds"]:
                if field == fld["name"] or field.lower() == "none":
                    return True
        return False

    def checkReadingType(self):
        rType = self.config.reading_type
        if rType not in ["rtgs", "ipa"]:
            show_info(
                'The "' + rType + '" value in the "ReadingType" configuration is incorrect. '
                'The value must be "rtgs" or "ipa".',
                level="err",
            )
            return False
        return True

    def _media_dir(self) -> str | None:
        if self.mw and self.mw.col:
            return self.mw.col.media.dir()
        return None

    def _clean_orphaned_media_files(self, keep: set[str]) -> None:
        media_dir = self._media_dir()
        if not media_dir:
            return
        try:
            for fname in os.listdir(media_dir):
                if fname.startswith(_MEDIA_PREFIX) and fname not in keep:
                    fpath = os.path.join(media_dir, fname)
                    try:
                        os.remove(fpath)
                    except OSError:
                        pass
        except OSError:
            pass

    def _write_combined_js_file(self) -> str | None:
        media_dir = self._media_dir()
        if not media_dir:
            return None

        content = self.injector.get_combined_js(
            reading_type=self.config.reading_type,
            thai_tones=self.config.thai_tones,
            font_size=self.config.font_size,
            rtgs_tone_style=self.config.rtgs_tone_style,
        )
        filepath = os.path.join(media_dir, _BUNDLE_FILENAME)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        self._clean_orphaned_media_files({_BUNDLE_FILENAME})
        return _BUNDLE_FILENAME

    def write_js_file(self) -> str | None:
        return self._write_combined_js_file()

    def injectWrapperElements(self):
        if not self.checkProfile():
            return
        if not self.config.auto_css_js_generation:
            return
        readingCheck = self.checkReadingType()
        self.wrapperDict, wrapperCheck = self.getWrapperDict()

        js_fn = self._write_combined_js_file()

        models = self.anki.all_models()
        for model in models:
            model["css"] = self.injector.remove("thai_css", model["css"])

            if model["name"] in self.wrapperDict:
                for idx, t in enumerate(model["tmpls"]):
                    modelDict = self.wrapperDict[model["name"]]
                    if self.templateInModelDict(t["name"], modelDict):
                        templateDict = self.templateFilteredDict(modelDict, t["name"])
                        t["qfmt"], t["afmt"] = self.cleanFieldWrappers(
                            t["qfmt"], t["afmt"], model["flds"], templateDict
                        )
                        t["qfmt"] = self.injector.remove("thai_js", t["qfmt"])
                        t["afmt"] = self.injector.remove("thai_js", t["afmt"])
                        t["qfmt"] = self.injector.remove("thai_js_file", t["qfmt"])
                        t["afmt"] = self.injector.remove("thai_js_file", t["afmt"])
                        for data in templateDict:
                            if data[2] == "both" or data[2] == "front":
                                t["qfmt"] = self.injector.overwrite_wrapper(t["qfmt"], data[1], data[3], data[4])
                                t["qfmt"] = self.injector.inject(
                                    "wrapper", t["qfmt"], field=data[1], display_type=data[3], reading_type=data[4]
                                )
                            if data[2] == "both" or data[2] == "back":
                                t["afmt"] = self.injector.overwrite_wrapper(t["afmt"], data[1], data[3], data[4])
                                t["afmt"] = self.injector.inject(
                                    "wrapper", t["afmt"], field=data[1], display_type=data[3], reading_type=data[4]
                                )
                        has_default_front = False
                        has_default_back = False
                        for field_info in model["flds"]:
                            field_name = field_info["name"]
                            sides = self.fieldInTemplateDict(field_name, templateDict)
                            if not sides:
                                continue
                            if "both" not in sides and "front" not in sides:
                                new_q = self.injector.inject(
                                    "wrapper", t["qfmt"], field=field_name, display_type="thai", reading_type="default"
                                )
                                if new_q != t["qfmt"]:
                                    has_default_front = True
                                    t["qfmt"] = new_q
                            if "both" not in sides and "back" not in sides:
                                new_a = self.injector.inject(
                                    "wrapper", t["afmt"], field=field_name, display_type="thai", reading_type="default"
                                )
                                if new_a != t["afmt"]:
                                    has_default_back = True
                                    t["afmt"] = new_a

                        has_front = len(templateDict) > 0 or has_default_front
                        has_back = len(templateDict) > 0 or has_default_back
                        if js_fn:
                            if has_front:
                                t["qfmt"] = self.injector.inject("thai_js_file", t["qfmt"], filename=js_fn)
                            if has_back:
                                t["afmt"] = self.injector.inject("thai_js_file", t["afmt"], filename=js_fn)
                    else:
                        t["qfmt"] = self.injector.remove("wrapper", t["qfmt"])
                        t["afmt"] = self.injector.remove("wrapper", t["afmt"])

            else:
                for t in model["tmpls"]:
                    t["qfmt"] = self.injector.remove("thai_js_file", self.injector.remove("wrapper", t["qfmt"]))
                    t["afmt"] = self.injector.remove("thai_js_file", self.injector.remove("wrapper", t["afmt"]))
            self.anki.save_model(model)
        return readingCheck and wrapperCheck

    def templateInModelDict(self, template, modelDict):
        for entries in modelDict:
            if entries[0] == template or entries[0].lower() == "all":
                return True
        return False

    def templateFilteredDict(self, modelDict, template):
        return list(filter(lambda data, tname=template: data[0] == tname or data[0].lower() == "all", modelDict))

    def fieldInTemplateDict(self, field, templateDict):
        sides = []
        for entries in templateDict:
            if entries[1] == field:
                sides.append(entries[2])
        return sides

    def cleanFieldWrappers(self, front, back, fields, templateDict):
        for field in fields:
            sides = self.fieldInTemplateDict(field["name"], templateDict)
            pattern = (
                r'<div reading-type="[^>]+?" display-type="[^>]+?" class="wrapped-thai">'
                r"({{(?:[^:}]+:)?" + field["name"] + r"}})"
                r"</div>"
            )

            if len(sides) > 0:
                if "both" not in sides and "front" not in sides:
                    front = re.sub(pattern, r"\g<1>", front)
                    front = self.injector.remove("thai_js", front)
                if "both" not in sides and "back" not in sides:
                    back = re.sub(pattern, r"\g<1>", back)
                    back = self.injector.remove("thai_js", back)
            else:
                front = re.sub(pattern, r"\g<1>", front)
                back = re.sub(pattern, r"\g<1>", back)
                front = self.injector.remove("thai_js", front)
                back = self.injector.remove("thai_js", back)
        return front, back
