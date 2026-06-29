"""Generic OpenAPI -> normalized operations.

The reusable, app-agnostic version of the parsing proven in
`experiments/token-bench/spec_source.py`: it takes any OpenAPI spec (no app
import, no server) and yields a normalized operation list that the menu
generators render. Loads a spec from a file path or an http(s) URL.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass


def load_spec(source: str) -> dict:
    if source.startswith(("http://", "https://")):
        import httpx

        resp = httpx.get(source, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.json()
    with open(source, "r", encoding="utf-8") as f:
        return json.load(f)


@dataclass
class Op:
    method: str  # GET / POST / PUT / PATCH / DELETE
    path: str
    summary: str
    path_params: list[tuple[str, str]]  # [(name, type_str)]
    body_fields: list[tuple[str, str, str]]  # [(name, type_str, constraint_str)]
    returns: str  # e.g. 'Book' | 'Book[]' | 'void'
    name: str  # tool name (operationId if present, else synthesized + deduped)
    raw: dict  # raw OpenAPI operation object


def _resolve_ref(spec: dict, ref: str) -> dict:
    node: dict = spec
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


def _num(x) -> str:
    return str(int(x)) if isinstance(x, float) and x.is_integer() else str(x)


def _type_str(spec: dict, schema: dict) -> str:
    if "$ref" in schema:
        target = _resolve_ref(spec, schema["$ref"])
        if "enum" in target:
            return "|".join(f'"{v}"' for v in target["enum"])
        # name the referenced object type rather than inlining it
        return schema["$ref"].rsplit("/", 1)[-1]
    if "enum" in schema:
        return "|".join(f'"{v}"' for v in schema["enum"])
    t = schema.get("type", "any")
    if t == "array":
        items = schema.get("items", {})
        return _type_str(spec, items) + "[]"
    return {"integer": "int", "number": "float", "boolean": "bool", "string": "string"}.get(t, t)


def _constraint_str(schema: dict) -> str:
    bits = []
    if "minimum" in schema:
        bits.append(f">={_num(schema['minimum'])}")
    if "maximum" in schema:
        bits.append(f"<={_num(schema['maximum'])}")
    if "minLength" in schema:
        bits.append(f"len>={_num(schema['minLength'])}")
    if "maxLength" in schema:
        bits.append(f"len<={_num(schema['maxLength'])}")
    return ",".join(bits)


def _schema_fields(spec: dict, schema: dict) -> list[tuple[str, str, str]]:
    if "$ref" in schema:
        schema = _resolve_ref(spec, schema["$ref"])
    out = []
    for fname, prop in schema.get("properties", {}).items():
        resolved = _resolve_ref(spec, prop["$ref"]) if "$ref" in prop else prop
        out.append((fname, _type_str(spec, prop), _constraint_str(resolved)))
    return out


def _json_body_schema(operation: dict) -> dict | None:
    rb = operation.get("requestBody")
    if not rb:
        return None
    return rb.get("content", {}).get("application/json", {}).get("schema")


def _returns_str(spec: dict, operation: dict) -> str:
    for code in ("200", "201"):
        resp = operation.get("responses", {}).get(code)
        if not resp:
            continue
        schema = resp.get("content", {}).get("application/json", {}).get("schema")
        if not schema:
            continue
        if schema.get("type") == "array":
            ref = schema.get("items", {}).get("$ref", "")
            return f"{ref.rsplit('/', 1)[-1] or 'object'}[]"
        ref = schema.get("$ref", "")
        return ref.rsplit("/", 1)[-1] or _type_str(spec, schema)
    return "void"


def _synth_name(method: str, path: str) -> str:
    segments = [p for p in path.strip("/").split("/") if not p.startswith("{")]
    resource = segments[-1] if segments else "root"
    singular = resource[:-1] if resource.endswith("s") else resource
    has_id = "{" in path
    verb = {"GET": "get" if has_id else "list", "POST": "create",
            "PUT": "update", "PATCH": "patch", "DELETE": "delete"}.get(method, method.lower())
    noun = singular if (has_id or method in ("POST", "PUT", "PATCH", "DELETE")) else resource
    return f"{verb}_{noun}"


def operations(spec: dict) -> list[Op]:
    """All operations in a stable order. Names prefer operationId, else a
    synthesized name; collisions are de-duplicated with a numeric suffix."""
    ops: list[Op] = []
    seen: dict[str, int] = {}
    for path in sorted(spec.get("paths", {})):
        methods = spec["paths"][path]
        for method in ("get", "post", "put", "patch", "delete"):
            if method not in methods:
                continue
            operation = methods[method]
            path_params = [
                (p["name"], _type_str(spec, p.get("schema", {})))
                for p in operation.get("parameters", [])
                if p.get("in") == "path"
            ]
            body_schema = _json_body_schema(operation)
            body_fields = _schema_fields(spec, body_schema) if body_schema else []
            name = operation.get("operationId") or _synth_name(method.upper(), path)
            if name in seen:
                seen[name] += 1
                name = f"{name}_{seen[name]}"
            else:
                seen[name] = 1
            ops.append(
                Op(
                    method=method.upper(),
                    path=path,
                    summary=operation.get("summary", ""),
                    path_params=path_params,
                    body_fields=body_fields,
                    returns=_returns_str(spec, operation),
                    name=name,
                    raw=operation,
                )
            )
    return ops


def inline_refs(spec: dict, node):
    """Deep-copy `node` with every $ref recursively inlined (what a naive
    OpenAPI->tools bridge emits). Guards against ref cycles."""

    def _walk(n, stack: frozenset):
        if isinstance(n, dict):
            if "$ref" in n:
                ref = n["$ref"]
                if ref in stack:
                    return {"$ref": ref}  # cycle: stop inlining
                resolved = _resolve_ref(spec, ref)
                siblings = {k: v for k, v in n.items() if k != "$ref"}
                return _walk({**resolved, **siblings}, stack | {ref})
            return {k: _walk(v, stack) for k, v in n.items()}
        if isinstance(n, list):
            return [_walk(x, stack) for x in n]
        return n

    return _walk(copy.deepcopy(node), frozenset())


def referenced_component_names(spec: dict) -> list[str]:
    """Component schema names referenced by operation bodies/returns, in order
    of first appearance — used to render shared type blocks in compact menus."""
    names: list[str] = []

    def visit(schema: dict | None):
        if not schema:
            return
        ref = schema.get("$ref") or schema.get("items", {}).get("$ref")
        if ref:
            name = ref.rsplit("/", 1)[-1]
            if name not in names:
                names.append(name)

    for op in operations(spec):
        visit(_json_body_schema(op.raw))
        for code in ("200", "201"):
            resp = op.raw.get("responses", {}).get(code, {})
            visit(resp.get("content", {}).get("application/json", {}).get("schema"))
    return names
