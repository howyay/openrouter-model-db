"""Shared test fixtures for openrouter-model-db tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def SAMPLE_RSC_HTML() -> str:  # noqa: N802
    r"""Minimal HTML mimicking OpenRouter RSC flight payloads.

    Contains two relevant ``self.__next_f.push([1,"..."])`` script tags:
    one with model data and one with category rankings.
    """
    # The content inside push() must be JSON-escaped (inner quotes as \",
    # angle brackets as \u003c / \u003e, etc.).  We use a raw string so
    # that the Python literal itself does not interpret the backslashes.
    return (
        r'<html><body>'
        r'<script>self.__next_f.push([1,"some irrelevant rsc data here"])</script>'
        r'<script>self.__next_f.push([1,"3e:[\"$\",\"$L42\",null,'
        r'{\"model\":{\"slug\":\"test/model-1\",\"name\":\"Test: Model-1\",\"short_name\":\"Model-1\",\"author\":\"test\",\"description\":\"A test model achieving SWE-bench (72.5%) and MMLU: 89.3% scores.\",\"context_length\":1048576,\"input_modalities\":[\"text\",\"image\"],\"output_modalities\":[\"text\"],\"group\":\"TestGroup\",\"supports_reasoning\":true,\"permaslug\":\"test/model-1-20260318\",\"created_at\":\"2026-03-18T19:54:03.793004+00:00\",\"updated_at\":\"2026-03-25T15:39:42.591683+00:00\",\"default_parameters\":{\"temperature\":1,\"top_p\":0.95,\"top_k\":null,\"frequency_penalty\":null,\"presence_penalty\":null,\"repetition_penalty\":null},\"knowledge_cutoff\":\"2025-01-31T23:59:59+00:00\",\"hf_slug\":\"test-org/model-1\",\"warning_message\":\"Test warning\",\"instruct_type\":null,\"reasoning_config\":{\"start_token\":\"\u003cthink\u003e\",\"end_token\":\"\u003c/think\u003e\",\"reasoning_return_mechanism\":\"reasoning-content\"},\"features\":{},\"endpoint\":{\"id\":\"abc-123\",\"name\":\"TestProvider | test/model-1-20260318\",\"context_length\":1048576,\"provider_name\":\"TestProvider\",\"provider_slug\":\"testprovider/fp8\",\"quantization\":\"fp8\",\"variant\":\"standard\",\"max_completion_tokens\":131072,\"max_prompt_tokens\":null,\"is_free\":false,\"is_byok\":false,\"moderation_required\":false,\"supports_tool_parameters\":true,\"supports_reasoning\":true,\"supports_multipart\":true,\"provider_region\":null,\"supported_parameters\":[\"reasoning\",\"max_tokens\",\"temperature\",\"tools\"],\"adapter_name\":\"TestAdapter\",\"provider_info\":{\"name\":\"TestProvider\",\"slug\":\"testprovider\",\"baseUrl\":\"https://api.test.com/v1\",\"dataPolicy\":{\"training\":false,\"trainingOpenRouter\":false,\"retainsPrompts\":true,\"retentionDays\":30,\"canPublish\":false,\"termsOfServiceURL\":\"https://test.com/terms\",\"privacyPolicyURL\":\"https://test.com/privacy\",\"requiresUserIDs\":true},\"headquarters\":\"US\",\"datacenters\":[\"US\",\"EU\"],\"isAbortable\":false,\"moderationRequired\":false,\"adapterName\":\"TestAdapter\",\"statusPageUrl\":\"https://status.test.com\",\"byokEnabled\":true},\"pricing\":{\"prompt\":\"0.000001\",\"completion\":\"0.000003\",\"input_cache_read\":\"0.0000002\",\"discount\":0,\"line_items\":[{\"type\":\"long_context_threshold\",\"value\":\"256000\"},{\"type\":\"input_tokens_above_threshold\",\"value\":\"0.000002\"},{\"type\":\"output_tokens_above_threshold\",\"value\":\"0.000006\"}]},\"variable_pricings\":[{\"type\":\"prompt-threshold\",\"threshold\":256000,\"prompt\":\"0.000002\",\"completions\":\"0.000006\"}]}},'
        r'\"analytics\":[{\"date\":\"2026-03-26 00:00:00\",\"model_permaslug\":\"test/model-1-20260318\",\"variant\":\"standard\",\"total_completion_tokens\":870654946,\"total_prompt_tokens\":196873314447,\"total_native_tokens_reasoning\":231862032,\"count\":2037879,\"num_media_prompt\":445,\"num_media_completion\":0,\"num_audio_prompt\":0,\"total_native_tokens_cached\":177544227776,\"total_tool_calls\":1555637,\"requests_with_tool_call_errors\":36289}],'
        r'\"routerAnalytics\":[],'
        r'\"modelNameMap\":{},'
        r'\"variantGroups\":[{\"variant\":\"standard\",\"endpoints\":[{\"id\":\"abc-123\",\"name\":\"TestProvider | test/model-1-20260318\",\"context_length\":1048576,\"provider_name\":\"TestProvider\",\"provider_slug\":\"testprovider/fp8\",\"quantization\":\"fp8\",\"variant\":\"standard\",\"max_completion_tokens\":131072,\"pricing\":{\"prompt\":\"0.000001\",\"completion\":\"0.000003\",\"input_cache_read\":\"0.0000002\",\"discount\":0},\"supported_parameters\":[\"reasoning\",\"max_tokens\",\"temperature\",\"tools\"],\"is_free\":false,\"is_byok\":false,\"moderation_required\":false,\"supports_tool_parameters\":true,\"supports_reasoning\":true,\"supports_multipart\":true,\"provider_region\":null}]}]'
        r'}]\n"])</script>'
        r'<script>self.__next_f.push([1,"3d:[\"$\",\"$L40\",null,{\"hidden\":false,\"className\":\"test\",\"children\":[\"$\",\"$L41\",null,{\"categories\":[{\"date\":\"2026-03-25\",\"model\":\"test/model-1-20260318\",\"category\":\"programming\",\"count\":37890,\"total_prompt_tokens\":3722017129,\"total_completion_tokens\":16407354,\"volume\":42.661911,\"rank\":1},{\"date\":\"2026-03-25\",\"model\":\"test/model-1-20260318\",\"category\":\"technology\",\"count\":9627,\"total_prompt_tokens\":518751670,\"total_completion_tokens\":3604866,\"volume\":7.702767,\"rank\":3}]}]}]\n"])</script>'
        r'</body></html>'
    )


@pytest.fixture()
def sample_api_models_response() -> dict:
    """A minimal /api/v1/models style response with one model entry."""
    return {
        "data": [
            {
                "id": "test/model-1",
                "name": "Test: Model-1",
                "created": 1742327643,
                "description": "A test model.",
                "context_length": 1048576,
                "architecture": {
                    "modality": "text+image->text",
                    "tokenizer": "Other",
                    "instruct_type": None,
                },
                "pricing": {
                    "prompt": "0.000001",
                    "completion": "0.000003",
                    "image": "0",
                    "request": "0",
                },
                "top_provider": {
                    "context_length": 1048576,
                    "max_completion_tokens": 131072,
                    "is_moderated": False,
                },
                "per_request_limits": None,
            }
        ]
    }
