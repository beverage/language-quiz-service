--  Database initial ideas.
-- CREATE TYPE pronoun          AS ENUM ('je', 'tu', 'on', 'il', 'elle', 'nous', 'vous', 'ils', 'elles');
-- CREATE TYPE direct_pronoun   AS ENUM ('la', 'le', 'les');
-- CREATE TYPE indirect_pronoun AS ENUM ('lui', 'leur');

CREATE TYPE pronoun          AS ENUM ('first_person', 'second_person', 'third_person', 'first_person_plural', 'second_person_plural', 'third_person_plural');
CREATE TYPE direct_object    AS ENUM ('none', 'masculine', 'feminine', 'plural');
CREATE TYPE indirect_object  AS ENUM ('none', 'masculine', 'feminine', 'plural');

--  Some verbs work both with and without a reflexive pronoun.  Verbs that
--  do not, or can do both, will all stored in their 'se <verb>' form:
CREATE TYPE reflexive_pronoun AS ENUM ('none', 'me', 'te', 'se');
CREATE TYPE reflexivity AS ENUM ('no', 'yes');

--  Some verbs can support either:
CREATE TYPE auxiliary AS ENUM ('avoir', 'être');

--  Aucun needs to match gender:
CREATE TYPE negation AS ENUM ('none', 'pas', 'jamais', 'rien', 'personne', 'plus', 'aucun', 'encore'); 

--  This structure needs reconsideration:
--
--  Modes and tenses.  There are exact combinations that need to be pre-loaded here:
-- CREATE TYPE mode  AS ENUM('indicative', 'subjunctive', 'imperative', 'infinitive', 'participle');
-- CREATE TYPE tense AS ENUM('present', 'passe_compose', 'imperfect', 'conditionnel présent');
CREATE TYPE tense AS ENUM('present', 'passe_compose', 'imparfait', 'future_simple', 'participle');

--  This represents a common suffix for groups of verbs:
CREATE TABLE verb_groups (
    id              serial      primary key,
    name            varchar     not null,
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
    auxiliary       varchar not null
);

--  This represents a conjugation for a valid tense of a verb above:
CREATE TABLE conjugations (
    id                          serial   primary key,
    verb_id                     serial   not null references verbs (id) on delete cascade,
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
    infinitive          varchar             not null,
    auxiliary           varchar             not null,
    pronoun             pronoun             not null,
    tense               tense               not null,
    direct_object       direct_object       not null,
    indirect_object     indirect_object     not null,
    reflexive_pronoun   reflexive_pronoun   not null,
    negation            negation            not null,
    content             varchar             not null,
    translation         varchar             not null,
    is_correct          boolean             default true
);
