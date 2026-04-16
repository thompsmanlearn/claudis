# Skill: Agent Development

## Purpose
Building, promoting, and retiring agents in the AADP fleet; writing and versioning agent prompts;
calling the Claude API and external integrations from agents and n8n workflows.

## When to Load
- Designing, scaffolding, promoting, or retiring agents in the ~25-agent fleet
- Writing or updating agent prompts, versioning via `prompt_update`
- Building or debugging n8n workflows that call external APIs
- Writing Supabase queries, ChromaDB operations, or Claude API calls within agent context

## Part 1: Building and Managing Agents

### Core Instructions

*(stub — fill with scaffolding procedures, sandbox-to-active promotion checklist, registry
management, prompt versioning workflow, behavioral_health_check usage)*

### Known Failure Modes

*(stub — fill with: forgetting to link workflow_id, promoting without running behavioral_health_check,
prompt rollback procedure, agent_registry column gotchas)*

## Part 2: API and Integration Patterns

### Core Instructions

*(stub — fill with: Supabase UPSERT pattern, n8n empty-array fix, Claude API prompt caching
requirements, Telegram 750-char limit, credential loading from .env, GitHub REST API via token,
host.docker.internal from Docker containers)*

### Known Failure Modes

*(stub — fill with: Haiku 4.5 ignoring cache_control silently, Supabase PostgREST vs Management API
distinction, n8n Code node 10-item limit, stats server port 9100 as Docker bridge)*

## Cross-Skill Warnings

See `skills/PROTECTED.md` for resources that must not be modified without explicit approval.
