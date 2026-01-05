-- Remove unused verbs_for_object_problems view
-- This view was never used in the codebase - all queries go directly to the verbs table
-- The view had RLS disabled, so removing it eliminates a potential security concern

DROP VIEW IF EXISTS "public"."verbs_for_object_problems";

