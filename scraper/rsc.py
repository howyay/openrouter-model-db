"""Extract model data from OpenRouter RSC (React Server Components) flight payloads.

OpenRouter model pages embed rich JSON data in Next.js RSC flight payloads
delivered via ``self.__next_f.push([1,"..."])`` script tags.  This module
provides helpers to pull out the model-data object and category rankings.
"""

from __future__ import annotations

import json
import re


def _iter_rsc_chunks(html: str) -> list[str]:
    """Extract all RSC flight data strings from ``__next_f.push()`` calls.

    Each match is the *string content* inside ``self.__next_f.push([1,"..."])``,
    with JSON/unicode escapes decoded so the result is plain text containing
    RSC wire-format lines.
    """
    pattern = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
    chunks: list[str] = []
    for m in pattern.finditer(html):
        raw = m.group(1)
        # The captured string is JSON-escaped (\" for quotes, \uXXXX for
        # unicode, \\n for newlines, etc.).  Wrapping it back in quotes and
        # using json.loads is the most reliable way to unescape.
        try:
            decoded: str = json.loads(f'"{raw}"')
        except (json.JSONDecodeError, UnicodeDecodeError):
            decoded = raw
        chunks.append(decoded)
    return chunks


def _extract_json_object(text: str, start_marker: str) -> dict | None:
    """Find and parse a JSON object beginning at *start_marker* using brace-depth counting.

    Returns the parsed ``dict`` or ``None`` if the marker is not found or
    parsing fails.
    """
    idx = text.find(start_marker)
    if idx == -1:
        return None

    # Walk forward from the marker to find the opening '{'
    brace_start = text.find("{", idx)
    if brace_start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    end = brace_start

    for i in range(brace_start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    candidate = text[brace_start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _extract_json_array(text: str, start_marker: str) -> list | None:
    """Find and parse a JSON array beginning right after *start_marker*.

    The marker should end just before the opening ``[``.
    """
    idx = text.find(start_marker)
    if idx == -1:
        return None

    bracket_start = text.find("[", idx + len(start_marker) - 1)
    if bracket_start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    end = bracket_start

    for i in range(bracket_start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i
                break

    candidate = text[bracket_start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def extract_rsc_model_data(html: str) -> dict | None:
    """Extract the model data object from RSC flight payloads.

    Searches for a chunk containing ``{"model":{"slug":`` and returns the
    full JSON object (with ``model``, ``analytics``, ``variantGroups``, etc.)
    or ``None`` if not found.
    """
    chunks = _iter_rsc_chunks(html)
    for chunk in chunks:
        result = _extract_json_object(chunk, '{"model":{"slug":')
        if result is not None:
            return result
    return None


def extract_rsc_categories(html: str) -> list[dict]:
    """Extract the category rankings array from RSC flight payloads.

    Looks for ``"categories":[`` in a chunk and returns the parsed array,
    or an empty list if not found.
    """
    chunks = _iter_rsc_chunks(html)
    for chunk in chunks:
        result = _extract_json_array(chunk, '"categories":[')
        if result is not None:
            return result
    return []
