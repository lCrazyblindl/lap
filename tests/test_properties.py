"""Property-based tests (v0.8 P6). The fuzz corpus (Stage 17) found the OpenAPI-2.0 gap
because real specs happened to exercise it; hypothesis hunts the next one generatively.
Invariants only — "never crashes, always returns the declared shape" — no numeric claims.
"""

from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st  # noqa: E402

# CI runs deterministically (a matrix that goes red must mean the code changed, not the
# seed); local runs explore fresh seeds every time; HYPOTHESIS_PROFILE=shake digs deeper.
settings.register_profile("dev", max_examples=100, deadline=None)
settings.register_profile("ci", max_examples=100, deadline=None, derandomize=True)
settings.register_profile("shake", max_examples=1500, deadline=None)
settings.load_profile(os.environ.get(
    "HYPOTHESIS_PROFILE", "ci" if os.environ.get("CI") else "dev"))

from lap import estimate, lint, menu, tokens  # noqa: E402
from lap import openapi_ir as ir  # noqa: E402

json_scalars = st.one_of(
    st.none(), st.booleans(), st.integers(-1000, 1000),
    st.floats(allow_nan=False, allow_infinity=False), st.text(max_size=10))
json_values = st.recursive(
    json_scalars,
    lambda kids: st.one_of(st.lists(kids, max_size=4),
                           st.dictionaries(st.text(max_size=8), kids, max_size=4)),
    max_leaves=20)

# Schema-shaped garbage: the right keys, adversarial values — incl. dangling, external
# and mutually-recursive $refs (cycle-safety is part of the flat_schema contract).
REFS = ["#/$defs/a", "#/$defs/b", "#/definitions/x", "#/components/schemas/Thing",
        "#/nope/missing", "https://ext.example/x.json#/Y", "not a pointer"]
SCHEMA_KEYS = st.sampled_from(
    ["type", "properties", "items", "required", "description", "enum", "example",
     "examples", "allOf", "oneOf", "anyOf", "$ref", "$defs", "definitions", "format"])
schema_values = st.recursive(
    st.one_of(json_scalars, st.sampled_from(REFS)),
    lambda kids: st.one_of(st.lists(kids, max_size=3),
                           st.dictionaries(SCHEMA_KEYS, kids, max_size=5)),
    max_leaves=25)


@given(st.one_of(json_values, schema_values))
def test_flat_schema_is_total(schema):
    props, required = lint.flat_schema(schema)
    assert isinstance(props, dict) and isinstance(required, list)


@given(st.one_of(json_values, schema_values))
def test_inline_refs_is_total_and_serializable(node):
    spec = {"$defs": {"a": {"$ref": "#/$defs/b"}, "b": {"$ref": "#/$defs/a"}},
            "components": {"schemas": {"Thing": {"type": "string"}}}}
    out = ir.inline_refs(spec, node)
    json.dumps(out)  # must terminate and stay JSON-serializable


@given(st.one_of(json_values, schema_values))
def test_example_instance_is_total_and_serializable(schema):
    spec = {"components": {"schemas": {"Thing": {"type": "object"}}}}
    out = estimate.example_instance(spec, schema)
    json.dumps(out)


# A generative mini-OpenAPI: sparse, often-malformed operation objects — the whole
# pipeline (IR -> every menu form -> token counts -> B/C estimates) must stay total.
operation_objects = st.fixed_dictionaries(
    {},
    optional={
        "summary": st.text(max_size=20),
        "operationId": st.text(max_size=12),
        "parameters": st.one_of(
            json_values,
            st.lists(st.fixed_dictionaries(
                {}, optional={"name": st.text(max_size=8),
                              "in": st.sampled_from(["path", "query", "header", "cookie"]),
                              "required": st.booleans(),
                              "schema": schema_values}), max_size=3)),
        "requestBody": st.one_of(json_values, st.fixed_dictionaries(
            {"content": st.dictionaries(
                st.sampled_from(["application/json", "text/xml", "application/x-www-form-urlencoded"]),
                st.fixed_dictionaries({}, optional={"schema": schema_values}), max_size=2)})),
        "responses": st.dictionaries(
            st.sampled_from(["200", "201", "204", "4XX", "default"]),
            st.one_of(json_values, st.fixed_dictionaries(
                {}, optional={"description": st.text(max_size=10),
                              "content": st.dictionaries(
                                  st.just("application/json"),
                                  st.fixed_dictionaries({}, optional={"schema": schema_values}),
                                  max_size=1)})),
            max_size=3),
    })

mini_specs = st.fixed_dictionaries({
    "openapi": st.just("3.0.0"),
    "info": st.fixed_dictionaries({"title": st.text(max_size=12), "version": st.just("1")}),
    "paths": st.dictionaries(
        st.from_regex(r"/[a-z]{1,8}(/\{[a-z]{1,5}\})?", fullmatch=True),
        st.dictionaries(st.sampled_from(["get", "post", "put", "delete"]),
                        operation_objects, max_size=2),
        max_size=3),
})


@given(mini_specs)
def test_pipeline_is_total_on_generated_specs(spec):
    ops = ir.operations(spec)
    for form, fn in menu.MENUS.items():
        tools_part, text_part = fn(spec)
        assert tokens.count_tools(tools_part) + tokens.count(text_part) >= 0
    for op in ops:
        _, per_item, per_page = estimate.estimate(spec, op)
        assert per_item >= 0 and per_page >= 0
        assert estimate.estimate_call(spec, op) >= 0
