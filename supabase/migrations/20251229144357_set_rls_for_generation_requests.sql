-- Enable Row Level Security for generation_requests table
ALTER TABLE "public"."generation_requests" ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for generation_requests table
-- Following the same pattern as problems table

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'generation_requests' 
        AND policyname = 'generation_requests_select_policy'
    ) THEN
        CREATE POLICY "generation_requests_select_policy" ON "public"."generation_requests" FOR SELECT USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'generation_requests' 
        AND policyname = 'generation_requests_insert_policy'
    ) THEN
        CREATE POLICY "generation_requests_insert_policy" ON "public"."generation_requests" FOR INSERT WITH CHECK (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'generation_requests' 
        AND policyname = 'generation_requests_update_policy'
    ) THEN
        CREATE POLICY "generation_requests_update_policy" ON "public"."generation_requests" FOR UPDATE USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'generation_requests' 
        AND policyname = 'generation_requests_delete_policy'
    ) THEN
        CREATE POLICY "generation_requests_delete_policy" ON "public"."generation_requests" FOR DELETE USING (true);
    END IF;
END $$;

