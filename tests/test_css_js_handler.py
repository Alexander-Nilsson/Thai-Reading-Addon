import os
from unittest.mock import patch

import pytest
from conftest import import_css_js_handler

from config.config import AddonConfig

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
