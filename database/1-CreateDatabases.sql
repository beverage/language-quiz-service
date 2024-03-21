--  Database initial ideas.
CREATE TYPE direct_pronoun   AS ENUM ('la', 'le', 'les');
CREATE TYPE indirect_pronoun AS ENUM ('lui', 'leur');

--  Some verbs work both with and without a reflexive pronoun.  Verbs that
--  do not, or can do both, will all stored in their 'se <verb>' form:
CREATE TYPE reflexive_pronoun AS ENUM ('me', 'te', 'se');
CREATE TYPE reflexivity AS ENUM ('no', 'conditional', 'mandatory');

--  Some verbs can support either:
CREATE TYPE auxiliary AS ENUM ('avoir', 'être');

--  Aucun needs to match gender:
CREATE TYPE negation AS ENUM ('pas', 'jamais', 'rien', 'personne', 'plus', 'aucun', 'encore'); 

--  This structure needs reconsideration:
--
--  Modes and tenses.  There are exact combinations that need to be pre-loaded here:
-- CREATE TYPE mode  AS ENUM('indicative', 'subjunctive', 'imperative', 'infinitive', 'participle');
-- CREATE TYPE tense AS ENUM('present', 'passe_compose', 'imparfait', 'conditionnel présent');
CREATE TYPE tense AS ENUM('present', 'passe_compose', 'imparfait', 'future_simple', 'participle');

--  This represents a common suffix for groups of verbs:
CREATE TABLE verb_groups (
    id              serial      primary key,
    example         varchar     not null,
    suffix          varchar     not null,
    classification  smallint    not null check (classification >= 1 and classification <= 3),

    unique(example, suffix)
);

--  This represents a verb within a group above:
CREATE TABLE verbs (
    id              serial  primary key,
    -- group_id        serial  not null references verb_groups (id),
    infinitive      varchar not null,
    auxiliary       varchar not null,
    reflexivity     reflexivity not null default 'no'
);

--  This represents a conjugation for a valid tense of a verb above:
CREATE TABLE conjugations (
    id                          serial   primary key,
--    verb_id                     serial   not null references verbs (id),
--    mode                        mode     not null,
    tense                       tense    not null,
    infinitive                  varchar  not null,  --  <- key this.
    first_person_singular       varchar,
    second_person_singular      varchar,
    third_person_singular       varchar,
    first_person_plural         varchar,
    second_person_formal        varchar,
    third_person_plural         varchar
);

--  These are actually slowdowns at small scale.  Try bringing it back later:
--  CREATE INDEX IF NOT EXISTS conjugation_index ON conjugations (infinitive);
--  CREATE INDEX IF NOT EXISTS conjugation_index ON conjugations (infinitive, tense);

--  This represents a sentence formed, either correct or incorrect, using
--  a selected verb as a question, and it's incorrect answers:
CREATE TABLE sentences (
    id                  serial              primary key,    
    verb_conjugation    serial              not null references conjugations (id),
    content             varchar             not null,
    correct             boolean             not null,
    reflexive_pronoun   reflexive_pronoun,
    direct_pronoun      direct_pronoun,
    indirect_pronoun    indirect_pronoun,
    negation            negation
);
