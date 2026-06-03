"""System action execution with approval workflow."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.intelligence.models import PendingSystemAction
from backend.app.intelligence.permissions import PermissionService


class SystemActionsService:
    def __init__(self):
        self.permissions = PermissionService()

    def plan_action(
        self,
        db: Session,
        *,
        user_id: int | None,
        action_type: str,
        description: str,
        affected_paths: list[str],
        payload: dict | None = None,
        category: str | None = None,
    ) -> dict:
        settings = self.permissions.get_settings(db, user_id)
        needs_approval = self.permissions.requires_approval(settings, action_type, category)

        if action_type in {"read_file", "search_files", "index", "summarize", "list_directory"}:
            return self.execute_immediately(action_type, affected_paths, payload or {})

        if needs_approval:
            pending = PendingSystemAction(
                user_id=user_id,
                action_type=action_type,
                description=description,
                affected_paths_json=json.dumps(affected_paths),
                payload_json=json.dumps(payload or {}),
                status="pending",
            )
            db.add(pending)
            db.commit()
            db.refresh(pending)
            return {
                "status": "approval_required",
                "action_id": pending.id,
                "description": description,
                "affected_paths": affected_paths,
                "planned_action": action_type,
            }

        result = self.execute_immediately(action_type, affected_paths, payload or {})
        return {"status": "executed", "result": result}

    def approve_and_execute(self, db: Session, action_id: int) -> dict:
        pending = db.get(PendingSystemAction, action_id)
        if not pending or pending.status != "pending":
            return {"status": "error", "message": "Action not found or already resolved"}

        paths = json.loads(pending.affected_paths_json or "[]")
        payload = json.loads(pending.payload_json or "{}")
        result = self.execute_immediately(pending.action_type, paths, payload)
        pending.status = "approved"
        pending.resolved_at = datetime.utcnow()
        db.commit()
        return {"status": "executed", "action_id": action_id, "result": result}

    def reject(self, db: Session, action_id: int) -> dict:
        pending = db.get(PendingSystemAction, action_id)
        if not pending or pending.status != "pending":
            return {"status": "error", "message": "Action not found"}
        pending.status = "rejected"
        pending.resolved_at = datetime.utcnow()
        db.commit()
        return {"status": "rejected", "action_id": action_id}

    def list_pending(self, db: Session, user_id: int | None = None) -> list[dict]:
        q = db.query(PendingSystemAction).filter(PendingSystemAction.status == "pending")
        if user_id is not None:
            q = q.filter(
                (PendingSystemAction.user_id == user_id)
                | (PendingSystemAction.user_id.is_(None))
            )
        rows = q.order_by(PendingSystemAction.created_at.desc()).limit(20).all()
        return [
            {
                "id": row.id,
                "action_type": row.action_type,
                "description": row.description,
                "affected_paths": json.loads(row.affected_paths_json or "[]"),
                "payload": json.loads(row.payload_json or "{}"),
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

    def execute_immediately(
        self, action_type: str, affected_paths: list[str], payload: dict
    ) -> dict:
        if action_type == "open_file":
            path = affected_paths[0] if affected_paths else payload.get("path")
            if path:
                subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"opened": path}

        if action_type == "open_folder":
            path = affected_paths[0] if affected_paths else payload.get("path")
            if path:
                subprocess.Popen(["xdg-open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"opened_folder": path}

        if action_type == "read_file":
            path = affected_paths[0] if affected_paths else payload.get("path")
            if not path:
                return {"error": "no path"}
            content = Path(path).read_text(encoding="utf-8", errors="ignore")[:8000]
            return {"path": path, "content_preview": content}

        if action_type == "list_directory":
            path = affected_paths[0] if affected_paths else payload.get("path", ".")
            entries = []
            for item in sorted(Path(path).iterdir())[:100]:
                entries.append({"name": item.name, "is_dir": item.is_dir()})
            return {"path": path, "entries": entries}

        if action_type == "run_command":
            command = payload.get("command")
            if not command:
                return {"error": "command required"}
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=int(payload.get("timeout", 30)),
                cwd=payload.get("cwd"),
            )
            return {
                "returncode": completed.returncode,
                "stdout": completed.stdout[:4000],
                "stderr": completed.stderr[:2000],
            }

        if action_type == "search_files":
            query = payload.get("query", "")
            from backend.app.agent.file_search import FileSearchAgent

            agent = FileSearchAgent()
            return {"result": agent.search(query)}

        return {"status": "unsupported", "action_type": action_type}
