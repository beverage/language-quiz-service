-- Modern sentences table schema
-- Focused on sentence storage with proper normalization
-- Problem/quiz structure handled separately at service level

-- Drop existing table (uncomment when ready to migrate)
-- DROP TABLE IF EXISTS sentences CASCADE;

-- Ensure required enum types exist (some may already be defined)
-- Pronouns
CREATE TYPE pronoun AS ENUM (
    'first_person', 
    'second_person', 
    'third_person', 
    'first_person_plural', 
    'second_person_plural', 
    'third_person_plural'
);

-- Direct objects
CREATE TYPE direct_object AS ENUM (
    'none', 
    'masculine', 
    'feminine', 
    'plural'
);

-- Indirect objects
CREATE TYPE indirect_object AS ENUM (
    'none', 
    'masculine', 
    'feminine', 
    'plural'
);

-- Negations
CREATE TYPE negation AS ENUM (
    'none', 
    'pas', 
    'jamais', 
    'rien', 
    'personne', 
    'plus', 
    'aucun', 
    'aucune', 
    'encore'
);

-- Tenses (already exists from verbs schema - reusing)
-- CREATE TYPE IF NOT EXISTS tense AS ENUM (...)

-- Problem types for more nuanced correctness tracking
-- NOTE: This will likely be moved to a separate problem/quiz system
-- that references sentences via JSON structure
/*
CREATE TYPE sentence_problem_type AS ENUM (
    'none',                    -- Correct phrase
    'conjugation',             -- Wrong verb conjugation  
    'pronoun_agreement',       -- Wrong pronoun agreement
    'object_placement',        -- Wrong object pronoun placement
    'negation_structure',      -- Wrong negation structure
    'auxiliary_choice',        -- Wrong auxiliary verb
    'reflexive_error',         -- Reflexive pronoun error
    'gender_agreement',        -- Gender agreement error
    'syntax',                  -- General syntax error
    'vocabulary'               -- Wrong word choice
);
*/

-- Modern sentences table
CREATE TABLE sentences (
    -- Core identification
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Timestamps (following Supabase conventions)
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Language and content
    target_language_code    CHAR(3) NOT NULL DEFAULT 'eng', 
    content                 TEXT NOT NULL,                   -- French phrase
    translation             TEXT NOT NULL,                   -- Translation in user's language
    
    -- Verb relationship (normalized!)
    verb_id                 UUID NOT NULL,  -- FK to verbs.id
    
    -- Grammatical structure
    pronoun                 pronoun NOT NULL,
    tense                   tense NOT NULL,
    direct_object           direct_object NOT NULL,
    indirect_object         indirect_object NOT NULL, 
    negation                negation NOT NULL,
    
    -- Correctness tracking (simplified - detailed problem analysis at service level)
    is_correct              BOOLEAN NOT NULL DEFAULT true,
    
    -- Optional metadata
    notes                   TEXT,
    source                  VARCHAR(100),  -- Where this phrase came from
    explanation             TEXT,
    
    -- Constraints
    CONSTRAINT sentences_verb_fk FOREIGN KEY (verb_id) REFERENCES verbs(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_sentences_verb_id ON sentences(verb_id);
CREATE INDEX idx_sentences_is_correct ON sentences(is_correct);
CREATE INDEX idx_sentences_created_at ON sentences(created_at);
CREATE INDEX idx_sentences_tense_pronoun ON sentences(tense, pronoun);  -- Common query pattern

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language plpgsql;

CREATE TRIGGER sentences_updated_at_trigger
    BEFORE UPDATE ON sentences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS (Row Level Security) - basic setup
ALTER TABLE sentences ENABLE ROW LEVEL SECURITY;

-- Basic RLS policy (adjust based on your auth requirements)
CREATE POLICY sentences_select_policy ON sentences
    FOR SELECT USING (true);  -- Adjust as needed

CREATE POLICY sentences_insert_policy ON sentences  
    FOR INSERT WITH CHECK (true);  -- Adjust as needed

CREATE POLICY sentences_update_policy ON sentences
    FOR UPDATE USING (true);  -- Adjust as needed

CREATE POLICY sentences_delete_policy ON sentences
    FOR DELETE USING (true);  -- Adjust as needed

-- Comments for documentation
COMMENT ON TABLE sentences IS 'Generated sentences with grammatical variations - problem analysis handled at service level';
COMMENT ON COLUMN sentences.target_language_code IS 'User''s native language for translations (English, Spanish, etc.)';
COMMENT ON COLUMN sentences.content IS 'French sentence';
COMMENT ON COLUMN sentences.translation IS 'Translation in the target language (user''s native language)';
COMMENT ON COLUMN sentences.is_correct IS 'Basic correctness flag - detailed problem analysis in separate problem/quiz system';
COMMENT ON COLUMN sentences.explanation IS 'Natural language explanation for incorrect sentences (from LLM)';
COMMENT ON COLUMN sentences.source IS 'Origin of the sentence (ai_generated, manual, imported, etc.)';
