-- Migration: Initial Verb List
-- Created: 2025-10-23
-- Description: Adds curated list of 107 essential French verbs with grammatical properties
--
-- This migration establishes the foundational verb vocabulary for the language quiz service.
-- Each verb includes:
--   - Infinitive form and auxiliary verb (avoir or être)
--   - Reflexivity status
--   - Translation to English
--   - Participle forms (past and present)
--   - Verb classification (first, second, or third group)
--   - Irregularity status
--   - Direct/indirect object compatibility (COD/COI flags)
--
-- IDEMPOTENCY & USAGE:
-- This migration is idempotent and can be safely rerun to:
--   1. Fix incorrect verb properties in existing data (updates via ON CONFLICT)
--   2. Restore missing verbs that were accidentally deleted
--   3. Update translations, classifications, or COD/COI flags
--
-- IMPORTANT NOTES:
--   - Rerunning will NOT delete extra verbs - only upserts the 107 defined here
--   - Conjugations must be downloaded separately via `lqs database init` or the API
--   - Unique constraint: (infinitive, auxiliary, reflexive, target_language_code, translation)
--
-- PRODUCTION DEPLOYMENT:
--   - Safe to run on production database (upsert logic prevents duplicates)
--   - Minimal downtime (individual row-level locks only)
--   - No data loss (existing conjugations are preserved)
--   - Run after schema migrations but before downloading conjugations
--
-- =============================================================================

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('aimer', 'avoir'::auxiliary, false, 'eng', 'to love', 'aimé', 'aimant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('aller', 'être'::auxiliary, false, 'eng', 'to go', 'allé', 'allant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('appartenir', 'avoir'::auxiliary, false, 'eng', 'to belong', 'appartenus', 'appartenant', 'third_group'::verb_classification, false, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('apprendre', 'avoir'::auxiliary, false, 'eng', 'to learn', 'appris', 'apprenant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('arriver', 'être'::auxiliary, false, 'eng', 'to arrive', 'arrivé', 'arrivant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('attendre', 'avoir'::auxiliary, false, 'eng', 'to wait', 'attendu', 'attendant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('avoir', 'avoir'::auxiliary, false, 'eng', 'to have', 'eu', 'ayant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('bâiller', 'avoir'::auxiliary, false, 'eng', 'to yawn', 'bâillé', 'bâillant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('boire', 'avoir'::auxiliary, false, 'eng', 'to drink', 'bu', 'buvant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('chanter', 'avoir'::auxiliary, false, 'eng', 'to sing', 'chanté', 'chantant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('choisir', 'avoir'::auxiliary, false, 'eng', 'to choose', 'choisi', 'choisissant', 'second_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('chuchoter', 'avoir'::auxiliary, false, 'eng', 'to whisper', 'chuchoté', 'chuchotant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('comprendre', 'avoir'::auxiliary, false, 'eng', 'to understand', 'compris', 'comprenant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('confier', 'avoir'::auxiliary, false, 'eng', 'to entrust', 'confié', 'confiant', 'first_group'::verb_classification, false, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('courir', 'avoir'::auxiliary, false, 'eng', 'to run', 'couru', 'courant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('croire', 'avoir'::auxiliary, false, 'eng', 'to believe', 'cru', 'croyant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('découvrir', 'avoir'::auxiliary, false, 'eng', 'to discover', 'découvert', 'découvrant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('décrire', 'avoir'::auxiliary, false, 'eng', 'to describe', 'décrit', 'décrivant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('demander', 'avoir'::auxiliary, false, 'eng', 'to ask', 'demandé', 'demandant', 'first_group'::verb_classification, false, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('descendre', 'être'::auxiliary, false, 'eng', 'to go down, to descend', 'descendu', 'descendant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('devenir', 'être'::auxiliary, false, 'eng', 'to become', 'devenu', 'devenant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('devoir', 'avoir'::auxiliary, false, 'eng', 'to have to, must', 'dû', 'devant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('dire', 'avoir'::auxiliary, false, 'eng', 'to say', 'dit', 'disant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('donner', 'avoir'::auxiliary, false, 'eng', 'to give', 'donné', 'donnant', 'first_group'::verb_classification, false, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('dormir', 'avoir'::auxiliary, false, 'eng', 'to sleep', 'dormi', 'dormant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('écrire', 'avoir'::auxiliary, false, 'eng', 'to write', 'écrit', 'écrivant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('enseigner', 'avoir'::auxiliary, false, 'eng', 'to teach', 'enseigné', 'enseignant', 'first_group'::verb_classification, false, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('entendre', 'avoir'::auxiliary, false, 'eng', 'to hear', 'entendu', 'entendant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('entrer', 'être'::auxiliary, false, 'eng', 'to enter', 'entré', 'entrant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('épeler', 'avoir'::auxiliary, false, 'eng', 'to spell', 'épelé', 'épelenant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('être', 'avoir'::auxiliary, false, 'eng', 'to be', 'été', 'étant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('étudier', 'avoir'::auxiliary, false, 'eng', 'to study', 'étudié', 'étudiant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('expliquer', 'avoir'::auxiliary, false, 'eng', 'to explain', 'expliqué', 'expliquant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('faire', 'avoir'::auxiliary, false, 'eng', 'to do, to make', 'fait', 'faisant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('finir', 'avoir'::auxiliary, false, 'eng', 'to finish', 'fini', 'finissant', 'second_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('flairer', 'avoir'::auxiliary, false, 'eng', 'to smell', 'flairé', 'flairant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('grincer', 'avoir'::auxiliary, false, 'eng', 'to creak', 'grincé', 'grinçant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('jouer', 'avoir'::auxiliary, false, 'eng', 'to play', 'joué', 'jouant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('lire', 'avoir'::auxiliary, false, 'eng', 'to read', 'lu', 'lisant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('manger', 'avoir'::auxiliary, false, 'eng', 'to eat', 'mangé', 'mangeant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('méditer', 'avoir'::auxiliary, false, 'eng', 'to meditate', 'médité', 'méditant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('mettre', 'avoir'::auxiliary, false, 'eng', 'to put', 'mis', 'mettant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('monter', 'être'::auxiliary, false, 'eng', 'to go up, to climb', 'monté', 'montant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('montrer', 'avoir'::auxiliary, false, 'eng', 'to show', 'montré', 'montrant', 'first_group'::verb_classification, false, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('mourir', 'être'::auxiliary, false, 'eng', 'to die', 'mort', 'mourant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('murmurer', 'avoir'::auxiliary, false, 'eng', 'to murmur', 'murmuré', 'murmurant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('naître', 'être'::auxiliary, false, 'eng', 'to be born', 'né', 'naissant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('obéir', 'avoir'::auxiliary, false, 'eng', 'to obey', 'obéi', 'obéissant', 'second_group'::verb_classification, false, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('offrir', 'avoir'::auxiliary, false, 'eng', 'to offer', 'offert', 'offrant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('ouvrir', 'avoir'::auxiliary, false, 'eng', 'to open', 'ouvert', 'ouvrant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('parler', 'avoir'::auxiliary, false, 'eng', 'to speak', 'parlé', 'parlant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('partir', 'être'::auxiliary, false, 'eng', 'to leave', 'parti', 'partant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('passer', 'être'::auxiliary, false, 'eng', 'to pass', 'passé', 'passant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('penser', 'avoir'::auxiliary, false, 'eng', 'to think', 'pensé', 'pensant', 'first_group'::verb_classification, false, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('perdre', 'avoir'::auxiliary, false, 'eng', 'to lose', 'perdu', 'perdant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('permettre', 'avoir'::auxiliary, false, 'eng', 'to allow', 'permis', 'permettant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('plaire', 'avoir'::auxiliary, false, 'eng', 'to please', 'plu', 'plaisant', 'third_group'::verb_classification, true, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('pouvoir', 'avoir'::auxiliary, false, 'eng', 'to be able to, can', 'pu', 'pouvant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('prendre', 'avoir'::auxiliary, false, 'eng', 'to take', 'pris', 'prenant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('promettre', 'avoir'::auxiliary, false, 'eng', 'to promise', 'promis', 'promettant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('réfléchir', 'avoir'::auxiliary, false, 'eng', 'to reflect', 'réfléchi', 'réfléchissant', 'second_group'::verb_classification, false, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('regarder', 'avoir'::auxiliary, false, 'eng', 'to watch', 'regardé', 'regardant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('rentrer', 'être'::auxiliary, false, 'eng', 'to return', 'rentré', 'rentrant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('répondre', 'avoir'::auxiliary, false, 'eng', 'to respond', 'répondu', 'répondant', 'third_group'::verb_classification, true, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('ressembler', 'avoir'::auxiliary, false, 'eng', 'to resemble', 'resemblé', 'ressemblant', 'first_group'::verb_classification, false, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('rester', 'être'::auxiliary, false, 'eng', 'to stay', 'resté', 'restant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('retourner', 'être'::auxiliary, false, 'eng', 'to return', 'retourné', 'retournant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('réussir', 'avoir'::auxiliary, false, 'eng', 'to succeed', 'réussi', 'réussissant', 'second_group'::verb_classification, false, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('révéler', 'avoir'::auxiliary, false, 'eng', 'to reveal', 'révélé', 'révélant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('revenir', 'être'::auxiliary, false, 'eng', 'to come back', 'revenu', 'revenant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('ricaner', 'avoir'::auxiliary, false, 'eng', 'to sneer', 'ricané', 'ricanant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('rire', 'avoir'::auxiliary, false, 'eng', 'to laugh', 'ri', 'riant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('s''appeler', 'être'::auxiliary, true, 'eng', 'to be called', 'appelé', 's''appelant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('s''arrêter', 'être'::auxiliary, true, 'eng', 'to stop', 'arrêté', 's''arrêtant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('s''asseoir', 'être'::auxiliary, true, 'eng', 'to sit down', 'assis', 's''asseyant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('s''habiller', 'être'::auxiliary, true, 'eng', 'to get dressed', 'habillé', 's''habillant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('savoir', 'avoir'::auxiliary, false, 'eng', 'to know', 'su', 'sachant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('se coucher', 'être'::auxiliary, true, 'eng', 'to go to bed', 'couché', 'couchant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('se laver', 'être'::auxiliary, true, 'eng', 'to wash oneself', 'lavé', 'se lavant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('se lever', 'être'::auxiliary, true, 'eng', 'to get up', 'levé', 'se levant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('se promener', 'être'::auxiliary, true, 'eng', 'to take a walk', 'promené', 'promenant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('se sentir', 'être'::auxiliary, true, 'eng', 'to feel', 'senti', 'se sentant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('se souvenir', 'être'::auxiliary, true, 'eng', 'to remember', 'souvenu', 'se souvenant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('sentir', 'avoir'::auxiliary, false, 'eng', 'to feel', 'senti', 'sentant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('servir', 'avoir'::auxiliary, false, 'eng', 'to serve', 'servi', 'servant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('sortir', 'être'::auxiliary, false, 'eng', 'to go out', 'sorti', 'sortant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('soupirer', 'avoir'::auxiliary, false, 'eng', 'to sigh', 'soupiré', 'soupirant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('sourire', 'avoir'::auxiliary, false, 'eng', 'to smile', 'souri', 'souriant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('suivre', 'avoir'::auxiliary, false, 'eng', 'to follow', 'suivi', 'suivant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('téléphoner', 'avoir'::auxiliary, false, 'eng', 'to phone', 'téléphoné', 'téléphonant', 'first_group'::verb_classification, false, false, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('tenir', 'avoir'::auxiliary, false, 'eng', 'to hold', 'tenu', 'tenant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('tomber', 'être'::auxiliary, false, 'eng', 'to fall', 'tombé', 'tombant', 'first_group'::verb_classification, false, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('travailler', 'avoir'::auxiliary, false, 'eng', 'to work', 'travaillé', 'travaillant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('trouver', 'avoir'::auxiliary, false, 'eng', 'to find', 'trouvé', 'trouvant', 'first_group'::verb_classification, false, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('vendre', 'avoir'::auxiliary, false, 'eng', 'to sell', 'vendu', 'vendant', 'third_group'::verb_classification, true, true, true)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('venir', 'être'::auxiliary, false, 'eng', 'to come', 'venu', 'venant', 'third_group'::verb_classification, true, false, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('vivre', 'avoir'::auxiliary, false, 'eng', 'to live', 'vécu', 'vivant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('voir', 'avoir'::auxiliary, false, 'eng', 'to see', 'vu', 'voyant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

INSERT INTO verbs (infinitive, auxiliary, reflexive, target_language_code, translation, past_participle, present_participle, classification, is_irregular, can_have_cod, can_have_coi)
VALUES ('vouloir', 'avoir'::auxiliary, false, 'eng', 'to want', 'voulu', 'voulant', 'third_group'::verb_classification, true, true, false)
ON CONFLICT (infinitive, auxiliary, reflexive, target_language_code, translation)
DO UPDATE SET
  translation = EXCLUDED.translation,
  past_participle = EXCLUDED.past_participle,
  present_participle = EXCLUDED.present_participle,
  classification = EXCLUDED.classification,
  is_irregular = EXCLUDED.is_irregular,
  can_have_cod = EXCLUDED.can_have_cod,
  can_have_coi = EXCLUDED.can_have_coi,
  updated_at = now();

