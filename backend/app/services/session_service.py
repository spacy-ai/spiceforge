from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from app.models.session import CircuitSession


class SessionService:
    def __init__(self, db: DBSession):
        self._db = db

    def create_session(
        self,
        user_id: Optional[int],
        prompt: str,
        intent: str,
        blueprint: dict,
        netlist: str,
    ) -> CircuitSession:
        conversation = [
            {
                "role": "user",
                "content": prompt,
                "intent": intent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "role": "assistant",
                "content": blueprint.get("summary", ""),
                "intent": intent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        session = CircuitSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            context=prompt,
            latest_blueprint_json=json.dumps(blueprint),
            latest_netlist=netlist,
            simulation_history_json=json.dumps([]),
            retry_history_json=json.dumps([]),
            conversation_history_json=json.dumps(conversation),
        )
        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[CircuitSession]:
        return (
            self._db.query(CircuitSession)
            .filter(CircuitSession.session_id == session_id)
            .first()
        )

    def update_session(
        self,
        session_id: str,
        prompt: str,
        intent: str,
        blueprint: dict,
        netlist: str,
        assistant_summary: str = "",
        changes_summary: Optional[str] = None,
    ) -> Optional[CircuitSession]:
        session = self.get_session(session_id)
        if session is None:
            return None

        history = json.loads(session.conversation_history_json or "[]")

        history.append(
            {
                "role": "user",
                "content": prompt,
                "intent": intent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        assistant_msg: dict = {
            "role": "assistant",
            "content": assistant_summary,
            "intent": intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if changes_summary:
            assistant_msg["changes_summary"] = changes_summary
        history.append(assistant_msg)

        session.context = prompt
        session.latest_blueprint_json = json.dumps(blueprint)
        session.latest_netlist = netlist
        session.conversation_history_json = json.dumps(history)
        session.updated_at = datetime.now(timezone.utc)

        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        return session

    def get_conversation_history(self, session_id: str) -> list[dict]:
        session = self.get_session(session_id)
        if session is None:
            return []
        return json.loads(session.conversation_history_json or "[]")

    def get_blueprint(self, session_id: str) -> Optional[dict]:
        session = self.get_session(session_id)
        if session is None or session.latest_blueprint_json is None:
            return None
        return json.loads(session.latest_blueprint_json)

    def get_netlist(self, session_id: str) -> str:
        session = self.get_session(session_id)
        if session is None:
            return ""
        return session.latest_netlist or ""

    def list_sessions(
        self, user_id: Optional[int], limit: int = 50
    ) -> list[CircuitSession]:
        query = self._db.query(CircuitSession)
        if user_id is not None:
            query = query.filter(CircuitSession.user_id == user_id)
        return query.order_by(CircuitSession.updated_at.desc()).limit(limit).all()
