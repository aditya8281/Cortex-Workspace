# Remaining Recommendations Research

## Issue-by-Issue Findings

---

### 1. H-S3: WebSocket tokens in URL

- **Still an issue:** YES
- **File:** `backend/app/api/ws.py:21`
- **Risk level:** LOW
- **Description:** The JWT token is passed as a query parameter (`ws.query_params.get("token")`). This means it appears in server access logs, browser history, and potentially proxy logs. However, this is the standard approach for WebSocket auth since WebSocket doesn't support custom headers in browsers. The endpoint is only `/ws/demo` (a demo endpoint), so exposure is limited.

---

### 2. H-S5: GitHub token encryption

- **Still an issue:** YES
- **File:** `backend/app/api/v1/github.py:69-78`
- **Risk level:** MEDIUM
- **Description:** The Fernet encryption key is derived deterministically from `SECRET_KEY` using `hashlib.sha256`. Anyone with access to `SECRET_KEY` can decrypt all GitHub tokens. This is intentional (tokens must be recoverable for API calls), but the key derivation is weak — a single SHA-256 hash with no salt. Should use HKDF or PBKDF2 with a proper info label to separate this key from other uses of `SECRET_KEY`.

---

### 3. H-S8: HuggingFace token plaintext

- **Still an issue:** YES
- **File:** `backend/app/api/v1/models.py:531,561` and `backend/app/models/user_settings.py:19`
- **Risk level:** MEDIUM
- **Description:** The HuggingFace token is stored as plaintext in the `user_model_settings` table (`huggingface_token` column is `String(255)`, nullable). The GET endpoint at line 531 returns it directly in the response. Unlike the GitHub token (which gets Fernet encryption), the HF token has zero encryption at rest.

---

### 4. H-S9: Vault password re-encryption not atomic

- **Still an issue:** YES
- **File:** `backend/app/services/vault_service.py:597-629`
- **Risk level:** MEDIUM
- **Description:** The password change function first decrypts all files into memory (lines 597-617), then re-encrypts and writes them one-by-one (lines 619-626). If the process crashes between writing some files but not others, some files will be re-encrypted with the new key and others left as-is (unreadable with the new password). The code decrypts everything first as a safety measure, but there's no rollback mechanism. The DB password hash is updated at line 629 only after all files are written, which helps — but a crash mid-write still causes data loss.

---

### 5. H-S10: Rate limiting fails open

- **Still an issue:** YES
- **File:** `backend/app/core/rate_limit.py:47-49`
- **Risk level:** MEDIUM
- **Description:** The except block at line 47-49 catches ALL exceptions and simply calls `return await call_next(request)`, completely bypassing rate limiting. This means a Redis outage instantly disables all rate limiting. The vault endpoint (`vault.py:116`) has an in-memory fallback, but the global middleware does not.

---

### 6. H-C1: Sync status field name

- **Still an issue:** YES
- **Files:** `frontend/src/shared/types.ts:714` vs `backend/app/api/v1/sync.py:242`
- **Risk level:** LOW
- **Description:** Frontend `IndexingStatus` type uses `watching_count` (line 714), but the backend `SyncStatusResponse` model uses `watching` (line 242). The field names don't match. The frontend component may need to use `.watching` when reading from the sync status endpoint.

---

### 7. H-C2: Sync watched_paths type

- **Still an issue:** NO (already aligned)
- **Files:** `frontend/src/shared/types.ts:718` and `backend/app/api/v1/sync.py:248`
- **Risk level:** N/A
- **Description:** Frontend `IndexingStatus.watched_paths` is `string[]` (line 718), but backend `SyncStatusResponse.watched_paths` is `list[dict[str, Any]]` (line 248) containing objects with `path`, `repo_id`, `embedding_model`, etc. The types are mismatched — the frontend expects strings but gets objects. This IS a real mismatch, but it depends on which frontend type is actually used. The `IndexingStatus` type (line 713-719) may not be the one used for the sync status API call.

---

### 8. H-C9: Chat timestamp drift

- **Still an issue:** NO (no evidence found)
- **Risk level:** N/A
- **Description:** No dedicated chat page/component was found in `frontend/src/`. The `ConversationMessage` type (types.ts:734-740) has `created_at: string | null`, which comes from the backend's `server_default=func.now()`. Backend uses PostgreSQL `now()` (timezone-aware). No frontend-side timestamp generation for chat messages was found, so there's no drift between client and server clocks.

---

### 9. H-C10: Vault upload returns encrypted size

- **Still an issue:** YES
- **Files:** `backend/app/services/vault_service.py:414-418` and `backend/app/schemas/vault.py:29-32`
- **Risk level:** LOW
- **Description:** The `upload_vault_file` function returns `"size": len(encrypted_content)` (line 417), which is the size of the encrypted file, not the original plaintext size. The `VaultUploadResponse` schema (vault.py:29-32) and frontend `VaultUploadResult` (types.ts:83-87) both have a `size` field. Users see the encrypted size (larger than original due to encryption overhead/salt) instead of the actual file size.

---

### 10. H-C13: Search filter params silently ignored

- **Still an issue:** YES
- **File:** `backend/app/api/v1/search.py:38-44`
- **Risk level:** LOW
- **Description:** The `SearchRequest` model (line 38-44) only accepts `query`, `repo_id`, `max_results`, `sources`, `diversity`, and `cursor`. There are no `node_type` or `language` filter parameters. The backend services (`hybrid_retrieval.py`, `fulltext_search.py`) DO support language filtering internally, but the search API endpoint doesn't expose these filters. Any client sending `node_type` or `language` params gets them silently ignored (Pydantic strips unknown fields).

---

### 11. H-D4: backref usage

- **Still an issue:** YES
- **Files:** `backend/app/models/graph.py:33-34` and `backend/app/models/file_index.py:30`
- **Risk level:** LOW
- **Description:** Three `backref` usages remain: `graph.py:33` (`chunk = relationship("CodeChunk", backref="graph_nodes")`), `graph.py:34` (`repo = relationship("RepoIndex", backref="graph_nodes")`), and `file_index.py:30` (`repo = relationship("RepoIndex", backref="indexed_files")`). The `backref` string form creates implicit relationships without type safety. Should use `back_populates` with explicit `relationship()` on both sides for consistency with the rest of the codebase.

---

### 12. H-D6: Missing FK indexes

- **Still an issue:** NO (already fixed)
- **Risk level:** N/A
- **Description:** The baseline migration (`b00000000000_baseline.py`) includes explicit `op.create_index()` calls for all FK columns: `ix_auth_events_user_id` (line 92), `ix_knowledge_entries_user_id` (line 111), `ix_repo_indexes_user_id` (line 146), `ix_code_chunks_repo_id` (line 165), `ix_graph_nodes_chunk_id` (line 201), `ix_graph_nodes_repo_id` (line 202), `ix_graph_edges_source_id` (line 224), `ix_graph_edges_target_id` (line 225), `ix_agent_runs_agent_id` (line 285), `ix_agent_runs_user_id` (line 286), `ix_agent_steps_run_id` (line 303), `ix_agent_feedback_run_id` (line 318), `ix_agent_feedback_user_id` (line 319), `ix_conversations_user_id` (line 357), `ix_document_chunks_document_id` (line 451), `ix_model_variants_model_catalog_id` (line 553), `ix_model_downloads_user_id` (line 578), `ix_model_usage_model_variant_id` (line 601), `ix_model_usage_user_id` (line 602), `ix_provider_models_provider_id` (line 662), `ix_sync_jobs_provider_id` (line 747), `ix_long_term_memories_user_id` (line 771). All FK columns have corresponding indexes.

---

## Summary

| Issue | Still an Issue | Risk | Fix Complexity |
|-------|---------------|------|----------------|
| H-S3: WS tokens in URL | YES | LOW | Low (demo endpoint only, standard WS pattern) |
| H-S5: GitHub token encryption | YES | MEDIUM | Medium (add HKDF key derivation) |
| H-S8: HF token plaintext | YES | MEDIUM | Medium (add Fernet encryption like GitHub token) |
| H-S9: Vault re-encryption atomicity | YES | MEDIUM | High (need temp files + rename or WAL approach) |
| H-S10: Rate limiting fails open | YES | MEDIUM | Low (add in-memory fallback like vault does) |
| H-C1: Sync field name mismatch | YES | LOW | Low (rename one side to match) |
| H-C2: watched_paths type mismatch | YES | LOW | Low (align frontend type) |
| H-C9: Chat timestamp drift | NO | N/A | N/A |
| H-C10: Vault upload encrypted size | YES | LOW | Low (store original size before encryption) |
| H-C13: Search filter params ignored | YES | LOW | Low (add node_type/language to SearchRequest) |
| H-D4: backref usage | YES | LOW | Low (convert to back_populates) |
| H-D6: Missing FK indexes | NO | N/A | N/A (already in baseline migration) |
