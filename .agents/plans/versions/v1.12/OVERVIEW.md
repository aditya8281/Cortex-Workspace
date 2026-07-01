# v1.12: Developer Intelligence (Expanded) — CORTEX

**Document:** Version 1.12 Overview (Expanded)
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-30
**Type:** Capability Delivery
**reference architecture Feature ID:** ODY-DEV-900

---

## Objective

Build a complete **IDE-grade developer intelligence** system: multi-language AST parsing via tree-sitter, LSP integration for live diagnostics/completion/navigation, code-aware agent tools (rename, extract, find-references, format, lint), an agent-in-the-loop coding protocol that cycles write→review→test→rewrite, repository intelligence, code review, documentation & test generation, refactoring with impact assessment, debugging assistance, architecture guidance, dependency/security/performance analysis, migration support, git intelligence, CI/CD integration, and a skills runtime.

This is not an external service layer. This is the agent operating on code **as an IDE does** — with language understanding, live diagnostics, surgical edits, and self-correcting iteration. It also includes a **subagent delegation system** where the main agent can decompose complex tasks, dispatch subagents with isolated contexts, run them in parallel, and synthesize results — exactly like Claude Code's agent→subagent→sub-subagent hierarchy.

---

## Question

"Can Cortex serve as an intelligent IDE agent?"

---

## What This Version Delivers

After completing v1.12, Cortex can:

### Core Intelligence
- Parse 13+ languages via tree-sitter AST (Python, JS, TS, JSX, TSX, Rust, Go, Java, C++, Kotlin, Swift, Ruby, PHP, C#, Scala)
- Index symbols across files: definitions, references, types, callers, callees
- Serve live LSP diagnostics, completions, hover info, go-to-definition, find-references (for any LSP-supported language)
- Provide file-level and project-level code understanding with cross-file dependency resolution

### Agent Coding Tools
- **Rename symbol** across all files with usage validation
- **Extract function/method** from selected lines
- **Find all references** to any symbol
- **Format code** per language formatter
- **Lint & auto-fix** diagnostics
- **Suggest edits** with diff preview
- **Multi-file refactoring** with dependency graph blast radius

### Agent-in-the-Loop Protocol
- Dedicated coding sessions with file context + LSP diagnostics
- Autonomous write→review→test→rewrite cycles
- User-in-the-loop checkpoints for approval before destructive edits
- Error-driven iteration: test fail → diagnose → fix → re-run
- Diff display for every proposed change

### Developer Services (from original scope)
- Repository intelligence with health scoring, complexity metrics, architectural analysis
- Code review with pattern matching, security vulnerability detection, best practices
- Documentation generation with docstring coverage, module docs, README generation
- Test scaffold generation with Arrange-Act-Assert, edge case detection, fixture suggestions
- Refactoring suggestions with dependency graph blast radius and impact assessment
- Debugging assistance with error pattern recognition and stack trace analysis
- Architecture guidance with pattern matching against established principles
- Dependency analysis for version pinning, security advisories, outdated packages
- Performance analysis: cyclomatic complexity, N+1 detection, resource usage patterns
- Security analysis: hardcoded secrets, injection patterns, insecure practices
- Migration support: schema diff analysis, rollback safety assessment
- Git intelligence: log, blame, diff, branch management, commit analysis
- CI/CD integration: pipeline detection, health monitoring, workflow analysis

### Agent Delegation & Subagent System
- **Decompose** complex tasks into subtasks via LLM planning
- **Dispatch subagents** with isolated context windows — each subagent starts fresh, doesn't inherit parent history
- **Parallel fan-out** — multiple subagents run concurrently for independent subtasks
- **Hierarchical delegation** — subagents can spawn their own sub-subagents (tree hierarchy)
- **Status reporting** — subagents report DONE, BLOCKED, NEEDS_CONTEXT, DONE_WITH_CONCERNS
- **Scoped tool access** — each subagent gets only the tools it needs (restricted context)
- **Result synthesis** — parent collects subagent results, synthesizes into final answer
- **Context isolation** — parent context never polluted by subagent internals; only final results flow back

---

## New Capabilities (Added in Expansion)

| ID | Name | Domain | Priority |
|----|------|--------|----------|
| D16 | Multi-Language AST Engine | Developer | Core |
| D17 | LSP Client & Diagnostics | Developer | Core |
| D18 | Symbol Index & Cross-Reference | Developer | Core |
| D19 | Code-Aware Agent Tools | Developer | Core |
| D20 | Agent-in-the-Loop Coding | Developer | Core |
| D21 | Debugger Integration | Developer | Core |
| D22 | Subagent Delegation System | Developer | Core |

**Total: 23 capabilities (16 original + 7 new)**

---

## Phases (Expanded)

| Phase | Name | Focus | Complexity | Duration |
|-------|------|-------|------------|----------|
| P01 | Developer Models & Schema | Database models, Pydantic schemas, migration — expanded with LSP/debug/agent-coding models | Medium | 3-4h |
| P02 | Multi-Language AST Engine | tree-sitter for 13+ languages, unified AST schema, symbol index | High | 6-8h |
| P03 | LSP Integration | LSP client manager, diagnostics, completion, hover, goto-def, find-refs | High | 6-8h |
| P04 | Code-Aware Agent Tools | Rename, extract, find-refs, format, lint, structured-edit agent tools | High | 5-7h |
| P05 | Agent-in-the-Loop Protocol | Coding session manager, review→test→rewrite cycles, user checkpoints | High | 5-7h |
| P06 | Code Understanding & Review (Enhanced) | Cross-file analysis, dependency mapping, code review, security detection | High | 6-7h |
| P07 | Generation, Refactoring & Debugging | Docs, tests, refactoring with impact, debug | High | 5-6h |
| P08 | Analysis Suite | Dependency, security, performance analysis | High | 5-6h |
| P09 | Git & CI/CD | Git intelligence, CI/CD integration | Medium | 4-5h |
| P10 | API, Frontend & Skills Runtime | REST endpoints, frontend dashboard, skills runtime | Medium | 4-5h |
| P11 | Subagent Delegation System | Task decomposition, subagent dispatch, parallel fan-out, status reporting, result synthesis | High | 5-7h |

---

## Dependencies

**Depends on:**
- v1.02 (Backend Architecture) — service patterns, middleware, DB infrastructure
- v1.03 (Memory Foundation) — symbol graphs stored in memory graph
- v1.04 (Awareness Foundation) — file watching triggers re-index on file change
- v1.06 (Cognition Core) — agent loop, tool infrastructure, intent classification
- v1.09 (The Knowledge) — File parsing, semantic search for code

**Blocks:**
- None (terminal version)

---

## Language Support Matrix

| Language | AST | LSP | Agent Tools | Status |
|----------|-----|-----|-------------|--------|
| Python | tree-sitter-python | pylsp / ruff | Full | P02-P04 |
| JavaScript | tree-sitter-js | typescript-language-server | Full | P02-P04 |
| TypeScript | tree-sitter-ts | typescript-language-server | Full | P02-P04 |
| TSX | tree-sitter-tsx | typescript-language-server | Full | P02-P04 |
| JSX | tree-sitter-jsx | typescript-language-server | Full | P02-P04 |
| Rust | tree-sitter-rust | rust-analyzer | Full | P02-P04 |
| Go | tree-sitter-go | gopls | Full | P02-P04 |
| Java | tree-sitter-java | eclipse-jdtls | Full | P02-P04 |
| C++ | tree-sitter-cpp | clangd | Full | P02-P04 |
| Kotlin | tree-sitter-kotlin | kotlin-language-server | Full | P02-P04 |
| Swift | tree-sitter-swift | sourcekit-lsp | Full | P02-P04 |
| Ruby | tree-sitter-ruby | solargraph | Full | P02-P04 |
| PHP | tree-sitter-php | intelephense | Full | P02-P04 |
| C# | tree-sitter-c-sharp | omnisharp | Full | P02-P04 |
| Scala | tree-sitter-scala | metals | Full | P02-P04 |
| Elixir | tree-sitter-elixir | elixir-ls | Basic | P02-P04 |
| Lua | tree-sitter-lua | lua-language-server | Basic | P02-P04 |
| SQL | tree-sitter-sql | sqls | Basic | P02-P04 |
| YAML/TOML/JSON | tree-sitter-* | schema-based | Config | P02-P04 |

---

## Agent Tool Registry (New Code-Aware Tools)

| Tool Name | Category | Description | Approval |
|-----------|----------|-------------|----------|
| `read_file` | files | Read file with line limit | Auto |
| `write_file` | files | Write full file content | Required |
| `edit_file` | code | Surgical edit (slice replace) | Auto |
| `search_code` | code | Semantic code search across project | Auto |
| `find_symbol` | code | Find symbol definition and references | Auto |
| `rename_symbol` | code | Rename symbol across all files | Required |
| `extract_function` | code | Extract lines into new function | Required |
| `format_file` | code | Format file per language formatter | Auto |
| `lint_file` | code | Lint file and show diagnostics | Auto |
| `fix_diagnostic` | code | Auto-fix specific diagnostic | Auto |
| `get_diagnostics` | code | Get LSP diagnostics for file | Auto |
| `get_completions` | code | Get completion suggestions at point | Auto |
| `get_hover_info` | code | Get hover/signature info at point | Auto |
| `go_to_definition` | code | Navigate to symbol definition | Auto |
| `find_references` | code | Find all references to symbol | Auto |
| `review_diff` | review | Review a diff for issues | Auto |
| `suggest_test` | test | Generate test for selected function | Auto |
| `debug_analyze` | debug | Analyze error/stack trace | Auto |
| `git_commit` | git | Create commit | Required |
| `git_branch` | git | Create/switch branch | Auto |

---

## Rust Crate Expansion

Existing `crates/code-intel/` (Python-only tree-sitter) expands to:

```
crates/code-intel/
├── src/
│   ├── lib.rs                # Python AST parse (existing)
│   ├── ast_engine.rs         # Multi-language AST dispatcher
│   ├── tree_sitter/           # tree-sitter FFI per language
│   │   ├── python.rs
│   │   ├── javascript.rs
│   │   ├── typescript.rs
│   │   ├── rust.rs
│   │   ├── go.rs
│   │   ├── java.rs
│   │   ├── cpp.rs
│   │   ├── kotlin.rs
│   │   ├── swift.rs
│   │   ├── ruby.rs
│   │   ├── php.rs
│   │   ├── csharp.rs
│   │   └── scala.rs
│   ├── symbol_index.rs        # Symbol extraction and cross-file index
│   ├── query.rs               # tree-sitter query patterns
│   └── ffi.rs                 # PyO3 FFI exports
├── Cargo.toml                 # Expanded dependencies
└── build.rs                   # Language grammar compilation
```

---

## Risk Matrix (Expanded)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LSP process crashes | Medium | Medium | Auto-restart with backoff, graceful degradation (no diagnostics = no LSP tools) |
| tree-sitter grammar missing for edge syntax | High | Low | Partial parse, never crash on malformed code |
| Rename symbol breaks imports across files | Medium | High | Dry-run first, diff preview, user must approve multi-file changes |
| Agent-in-loop infinite write-test cycles | Low | High | Max iteration limit (default 5), user interrupt always available |
| LSP memory usage with many files open | Medium | Medium | Cap active LSP sessions (max 5), close idle sessions after 15min |
| Formatter tool modifies too many files | Medium | Medium | Only format files explicitly requested, not entire projects |

---

## Architecture Principle Cross-References

| Principle | How v1.12 Satisfies It |
|-----------|----------------------|
| 3.1 Local-First | All AST parsing, LSP connections, symbol indexing run locally. No code sent externally. |
| 3.2 Graceful Degradation | No LSP → regex fallback. No tree-sitter → ILIKE text search. Any language gets basic file ops. |
| 3.3 Daemon-First | LSP session manager runs as daemon. Agent tools call via daemon API. Watchdog triggers re-index. |
| 3.6 Evidence Over Opinion | Refactoring based on actual dependency graphs. Rename validated against symbol index. |
| 3.7 Incremental Safety | Rename dry-run. Extract preserves imports. Edit_file validates syntax before applying. |

---

## Estimated Duration

14-18 days (expanded from 9-10).

---

## Definition of Done

- [ ] All 23 developer capabilities implemented and tested
- [ ] 13+ languages parseable via tree-sitter AST
- [ ] Symbol index works cross-file for at least Python, JS/TS, Rust, Go
- [ ] LSP integration provides diagnostics, completion, hover, goto-def for 8+ languages
- [ ] All code-aware agent tools functional (rename, extract, find-refs, format, lint)
- [ ] Agent-in-the-loop coding protocol cycles write→review→test→rewrite with max-iteration guard
- [ ] code-review tool detects common quality/security issues
- [ ] Test / doc generation produces correct scaffolds
- [ ] Refactoring service calculates blast radius
- [ ] Security scanner detects hardcoded secrets, injection patterns
- [ ] Git intelligence provides log, blame, branch, diff
- [ ] Skills runtime supports composition
- [ ] Subagent delegation system decomposes, dispatches, and synthesizes parallel subtasks
- [ ] Subagent status reporting (DONE, BLOCKED, NEEDS_CONTEXT, DONE_WITH_CONCERNS)
- [ ] All unit tests passing
- [ ] Lint clean
- [ ] Frontend developer dashboard

---

## Success Criteria

| Metric | Target |
|--------|--------|
| AST parse latency (single file) | < 100ms |
| Symbol index build (100 files) | < 5 seconds |
| LSP diagnostic response | < 500ms |
| Rename symbol (single file, 50 refs) | < 2 seconds |
| Agent loop cycle (write→test→rewrite) | < 15 seconds |
| Code review scoring accuracy | > 90% agreement |
| Security scan false positive rate | < 10% |
| Test generation | < 500ms per file |
