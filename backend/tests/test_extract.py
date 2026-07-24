"""Code extraction must tolerate plain, unclosed, and unfenced LLM responses."""

from app.pipeline.tasks import extract_code


def test_plain_fenced_block():
    assert extract_code("```python\nprint(1)\n```") == "print(1)"


def test_unclosed_fence_from_truncation():
    # A truncated response whose closing ``` never arrived.
    assert extract_code("```python\nimport numpy\nprint(1)") == "import numpy\nprint(1)"


def test_no_fence_returns_text():
    assert extract_code("print(1)") == "print(1)"
