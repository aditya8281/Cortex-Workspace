from typing import List, Dict, Any, Optional
import re
from pathlib import Path
from backend.app.agent.base import BaseAgent
from backend.app.core.logging import get_logger
from backend.app.db.session import SessionLocal
from backend.app.intelligence.memory_service import PersistentMemoryService
from backend.app.intelligence.system_actions import SystemActionsService
from backend.app.intelligence.models import RepositoryProfile

logger = get_logger(__name__)

class ChatAgent(BaseAgent):
    name = "ChatAgent"
    description = "Handles conversational greetings, small talk, and general assistance."
    capabilities = ["chat"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower().strip()
        greetings = ["hello", "hi", "hey", "how are you", "who are you", "what is your name", "greetings", "good morning", "good afternoon"]
        if any(q.startswith(g) or f" {g} " in f" {q} " for g in greetings) or len(q.split()) <= 2:
            return 0.95
        return 0.15

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a friendly, helpful, local-first AI assistant for Cortex Workspace.\n"
            "Respond directly to the user's greeting or general chat. Be warm, human-like, and conversational.\n"
            "Do not mention workspace directories, files, or tools unless the user explicitly asks about them."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return {
            "result": res["response"],
            "confidence": self.confidence(query, context),
            "reasoning_summary": "Handled greeting or conversational query directly."
        }


class SearchAgent(BaseAgent):
    name = "SearchAgent"
    description = "Handles file search and memory search."
    capabilities = ["search", "file_search", "memory_retrieval"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        if any(kw in q for kw in search_keywords):
            return 0.92
        return 0.20

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        # 1. Run file search
        file_results = self.executor.file_agent.search(query)

        # 2. Run memory search
        memory_results = []
        db = SessionLocal()
        try:
            mems = PersistentMemoryService().search(db, query, limit=3, user_id=kwargs.get("user_id"))
            memory_results = [f"- {m['title']}: {m['content'][:200]}" for m in mems]
        except Exception as e:
            logger.warning(f"SearchAgent memory search failed: {e}")
        finally:
            db.close()

        system_prompt = (
            "You are a search and retrieval expert for Cortex Workspace.\n"
            "Synthesize the file results and memory matches below to answer the query.\n"
            "Explicitly reference matching files or retrieved memories. Be precise."
        )

        search_context = (
            f"=== Search Agent Results ===\n"
            f"[File Search Results]:\n{file_results}\n\n"
            "[Retrieved Memories]:\n" + ("\n".join(memory_results) if memory_results else "No matching memories.") + "\n"
            "============================="
        )

        prompt = f"{context or ''}\n\n{search_context}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return {
            "result": res["response"],
            "confidence": self.confidence(query, context),
            "reasoning_summary": "Searched codebase files and persistent memory to construct response."
        }


class RepositoryAgent(BaseAgent):
    name = "RepositoryAgent"
    description = "Analyzes repository architecture, dependencies, summaries, and codebase layout."
    capabilities = ["repo_analysis", "dependency_analysis", "repo_summaries", "codebase_understanding"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        repo_keywords = ["architecture", "repo summary", "tech stack", "dependency", "project structure", "workspace layout", "modules", "packages", "codebase"]
        if any(kw in q for kw in repo_keywords):
            return 0.90
        return 0.25

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        # Load profile details from database
        db = SessionLocal()
        profile_details = ""
        try:
            profile = db.query(RepositoryProfile).order_by(RepositoryProfile.updated_at.desc()).first()
            if profile:
                profile_details = (
                    f"Repository: {profile.name}\n"
                    f"Path: {profile.path}\n"
                    f"Architecture Overview: {profile.architecture_summary}\n"
                    f"Tech Stack: {profile.tech_stack}\n"
                    f"Entry Points: {profile.entry_points_json}\n"
                    f"Dependencies: {profile.dependencies_json[:1000]}"
                )
            else:
                profile_details = "No repository profile indexed in database yet."
        except Exception as e:
            logger.warning(f"RepositoryAgent failed to fetch profile: {e}")
        finally:
            db.close()

        system_prompt = (
            "You are a repository analysis agent for Cortex.\n"
            "Explain the architecture, structure, dependencies, and code composition using the database profile details.\n"
            "Be clear and summarize technical stacks concisely."
        )
        prompt = f"{context or ''}\n\n[Database Repository Profile]:\n{profile_details}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return {
            "result": res["response"],
            "confidence": self.confidence(query, context),
            "reasoning_summary": "Analyzed repository profile data from the intelligence database to output layout and architecture."
        }


class CodingAgent(BaseAgent):
    name = "CodingAgent"
    description = "Generates code, fixes bugs, refactors codebases, and creates unified patch diffs."
    capabilities = ["coding", "bug_fixing", "refactoring", "patch_creation"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        coding_keywords = ["code", "class", "function", "write a", "implement", "refactor", "bug", "fix", "syntax", "compile", "diff", "patch", "git diff"]
        if any(kw in q for kw in coding_keywords):
            return 0.90
        return 0.30

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are an expert developer agent.\n"
            "Produce clean, standard-compliant implementations.\n"
            "If the user asks for a patch, diff, or file modification, output a standard unified git diff format:\n"
            "```diff\n"
            "--- a/path/to/file.py\n"
            "+++ b/path/to/file.py\n"
            "@@ ... @@\n"
            "- old line\n"
            "+ new line\n"
            "```\n"
            "Be precise with diff changes."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return {
            "result": res["response"],
            "confidence": self.confidence(query, context),
            "reasoning_summary": "Generated programming solution or patch diff output matching user constraints."
        }


class MemoryAgent(BaseAgent):
    name = "MemoryAgent"
    description = "Retrieves and updates knowledge database memories, and summarizes inputs."
    capabilities = ["memory_retrieval", "memory_updates", "summarization", "knowledge_lookup"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        memory_keywords = ["memory", "recall", "stored", "learned", "note", "remember", "knowledge", "save to memory", "update note", "summarize"]
        if any(kw in q for kw in memory_keywords):
            return 0.92
        return 0.22

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        q_lower = query.lower()
        db = SessionLocal()
        try:
            # Check if this query is a request to save/update a memory
            save_triggers = ["remember that", "save to memory", "store memory", "learn that", "update memory", "save note"]
            if any(t in q_lower for t in save_triggers):
                extracted_title = "User Fact"
                extracted_content = query
                for t in save_triggers:
                    if t in q_lower:
                        parts = query.split(t, 1)
                        if len(parts) > 1 and parts[1].strip():
                            extracted_content = parts[1].strip()
                            extracted_title = extracted_content[:30] + "..." if len(extracted_content) > 30 else extracted_content
                            break
                
                # Write to DB memory
                mem_service = PersistentMemoryService()
                mem_service.add_document_memory(
                    db,
                    title=f"Memory: {extracted_title}",
                    content=extracted_content,
                    source_path="user_chat",
                    user_id=kwargs.get("user_id")
                )
                db.commit()
                result_str = f"🧠 Memory saved successfully!\n- **Title**: Memory: {extracted_title}\n- **Saved Content**: {extracted_content}"
                return {
                    "result": result_str,
                    "confidence": 0.95,
                    "reasoning_summary": "Saved custom user fact into persistent SQLite database storage."
                }

            # General lookup
            memories = PersistentMemoryService().search(db, query, limit=5, user_id=kwargs.get("user_id"))
            db_mems_str = ""
            if memories:
                db_mems_str = "\n".join(f"- {m['title']}: {m['content']}" for m in memories)
            else:
                db_mems_str = "No database memory items match."

            system_prompt = (
                "You are a memory specialist agent.\n"
                "Your role is to recall and explain memories from the database matching the query.\n"
                "Summarize key points if requested."
            )
            prompt = f"{context or ''}\n\n[Database Memory List]:\n{db_mems_str}\n\nUser Query:\n{query}"
            res = await self.executor.router.route_and_generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=kwargs.get("llm_model"),
                history=history,
                inference_engine=kwargs.get("inference_engine"),
                api_key=kwargs.get("api_key"),
                api_base_url=kwargs.get("api_base_url")
            )
            self.executor.last_routing_info = res.get("routing_info")
            return {
                "result": res["response"],
                "confidence": self.confidence(query, context),
                "reasoning_summary": "Queried persistent memory base to find related facts."
            }
        finally:
            db.close()


class PlanningAgent(BaseAgent):
    name = "PlanningAgent"
    description = "Decomposes complex requests into project plans, milestones, roadmaps, and todo lists."
    capabilities = ["planning", "roadmap_generation", "task_decomposition"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        plan_keywords = ["plan", "steps", "how to", "roadmap", "recipe", "implementation steps", "strategy", "checklist", "milestone", "todo"]
        if any(kw in q for kw in plan_keywords):
            return 0.90
        return 0.25

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are a strategic planning agent.\n"
            "Generate logical roadmap milestones, check task dependencies, and list explicit implementation tasks.\n"
            "Format the roadmap beautifully with todo indicators."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return {
            "result": res["response"],
            "confidence": self.confidence(query, context),
            "reasoning_summary": "Created checklist, decomposition tasks, and chronological steps to fulfill the user request."
        }


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    description = "Conducts deep concept research, explains technical documentation, and analyzes concepts."
    capabilities = ["research", "documentation_analysis", "concept_explanation"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        research_keywords = ["research", "explain concept", "investigate", "deep dive", "theory", "paper", "pldnet", "rlhf", "documentation", "how does"]
        if any(kw in q for kw in research_keywords):
            return 0.88
        return 0.35

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are an academic and technical research agent.\n"
            "Deconstruct technical concepts using the code documentation and references.\n"
            "Write clean, clear explanations."
        )
        prompt = f"{context or ''}\n\nUser Query:\n{query}"
        res = await self.executor.router.route_and_generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=kwargs.get("llm_model"),
            history=history,
            inference_engine=kwargs.get("inference_engine"),
            api_key=kwargs.get("api_key"),
            api_base_url=kwargs.get("api_base_url")
        )
        self.executor.last_routing_info = res.get("routing_info")
        return {
            "result": res["response"],
            "confidence": self.confidence(query, context),
            "reasoning_summary": "Analyzed documentation and references to construct a concept explanation."
        }


class ExecutionAgent(BaseAgent):
    name = "ExecutionAgent"
    description = "Performs terminal command actions, file operations, and application launching while respecting permissions."
    capabilities = ["execution", "terminal_action", "file_operation", "app_launch"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        exec_keywords = ["run command", "execute command", "launch", "open file", "open folder", "read file", "list directory", "terminal", "system diagnostic"]
        if any(kw in q for kw in exec_keywords):
            return 0.95
        return 0.20

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        q_lower = query.lower()
        db = SessionLocal()
        try:
            service = SystemActionsService()
            action_type = "run_command"
            paths = []
            payload = {}

            # Parse query to map action types
            if "open folder" in q_lower:
                action_type = "open_folder"
                paths = [str(self.executor.file_agent.workspace_root)]
            elif "open file" in q_lower:
                action_type = "open_file"
                paths = [str(self.executor.file_agent.workspace_root / "README.md")]
            elif "read file" in q_lower:
                action_type = "read_file"
                paths = [str(self.executor.file_agent.workspace_root / "pyproject.toml")]
            elif "list directory" in q_lower:
                action_type = "list_directory"
                paths = ["."]
            else:
                action_type = "run_command"
                cmd_str = query
                if "run command" in q_lower:
                    parts = query.split("run command", 1)
                    if len(parts) > 1 and parts[1].strip():
                        cmd_str = parts[1].strip()
                payload = {"command": cmd_str}

            user_id = kwargs.get("user_id")
            result = service.plan_action(
                db,
                user_id=user_id,
                action_type=action_type,
                description=f"Action requested by ExecutionAgent for query: {query}",
                affected_paths=paths,
                payload=payload
            )

            status = result.get("status")
            if status == "approval_required":
                result_str = (
                    f"⚠️ **Action Blocked (Approval Required)**\n"
                    f"- **Reason**: This system command or file modification requires explicit user confirmation under the current automation security settings.\n"
                    f"- **Action ID**: `{result.get('action_id')}`\n"
                    f"- **Planned Action**: `{result.get('planned_action')}`\n"
                    f"- **Description**: {result.get('description')}\n"
                    f"- **Affected Paths**: `{result.get('affected_paths')}`"
                )
                return {
                    "result": result_str,
                    "confidence": 1.0,
                    "reasoning_summary": "System action requires explicit user approval under the active security policy."
                }
            
            res_val = result.get("result") or result
            
            if action_type == "read_file":
                content = res_val.get("content_preview", "")
                path = res_val.get("path", "")
                result_str = (
                    f"✅ **File Read Successfully**\n"
                    f"- **File**: `{path}`\n\n"
                    f"```\n{content}\n```"
                )
            elif action_type == "list_directory":
                entries = res_val.get("entries", [])
                path = res_val.get("path", "")
                entries_str = "\n".join(f"- {'[DIR] ' if e.get('is_dir') else ''}{e.get('name')}" for e in entries)
                result_str = (
                    f"✅ **Directory Listed Successfully**\n"
                    f"- **Directory**: `{path}`\n\n"
                    f"{entries_str or 'No entries found.'}"
                )
            elif action_type in {"open_file", "open_folder"}:
                path = res_val.get("opened") or res_val.get("opened_folder", "")
                result_str = f"✅ **Path Opened Successfully**: `{path}`"
            else:
                stdout = res_val.get("stdout", "")
                stderr = res_val.get("stderr", "")
                code = res_val.get("returncode", 0)

                result_str = (
                    f"✅ **Action Executed Successfully**\n"
                    f"- **Action**: `{action_type}`\n"
                    f"- **Return Code**: `{code}`\n"
                    f"- **Standard Output**:\n```\n{stdout or 'None'}\n```\n"
                    f"- **Standard Error**:\n```\n{stderr or 'None'}\n```"
                )
            return {
                "result": result_str,
                "confidence": 1.0,
                "reasoning_summary": f"Executed system action '{action_type}' successfully."
            }
        except Exception as e:
            logger.error(f"ExecutionAgent fail: {e}")
            return {
                "result": f"❌ **Execution Error**: {e}",
                "confidence": 0.0,
                "reasoning_summary": f"System action execution encountered an error: {e}"
            }
        finally:
            db.close()


class VerificationAgent(BaseAgent):
    name = "VerificationAgent"
    description = "Validates file paths, repository references, claims, and patches to prevent hallucinations."
    capabilities = ["verification", "validate_paths", "validate_references", "detect_unsupported_claims", "verify_patches"]

    def __init__(self, executor: Any):
        self.executor = executor

    def confidence(self, query: str, context: Optional[str] = None) -> float:
        q = query.lower()
        if any(kw in q for kw in ["verify", "validate", "check path", "check claim", "check patch"]):
            return 0.95
        return 0.30

    async def execute(
        self,
        query: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        target_text = kwargs.get("target_text", query)
        issues = []
        verified_paths = []
        verified_patches = []
        
        # 1. Validate file paths (look for paths in workspace root)
        potential_paths = re.findall(r'(?:[a-zA-Z0-9_\-\.]+/)*[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+', target_text)
        workspace_root = getattr(self.executor.file_agent, "workspace_root", None)
        if workspace_root:
            for path_str in set(potential_paths):
                # Simple check to avoid random words with dots (e.g. 'cortex.ts', 'v1', etc)
                if path_str.split('.')[-1] in ['py', 'ts', 'tsx', 'js', 'json', 'toml', 'sh', 'md', 'yml', 'yaml']:
                    try:
                        p = Path(path_str)
                        if not p.is_absolute():
                            p = Path(workspace_root) / p
                        if p.exists() and p.is_file():
                            verified_paths.append(path_str)
                        else:
                            # Handle diff headers starting with a/ or b/
                            if path_str.startswith("a/") or path_str.startswith("b/"):
                                p_alt = Path(workspace_root) / path_str[2:]
                                if p_alt.exists() and p_alt.is_file():
                                    verified_paths.append(path_str)
                                    continue
                            issues.append(f"Invalid path referenced: `{path_str}` does not exist in workspace.")
                    except Exception:
                        pass

        # 2. Validate patch diffs
        if "```diff" in target_text or "--- a/" in target_text:
            diff_pattern = re.compile(r'--- a/(.+)\n\+\+\+ b/(.+)\n@@ .+', re.MULTILINE)
            matches = diff_pattern.findall(target_text)
            if not matches:
                issues.append("Malformed diff formatting: missing headers (--- a/ and +++ b/) or hunk headers (@@).")
            else:
                for src, dst in matches:
                    verified_patches.append(f"{src} -> {dst}")



        verified = len(issues) == 0
        status_text = "PASSED" if verified else "FAILED"
        
        result_details = (
            f"=== Verification Report ===\n"
            f"Status: {status_text}\n"
            f"Verified Paths: {verified_paths}\n"
            f"Verified Patches: {verified_patches}\n"
            f"Issues Detected:\n" + ("\n".join(f"- {i}" for i in issues) if issues else "None")
        )
        
        return {
            "result": result_details,
            "confidence": 1.0,
            "reasoning_summary": f"Verification completed with status: {status_text}.",
            "verified": verified,
            "issues": issues,
            "verified_paths": verified_paths,
            "verified_patches": verified_patches
        }
