# OpenAI Client Update - Consumer Migration

## Change Summary

`OpenAIClient.handle_request()` now returns `LLMResponse` instead of `str`.

## Required Code Changes

### Pattern: Access `.content` instead of using response directly

```python
# Before
response = await self.openai_client.handle_request(prompt, model=model)
data = json.loads(response)

# After  
response = await self.openai_client.handle_request(prompt, model=model)
data = json.loads(response.content)
```

### Files to Update

**src/services/sentence_service.py** (~line 150):
```python
response = await self.openai_client.handle_request(...)
response_json = json.loads(response.content)  # Add .content
```

**src/services/verb_service.py** (~line 180, objects_response):
```python
objects_response = await self.openai_client.handle_request(...)
objects_json = json.loads(objects_response.content)  # Add .content
```

**src/services/verb_service.py** (~line 280, llm_response):
```python
llm_response = await self.openai_client.handle_request(...)
response_json = json.loads(llm_response.content)  # Add .content
```

## Test Mocking

```python
from src.schemas.llm_response import LLMResponse

# Helper function
def mock_llm_response(content: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="test",
        response_id="test-id",
        duration_ms=0,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
    )

# Usage
mock_client.handle_request.return_value = mock_llm_response('{"key": "value"}')
```

## New Capabilities

```python
response = await client.handle_request(prompt, model="gpt-5-nano-2025-08-07")

response.content              # Cleaned content (str)
response.model                # "gpt-5-nano-2025-08-07"
response.response_id          # "chatcmpl-abc123"
response.duration_ms          # 1234.5
response.prompt_tokens        # 150
response.completion_tokens    # 75
response.total_tokens         # 225
response.reasoning_tokens     # 500 (gpt-5 only, else None)
response.reasoning_content    # "First, I need to..." (gpt-5 only, else None)
response.raw_content          # Original response before cleaning
```
