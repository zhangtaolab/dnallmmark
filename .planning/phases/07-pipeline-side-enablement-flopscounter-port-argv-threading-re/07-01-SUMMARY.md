---
phase: 07-pipeline-side-enablement-flopscounter-port-argv-threading-re
plan: 01
subsystem: pipeline
tags: [flops, torch, json-schema, calibration, cpu-testing]
status: in-progress
---

# Phase 7 Plan 01: FLOPs Report Chain (FlopsCounter Port, Schema, Tolerant Loader) Summary

> **IN-PROGRESS RECORD** — Task 1's checkpoint decision is recorded below per the
> plan's checkpoint completion criteria ("recorded in 07-01-SUMMARY.md before
> Task 2 starts"). This file is finalized (full frontmatter, accomplishments,
> commits, deviations) when the plan completes.

## Task 1 Decision Record (checkpoint:decision, gate=blocking-human)

**Decision:** `publish-as-derived` — publish the `flops_report.json` v1 schema
EXACTLY as derived from the locked decisions. No field-name amendments.

- **Decided by:** maintainer, 2026-10-11 13:46 CST (authoritative user decision
  delivered to the continuation executor).
- **Ratified contract (D-02/D-03/D-05/D-27):**
  - Required top-level keys (legacy, D-02): `num_tokens`, `all_tokens`,
    `num_params`, `total_flops_G`, `total_flops_exact`,
    `total_flops_per_token`, `total_flops_all_tokens`,
    `computation_size_ratio` (number or null), `config` (closed object
    `{include_norm, include_act, include_embed}` booleans), `layer_details`
    (open object mapping layer names to integers)
  - New per D-03: `uncovered_layers` — array of closed `{name, classname}` objects
  - New per D-05 (optional section, present only when captured): `hardware` —
    `gpu_device` (string or null, verbatim `torch.cuda.get_device_name()`, no
    enum mapping), `train_time` (number or null), `max_mem_gb` (number or null)
  - New per D-27: `schema_version` const `1`
  - Discipline: draft-2020-12, `$id` =
    `https://raw.githubusercontent.com/zhangtaolab/dnallmmark/main/schemas/flops_report.json`,
    `additionalProperties: false` on every closed object, `layer_details` as an
    open integer map
- **Consequence:** the v1 field names are now immutable downstream contract
  (D-27 one-way); Task 2 publishes the schema matching this shape exactly.
