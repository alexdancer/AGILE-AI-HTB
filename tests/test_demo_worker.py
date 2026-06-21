from agile_ai_htb.demo_worker import _tool


def test_demo_worker_tool_schema_is_openai_chat_compatible():
    tool = _tool("read_file")

    assert tool == {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Synthetic DEMO tool named read_file.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    }
