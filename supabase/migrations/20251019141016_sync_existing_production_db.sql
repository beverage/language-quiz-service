

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






DO $$ 
BEGIN
    CREATE TYPE "public"."auxiliary" AS ENUM (
        'avoir',
        'être'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."auxiliary" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."direct_object" AS ENUM (
        'none',
        'masculine',
        'feminine',
        'plural'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."direct_object" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."indirect_object" AS ENUM (
        'none',
        'masculine',
        'feminine',
        'plural'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."indirect_object" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."negation" AS ENUM (
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
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."negation" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."problem_type" AS ENUM (
        'grammar',
        'functional',
        'vocabulary'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."problem_type" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."pronoun" AS ENUM (
        'first_person',
        'second_person',
        'third_person',
        'first_person_plural',
        'second_person_plural',
        'third_person_plural'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."pronoun" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."reflexive_pronoun" AS ENUM (
        'none',
        'first_person',
        'second_person',
        'third_person'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."reflexive_pronoun" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."reflexivity" AS ENUM (
        'no',
        'yes'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."reflexivity" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."tense" AS ENUM (
        'present',
        'passe_compose',
        'imparfait',
        'future_simple',
        'conditionnel',
        'subjonctif',
        'imperatif'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."tense" OWNER TO "postgres";


DO $$ 
BEGIN
    CREATE TYPE "public"."verb_classification" AS ENUM (
        'first_group',
        'second_group',
        'third_group'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

ALTER TYPE "public"."verb_classification" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_random_verb_simple"("p_target_language" "text" DEFAULT 'eng'::"text") RETURNS TABLE("id" "uuid", "infinitive" "text", "auxiliary" "public"."auxiliary", "reflexive" boolean, "translation" "text", "past_participle" "text", "present_participle" "text", "target_language_code" "text", "created_at" timestamp with time zone, "updated_at" timestamp with time zone)
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    tbl_count INT;
    rand_offset INT;
BEGIN
    SELECT count(*) INTO tbl_count FROM verbs WHERE verbs.target_language_code = p_target_language;
    rand_offset := floor(random() * tbl_count);

    RETURN QUERY
    SELECT v.id, v.infinitive, v.auxiliary, v.reflexive, v.translation, v.past_participle, v.present_participle, v.target_language_code, v.created_at, v.updated_at
    FROM verbs v
    WHERE v.target_language_code = p_target_language
    OFFSET rand_offset
    LIMIT 1;
END;
$$;


ALTER FUNCTION "public"."get_random_verb_simple"("p_target_language" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."increment_api_key_usage"("key_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    UPDATE api_keys 
    SET 
        usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE id = key_id;
END;
$$;


ALTER FUNCTION "public"."increment_api_key_usage"("key_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_api_keys_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_api_keys_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."validate_iso639_3_code"("code" "text") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $_$
BEGIN
    RETURN code ~ '^[a-z]{3}$';
END;
$_$;


ALTER FUNCTION "public"."validate_iso639_3_code"("code" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."validate_problem_statements"("prob_type" "public"."problem_type", "statements" "jsonb") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
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
$$;


ALTER FUNCTION "public"."validate_problem_statements"("prob_type" "public"."problem_type", "statements" "jsonb") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."api_keys" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "key_hash" "text" NOT NULL,
    "key_prefix" "text" NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "client_name" "text",
    "is_active" boolean DEFAULT true NOT NULL,
    "permissions_scope" "text"[] DEFAULT ARRAY['read'::"text"],
    "allowed_ips" "text"[],
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "last_used_at" timestamp with time zone,
    "usage_count" bigint DEFAULT 0,
    "rate_limit_rpm" integer DEFAULT 100,
    CONSTRAINT "api_keys_key_hash_check" CHECK (("key_hash" <> ''::"text")),
    CONSTRAINT "api_keys_key_prefix_check" CHECK (("key_prefix" <> ''::"text")),
    CONSTRAINT "api_keys_name_check" CHECK (("name" <> ''::"text")),
    CONSTRAINT "api_keys_rate_limit_rpm_check" CHECK (("rate_limit_rpm" > 0))
);


ALTER TABLE "public"."api_keys" OWNER TO "postgres";


COMMENT ON TABLE "public"."api_keys" IS 'API keys for service-to-service authentication';



COMMENT ON COLUMN "public"."api_keys"."key_hash" IS 'Hashed API key using bcrypt - never store plain text';



COMMENT ON COLUMN "public"."api_keys"."key_prefix" IS 'First 12 characters of key for identification (e.g., sk_live_abcd)';



COMMENT ON COLUMN "public"."api_keys"."permissions_scope" IS 'Array of permissions: read, write, admin';



COMMENT ON COLUMN "public"."api_keys"."allowed_ips" IS 'Optional IP allowlist in CIDR notation (e.g., ["192.168.1.0/24", "203.0.113.42/32"])';



COMMENT ON COLUMN "public"."api_keys"."usage_count" IS 'Total number of requests made with this key';



COMMENT ON COLUMN "public"."api_keys"."rate_limit_rpm" IS 'Requests per minute limit for this key';



CREATE TABLE IF NOT EXISTS "public"."conjugations" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "infinitive" "text" NOT NULL,
    "auxiliary" "public"."auxiliary" NOT NULL,
    "reflexive" boolean NOT NULL,
    "tense" "public"."tense" NOT NULL,
    "first_person_singular" "text",
    "second_person_singular" "text",
    "third_person_singular" "text",
    "first_person_plural" "text",
    "second_person_plural" "text",
    "third_person_plural" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    CONSTRAINT "conjugations_infinitive_check" CHECK (("infinitive" <> ''::"text"))
);


ALTER TABLE "public"."conjugations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."problems" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "problem_type" "public"."problem_type" NOT NULL,
    "title" "text",
    "instructions" "text" NOT NULL,
    "correct_answer_index" integer NOT NULL,
    "target_language_code" character(3) DEFAULT 'eng'::"bpchar" NOT NULL,
    "statements" "jsonb" NOT NULL,
    "topic_tags" "text"[],
    "source_statement_ids" "uuid"[],
    "metadata" "jsonb",
    CONSTRAINT "correct_index_within_bounds" CHECK (("correct_answer_index" < "jsonb_array_length"("statements"))),
    CONSTRAINT "statements_not_empty" CHECK (("jsonb_array_length"("statements") > 0)),
    CONSTRAINT "valid_correct_index" CHECK (("correct_answer_index" >= 0)),
    CONSTRAINT "valid_statements_array" CHECK (("jsonb_typeof"("statements") = 'array'::"text")),
    CONSTRAINT "valid_statements_for_type" CHECK ("public"."validate_problem_statements"("problem_type", "statements"))
);


ALTER TABLE "public"."problems" OWNER TO "postgres";


COMMENT ON TABLE "public"."problems" IS 'Universal atomic problems for grammar, functional, and vocabulary learning';



COMMENT ON COLUMN "public"."problems"."problem_type" IS 'Top-level problem category: grammar, functional, or vocabulary';



COMMENT ON COLUMN "public"."problems"."target_language_code" IS 'User''s native language for translations and explanations (source is always French)';



COMMENT ON COLUMN "public"."problems"."statements" IS 'Self-contained JSONB array - structure varies by problem_type';



COMMENT ON COLUMN "public"."problems"."topic_tags" IS 'Universal topic tags like food, animals, daily_activities, restaurant_situations';



COMMENT ON COLUMN "public"."problems"."source_statement_ids" IS 'Array of source statement IDs (sentences, vocab items, scenarios, etc.)';



COMMENT ON COLUMN "public"."problems"."metadata" IS 'Type-specific metadata including difficulty, learning objectives, and domain-specific fields';



CREATE TABLE IF NOT EXISTS "public"."sentences" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "target_language_code" character(3) DEFAULT 'eng'::"bpchar" NOT NULL,
    "content" "text" NOT NULL,
    "translation" "text" NOT NULL,
    "verb_id" "uuid" NOT NULL,
    "pronoun" "public"."pronoun" NOT NULL,
    "tense" "public"."tense" NOT NULL,
    "direct_object" "public"."direct_object" NOT NULL,
    "indirect_object" "public"."indirect_object" NOT NULL,
    "negation" "public"."negation" NOT NULL,
    "is_correct" boolean DEFAULT true NOT NULL,
    "notes" "text",
    "source" character varying(100),
    "explanation" "text"
);


ALTER TABLE "public"."sentences" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."verbs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "infinitive" "text" NOT NULL,
    "auxiliary" "public"."auxiliary" NOT NULL,
    "reflexive" boolean DEFAULT false NOT NULL,
    "target_language_code" "text" NOT NULL,
    "translation" "text" NOT NULL,
    "past_participle" "text" NOT NULL,
    "present_participle" "text" NOT NULL,
    "classification" "public"."verb_classification",
    "is_irregular" boolean DEFAULT false NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "last_used_at" timestamp with time zone,
    "can_have_cod" boolean DEFAULT true NOT NULL,
    "can_have_coi" boolean DEFAULT true NOT NULL,
    CONSTRAINT "verbs_infinitive_check" CHECK (("infinitive" <> ''::"text")),
    CONSTRAINT "verbs_past_participle_check" CHECK (("past_participle" <> ''::"text")),
    CONSTRAINT "verbs_present_participle_check" CHECK (("present_participle" <> ''::"text")),
    CONSTRAINT "verbs_target_language_code_check" CHECK (("target_language_code" ~ '^[a-z]{3}$'::"text")),
    CONSTRAINT "verbs_translation_check" CHECK (("translation" <> ''::"text"))
);


ALTER TABLE "public"."verbs" OWNER TO "postgres";


COMMENT ON COLUMN "public"."verbs"."can_have_cod" IS 'Whether this verb can take a direct object (COD) - useful for object pronoun problems';



COMMENT ON COLUMN "public"."verbs"."can_have_coi" IS 'Whether this verb can take an indirect object (COI) - useful for object pronoun problems';



CREATE OR REPLACE VIEW "public"."verbs_for_object_problems" AS
 SELECT "id",
    "infinitive",
    "auxiliary",
    "reflexive",
    "target_language_code",
    "translation",
    "past_participle",
    "present_participle",
    "classification",
    "is_irregular",
    "created_at",
    "updated_at",
    "last_used_at",
    "can_have_cod",
    "can_have_coi",
        CASE
            WHEN (("can_have_cod" = true) AND ("can_have_coi" = true)) THEN 'both'::"text"
            WHEN ("can_have_cod" = true) THEN 'cod_only'::"text"
            WHEN ("can_have_coi" = true) THEN 'coi_only'::"text"
            ELSE 'neither'::"text"
        END AS "object_capability"
   FROM "public"."verbs" "v"
  WHERE (("can_have_cod" = true) OR ("can_have_coi" = true));


ALTER VIEW "public"."verbs_for_object_problems" OWNER TO "postgres";


COMMENT ON VIEW "public"."verbs_for_object_problems" IS 'Verbs that can be used for COD/COI pronoun placement problems';



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'api_keys_key_hash_key' 
        AND conrelid = 'public.api_keys'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."api_keys"
            ADD CONSTRAINT "api_keys_key_hash_key" UNIQUE ("key_hash");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'api_keys_pkey' 
        AND conrelid = 'public.api_keys'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."api_keys"
            ADD CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'conjugations_infinitive_auxiliary_reflexive_tense_key' 
        AND conrelid = 'public.conjugations'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."conjugations"
            ADD CONSTRAINT "conjugations_infinitive_auxiliary_reflexive_tense_key" UNIQUE ("infinitive", "auxiliary", "reflexive", "tense");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'conjugations_pkey' 
        AND conrelid = 'public.conjugations'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."conjugations"
            ADD CONSTRAINT "conjugations_pkey" PRIMARY KEY ("id");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'problems_pkey' 
        AND conrelid = 'public.problems'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."problems"
            ADD CONSTRAINT "problems_pkey" PRIMARY KEY ("id");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'problems_title_type_unique' 
        AND conrelid = 'public.problems'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."problems"
            ADD CONSTRAINT "problems_title_type_unique" UNIQUE ("title", "problem_type");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'sentences_pkey' 
        AND conrelid = 'public.sentences'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."sentences"
            ADD CONSTRAINT "sentences_pkey" PRIMARY KEY ("id");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'verbs_infinitive_auxiliary_reflexive_target_language_code_t_key' 
        AND conrelid = 'public.verbs'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."verbs"
            ADD CONSTRAINT "verbs_infinitive_auxiliary_reflexive_target_language_code_t_key" UNIQUE ("infinitive", "auxiliary", "reflexive", "target_language_code", "translation");
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'verbs_pkey' 
        AND conrelid = 'public.verbs'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."verbs"
            ADD CONSTRAINT "verbs_pkey" PRIMARY KEY ("id");
    END IF;
END $$;



CREATE INDEX IF NOT EXISTS "idx_api_keys_active" ON "public"."api_keys" USING "btree" ("is_active");



CREATE INDEX IF NOT EXISTS "idx_api_keys_created_at" ON "public"."api_keys" USING "btree" ("created_at");



CREATE INDEX IF NOT EXISTS "idx_api_keys_key_hash" ON "public"."api_keys" USING "btree" ("key_hash");



CREATE INDEX IF NOT EXISTS "idx_api_keys_last_used" ON "public"."api_keys" USING "btree" ("last_used_at");



CREATE INDEX IF NOT EXISTS "idx_conjugations_infinitive" ON "public"."conjugations" USING "btree" ("infinitive");



CREATE INDEX IF NOT EXISTS "idx_conjugations_tense" ON "public"."conjugations" USING "btree" ("tense");



CREATE INDEX IF NOT EXISTS "idx_conjugations_verb_form" ON "public"."conjugations" USING "btree" ("infinitive", "auxiliary", "reflexive");



CREATE INDEX IF NOT EXISTS "idx_conjugations_verb_tense" ON "public"."conjugations" USING "btree" ("infinitive", "auxiliary", "reflexive", "tense");



CREATE INDEX IF NOT EXISTS "idx_problems_created_at" ON "public"."problems" USING "btree" ("created_at");



CREATE INDEX IF NOT EXISTS "idx_problems_metadata_gin" ON "public"."problems" USING "gin" ("metadata");



CREATE INDEX IF NOT EXISTS "idx_problems_metadata_updated_at" ON "public"."problems" USING "btree" ((("metadata" ->> 'updated_at'::"text")));



CREATE INDEX IF NOT EXISTS "idx_problems_source_statements_gin" ON "public"."problems" USING "gin" ("source_statement_ids");



CREATE INDEX IF NOT EXISTS "idx_problems_statements_gin" ON "public"."problems" USING "gin" ("statements");



CREATE INDEX IF NOT EXISTS "idx_problems_target_language" ON "public"."problems" USING "btree" ("target_language_code");



CREATE INDEX IF NOT EXISTS "idx_problems_topic_tags_gin" ON "public"."problems" USING "gin" ("topic_tags");



CREATE INDEX IF NOT EXISTS "idx_problems_type" ON "public"."problems" USING "btree" ("problem_type");



CREATE INDEX IF NOT EXISTS "idx_verbs_auxiliary" ON "public"."verbs" USING "btree" ("auxiliary");



CREATE INDEX IF NOT EXISTS "idx_verbs_classification" ON "public"."verbs" USING "btree" ("classification");



CREATE INDEX IF NOT EXISTS "idx_verbs_cod_coi_support" ON "public"."verbs" USING "btree" ("can_have_cod", "can_have_coi") WHERE (("can_have_cod" IS NOT NULL) OR ("can_have_coi" IS NOT NULL));



CREATE INDEX IF NOT EXISTS "idx_verbs_infinitive" ON "public"."verbs" USING "btree" ("infinitive");



CREATE INDEX IF NOT EXISTS "idx_verbs_infinitive_language" ON "public"."verbs" USING "btree" ("infinitive", "target_language_code");



CREATE INDEX IF NOT EXISTS "idx_verbs_language_translation" ON "public"."verbs" USING "btree" ("target_language_code", "translation");



CREATE INDEX IF NOT EXISTS "idx_verbs_past_participle" ON "public"."verbs" USING "btree" ("past_participle");



CREATE INDEX IF NOT EXISTS "idx_verbs_present_participle" ON "public"."verbs" USING "btree" ("present_participle");



CREATE INDEX IF NOT EXISTS "idx_verbs_target_language" ON "public"."verbs" USING "btree" ("target_language_code");



CREATE INDEX IF NOT EXISTS "idx_verbs_translation" ON "public"."verbs" USING "btree" ("translation");



CREATE OR REPLACE TRIGGER "api_keys_updated_at_trigger" BEFORE UPDATE ON "public"."api_keys" FOR EACH ROW EXECUTE FUNCTION "public"."update_api_keys_updated_at"();



CREATE OR REPLACE TRIGGER "problems_updated_at_trigger" BEFORE UPDATE ON "public"."problems" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_conjugations_updated_at" BEFORE UPDATE ON "public"."conjugations" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_verbs_updated_at" BEFORE UPDATE ON "public"."verbs" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'sentences_verb_fk' 
        AND conrelid = 'public.sentences'::regclass
    ) THEN
        ALTER TABLE ONLY "public"."sentences"
            ADD CONSTRAINT "sentences_verb_fk" FOREIGN KEY ("verb_id") REFERENCES "public"."verbs"("id") ON DELETE CASCADE;
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'conjugations' 
        AND policyname = 'Enable all operations for conjugations'
    ) THEN
        CREATE POLICY "Enable all operations for conjugations" ON "public"."conjugations" USING (true);
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'verbs' 
        AND policyname = 'Enable all operations for verbs'
    ) THEN
        CREATE POLICY "Enable all operations for verbs" ON "public"."verbs" USING (true);
    END IF;
END $$;



ALTER TABLE "public"."api_keys" ENABLE ROW LEVEL SECURITY;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'api_keys' 
        AND policyname = 'api_keys_service_policy'
    ) THEN
        CREATE POLICY "api_keys_service_policy" ON "public"."api_keys" USING (true) WITH CHECK (true);
    END IF;
END $$;



ALTER TABLE "public"."conjugations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."problems" ENABLE ROW LEVEL SECURITY;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'problems' 
        AND policyname = 'problems_delete_policy'
    ) THEN
        CREATE POLICY "problems_delete_policy" ON "public"."problems" FOR DELETE USING (true);
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'problems' 
        AND policyname = 'problems_insert_policy'
    ) THEN
        CREATE POLICY "problems_insert_policy" ON "public"."problems" FOR INSERT WITH CHECK (true);
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'problems' 
        AND policyname = 'problems_select_policy'
    ) THEN
        CREATE POLICY "problems_select_policy" ON "public"."problems" FOR SELECT USING (true);
    END IF;
END $$;



DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'problems' 
        AND policyname = 'problems_update_policy'
    ) THEN
        CREATE POLICY "problems_update_policy" ON "public"."problems" FOR UPDATE USING (true);
    END IF;
END $$;



ALTER TABLE "public"."sentences" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."verbs" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."get_random_verb_simple"("p_target_language" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."get_random_verb_simple"("p_target_language" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_random_verb_simple"("p_target_language" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."increment_api_key_usage"("key_id" "uuid") TO "anon";
GRANT ALL ON FUNCTION "public"."increment_api_key_usage"("key_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."increment_api_key_usage"("key_id" "uuid") TO "service_role";



GRANT ALL ON FUNCTION "public"."update_api_keys_updated_at"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_api_keys_updated_at"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_api_keys_updated_at"() TO "service_role";



GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";



GRANT ALL ON FUNCTION "public"."validate_iso639_3_code"("code" "text") TO "anon";
GRANT ALL ON FUNCTION "public"."validate_iso639_3_code"("code" "text") TO "authenticated";
GRANT ALL ON FUNCTION "public"."validate_iso639_3_code"("code" "text") TO "service_role";



GRANT ALL ON FUNCTION "public"."validate_problem_statements"("prob_type" "public"."problem_type", "statements" "jsonb") TO "anon";
GRANT ALL ON FUNCTION "public"."validate_problem_statements"("prob_type" "public"."problem_type", "statements" "jsonb") TO "authenticated";
GRANT ALL ON FUNCTION "public"."validate_problem_statements"("prob_type" "public"."problem_type", "statements" "jsonb") TO "service_role";


















GRANT ALL ON TABLE "public"."api_keys" TO "anon";
GRANT ALL ON TABLE "public"."api_keys" TO "authenticated";
GRANT ALL ON TABLE "public"."api_keys" TO "service_role";



GRANT ALL ON TABLE "public"."conjugations" TO "anon";
GRANT ALL ON TABLE "public"."conjugations" TO "authenticated";
GRANT ALL ON TABLE "public"."conjugations" TO "service_role";



GRANT ALL ON TABLE "public"."problems" TO "anon";
GRANT ALL ON TABLE "public"."problems" TO "authenticated";
GRANT ALL ON TABLE "public"."problems" TO "service_role";



GRANT ALL ON TABLE "public"."sentences" TO "anon";
GRANT ALL ON TABLE "public"."sentences" TO "authenticated";
GRANT ALL ON TABLE "public"."sentences" TO "service_role";



GRANT ALL ON TABLE "public"."verbs" TO "anon";
GRANT ALL ON TABLE "public"."verbs" TO "authenticated";
GRANT ALL ON TABLE "public"."verbs" TO "service_role";



GRANT ALL ON TABLE "public"."verbs_for_object_problems" TO "anon";
GRANT ALL ON TABLE "public"."verbs_for_object_problems" TO "authenticated";
GRANT ALL ON TABLE "public"."verbs_for_object_problems" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";






























RESET ALL;
