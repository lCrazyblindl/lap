"""Token counting for LAP — faithful Anthropic count_tokens, or tiktoken approx.

Same approach proven in the token-bench, made standalone so the `lap` toolkit
has no dependency on the pet-zoo experiment. With ANTHROPIC_API_KEY set it uses
the free `messages.count_tokens` endpoint (tool defs counted via the real
`tools=` parameter); otherwise a GPT-style BPE approximation (absolute numbers
approximate, relative ordering robust).
"""

from __future__ import annotations

import functools
import json
import os

MODEL = os.environ.get("LAP_MODEL", os.environ.get("BENCH_MODEL", "claude-opus-4-8"))
_FRAME = [{"role": "user", "content": "."}]

_backend: str | None = None
_anthropic = None
_enc = None


def _init() -> str:
    global _backend, _anthropic, _enc
    if _backend is not None:
        return _backend
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from anthropic import Anthropic

            _anthropic = Anthropic()
            _anthropic.messages.count_tokens(model=MODEL, messages=_FRAME)
            _backend = "anthropic"
            return _backend
        except Exception as exc:  # noqa: BLE001
            print(f"[lap.tokens] anthropic backend unavailable ({exc!r}); using tiktoken-approx")
    import tiktoken

    _enc = tiktoken.get_encoding("cl100k_base")
    _backend = "tiktoken-approx"
    return _backend


def backend_name() -> str:
    return _init()


@functools.lru_cache(maxsize=4096)
def count(text: str) -> int:
    if _init() == "anthropic":
        full = _anthropic.messages.count_tokens(
            model=MODEL, messages=[{"role": "user", "content": text or "."}]
        ).input_tokens
        return max(0, full - _frame_overhead()) if text else 0
    # disallowed_special=(): treat tiktoken control strings (e.g. "<|endoftext|>"
    # that appear verbatim in some specs, like OpenAI's) as ordinary text, not a
    # special token — otherwise tiktoken raises.
    return len(_enc.encode(text, disallowed_special=()))


def count_tools(tools: list[dict]) -> int:
    if not tools:
        return 0
    if _init() == "anthropic":
        with_tools = _anthropic.messages.count_tokens(
            model=MODEL, messages=_FRAME, tools=tools
        ).input_tokens
        return max(0, with_tools - _frame_tokens())
    return len(_enc.encode(json.dumps(tools), disallowed_special=()))


@functools.lru_cache(maxsize=1)
def _frame_tokens() -> int:
    return _anthropic.messages.count_tokens(model=MODEL, messages=_FRAME).input_tokens


@functools.lru_cache(maxsize=1)
def _frame_overhead() -> int:
    return _frame_tokens() - 1  # frame content is "." (one token)
