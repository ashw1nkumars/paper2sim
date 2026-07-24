"""arXiv id normalization, including the older physics-style identifiers."""

import pytest

from services.ingest import arxiv


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # New-style ids (math, CS, physics all share this scheme).
        ("2301.01234", "2301.01234"),
        ("2301.01234v3", "2301.01234"),
        ("https://arxiv.org/abs/1706.03762", "1706.03762"),
        ("arXiv:1706.03762", "1706.03762"),
        # Older physics-style ids with a subject class.
        ("quant-ph/0201082", "quant-ph/0201082"),
        ("cond-mat/9910446", "cond-mat/9910446"),
        ("physics/0503066", "physics/0503066"),
        ("hep-th/9711200", "hep-th/9711200"),
    ],
)
def test_normalize_id(raw, expected):
    assert arxiv.normalize_id(raw) == expected
