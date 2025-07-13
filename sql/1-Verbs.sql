-- ===== VERBS SCHEMA FOR SUPABASE =====
-- Clean implementation with ISO-639-3 language codes and participles

-- DROP TABLE conjugations CASCADE;
-- DROP TABLE verbs CASCADE;

-- Enum types
CREATE TYPE auxiliary_type AS ENUM ('avoir', 'être');
CREATE TYPE verb_classification AS ENUM ('first_group', 'second_group', 'third_group');
CREATE TYPE tense AS ENUM (
    'present',
    'passe_compose', 
    'imparfait',
    'future_simple',
    'conditionnel',
    'subjonctif',
    'imperatif'
);

-- Verbs table
CREATE TABLE verbs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    infinitive TEXT NOT NULL,
    auxiliary auxiliary NOT NULL,
    reflexive BOOLEAN NOT NULL DEFAULT FALSE,
    target_language_code TEXT NOT NULL CHECK (target_language_code ~ '^[a-z]{3}$'),
    translation TEXT NOT NULL,
    past_participle TEXT NOT NULL,
    present_participle TEXT NOT NULL,
    classification verb_classification,
    is_irregular BOOLEAN NOT NULL DEFAULT FALSE,
    can_have_cod BOOLEAN NOT NULL DEFAULT TRUE,
    can_have_coi BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    CHECK (infinitive != ''),
    CHECK (translation != ''),
    CHECK (past_participle != ''),
    CHECK (present_participle != ''),
    UNIQUE(infinitive, auxiliary, reflexive, target_language_code, translation)
);

COMMENT ON COLUMN verbs.can_have_cod IS 'Whether this verb can take a direct object (COD) - useful for object pronoun problems';
COMMENT ON COLUMN verbs.can_have_coi IS 'Whether this verb can take an indirect object (COI) - useful for object pronoun problems';

-- Conjugations table
CREATE TABLE conjugations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    infinitive TEXT NOT NULL,
    auxiliary auxiliary NOT NULL,
    reflexive BOOLEAN NOT NULL,
    tense tense NOT NULL,
    first_person_singular TEXT,
    second_person_singular TEXT,
    third_person_singular TEXT,
    first_person_plural TEXT,
    second_person_formal TEXT,
    third_person_plural TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (infinitive != ''),
    UNIQUE(infinitive, auxiliary, reflexive, tense)
);

-- Indexes
CREATE INDEX idx_verbs_infinitive ON verbs(infinitive);
CREATE INDEX idx_verbs_auxiliary ON verbs(auxiliary);
CREATE INDEX idx_verbs_classification ON verbs(classification);
CREATE INDEX idx_verbs_target_language ON verbs(target_language_code);
CREATE INDEX idx_verbs_translation ON verbs(translation);
CREATE INDEX idx_verbs_past_participle ON verbs(past_participle);
CREATE INDEX idx_verbs_present_participle ON verbs(present_participle);
CREATE INDEX idx_verbs_infinitive_language ON verbs(infinitive, target_language_code);
CREATE INDEX idx_verbs_language_translation ON verbs(target_language_code, translation);
CREATE INDEX idx_verbs_cod_coi_support ON verbs(can_have_cod, can_have_coi) 

CREATE INDEX idx_conjugations_tense ON conjugations(tense);
CREATE INDEX idx_conjugations_infinitive ON conjugations(infinitive);
CREATE INDEX idx_conjugations_verb_form ON conjugations(infinitive, auxiliary, reflexive);
CREATE INDEX idx_conjugations_verb_tense ON conjugations(infinitive, auxiliary, reflexive, tense);

-- Auto-update triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_verbs_updated_at 
    BEFORE UPDATE ON verbs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conjugations_updated_at 
    BEFORE UPDATE ON conjugations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Utility functions
CREATE OR REPLACE FUNCTION get_random_verb_simple(
    p_target_language TEXT DEFAULT 'eng'
)
RETURNS TABLE (
    id UUID,
    infinitive TEXT,
    auxiliary auxiliary,
    reflexive BOOLEAN,
    translation TEXT,
    past_participle TEXT,
    present_participle TEXT,
    target_language_code TEXT,
    can_have_cod BOOLEAN,
    can_have_coi BOOLEAN,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
) AS $$
DECLARE
    tbl_count INT;
    rand_offset INT;
BEGIN
    SELECT count(*) INTO tbl_count FROM verbs WHERE verbs.target_language_code = p_target_language;
    rand_offset := floor(random() * tbl_count);

    RETURN QUERY
    SELECT v.id, v.infinitive, v.auxiliary, v.reflexive, v.translation, v.past_participle, v.present_participle, v.target_language_code, v.can_have_cod, v.can_have_coi, v.created_at, v.updated_at
    FROM verbs v
    WHERE v.target_language_code = p_target_language
    OFFSET rand_offset
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION validate_iso639_3_code(code TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN code ~ '^[a-z]{3}$';
END;
$$ LANGUAGE plpgsql;

-- RLS policies
ALTER TABLE verbs ENABLE ROW LEVEL SECURITY;
ALTER TABLE conjugations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable all operations for verbs" ON verbs FOR ALL USING (true);
CREATE POLICY "Enable all operations for conjugations" ON conjugations FOR ALL USING (true);

-- Example data with participles (commented for reference)
-- INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular) VALUES
-- ('être', 'être', false, 'fra', 'to be', 'été', 'étant', 'third_group', true),
-- ('avoir', 'avoir', false, 'fra', 'to have', 'eu', 'ayant', 'third_group', true),
-- ('aller', 'être', false, 'fra', 'to go', 'allé', 'allant', 'third_group', true),
-- ('faire', 'avoir', false, 'fra', 'to do/make', 'fait', 'faisant', 'third_group', true),
-- ('parler', 'avoir', false, 'fra', 'to speak', 'parlé', 'parlant', 'first_group', false),
-- ('finir', 'avoir', false, 'fra', 'to finish', 'fini', 'finissant', 'second_group', false);