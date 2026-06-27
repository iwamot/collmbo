import pytest

from app.vector_store_logic import (
    NO_RESULTS_MESSAGE,
    VECTOR_STORE_TOOL_NAME,
    build_tool_result_content,
    build_vector_store_tool,
    parse_vector_store_ids,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("kb-1", ["kb-1"]),
        ("kb-1,kb-2", ["kb-1", "kb-2"]),
        (" kb-1 , kb-2 ", ["kb-1", "kb-2"]),
        ("kb-1,,kb-2,", ["kb-1", "kb-2"]),
        ("", []),
        ("  ,  ", []),
    ],
)
def test_parse_vector_store_ids(raw, expected):
    result = parse_vector_store_ids(raw)

    assert result == expected


def test_build_vector_store_tool():
    result = build_vector_store_tool("Search the knowledge base.")

    assert result["type"] == "function"
    assert result["function"]["name"] == VECTOR_STORE_TOOL_NAME
    assert result["function"]["description"] == "Search the knowledge base."
    assert result["function"]["parameters"]["required"] == ["query"]
    assert "query" in result["function"]["parameters"]["properties"]


@pytest.mark.parametrize(
    "search_responses, expected",
    [
        (
            [{"data": [{"content": [{"text": "chunk one"}]}]}],
            "chunk one",
        ),
        (
            [
                {"data": [{"content": [{"text": "a"}, {"text": "b"}]}]},
                {"data": [{"content": [{"text": "c"}]}]},
            ],
            "a\n\nb\n\nc",
        ),
        ([], NO_RESULTS_MESSAGE),
        ([{"data": None}], NO_RESULTS_MESSAGE),
        ([{"data": []}], NO_RESULTS_MESSAGE),
        ([{}], NO_RESULTS_MESSAGE),
        ([{"data": [{"content": None}]}], NO_RESULTS_MESSAGE),
        ([{"data": [{"content": [{"text": None}]}]}], NO_RESULTS_MESSAGE),
        ([{"data": [{"content": [{}]}]}], NO_RESULTS_MESSAGE),
    ],
)
def test_build_tool_result_content(search_responses, expected):
    result = build_tool_result_content(search_responses)

    assert result == expected
