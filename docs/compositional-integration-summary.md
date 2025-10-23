# Compositional Prompt System - Integration Summary

## Overview

The compositional prompt system has been successfully integrated into the sentence and problem generation services. This replaces the monolithic prompt approach with targeted, explicit error injection prompts.

## What Changed

### 1. New Files Created

- **`src/prompts/compositional_prompts.py`** - Core compositional prompt builder
  - `ErrorType` enum with 5 error types
  - `CompositionalPromptBuilder` class with 6 prompt builders (1 correct + 5 error types)
  - `select_error_types()` method for intelligent error selection

- **`test_compositional_prompts.py`** - Unit tests for prompt builder
- **`test_integration_compositional.py`** - Integration tests with services
- **`docs/compositional-integration-summary.md`** - This document

### 2. Modified Files

#### `src/services/sentence_service.py`
**Changes:**
- Added `compositional_builder` parameter to `__init__()`
- Added `use_compositional` flag (default: `True`) to toggle between old/new system
- Added `error_type` parameter to `generate_sentence()`
- Updated prompt generation to use compositional builder when enabled

**Backward Compatibility:**
- Legacy `SentencePromptGenerator` still available
- Can switch back by setting `use_compositional=False`

#### `src/services/problem_service.py`
**Changes:**
- Added `compositional_builder` parameter to `__init__()`
- Modified `create_random_grammar_problem()` to:
  - Call `select_error_types()` before generating sentences
  - Pass selected error types to each incorrect sentence generation
  - Use same parameters for all 4 sentences (no parameter variation)
- Commented out legacy `_vary_parameters_for_statement()` method

**Key Difference:**
- **Old approach:** Varied parameters (COD/COI/negation) between sentences to create errors
- **New approach:** Same parameters for all sentences, errors injected via targeted prompts

### 3. Error Type Catalog

The system now supports **5 error types** for v1:

1. **`COD_PRONOUN_ERROR`** - Wrong direct object pronoun (le/la/les)
   - **Mandatory** when `direct_object != NONE`

2. **`COI_PRONOUN_ERROR`** - Wrong indirect object pronoun (lui/leur)
   - **Mandatory** when `indirect_object != NONE`

3. **`WRONG_CONJUGATION`** - Incorrect verb conjugation
   - Always available

4. **`WRONG_AUXILIARY`** - Wrong auxiliary verb (avoir vs être)
   - Available only for compound tenses (passé composé)

5. **`PAST_PARTICIPLE_AGREEMENT`** - Wrong past participle agreement with être
   - Available only for être + compound tenses

## Selection Logic

The error selection follows these rules:

```python
mandatory_errors = []
available_errors = []

# Mandatory: COD error if direct object is present
if direct_object != NONE:
    mandatory_errors.append(COD_PRONOUN_ERROR)

# Mandatory: COI error if indirect object is present
if indirect_object != NONE:
    mandatory_errors.append(COI_PRONOUN_ERROR)

# Available: Always
available_errors.append(WRONG_CONJUGATION)

# Available: Compound tenses only
if tense == PASSE_COMPOSE:
    available_errors.append(WRONG_AUXILIARY)
    
    # Available: être + compound tenses only
    if auxiliary == ETRE:
        available_errors.append(PAST_PARTICIPLE_AGREEMENT)

# Select 3 total: mandatory + random from available
remaining = 3 - len(mandatory_errors)
selected = mandatory_errors + random.sample(available_errors, remaining)
```

## How to Use

### Generate a Problem (Default - Uses Compositional)

```python
from src.services.problem_service import ProblemService

problem_service = ProblemService()
problem = await problem_service.create_random_grammar_problem(
    constraints=GrammarProblemConstraints(
        includes_cod=True,  # Will force COD error in one sentence
        includes_coi=False,
    )
)
```

### Generate Individual Sentences

```python
from src.services.sentence_service import SentenceService
from src.prompts.compositional_prompts import ErrorType

sentence_service = SentenceService(use_compositional=True)

# Correct sentence
correct = await sentence_service.generate_sentence(
    verb_id=verb_id,
    pronoun=Pronoun.FIRST_PERSON,
    tense=Tense.PRESENT,
    direct_object=DirectObject.MASCULINE,
    is_correct=True,
)

# Incorrect sentence with COD error
incorrect = await sentence_service.generate_sentence(
    verb_id=verb_id,
    pronoun=Pronoun.FIRST_PERSON,
    tense=Tense.PRESENT,
    direct_object=DirectObject.MASCULINE,
    is_correct=False,
    error_type=ErrorType.COD_PRONOUN_ERROR,  # Required for incorrect sentences
)
```

## Rollback Instructions

If you need to rollback to the legacy system:

### Option 1: Quick Toggle (No Code Changes)

```python
# In your service initialization
sentence_service = SentenceService(use_compositional=False)
```

### Option 2: Complete Rollback

1. Revert changes to `src/services/sentence_service.py`:
   ```bash
   git checkout HEAD~1 -- src/services/sentence_service.py
   ```

2. Revert changes to `src/services/problem_service.py`:
   ```bash
   git checkout HEAD~1 -- src/services/problem_service.py
   ```

3. Remove new files:
   ```bash
   rm src/prompts/compositional_prompts.py
   rm test_compositional_prompts.py
   rm test_integration_compositional.py
   ```

### Option 3: Keep Both Systems (Recommended for Testing)

The integration supports running both systems in parallel:

```python
# Use compositional for new problems
sentence_service_new = SentenceService(use_compositional=True)

# Use legacy for existing problems
sentence_service_old = SentenceService(use_compositional=False)
```

## Testing

### Unit Tests
```bash
python test_compositional_prompts.py
```

### Integration Tests
```bash
python test_integration_compositional.py
```

### End-to-End Test (With Actual LLM Calls)
```bash
# TODO: Create end-to-end test script that:
# 1. Generates a problem using the API
# 2. Verifies error types match expected
# 3. Validates sentence quality manually
```

## Monitoring

### Logging

The system adds these log messages:

- `🎨 Using compositional prompt builder` (or `📝 Using legacy prompt generator`)
- `🎯 Selected error types: [...]` - Shows which errors were selected for each problem
- `🔄 Preparing statement N/M (incorrect: error_type)` - Shows error type per sentence

### Metrics to Track

1. **Error Type Distribution** - Are COD/COI errors appearing when they should?
2. **Explanation Quality** - Do explanations match the actual errors?
3. **Single Error Rate** - Are incorrect sentences containing only one error?
4. **Generation Latency** - Still ~3-4 seconds for 4 sentences in parallel?

### Debugging Tips

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check which error types were selected
from src.prompts.compositional_prompts import CompositionalPromptBuilder
builder = CompositionalPromptBuilder()
errors = builder.select_error_types(sentence, verb, count=3)
print(f"Selected: {[e.value for e in errors]}")

# Inspect generated prompt
prompt = builder.build_prompt(sentence, verb, error_type=errors[0])
print(prompt)
```

## Next Steps

### Immediate (v1.1)
1. **Manual Quality Review** - Generate 50-100 problems, manually review
2. **Tune Prompts** - Adjust individual error prompts based on quality
3. **Add Observability** - Log error type usage to dashboard

### Short Term (v1.2)
1. **Add More Error Types**
   - Adjective agreement errors
   - Reflexive pronoun errors (if we keep reflexive verbs)
   - Preposition errors (requires verb-preposition mapping)

2. **Two-Clause Sentences** - Make sentences more complex to hide errors better

### Long Term (v2.0)
1. **Background Queue System** - Pre-generate problems with LLM validation
2. **Judge LLM** - Validate generated sentences before serving
3. **A/B Testing** - Compare compositional vs legacy quality metrics

## Known Limitations

1. **No deterministic validation** - Can't guarantee 100% that error was injected correctly
2. **Negation not an error type** - Negation errors excluded due to complexity
3. **No preposition errors** - Requires verb-preposition mapping data
4. **Single-clause sentences** - More complex sentence structures deferred to v2

## Success Criteria

Target metrics for declaring compositional system successful:

- ✅ **Latency:** ~3-4 seconds (same as legacy)
- 🎯 **Correctness Rate:** >80% of incorrect sentences contain the stated error
- 🎯 **Explanation Accuracy:** >80% of explanations correctly identify the error
- 🎯 **Single Error Rate:** >90% of incorrect sentences have exactly one error
- 🎯 **Mandatory Error Rate:** 100% of COD/COI errors appear when configured

## Questions / Issues

If you encounter issues:

1. Check logs for error type selection
2. Verify prompt is being generated correctly
3. Test with legacy system to isolate issue
4. Review generated sentence quality manually
5. Consider adjusting specific error prompt templates

For questions, see:
- `docs/compositional-prompt-design.md` - Original design document
- `src/prompts/compositional_prompts.py` - Implementation
- Test files for usage examples
