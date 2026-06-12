import os
from unittest.mock import patch

import pytest

from config.config import AddonConfig
from conftest import import_css_js_handler

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_config(**overrides):
    raw = {
        "MandarinTones12345": ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"],
        "CantoneseTones123456": ["#E60000", "#E68A00", "#00802B", "#005CE6", "#AC00E6", "gray"],
        "FontSize": 75,
        "ReadingType": "pinyin",
        "AutoCssJsGeneration": True,
        "ActiveFields": [],
        "Profiles": ["all"],
        "hanziConversion": "None",
        "readingConversion": "None",
        "SimplifiedField": "Simplified;overwrite",
        "TraditionalField": "Traditional;overwrite",
        "SimpTradField": "Traditional,Variant;overwrite",
        "traditionalIcons": False,
        "BopomofoTonesToNumber": True,
    }
    raw.update(overrides)
    return AddonConfig(_raw=raw)


class _MockAnkiServices:
    def __init__(self, profile_name="User 1"):
        self._profile_name = profile_name
        self._models = []

    @property
    def profile_name(self):
        return self._profile_name

    @property
    def col(self):
        return None

    @property
    def addon_folder(self):
        return "/tmp/addons21/chinese_reading"

    def all_models(self):
        return self._models


@pytest.fixture(scope="module")
def CSSJSHandler():
    return import_css_js_handler()


@pytest.fixture
def handler(CSSJSHandler):
    return CSSJSHandler(mw=None, anki_services=_MockAnkiServices(), path=ROOT, config=_make_config())


@pytest.fixture
def handler_custom_font(CSSJSHandler):
    return CSSJSHandler(
        mw=None,
        anki_services=_MockAnkiServices(),
        path=ROOT,
        config=_make_config(FontSize=100),
    )


class TestTemplateInModelDict:
    def test_matching_template(self, handler):
        model_dict = [["Card 1", "Field1", "front", "hover", "pinyin"]]
        assert handler.templateInModelDict("Card 1", model_dict) is True

    def test_non_matching_template(self, handler):
        model_dict = [["Card 1", "Field1", "front", "hover", "pinyin"]]
        assert handler.templateInModelDict("Card 2", model_dict) is False


class TestTemplateFilteredDict:
    def test_filters_by_template(self, handler):
        model_dict = [
            ["Card 1", "Field1", "front", "hover", "pinyin"],
            ["Card 1", "Field2", "back", "coloredhover", "bopomofo"],
            ["Card 2", "Field1", "both", "reading", "pinyin"],
        ]
        result = handler.templateFilteredDict(model_dict, "Card 1")
        assert len(result) == 2
        assert result[0][0] == "Card 1"
        assert result[1][0] == "Card 1"


class TestCheckProfile:
    def test_all_profile_matches(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(Profiles=["all"]),
        )
        assert handler.checkProfile() is True

    def test_matching_named_profile(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices("User 1"),
            path=ROOT,
            config=_make_config(Profiles=["User 1"]),
        )
        assert handler.checkProfile() is True

    def test_non_matching_profile(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices("User 1"),
            path=ROOT,
            config=_make_config(Profiles=["Other User"]),
        )
        assert handler.checkProfile() is False


class TestCheckReadingType:
    def test_valid_pinyin(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="pinyin"),
        )
        assert handler.checkReadingType() is True

    def test_valid_bopomofo(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="bopomofo"),
        )
        assert handler.checkReadingType() is True

    def test_valid_jyutping(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="jyutping"),
        )
        assert handler.checkReadingType() is True

    def test_invalid_type(self, CSSJSHandler):
        handler = CSSJSHandler(
            mw=None,
            anki_services=_MockAnkiServices(),
            path=ROOT,
            config=_make_config(ReadingType="invalid"),
        )
        import chinese_reading_addon_test.template.handler as _mod

        with patch.object(_mod, "show_info"):
            assert handler.checkReadingType() is False


class TestCleanFieldWrappers:
    def test_removes_wrapper_from_front_when_not_in_sides(self, handler):
        template_dict = [["Card 1", "MyField", "back", "hover", "pinyin"]]
        fields = [{"name": "MyField"}]
        front = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        back = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        new_front, _new_back = handler.cleanFieldWrappers(front, back, fields, template_dict)
        assert "{{MyField}}" in new_front
        assert "wrapped-chinese" not in new_front

    def test_removes_wrapper_from_front_and_back_when_no_sides(self, handler):
        template_dict = [["Card 1", "OtherField", "front", "hover", "pinyin"]]
        fields = [{"name": "MyField"}]
        front = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        back = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        new_front, new_back = handler.cleanFieldWrappers(front, back, fields, template_dict)
        assert "wrapped-chinese" not in new_front
        assert "wrapped-chinese" not in new_back

    def test_keeps_wrapper_on_front_when_side_is_front(self, handler_custom_font):
        template_dict = [["Card 1", "MyField", "front", "hover", "pinyin"]]
        fields = [{"name": "MyField"}]
        front = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        back = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        new_front, new_back = handler_custom_font.cleanFieldWrappers(front, back, fields, template_dict)
        assert "wrapped-chinese" in new_front
        assert "wrapped-chinese" not in new_back

    def test_keeps_wrapper_on_both_when_side_is_both(self, handler_custom_font):
        template_dict = [["Card 1", "MyField", "both", "hover", "pinyin"]]
        fields = [{"name": "MyField"}]
        front = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        back = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        new_front, new_back = handler_custom_font.cleanFieldWrappers(front, back, fields, template_dict)
        assert "wrapped-chinese" in new_front
        assert "wrapped-chinese" in new_back

    def test_handles_edit_filter_on_front_when_side_is_front(self, handler_custom_font):
        template_dict = [["Card 1", "MyField", "front", "hover", "pinyin"]]
        fields = [{"name": "MyField"}]
        front = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{edit:MyField}}</div>'
        back = '<div reading-type="pinyin" display-type="hover" class="wrapped-chinese">{{MyField}}</div>'
        new_front, new_back = handler_custom_font.cleanFieldWrappers(front, back, fields, template_dict)
        assert "wrapped-chinese" in new_front
        assert "{{edit:MyField}}" in new_front
        assert "wrapped-chinese" not in new_back


# ── Default Hanzi wrapper tests ────────────────────────────────


class _HanziMockServices:
    """Minimal mock that simulates models with fields for injectWrapperElements."""

    def __init__(self, models, profile_name="User 1"):
        self._models = models
        self._profile_name = profile_name

    @property
    def profile_name(self):
        return self._profile_name

    @property
    def col(self):
        return None

    @property
    def addon_folder(self):
        return "/tmp/addons21/chinese_reading"

    def all_models(self):
        return self._models

    def save_model(self, model):
        pass

    def model_by_name(self, name):
        for m in self._models:
            if m["name"] == name:
                return m
        return None

    def field_names(self, model):
        return [f["name"] for f in model["flds"]]

    def get_note(self, nid):
        return None

    def checkpoint(self, name):
        pass

    def reset(self):
        pass

    def process_events(self):
        pass

    def progress_finish(self):
        pass

    def progress_timer(self, ms, callback, repeat):
        pass

    def write_config(self, addon_module_name, config):
        pass

    def config_defaults(self, addon_dir):
        return {}


class TestDefaultHanzi:
    def test_configured_field_gets_explicit_wrapper_unconfigured_left_alone(self, CSSJSHandler):
        models = [
            {
                "name": "Basic",
                "flds": [{"name": "ConfiguredField"}, {"name": "DefaultField"}],
                "tmpls": [
                    {
                        "name": "Card 1",
                        "qfmt": "{{ConfiguredField}} {{DefaultField}}",
                        "afmt": "",
                    }
                ],
                "css": "",
            }
        ]
        svc = _HanziMockServices(models)
        config = _make_config(ActiveFields=["hover;User 1;Basic;Card 1;ConfiguredField;front;pinyin"])
        handler = CSSJSHandler(mw=None, anki_services=svc, path=HERE, config=config)
        handler.injectWrapperElements()
        tmpl = models[0]["tmpls"][0]
        assert 'display-type="hover"' in tmpl["qfmt"]
        # DefaultField has no ActiveFields entry — should NOT be wrapped
        assert "{{DefaultField}}" in tmpl["qfmt"]
        assert "{{ConfiguredField}}" in tmpl["qfmt"]
        # Only ConfiguredField gets wrapped; DefaultField stays bare
        assert tmpl["qfmt"].count('reading-type="') == 1

    def test_configured_field_preserves_explicit_display_type(self, CSSJSHandler):
        models = [
            {
                "name": "Basic",
                "flds": [{"name": "Expression"}, {"name": "Reading"}],
                "tmpls": [
                    {
                        "name": "Card 1",
                        "qfmt": "{{Expression}} {{Reading}}",
                        "afmt": "{{Reading}}",
                    }
                ],
                "css": "",
            }
        ]
        svc = _HanziMockServices(models)
        config = _make_config(ActiveFields=["coloredhover;User 1;Basic;Card 1;Expression;front;pinyin"])
        handler = CSSJSHandler(mw=None, anki_services=svc, path=HERE, config=config)
        handler.injectWrapperElements()
        tmpl = models[0]["tmpls"][0]
        assert 'display-type="coloredhover"' in tmpl["qfmt"]
        # Reading has no config at all — left unwrapped on both sides
        assert "{{Reading}}" in tmpl["qfmt"]
        assert "{{Reading}}" in tmpl["afmt"]
        # Only Expression on front gets a wrapper
        assert tmpl["qfmt"].count('reading-type="') == 1
        # Back has no configured fields — no wrappers at all
        assert tmpl["afmt"].count('reading-type="') == 0

    def test_all_fields_configured_no_default_hanzi(self, CSSJSHandler):
        models = [
            {
                "name": "Basic",
                "flds": [{"name": "Expression"}, {"name": "Reading"}],
                "tmpls": [
                    {
                        "name": "Card 1",
                        "qfmt": "{{Expression}} {{Reading}}",
                        "afmt": "",
                    }
                ],
                "css": "",
            }
        ]
        svc = _HanziMockServices(models)
        config = _make_config(
            ActiveFields=[
                "hover;User 1;Basic;Card 1;Expression;front;pinyin",
                "reading;User 1;Basic;Card 1;Reading;front;jyutping",
            ]
        )
        handler = CSSJSHandler(mw=None, anki_services=svc, path=HERE, config=config)
        handler.injectWrapperElements()
        tmpl = models[0]["tmpls"][0]
        assert 'display-type="hover"' in tmpl["qfmt"]
        assert 'display-type="reading"' in tmpl["qfmt"]
        # No hanzi wrappers needed since all fields have config
        assert 'display-type="hanzi"' not in tmpl["qfmt"]


# ── Media file injection tests ────────────────────────────────


class _MediaMockServices:
    """Mock that simulates a real collection with a media dir."""

    def __init__(self, tmpdir, profile_name="User 1"):
        self._profile_name = profile_name
        self._models = []
        self._media_dir = tmpdir

    @property
    def profile_name(self):
        return self._profile_name

    @property
    def col(self):
        class FakeCol:
            def __init__(self, media_dir):
                self._media = _FakeMedia(media_dir)

            @property
            def media(self):
                return self._media

        return FakeCol(self._media_dir)

    @property
    def addon_folder(self):
        return "/tmp/addons21/chinese_reading"

    def all_models(self):
        return self._models

    def save_model(self, model):
        pass

    def model_by_name(self, name):
        for m in self._models:
            if m["name"] == name:
                return m
        return None

    def field_names(self, model):
        return [f["name"] for f in model["flds"]]

    def get_note(self, nid):
        return None

    def checkpoint(self, name):
        pass

    def reset(self):
        pass

    def process_events(self):
        pass

    def progress_finish(self):
        pass

    def progress_timer(self, ms, callback, repeat):
        pass

    def write_config(self, addon_module_name, config):
        pass

    def config_defaults(self, addon_dir):
        return {}


class _FakeMedia:
    def __init__(self, media_dir):
        self.dir_path = media_dir

    def dir(self):
        return self.dir_path


def _make_media_config(**overrides):
    raw = {
        "MandarinTones12345": ["#E60000", "#E68A00", "#00802B", "#005CE6", "gray"],
        "CantoneseTones123456": ["#E60000", "#E68A00", "#00802B", "#005CE6", "#AC00E6", "gray"],
        "FontSize": 75,
        "ReadingType": "pinyin",
        "AutoCssJsGeneration": True,
        "ActiveFields": [
            "hover;all;Basic;Card 1;Front;front;pinyin",
        ],
        "Profiles": ["all"],
        "hanziConversion": "None",
        "readingConversion": "None",
        "SimplifiedField": "Simplified;overwrite",
        "TraditionalField": "Traditional;overwrite",
        "SimpTradField": "Traditional,Variant;overwrite",
        "traditionalIcons": False,
        "BopomofoTonesToNumber": True,
    }
    raw.update(overrides)
    return AddonConfig(_raw=raw)


class TestMediaFileInjection:
    def test_writes_css_file(self, tmpdir, CSSJSHandler):
        svc = _MediaMockServices(str(tmpdir))
        handler = CSSJSHandler(
            mw=svc,
            anki_services=svc,
            path=HERE,
            config=_make_media_config(),
        )
        svc._models = [
            {
                "name": "Basic",
                "flds": [{"name": "Front"}],
                "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{BackSide}}"}],
                "css": "",
            }
        ]

        result = handler.injectWrapperElements(use_file_references=True)
        assert result is True
        # CSS file should exist
        files = os.listdir(str(tmpdir))
        css_files = [f for f in files if f.startswith("_chinese_reading_") and f.endswith(".css")]
        assert len(css_files) == 1

    def test_writes_js_file(self, tmpdir, CSSJSHandler):
        svc = _MediaMockServices(str(tmpdir))
        handler = CSSJSHandler(
            mw=svc,
            anki_services=svc,
            path=HERE,
            config=_make_media_config(),
        )
        svc._models = [
            {
                "name": "Basic",
                "flds": [{"name": "Front"}],
                "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{BackSide}}"}],
                "css": "",
            }
        ]

        result = handler.injectWrapperElements(use_file_references=True)
        assert result is True
        files = os.listdir(str(tmpdir))
        js_files = [f for f in files if f.startswith("_chinese_reading_") and f.endswith(".js")]
        assert len(js_files) == 1

    def test_injects_css_link_in_template(self, tmpdir, CSSJSHandler):
        svc = _MediaMockServices(str(tmpdir))
        handler = CSSJSHandler(
            mw=svc,
            anki_services=svc,
            path=HERE,
            config=_make_media_config(),
        )
        svc._models = [
            {
                "name": "Basic",
                "flds": [{"name": "Front"}],
                "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{BackSide}}"}],
                "css": "",
            }
        ]

        handler.injectWrapperElements(use_file_references=True)
        model = svc._models[0]
        tmpl = model["tmpls"][0]
        assert "###CHINESE READING CSS FILE START###" not in model["css"]
        assert "###CHINESE READING CSS FILE START###" in tmpl["qfmt"]
        assert '<link rel="stylesheet" href="_chinese_reading_' in tmpl["qfmt"]

    def test_injects_script_ref_in_template(self, tmpdir, CSSJSHandler):
        svc = _MediaMockServices(str(tmpdir))
        handler = CSSJSHandler(
            mw=svc,
            anki_services=svc,
            path=HERE,
            config=_make_media_config(),
        )
        svc._models = [
            {
                "name": "Basic",
                "flds": [{"name": "Front"}],
                "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{BackSide}}"}],
                "css": "",
            }
        ]

        handler.injectWrapperElements(use_file_references=True)
        tmpl = svc._models[0]["tmpls"][0]
        assert "###CHINESE READING JS FILE START###" in tmpl["qfmt"]
        assert '<script src="_chinese_reading_' in tmpl["qfmt"]

    def test_wrapper_still_injected_in_file_mode(self, tmpdir, CSSJSHandler):
        svc = _MediaMockServices(str(tmpdir))
        handler = CSSJSHandler(
            mw=svc,
            anki_services=svc,
            path=HERE,
            config=_make_media_config(),
        )
        svc._models = [
            {
                "name": "Basic",
                "flds": [{"name": "Front"}],
                "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": "{{BackSide}}"}],
                "css": "",
            }
        ]

        handler.injectWrapperElements(use_file_references=True)
        tmpl = svc._models[0]["tmpls"][0]
        assert 'class="wrapped-chinese"' in tmpl["qfmt"]
        assert 'display-type="hover"' in tmpl["qfmt"]

    def test_file_mode_handles_edit_filter(self, tmpdir, CSSJSHandler):
        svc = _MediaMockServices(str(tmpdir))
        handler = CSSJSHandler(
            mw=svc,
            anki_services=svc,
            path=HERE,
            config=_make_media_config(),
        )
        svc._models = [
            {
                "name": "Basic",
                "flds": [{"name": "Front"}],
                "tmpls": [{"name": "Card 1", "qfmt": "{{edit:Front}}", "afmt": ""}],
                "css": "",
            }
        ]

        handler.injectWrapperElements(use_file_references=True)
        tmpl = svc._models[0]["tmpls"][0]
        assert 'class="wrapped-chinese"' in tmpl["qfmt"]
        assert "{{edit:Front}}" in tmpl["qfmt"]

    def test_cleanup_orphaned_files(self, tmpdir, CSSJSHandler):
        svc = _MediaMockServices(str(tmpdir))
        handler = CSSJSHandler(
            mw=svc,
            anki_services=svc,
            path=HERE,
            config=_make_media_config(),
        )
        svc._models = [
            {
                "name": "Basic",
                "flds": [{"name": "Front"}],
                "tmpls": [{"name": "Card 1", "qfmt": "{{Front}}", "afmt": ""}],
                "css": "",
            }
        ]

        # Create some orphaned files
        with open(os.path.join(str(tmpdir), "_chinese_reading_orphan.css"), "w") as f:
            f.write("/* orphan */")
        with open(os.path.join(str(tmpdir), "_chinese_reading_orphan.js"), "w") as f:
            f.write("// orphan")

        handler.injectWrapperElements(use_file_references=True)

        files = os.listdir(str(tmpdir))
        orphan_css = [f for f in files if f == "_chinese_reading_orphan.css"]
        orphan_js = [f for f in files if f == "_chinese_reading_orphan.js"]
        assert len(orphan_css) == 0
        assert len(orphan_js) == 0
