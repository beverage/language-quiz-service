-- ===== UNIVERSAL PROBLEMS DATA MODEL =====
-- Clean, simple schema that works across grammar, functional, and vocabulary domains

-- Problem types enum - top-level categories
CREATE TYPE problem_type AS ENUM (
    'grammar',           -- Your current implementation
    'functional',        -- Your separate app
    'vocabulary'         -- Future implementation
);

-- Core problems table - universal and extensible
CREATE TABLE problems (
    -- Core identification
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Universal problem metadata
    problem_type            problem_type NOT NULL,
    title                   TEXT,
    instructions            TEXT NOT NULL,
    correct_answer_index    INTEGER NOT NULL,
    
    -- Language settings (simplified)
    target_language_code    CHAR(3) NOT NULL DEFAULT 'eng', -- User's language for translations/explanations
    -- Source language is always French - no need for column
    
    -- Universal content
    statements              JSONB NOT NULL,
    -- Grammar problem example:
    -- [
    --   {"content": "Je le mange", "translation": "I eat it", "explanation": null, "is_correct": true},
    --   {"content": "Je lui mange", "translation": null, "explanation": "Incorrect: 'lui' is indirect object", "is_correct": false},
    --   {"content": "Je les mange", "translation": "I eat them", "explanation": null, "is_correct": true}, 
    --   {"content": "Je leur mange", "translation": null, "explanation": "Incorrect: 'leur' is indirect object", "is_correct": false}
    -- ]
    --
    -- Vocabulary problem example:
    -- [
    --   {"word": "chien", "definition": "dog", "pronunciation": "/ʃjɛ̃/", "example": "Le chien aboie"},
    --   {"word": "chat", "definition": "cat", "pronunciation": "/ʃa/", "example": "Le chat miaule"},
    --   {"word": "oiseau", "definition": "bird", "pronunciation": "/wazo/", "example": "L'oiseau chante"},
    --   {"word": "poisson", "definition": "fish", "pronunciation": "/pwasɔ̃/", "example": "Le poisson nage"}
    -- ]
    --
    -- Functional problem example (parts of speech/grammatical function):
    -- [
    --   {"sentence": "Je ne vais _____ au cinéma.", "option": "jamais", "explanation": "Correct: 'jamais' functions as temporal negation", "is_correct": true},
    --   {"sentence": "Je ne vais _____ au cinéma.", "option": "rien", "explanation": "Incorrect: 'rien' negates objects, not actions", "is_correct": false},
    --   {"sentence": "Je ne vais _____ au cinéma.", "option": "personne", "explanation": "Incorrect: 'personne' negates people, not actions", "is_correct": false},
    --   {"sentence": "Je ne vais _____ au cinéma.", "option": "plus", "explanation": "Possible but changes meaning to 'no longer'", "is_correct": false}
    -- ]
    
    -- Universal searchable fields
    topic_tags              TEXT[],     -- ['food', 'animals', 'negation', 'logical_connectors', 'prepositions']
    
    -- Universal source tracking (for any statement type)
    source_statement_ids    UUID[],     -- References to sentences, vocab_items, functional_scenarios, etc.
    
    -- Type-specific and flexible metadata
    metadata                JSONB,
    -- Grammar example:
    -- {
    --   "grammatical_focus": ["direct_objects", "pronoun_placement"],
    --   "verb_infinitives": ["manger", "finir"],
    --   "tenses_used": ["present", "passe_compose"],
    --   "pronouns_used": ["first_person", "third_person"],
    --   "includes_negation": true,
    --   "includes_cod": true,
    --   "includes_coi": false,
    --   "source_verb_ids": ["verb-uuid-1", "verb-uuid-2"],
    --   "estimated_time_minutes": 2,
    --   "learning_objective": "Practice direct object placement"
    -- }
    --
    -- Vocabulary example:
    -- {
    --   "semantic_field": ["animals", "pets"],
    --   "word_difficulty": "beginner",
    --   "includes_pronunciation": true,
    --   "source_vocabulary_ids": ["vocab-uuid-1", "vocab-uuid-2"],
    --   "estimated_time_minutes": 3,
    --   "learning_objective": "Learn basic animal vocabulary"
    -- }
    --
    -- Functional example:
    -- {
    --   "part_of_speech": "adverb",
    --   "grammatical_function": "negation",
    --   "function_category": "temporal_negation",
    --   "target_construction": "ne_jamais",
    --   "difficulty_level": "intermediate",
    --   "estimated_time_minutes": 3,
    --   "learning_objective": "Distinguish between different types of negation adverbs"
    -- }
    
    -- Constraints
    CONSTRAINT valid_correct_index CHECK (correct_answer_index >= 0),
    CONSTRAINT valid_statements_array CHECK (jsonb_typeof(statements) = 'array'),
    CONSTRAINT statements_not_empty CHECK (jsonb_array_length(statements) > 0),
    CONSTRAINT correct_index_within_bounds CHECK (correct_answer_index < jsonb_array_length(statements)),
    CONSTRAINT problems_title_type_unique UNIQUE (title, problem_type)
);

-- ===== INDEXES FOR EFFICIENT QUERYING =====

-- Core universal indexes
CREATE INDEX idx_problems_type ON problems(problem_type);
CREATE INDEX idx_problems_created_at ON problems(created_at);
CREATE INDEX idx_problems_target_language ON problems(target_language_code);

-- Universal searchable fields
CREATE INDEX idx_problems_topic_tags_gin ON problems USING GIN (topic_tags);
CREATE INDEX idx_problems_source_statements_gin ON problems USING GIN (source_statement_ids);

-- Full-text search on statements content
CREATE INDEX idx_problems_statements_gin ON problems USING GIN (statements);

-- Flexible metadata search (for type-specific queries)
CREATE INDEX idx_problems_metadata_gin ON problems USING GIN (metadata);

-- ===== EXAMPLE QUERY PATTERNS =====

-- Universal queries:
-- Find all grammar problems:
-- SELECT * FROM problems WHERE problem_type = 'grammar';

-- Find problems by topic:
-- SELECT * FROM problems WHERE 'food' = ANY(topic_tags);

-- Find problems that used a specific source statement:
-- SELECT * FROM problems WHERE 'statement-uuid' = ANY(source_statement_ids);

-- Grammar-specific queries (using metadata):
-- Find grammar problems focusing on direct objects:
-- SELECT * FROM problems 
-- WHERE problem_type = 'grammar' 
-- AND metadata @> '{"grammatical_focus": ["direct_objects"]}';

-- Find grammar problems using specific verb:
-- SELECT * FROM problems 
-- WHERE problem_type = 'grammar' 
-- AND metadata @> '{"verb_infinitives": ["manger"]}';

-- Vocabulary-specific queries:
-- Find vocabulary problems about animals:
-- SELECT * FROM problems 
-- WHERE problem_type = 'vocabulary' 
-- AND metadata @> '{"semantic_field": ["animals"]}';

-- Functional-specific queries:
-- Find negation adverb problems:
-- SELECT * FROM problems 
-- WHERE problem_type = 'functional' 
-- AND metadata @> '{"grammatical_function": "negation"}';

-- Find connector word problems:
-- SELECT * FROM problems 
-- WHERE problem_type = 'functional' 
-- AND metadata @> '{"part_of_speech": "connector"}';

-- Find fill-in-the-blank problems for intermediate level:
-- SELECT * FROM problems 
-- WHERE problem_type = 'functional' 
-- AND metadata @> '{"difficulty_level": "intermediate"}';

-- Complex cross-type query:
-- Find all beginner problems about food (any type):
-- SELECT * FROM problems 
-- WHERE 'food' = ANY(topic_tags) 
-- AND (
--   metadata->>'word_difficulty' = 'beginner' OR 
--   metadata->>'difficulty_level' = 'beginner'
-- );

-- ===== UPDATED TIMESTAMP TRIGGER =====
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language plpgsql;

CREATE TRIGGER problems_updated_at_trigger
    BEFORE UPDATE ON problems
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===== ROW LEVEL SECURITY (RLS) =====
ALTER TABLE problems ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (adjust based on your auth requirements)
CREATE POLICY problems_select_policy ON problems
    FOR SELECT USING (true);

CREATE POLICY problems_insert_policy ON problems  
    FOR INSERT WITH CHECK (true);

CREATE POLICY problems_update_policy ON problems
    FOR UPDATE USING (true);

CREATE POLICY problems_delete_policy ON problems
    FOR DELETE USING (true);

-- ===== VALIDATION FUNCTIONS =====

-- Validate statement structure based on problem type
CREATE OR REPLACE FUNCTION validate_problem_statements(prob_type problem_type, statements JSONB) 
RETURNS BOOLEAN AS $$
BEGIN
    CASE prob_type
        WHEN 'grammar' THEN
            -- Grammar problems need content and correctness info
            RETURN (
                SELECT bool_and(
                    statement ? 'content' AND 
                    statement ? 'is_correct' AND
                    (
                        (statement->>'is_correct')::boolean = true AND statement ? 'translation'
                        OR 
                        (statement->>'is_correct')::boolean = false AND statement ? 'explanation'
                    )
                )
                FROM jsonb_array_elements(statements) AS statement
            );
        
        WHEN 'vocabulary' THEN
            -- Vocabulary problems need word and definition
            RETURN (
                SELECT bool_and(statement ? 'word' AND statement ? 'definition')
                FROM jsonb_array_elements(statements) AS statement
            );
        
        WHEN 'functional' THEN
            -- Functional problems need sentence with blank and option
            RETURN (
                SELECT bool_and(statement ? 'sentence' AND statement ? 'option')
                FROM jsonb_array_elements(statements) AS statement
            );
        
        ELSE
            RETURN TRUE; -- Unknown types pass validation
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Add constraint for statement validation
ALTER TABLE problems ADD CONSTRAINT valid_statements_for_type 
CHECK (validate_problem_statements(problem_type, statements));

-- ===== COMMENTS FOR DOCUMENTATION =====
COMMENT ON TABLE problems IS 'Universal atomic problems for grammar, functional, and vocabulary learning';
COMMENT ON COLUMN problems.problem_type IS 'Top-level problem category: grammar, functional, or vocabulary';
COMMENT ON COLUMN problems.target_language_code IS 'User''s native language for translations and explanations (source is always French)';
COMMENT ON COLUMN problems.statements IS 'Self-contained JSONB array - structure varies by problem_type';
COMMENT ON COLUMN problems.topic_tags IS 'Universal topic tags like food, animals, daily_activities, restaurant_situations';
COMMENT ON COLUMN problems.source_statement_ids IS 'Array of source statement IDs (sentences, vocab items, scenarios, etc.)';
COMMENT ON COLUMN problems.metadata IS 'Type-specific metadata including difficulty, learning objectives, and domain-specific fields';

-- ===== INTEGRATION EXAMPLES =====
/*
Grammar Problem Creation (your current system):
1. Generate 4 sentences using SentenceService.generate_sentence()
2. Package into problem:
   {
     "problem_type": "grammar",
     "statements": [...sentence data...],
     "topic_tags": ["food"], // derived from verbs/context
     "source_statement_ids": [sentence1.id, sentence2.id, ...],
     "metadata": {
       "grammatical_focus": ["direct_objects"],
       "verb_infinitives": ["manger"],
       "source_verb_ids": [verb.id],
       "includes_cod": true
     }
   }

Future Vocabulary Problem:
   {
     "problem_type": "vocabulary", 
     "statements": [{"word": "chien", "definition": "dog", ...}],
     "topic_tags": ["animals"],
     "metadata": {
       "semantic_field": ["pets"],
       "word_difficulty": "beginner"
     }
   }

Future Functional Problem:
   {
     "problem_type": "functional",
     "statements": [{"sentence": "Je ne vais _____ au cinéma.", "option": "jamais", ...}],
     "topic_tags": ["negation", "adverbs"],
     "metadata": {
       "part_of_speech": "adverb",
       "grammatical_function": "negation",
       "function_category": "temporal_negation"
     }
   }
*/