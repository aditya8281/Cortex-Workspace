# Cortex Project — Master Plan Index

## Vision

Cortex is a self-hosted, privacy-first AI operating system that unifies local LLM inference, intelligent document management, and autonomous agent workflows into a single cohesive platform. It empowers users to run powerful AI capabilities on their own hardware without sacrificing data sovereignty.

## Current Status

The codebase has undergone rapid iteration with foundational issues being addressed. Backend infrastructure (FastAPI, SQLAlchemy, Alembic) and frontend (Next.js, React) are in place. Core bugs around route shadowing, IDOR vulnerabilities, and DB enum mismatches have been resolved. LLM provider abstraction and model management APIs exist but require full integration wiring.

---

## Phase Overview

| Phase | Name | Status | Dependencies | Complexity |
|-------|------|--------|--------------|------------|
| 01 | [Foundation Stability & Bug Fixes](./01-PHASE-1-FOUNDATION.md) | 🟡 In Progress | None | M |
| 02 | [Core Intelligence — LLM Integration & Model Management](./02-PHASE-2-CORE-INTELLIGENCE.md) | 🔴 Not Started | Phase 1 | L |
| 03 | Agent System & Workflows | 🔴 Not Started | Phase 2 | L |
| 04 | Document Intelligence & RAG | 🔴 Not Started | Phase 2 | L |
| 05 | UI Polish & User Experience | 🔴 Not Started | Phase 1 | M |
| 06 | Security Hardening & Production Readiness | 🔴 Not Started | Phases 1-4 | M |
| 07 | Performance Optimization & Scaling | 🔴 Not Started | Phases 1-5 | M |

---

## How to Use These Plans

1. **Start with Phase 1** — Foundation stability is non-negotiable. Every subsequent phase builds on it.
2. **Each phase file** contains: goals, deliverables table, validation checkpoints, dependencies, and complexity estimate.
3. **Track status** using the deliverable tables: `DONE`, `PARTIAL`, `TODO`.
4. **Validation checkpoints** are the "definition of done" for each phase — all must pass before moving on.
5. **Dependencies** are hard requirements — do not start a phase until its dependencies are complete.
6. **Update these files** as work progresses. Move items from TODO → PARTIAL → DONE.
