# Compositional Sentence Generation System Design

## Overview

Replace the monolithic prompt system with a compositional approach that generates explicit, targeted prompts for correct and incorrect sentences. All 4 sentences (1 correct + 3 incorrect) are generated in parallel for ~3-4s total latency.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Problem Generation Request                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Generate Base Parameters (No LLM)                        │
│    - Select verb                                             │
│    - Choose: pronoun, tense, negation, COD, COI             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Build 4 Specialized Prompts (No LLM)                     │
│    - Prompt 1: Correct sentence                             │
│    - Prompt 2-4: Each with specific grammatical error       │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Execute All 4 LLM Calls in Parallel (asyncio.gather)    │
│    Total time: ~3-4 seconds                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Package Problem & Return                                  │
└─────────────────────────────────────────────────────────────┘
```

## Prompt Templates

### Base Template Structure

Every prompt (correct or incorrect) shares this foundation:

```
You are a French grammar expert. Generate a creative, natural-sounding French sentence.

VERB DETAILS:
- Infinitive: {verb.infinitive}
- Translation: {verb.translation}
- Past Participle: {verb.past_participle}
- Auxiliary: {verb.auxiliary} (avoir/être)
- Reflexive: {verb.reflexive}
- Can have COD: {verb.can_have_cod}
- Can have COI: {verb.can_have_coi}

REQUIRED PARAMETERS:
- Pronoun: {pronoun} (je, tu, il/elle, nous, vous, ils/elles)
- Tense: {tense}
- Negation: {negation} (none, pas, jamais, rien, personne, plus, aucune, encore)
- Direct Object (COD): {direct_object} (none, masculine, feminine, plural)
- Indirect Object (COI): {indirect_object} (none, masculine, feminine, plural)

[SPECIFIC INSTRUCTIONS SECTION - varies by prompt type]

CREATIVITY REQUIREMENTS:
- Use varied vocabulary and contexts
- Create realistic, interesting scenarios
- Vary sentence complexity when appropriate
- Include complements/infinitives when the verb allows
- Avoid repetitive patterns

RESPONSE FORMAT (JSON):
{
    "sentence": "The French sentence",
    "translation": "English translation",
    "explanation": "Explanation of error (empty for correct sentences)"
}
```

### 1. Correct Sentence Prompt

```
[SPECIFIC INSTRUCTIONS]
Generate a grammatically CORRECT sentence that:
1. Uses all required parameters exactly as specified
2. Follows all French grammar rules:
   - Correct auxiliary verb (avoir/être)
   - Proper past participle agreement with être
   - Correct reflexive pronoun placement if reflexive verb
   - Proper negation structure (ne...pas, ne...jamais, etc.)
   - Correct COD/COI pronoun placement and agreement
   - Proper prepositions for indirect objects
3. Is semantically meaningful and idiomatic
4. Sounds natural to native speakers

Return explanation as an empty string.
```

### 2. Incorrect Sentence Prompts

Each incorrect prompt targets ONE specific error type. The system randomly selects 3 error types from the catalog below.

#### Error Type Catalog

##### **Agreement Errors**

###### Past Participle Agreement Error
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence that violates the past participle agreement rule:

DELIBERATE ERROR: When using auxiliary "être", the past participle MUST agree with the subject in gender and number. You must generate a sentence where this agreement is WRONG.

Example violation:
- Correct: "Elle est allée" (feminine agreement)
- INCORRECT: "Elle est allé" (missing feminine agreement) ← Generate this type

Follow all other grammar rules correctly. Only violate past participle agreement.
Return explanation: "The past participle '{participle}' should agree with the subject '{subject}' and be '{correct_form}' instead."
```

###### Adjective Agreement Error
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence with an adjective that violates gender/number agreement:

DELIBERATE ERROR: Adjectives must agree with the nouns they modify. You must generate a sentence where an adjective has the WRONG gender or number.

Example violation:
- Correct: "une grande maison" (feminine)
- INCORRECT: "une grand maison" (masculine form on feminine noun) ← Generate this type

Include at least one adjective in the sentence and make it disagree with its noun.
Return explanation: "The adjective '{adjective}' should agree with '{noun}' and be '{correct_form}' instead."
```

###### COD Pronoun Agreement Error
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence where a COD pronoun (le/la/les) has incorrect placement or form:

DELIBERATE ERROR: COD pronouns must match the gender/number of the object they replace and be placed before the conjugated verb.

Example violation:
- Correct: "Je les ai vus" (plural masculine)
- INCORRECT: "Je le ai vu" (wrong number) ← Generate this type

The sentence must include a COD pronoun that is incorrectly used.
Return explanation: "The COD pronoun '{wrong_pronoun}' should be '{correct_pronoun}' to match '{object}'."
```

##### **Auxiliary Verb Errors**

###### Wrong Auxiliary Verb
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence that uses the WRONG auxiliary verb:

DELIBERATE ERROR: This verb requires auxiliary "{correct_auxiliary}" but you must use "{wrong_auxiliary}" instead.

Example violation:
- Correct: "Je suis allé" (aller uses être)
- INCORRECT: "J'ai allé" (using avoir instead) ← Generate this type

Use the wrong auxiliary while following all other grammar rules.
Return explanation: "The verb '{verb}' requires auxiliary '{correct_auxiliary}', not '{wrong_auxiliary}'."
```

##### **Preposition Errors**

###### Incorrect Preposition with COI
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence with an INCORRECT preposition before an indirect object:

DELIBERATE ERROR: The verb or context requires preposition "{correct_prep}" but you must use "{wrong_prep}" instead.

Example violation:
- Correct: "Je parle à Pierre" (parler requires "à")
- INCORRECT: "Je parle de Pierre" (wrong preposition) ← Generate this type

Return explanation: "The preposition '{wrong_prep}' is incorrect; '{correct_prep}' should be used with '{verb}'."
```

###### Missing Required Preposition
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence that OMITS a required preposition:

DELIBERATE ERROR: The verb "{verb}" requires preposition "{required_prep}" but you must omit it.

Example violation:
- Correct: "Je pense à toi"
- INCORRECT: "Je pense toi" (missing "à") ← Generate this type

Return explanation: "The preposition '{required_prep}' is required after '{verb}'."
```

##### **Negation Errors**

###### Incomplete Negation Structure
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence with INCOMPLETE negation structure:

DELIBERATE ERROR: French negation requires both "ne" and "{negation_word}", but you must omit one part.

Example violation:
- Correct: "Je ne parle pas"
- INCORRECT: "Je parle pas" (missing "ne") ← Generate this type

Return explanation: "The negation is incomplete; French requires both 'ne' and '{negation_word}'."
```

###### Wrong Negation Word
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence using the WRONG negation word:

DELIBERATE ERROR: The required negation is "{correct_negation}" but you must use "{wrong_negation}" instead, creating a semantic mismatch.

Example violation:
- Correct: "Je ne vois rien" (nothing)
- INCORRECT: "Je ne vois personne" (nobody - wrong meaning) ← Generate this type

Return explanation: "The negation '{wrong_negation}' changes the meaning; '{correct_negation}' is required here."
```

##### **Reflexive Verb Errors**

###### Missing Reflexive Pronoun
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence that OMITS the required reflexive pronoun:

DELIBERATE ERROR: "{verb}" is a reflexive verb requiring pronoun "{reflexive_pronoun}", but you must omit it.

Example violation:
- Correct: "Je me lève"
- INCORRECT: "Je lève" (missing "me") ← Generate this type

Return explanation: "The reflexive pronoun '{reflexive_pronoun}' is required for reflexive verb '{verb}'."
```

###### Wrong Reflexive Pronoun
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence with the WRONG reflexive pronoun:

DELIBERATE ERROR: The subject "{subject}" requires reflexive pronoun "{correct_pronoun}", but you must use "{wrong_pronoun}".

Example violation:
- Correct: "Tu te lèves" (2nd person)
- INCORRECT: "Tu me lèves" (1st person pronoun) ← Generate this type

Return explanation: "The reflexive pronoun should be '{correct_pronoun}' to match subject '{subject}', not '{wrong_pronoun}'."
```

##### **Pronoun Placement Errors**

###### Incorrect COD/COI Placement
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence where the COD/COI pronoun is in the WRONG position:

DELIBERATE ERROR: Object pronouns must be placed before the conjugated verb, but you must place it incorrectly (after the verb or in wrong position in compound tenses).

Example violation:
- Correct: "Je l'ai vu"
- INCORRECT: "J'ai le vu" (after auxiliary) ← Generate this type

Return explanation: "The object pronoun '{pronoun}' should be placed before '{verb}', not after."
```

##### **Word Order Errors**

###### Inverted Word Order (Non-Question)
```
[SPECIFIC INSTRUCTIONS]
Generate a sentence with INCORRECT word order:

DELIBERATE ERROR: Create an unnatural or grammatically incorrect word order that French grammar doesn't allow.

Example violation:
- Correct: "Je vois souvent mes amis"
- INCORRECT: "Je souvent vois mes amis" (adverb in wrong position) ← Generate this type

Return explanation: "The word order is incorrect; '{correct_order}' is the proper structure."
```

## Implementation Strategy

### Phase 1: Core Infrastructure
1. Create `ErrorType` enum with all error types
2. Create `PromptBuilder` class with methods for each error type
3. Implement base template composition
4. Add error type selection logic (random 3 from catalog)

### Phase 2: Prompt Templates
1. Implement correct sentence prompt builder
2. Implement each error type prompt builder
3. Add parameter interpolation
4. Add creativity instructions

### Phase 3: Integration
1. Replace existing `SentencePromptGenerator`
2. Update `SentenceService.generate_sentence()` to use new system
3. Keep parallel execution in `ProblemService`
4. Add logging for which error types were selected

### Phase 4: Future Enhancements (Queue System)
1. Build problem queue/cache system
2. Add judge LLM for quality validation
3. Implement retry logic for failed generations
4. Add metrics for error type quality

## Error Type Selection Strategy

For each problem, randomly select 3 error types from the catalog, ensuring:
- No duplicate error types
- At least one agreement error (most common/important)
- Variety across error categories
- Consider verb properties (e.g., don't select auxiliary errors for present tense)

```python
def select_error_types(verb: Verb, tense: Tense, count: int = 3) -> list[ErrorType]:
    """Select appropriate error types for this verb/tense combination."""
    available_errors = []
    
    # Always include agreement errors
    available_errors.extend([
        ErrorType.PAST_PARTICIPLE_AGREEMENT,
        ErrorType.ADJECTIVE_AGREEMENT,
        ErrorType.COD_PRONOUN_AGREEMENT
    ])
    
    # Add auxiliary errors only for compound tenses
    if tense in [Tense.PASSE_COMPOSE, Tense.PLUS_QUE_PARFAIT]:
        available_errors.append(ErrorType.WRONG_AUXILIARY)
    
    # Add reflexive errors only for reflexive verbs
    if verb.reflexive:
        available_errors.extend([
            ErrorType.MISSING_REFLEXIVE_PRONOUN,
            ErrorType.WRONG_REFLEXIVE_PRONOUN
        ])
    
    # Add preposition errors for verbs with COI
    if verb.can_have_coi:
        available_errors.extend([
            ErrorType.INCORRECT_PREPOSITION,
            ErrorType.MISSING_PREPOSITION
        ])
    
    # Add negation errors if negation is required
    # Add pronoun placement errors if COD/COI present
    # etc...
    
    return random.sample(available_errors, min(count, len(available_errors)))
```

## Expected Improvements

### Quality
- ✅ **Explicit error generation**: LLM knows exactly what rule to break
- ✅ **Accurate explanations**: Explanation matches the actual error injected
- ✅ **Single error per sentence**: More predictable and testable
- ✅ **Better debugging**: Know which error type failed

### Maintainability
- ✅ **Modular prompts**: Easy to add/modify error types
- ✅ **Clear separation**: Each error type is self-contained
- ✅ **Testable**: Can test each error type independently
- ✅ **Tunable**: Adjust individual error type quality

### Performance
- ✅ **Same latency**: Still ~3-4s with parallel execution
- ✅ **Future-ready**: Can add queue system without changing core logic

## Success Metrics

1. **Correctness Rate**: % of incorrect sentences that actually have the stated error
2. **Explanation Accuracy**: % of explanations that correctly identify the error
3. **Single Error Rate**: % of incorrect sentences with exactly one error
4. **Naturalness**: Subjective quality of generated sentences

Target: >90% correctness on all metrics within 2 weeks of tuning.