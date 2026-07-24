"""Fetch a paper's title + abstract from the arXiv API.

We deliberately use the abstract (not the full PDF): the central claim almost
always lives there, it is small and reliable to fetch, and results are cached in
Redis so repeat submissions of the same paper are instant.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

import httpx

from .. import store

_ARXIV_API = "http://export.arxiv.org/api/query"
_ATOM = {"a": "http://www.w3.org/2005/Atom"}
_ID_RE = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")


def normalize_id(ref: str) -> str:
    """Accept a bare id, a versioned id, or any arxiv.org URL."""
    ref = ref.strip()
    match = _ID_RE.search(ref)
    if match:
        return match.group(1)
    # Older-style ids like "math/0211159"
    match = re.search(r"([a-z\-]+/\d{7})", ref)
    if match:
        return match.group(1)
    return ref


def fetch_text(ref: str) -> str:
    arxiv_id = normalize_id(ref)
    cache_key = f"arxiv:{arxiv_id}"
    cached = store.cache_get(cache_key)
    if cached:
        return cached

    resp = httpx.get(_ARXIV_API, params={"id_list": arxiv_id}, timeout=30.0)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    entry = root.find("a:entry", _ATOM)
    if entry is None:
        raise ValueError(f"No arXiv entry found for '{arxiv_id}'.")

    title_el = entry.find("a:title", _ATOM)
    summary_el = entry.find("a:summary", _ATOM)
    if title_el is None or summary_el is None or not (summary_el.text or "").strip():
        raise ValueError(f"arXiv entry for '{arxiv_id}' is missing a title/abstract.")

    title = " ".join((title_el.text or "").split())
    summary = (summary_el.text or "").strip()
    text = f"Title: {title}\n\narXiv:{arxiv_id}\n\nAbstract:\n{summary}"

    store.cache_set(cache_key, text)
    return text
