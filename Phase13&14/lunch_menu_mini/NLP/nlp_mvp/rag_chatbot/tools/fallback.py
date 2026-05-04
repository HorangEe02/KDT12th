"""
Prompt-based tool call fallback parser.

For LLMs that don't support native tool calling, we ask them to emit one or
more markers in their response and parse them out afterwards.

Supported formats (all matched case-insensitively on the keyword):

    [TOOL: get_current_weather]
    [TOOL: get_lunch_recommendations(top_n=3)]
    [TOOL: cast_vote(user_id="u1", restaurant_id="R001")]
    [TOOL: get_restaurant_info(restaurant_id=R001)]

Argument values may be bare identifiers, quoted strings, or integers. The
parser is intentionally permissive (it ignores unparseable blocks instead of
raising) so the downstream chat loop always makes progress.
"""
from __future__ import annotations

import json
import re
from typing import Any

# Entire `[TOOL: ...]` block
_BLOCK_RE = re.compile(r"\[\s*TOOL\s*:\s*([^\[\]]+?)\s*\]", re.IGNORECASE)

# "name(arg1=value1, arg2=value2)" — optional args
_CALL_RE = re.compile(
    r"^(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*(?:\((?P<args>.*)\))?\s*$"
)

# key=value pair (value is quoted string, bare identifier, int, or float)
_ARG_RE = re.compile(
    r"""
    (?P<key>[A-Za-z_][A-Za-z0-9_]*)
    \s*=\s*
    (?P<val>
        "(?:\\.|[^"\\])*"        # "quoted"
      | '(?:\\.|[^'\\])*'        # 'quoted'
      | -?\d+(?:\.\d+)?          # number
      | [A-Za-z_][A-Za-z0-9_\-]* # bare identifier
    )
    """,
    re.VERBOSE,
)


def _parse_value(raw: str) -> Any:
    raw = raw.strip()
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        # JSON string-ish
        try:
            return json.loads(raw.replace("'", '"'))
        except Exception:
            return raw[1:-1]
    # try number
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        pass
    return raw


def _parse_args(arg_str: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for m in _ARG_RE.finditer(arg_str):
        key = m.group("key")
        val = _parse_value(m.group("val"))
        result[key] = val
    return result


def parse_tool_calls(text: str) -> list[dict[str, Any]]:
    """
    Extract all tool invocations from an LLM response.

    Returns a list of `{"name": str, "args": dict}`. Unparseable blocks are
    silently skipped.
    """
    if not text:
        return []
    calls: list[dict[str, Any]] = []
    for block_match in _BLOCK_RE.finditer(text):
        body = block_match.group(1).strip()
        call_match = _CALL_RE.match(body)
        if not call_match:
            continue
        name = call_match.group("name")
        args_str = call_match.group("args") or ""
        calls.append({"name": name, "args": _parse_args(args_str)})
    return calls


def strip_tool_calls(text: str) -> str:
    """Remove `[TOOL: ...]` blocks from text (for clean user display)."""
    if not text:
        return ""
    return _BLOCK_RE.sub("", text).strip()


__all__ = ["parse_tool_calls", "strip_tool_calls"]
