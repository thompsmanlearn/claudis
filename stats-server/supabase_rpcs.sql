-- Supabase RPC functions required by stats_server.py
-- Queried from live database 2026-04-17
-- Both functions increment times_applied in lessons_learned.
-- Called by inject_context_v3 (/inject_context_v3, /inject_context_v2) and /lessons_applied endpoint.

-- Primary: match by chromadb_id (preferred — stable identifier)
CREATE OR REPLACE FUNCTION public.increment_lessons_applied_by_id(lesson_ids text[])
 RETURNS void
 LANGUAGE sql
 SECURITY DEFINER
AS $function$
  UPDATE lessons_learned
  SET times_applied = times_applied + 1,
      updated_at = now()
  WHERE chromadb_id = ANY(lesson_ids);
$function$;

-- Fallback: match by content (for legacy lessons without chromadb_id set)
CREATE OR REPLACE FUNCTION public.increment_lessons_applied(lesson_contents text[])
 RETURNS void
 LANGUAGE sql
 SECURITY DEFINER
AS $function$
  UPDATE lessons_learned
  SET times_applied = times_applied + 1,
      updated_at = now()
  WHERE content = ANY(lesson_contents);
$function$;
