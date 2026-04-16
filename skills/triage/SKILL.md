# Skill: Triage

## Purpose
Cross-layer diagnostic reasoning when something is broken and the failing layer is unclear.
Distinct from system-ops (which handles known procedures for healthy-layer operations).

## When to Load
- An n8n execution fails and it's unclear whether the fault is in the workflow, MCP tool, or Supabase
- A tool call returns an unexpected result and the root cause could be any of: credentials, schema change, service health, or logic error
- An agent is not producing expected output and the cause is undiagnosed
- `error_log` has entries without an obvious owner

## Core Instructions

*(stub — fill with: cross-layer trace procedure, isolation steps for n8n→MCP→Supabase chain,
when to check error_log vs audit_log vs execution_log, escalation ladder when blocked)*

## Cross-Skill Warnings

See `skills/PROTECTED.md` for resources that must not be modified without explicit approval.

## Known Failure Modes

*(stub — fill with: misattributing n8n credential errors as logic errors, checking the wrong log
table, fixing symptoms without diagnosing root cause)*
