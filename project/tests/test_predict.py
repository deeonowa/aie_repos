
import pytest

from src.features.text import clean_description


def test_clean_description_collapses_whitespace():
    assert clean_description("  hello   world  ") == "hello world"


def test_clean_description_truncates():
    long_text = "a" * 100
    assert len(clean_description(long_text, max_length=50)) == 50
