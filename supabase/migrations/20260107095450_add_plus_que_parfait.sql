-- Add plus-que-parfait tense to the tense enum
-- The plus-que-parfait (pluperfect) expresses an action completed before another past action
-- Formation: auxiliary (avoir/être) in imparfait + past participle

ALTER TYPE tense ADD VALUE 'plus_que_parfait';
