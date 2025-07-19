-- ===== TEST VERB DATA =====
-- Pre-seed database with verbs that tests expect to exist

-- Insert test verbs that API tests expect to find
INSERT INTO verbs (
    infinitive, 
    auxiliary, 
    reflexive, 
    target_language_code, 
    translation, 
    past_participle, 
    present_participle, 
    classification, 
    is_irregular,
    can_have_cod,
    can_have_coi
) VALUES 
-- parler - expected to exist in download conflict test
(
    'parler', 
    'avoir', 
    false, 
    'eng', 
    'to speak', 
    'parlé', 
    'parlant', 
    'first_group', 
    false,
    true,
    false
),
-- être - common irregular verb for comprehensive testing
(
    'être', 
    'être', 
    false, 
    'eng', 
    'to be', 
    'été', 
    'étant', 
    'third_group', 
    true,
    false,
    false
),
-- avoir - common irregular verb for comprehensive testing
(
    'avoir', 
    'avoir', 
    false, 
    'eng', 
    'to have', 
    'eu', 
    'ayant', 
    'third_group', 
    true,
    true,
    true
);

-- Insert basic conjugations for the test verbs
INSERT INTO conjugations (
    infinitive,
    auxiliary,
    reflexive,
    tense,
    first_person_singular,
    second_person_singular,
    third_person_singular,
    first_person_plural,
    second_person_plural,
    third_person_plural
) VALUES
-- parler present tense
(
    'parler',
    'avoir',
    false,
    'present',
    'parle',
    'parles', 
    'parle',
    'parlons',
    'parlez',
    'parlent'
),
-- être present tense
(
    'être',
    'être',
    false,
    'present',
    'suis',
    'es',
    'est', 
    'sommes',
    'êtes',
    'sont'
),
-- avoir present tense
(
    'avoir',
    'avoir', 
    false,
    'present',
    'ai',
    'as',
    'a',
    'avons',
    'avez',
    'ont'
);

-- Verify the test data was inserted
DO $$
DECLARE
    verb_count INTEGER;
    conjugation_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO verb_count FROM verbs WHERE target_language_code = 'eng';
    SELECT COUNT(*) INTO conjugation_count FROM conjugations;
    
    RAISE NOTICE 'Inserted % test verbs and % conjugations', verb_count, conjugation_count;
    
    IF verb_count < 3 THEN
        RAISE EXCEPTION 'Expected at least 3 test verbs, but found %', verb_count;
    END IF;
    
    IF conjugation_count < 3 THEN  
        RAISE EXCEPTION 'Expected at least 3 test conjugations, but found %', conjugation_count;
    END IF;
END $$; 