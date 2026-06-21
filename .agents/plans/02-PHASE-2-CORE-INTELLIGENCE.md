# Phase 2: Core Intelligence — LLM Integration & Model Management

## Context

Cortex needs a brain. The LLM infrastructure exists (Ollama catalog, model download, provider abstraction) but needs to be fully wired and production-quality.

## Goals

- Local LLM inference works end-to-end
- Model management UI is fully functional
- Hardware detection and recommendations work
- LLM is wired into agents, search, and chat

## Key Deliverables

| # | Deliverable | Description | Status |
|---|-------------|-------------|--------|
| 1 | LLM Provider Abstraction | ABC + Ollama + llama.cpp providers with streaming | ✅ DONE |
| 2 | LLMManager Singleton | Provider routing, health checks, token metrics | ✅ DONE |
| 3 | Model Catalog API | Full CRUD + search + recommendations | ✅ DONE |
| 4 | Model Download Service | Ollama pull with progress tracking | ✅ DONE |
| 5 | Frontend Model Manager | Browser, detail page, download queue | ✅ DONE |
| 6 | Hardware Detection | GPU/RAM/CPU detection + recommendations | ✅ DONE |
| 7 | Model Comparison | Side-by-side comparison UI | ✅ DONE |
| 8 | Settings Persistence | User model settings saved to DB | ✅ DONE |
| 9 | Download Queue Management | Pause/resume/cancel downloads | ✅ DONE |
| 10 | Model Update Checker | Compare installed vs catalog versions | ✅ DONE |
| 11 | LLM → Agent Integration | ExecutorAgent uses LLM for reasoning | 🟡 PARTIAL |
| 12 | LLM → Search Integration | AI-powered answer synthesis | 🟡 PARTIAL |
| 13 | LLM → Chat Integration | Streaming chat with context | 🟡 PARTIAL |
| 14 | Inference Configuration | Per-model temperature, top_p, etc. | ✅ DONE |

## Validation Checkpoints

- [ ] Can download a model via UI
- [ ] Can query a model via API
- [ ] Agent uses LLM for task execution
- [ ] Search returns AI-synthesized answers
- [ ] Chat streams responses in real-time

## Dependencies

Phase 1 complete

## Complexity

L (large — many integration points)
