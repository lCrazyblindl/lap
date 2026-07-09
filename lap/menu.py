"""Menu (bucket A) generators for an arbitrary OpenAPI spec.

Bucket A is the definitions/menu that sits in the model's context — the part of
an API's cost that is intrinsic to the interface (independent of any task), and
the biggest cacheable cost. We render the same three forms the token-bench
compared, generalized to any spec:

* `openapi_full`  - each operation as a full $ref-inlined JSON-Schema tool (what a
                    naive OpenAPI->tools / MCP bridge emits);
* `compact_sig`   - compact TS-like signatures + shared type blocks;
* `numbered`      - a number->endpoint dictionary.

Each generator returns (tools, text); the score counts tools via `count_tools`
and text via `count`. B (the call) and C (results) need per-API tasks and are out
of scope for a generic scorer.
"""

from __future__ import annotations

from . import openapi_ir as ir


def _input_schema(spec: dict, op: ir.Op) -> dict:
    # v0.7 M3: path AND query parameters - real OpenAPI->tools bridges ship query params
    # in tool schemas, so the naive baseline must too (before M3 it undercounted).
    # Headers/cookies stay out: bridges typically map those to transport, not arguments.
    props: dict = {}
    required: list[str] = []
    for param in op.params:
        if param.get("in") in ("path", "query"):
            props[param["name"]] = ir.inline_refs(spec, ir._param_schema(param))
            if param.get("required", param.get("in") == "path"):
                required.append(param["name"])
    body = ir._json_body_schema(spec, op.raw)
    if body:
        for fname, prop in ir._collect_properties(spec, body).items():
            props[fname] = ir.inline_refs(spec, prop)
        body_req = ir._deref(spec, body).get("required")
        required.extend(body_req if isinstance(body_req, list) else [])
    return {"type": "object", "properties": props, "required": required}


def _required_query_params(spec: dict, op: ir.Op) -> list[tuple[str, str]]:
    """Required query params only - the compact/numbered forms show the *curated* calling
    surface (D1): everything you must send, nothing you merely may."""
    return [(p["name"], ir._type_str(spec, ir._param_schema(p))) for p in op.params
            if p.get("in") == "query" and p.get("required")]


def full(spec: dict) -> tuple[list[dict], str]:
    tools = [
        {"name": op.name, "description": op.summary, "input_schema": _input_schema(spec, op)}
        for op in ir.operations(spec)
    ]
    return tools, ""


def _field(name: str, type_str: str, constraint: str = "") -> str:
    return f"{name}:{type_str}" + (f" {constraint}" if constraint else "")


def _type_block(spec: dict, name: str) -> str:
    fields = ir._schema_fields(spec, {"$ref": ir.schema_ref(spec, name)})
    body = ", ".join(_field(n, t, c) for n, t, c in fields)
    return f"type {name} = {{ {body} }}"


def _signature(spec: dict, op: ir.Op) -> str:
    params = [_field(n, t) for n, t in op.path_params]
    params += [_field(n, t) for n, t in _required_query_params(spec, op)]
    params += [_field(n, t, c) for n, t, c in op.body_fields]
    return f"{op.name}({', '.join(params)}) -> {op.returns}"


def compact(spec: dict) -> tuple[list[dict], str]:
    lines = ['# API tools. Call as a tool: {"name": <fn>, "input": {<args>}}.']
    for name in ir.referenced_component_names(spec):
        lines.append(_type_block(spec, name))
    lines.append("")
    lines += [_signature(spec, op) for op in ir.operations(spec)]
    return [], "\n".join(lines)


def numbered(spec: dict) -> tuple[list[dict], str]:
    lines = ['# Endpoint dictionary. Call by number: {"name": "<n>", "input": {<args>}}.']
    for i, op in enumerate(ir.operations(spec), 1):
        args = [f"{n}:{t}" for n, t in op.path_params]
        args += [f"{n}:{t}" for n, t in _required_query_params(spec, op)]
        args += [f"{n}:{t}" + (f" {c}" if c else "") for n, t, c in op.body_fields]
        arg_str = f" ({', '.join(args)})" if args else ""
        lines.append(f"{i} = {op.method} {op.path}{arg_str} -> {op.returns}")
    return [], "\n".join(lines)


_SEARCH_TOOL = {
    "name": "search_tools",
    "description": "Search this API's operations by keyword; returns matching names + schemas on demand.",
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
}
_CALL_TOOL = {
    "name": "call_tool",
    "description": "Call an operation found via search_tools.",
    "input_schema": {"type": "object",
                     "properties": {"name": {"type": "string"}, "input": {"type": "object"}},
                     "required": ["name"]},
}


def tool_search(spec: dict) -> tuple[list[dict], str]:
    """Lazy-loading (search+execute) form: a fixed 2-tool menu plus a name-only
    index. Full schemas load on demand, so bucket A is ~constant in the number of
    operations instead of growing with every schema. (Anthropic Tool Search /
    Cloudflare Code Mode pattern.)"""
    names = ", ".join(op.name for op in ir.operations(spec))
    text = ("# Lazy tools: search_tools(query) then call_tool(name, input). "
            "Full schemas load on demand (not preloaded).\n"
            f"# operations: {names}")
    return [_SEARCH_TOOL, _CALL_TOOL], text


MENUS = {"openapi_full": full, "compact_sig": compact, "numbered": numbered, "tool_search": tool_search}
