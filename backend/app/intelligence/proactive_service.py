"""High-value proactive suggestions — avoid spamming the user."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.intelligence.models import ProactiveNotification


class ProactiveService:
    COOLDOWN_HOURS = 6
    PDF_BATCH_THRESHOLD = 10

    def evaluate_after_sync(
        self,
        db: Session,
        *,
        user_id: int | None,
        new_repos: int,
        new_pdfs: int,
        modified_project_files: int,
        repo_count: int,
        pdf_total: int,
    ) -> list[ProactiveNotification]:
        created: list[ProactiveNotification] = []

        if new_repos > 0 and self._can_notify(db, user_id, "new_repository"):
            created.append(
                self._create(
                    db,
                    user_id=user_id,
                    priority="high",
                    title="New repository detected",
                    message=(
                        f"Cortex found {new_repos} new repository location(s). "
                        "Would you like an architecture analysis?"
                    ),
                    action_type="repository_analysis",
                    action_payload={"scope": "new_repositories"},
                )
            )

        if new_pdfs >= self.PDF_BATCH_THRESHOLD and self._can_notify(db, user_id, "pdf_batch"):
            created.append(
                self._create(
                    db,
                    user_id=user_id,
                    priority="normal",
                    title="New documents available",
                    message=(
                        f"I found {new_pdfs} new PDFs (≈{pdf_total} total tracked). "
                        "Would you like a consolidated summary?"
                    ),
                    action_type="document_summary",
                    action_payload={"pdf_count": new_pdfs},
                )
            )

        if modified_project_files >= 25 and self._can_notify(db, user_id, "project_changes"):
            created.append(
                self._create(
                    db,
                    user_id=user_id,
                    priority="normal",
                    title="Significant project changes",
                    message=(
                        f"Cortex detected {modified_project_files} modified project files. "
                        "Would you like an updated architecture report?"
                    ),
                    action_type="architecture_report",
                    action_payload={"modified_files": modified_project_files},
                )
            )

        if repo_count > 0 and not created and self._can_notify(db, user_id, "sync_complete"):
            if new_pdfs > 0 or modified_project_files > 5:
                pass
            else:
                pass

        db.commit()
        return created

    def list_active(self, db: Session, user_id: int | None = None, limit: int = 10) -> list[dict]:
        q = db.query(ProactiveNotification).filter(ProactiveNotification.dismissed.is_(False))
        if user_id is not None:
            q = q.filter(
                (ProactiveNotification.user_id == user_id)
                | (ProactiveNotification.user_id.is_(None))
            )
        rows = q.order_by(ProactiveNotification.created_at.desc()).limit(limit).all()
        return [
            {
                "id": row.id,
                "priority": row.priority,
                "title": row.title,
                "message": row.message,
                "action_type": row.action_type,
                "action_payload": json.loads(row.action_payload_json or "{}"),
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]

    def dismiss(self, db: Session, notification_id: int) -> bool:
        row = db.get(ProactiveNotification, notification_id)
        if not row:
            return False
        row.dismissed = True
        db.commit()
        return True

    def _can_notify(self, db: Session, user_id: int | None, kind: str) -> bool:
        since = datetime.utcnow() - timedelta(hours=self.COOLDOWN_HOURS)
        recent = (
            db.query(ProactiveNotification)
            .filter(
                ProactiveNotification.created_at >= since,
                ProactiveNotification.title.contains(kind.replace("_", " ").title()),
            )
            .first()
        )
        if recent:
            return False

        count = (
            db.query(ProactiveNotification)
            .filter(
                ProactiveNotification.dismissed.is_(False),
                ProactiveNotification.created_at >= since,
            )
            .count()
        )
        return count < 3

    def _create(
        self,
        db: Session,
        *,
        user_id: int | None,
        priority: str,
        title: str,
        message: str,
        action_type: str,
        action_payload: dict,
    ) -> ProactiveNotification:
        row = ProactiveNotification(
            user_id=user_id,
            priority=priority,
            title=title,
            message=message,
            action_type=action_type,
            action_payload_json=json.dumps(action_payload),
        )
        db.add(row)
        db.flush()
        return row
