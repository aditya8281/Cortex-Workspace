# v1.01: Repository Restructure — CORTEX

**Document:** Version 1.01 Overview
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Type:** Structural

---

## Objective

Transform the flat backend into a domain-organized architecture with 11 service domains and 8 model domains, then reorganize all other project directories (docs, planning, frontend, testing).

---

## Question

Can we reorganize the entire CORTEX codebase into domain-driven structure without breaking any functionality?

---

## What This Version Delivers

After completing v1.01, a contributor can:

- Navigate services by domain (memory, awareness, intelligence, etc.)
- Navigate models by domain (memory, awareness, intelligence, etc.)
- Find documentation by topic in organized subdirectories
- Find planning documents by version in standardized templates

---

## Phases

| Phase | Name | Focus | Complexity | Duration | Dependencies |
|-------|------|-------|------------|----------|--------------|
| P01 | Backend Services Reorganization | Move services to domains | Medium | 4-6h | None |
| P02 | Backend Models Reorganization | Move models to domains | Medium | 3-4h | None |
| P03 | Import Migration | Update all import paths | High | 2-3h | P01, P02 |
| P04 | Frontend Reorganization | Organize frontend components | Low | 2-3h | P01-P03 |
| P05 | Documentation Reorganization | Organize docs by topic | Low | 1-2h | None |
| P06 | Planning Reorganization | Organize planning docs | Low | 0.5-1h | None |
| P07 | Frontend Feature Scaffolding | Create feature module templates | Low | 1-2h | P04 |
| P08 | Testing Infrastructure | Improve test organization | Low | 1-2h | P01-P03 |

---

## Estimated Duration

3-5 days (14-23 hours)
