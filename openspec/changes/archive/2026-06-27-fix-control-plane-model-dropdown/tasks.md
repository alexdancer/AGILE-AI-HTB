## 1. Model selector UI

- [x] 1.1 Define the curated Control Plane model choices used by the settings page, keeping them separate from Worker Adapter discovered/allowed models.
- [x] 1.2 Replace the `control_plane_model` datalist textbox with a native dropdown for curated model choices.
- [x] 1.3 Add or preserve an explicit custom model path for OpenAI-compatible endpoints and for already-saved model IDs that are not in the curated list.
- [x] 1.4 Update preset button behavior so OpenAI, Anthropic, and OpenAI-compatible choices set provider/model/base URL coherently with the new dropdown/custom controls.

## 2. Save behavior and preservation

- [x] 2.1 Ensure form submission still sends the intended `control_plane_model` value for both curated dropdown choices and custom model entries.
- [x] 2.2 Verify saving without changing an existing custom model does not silently replace it with a curated default.
- [x] 2.3 Preserve existing behavior for config persistence, runtime hot-swap, secret redaction, blank-key preservation, and stale `needs_test` connection status.

## 3. Tests and verification

- [x] 3.1 Update portal rendering tests to assert the model control is a real `<select>` and no longer uses `list="control-plane-model-options"`/`datalist` as the normal picker.
- [x] 3.2 Add or update tests for custom model preservation and OpenAI-compatible custom model submission.
- [x] 3.3 Run targeted Control Plane portal tests.
- [x] 3.4 Run `openspec validate fix-control-plane-model-dropdown --strict` and `uv run pytest` before marking tasks complete.
