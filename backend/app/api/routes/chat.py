from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from app.core.dependencies import get_db, get_optional_current_user
from app.models.pipeline_models import PipelineResult
from app.models.user import User
from app.schema.chat import (
    ChatCreateRequest,
    ChatExplainRequest,
    ChatModifyRequest,
    ChatResponse,
    SessionInfoResponse,
    SimulationInfo,
)
from app.services.netlist_generation_pipeline import NetlistGenerationPipeline
from app.services.session_service import SessionService

router = APIRouter(tags=["chat"])
log = logging.getLogger(__name__)


def _build_response(result: PipelineResult, session_id: str | None) -> ChatResponse:
    netlist = ""
    if result.synthesis:
        netlist = result.synthesis.netlist

    intent_str = result.intent.intent.value if result.intent else None

    sim_info = None
    if result.simulation:
        sim_info = SimulationInfo(
            success=result.simulation.success,
            analyses=result.simulation.analyses,
            results=result.simulation.results,
            stdout=result.simulation.stdout[-2000:] if result.simulation.stdout else "",
            stderr=result.simulation.stderr[-2000:] if result.simulation.stderr else "",
            error=result.simulation.error,
            convergence_failures=result.simulation.convergence_failures,
        )

    return ChatResponse(
        success=result.success,
        session_id=session_id,
        intent=intent_str,
        summary=result.summary or "",
        blueprint=result.blueprint,
        netlist=netlist or None,
        changes_summary=result.changes_summary,
        clarifications=result.clarifications,
        error=result.error,
        simulation=sim_info,
    )


@router.post("/create", response_model=ChatResponse)
def chat_create(
    request: ChatCreateRequest,
    db: DBSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    pipeline = NetlistGenerationPipeline(
        api_key=request.api_key,
        model=request.model,
    )

    result: PipelineResult = pipeline.run(
        prompt=request.prompt,
        run_simulation=request.run_simulation,
    )

    if result.clarifications:
        return _build_response(result, session_id=None)

    if not result.success:
        return _build_response(result, session_id=None)

    try:
        svc = SessionService(db)
        session = svc.create_session(
            user_id=current_user.id if current_user else None,
            prompt=request.prompt,
            intent=result.intent.intent.value if result.intent else "CREATE_CIRCUIT",
            blueprint=result.blueprint or {},
            netlist=result.synthesis.netlist if result.synthesis else "",
        )
        return _build_response(result, session_id=session.session_id)
    except Exception as exc:
        log.warning("Failed to persist session: %s", exc)
        return _build_response(result, session_id=None)


@router.post("/modify", response_model=ChatResponse)
def chat_modify(
    request: ChatModifyRequest,
    db: DBSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    existing_blueprint = None
    try:
        svc = SessionService(db)
        session = svc.get_session(request.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.latest_blueprint_json:
            existing_blueprint = json.loads(session.latest_blueprint_json)
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("Failed to load session %s: %s", request.session_id, exc)
        raise HTTPException(status_code=503, detail="Database unavailable")

    pipeline = NetlistGenerationPipeline(
        api_key=request.api_key,
        model=request.model,
    )

    result: PipelineResult = pipeline.run(
        prompt=request.prompt,
        existing_blueprint=existing_blueprint,
        run_simulation=True,
    )

    if result.clarifications:
        return _build_response(result, session_id=request.session_id)

    if not result.success:
        return _build_response(result, session_id=request.session_id)

    intent_str = result.intent.intent.value if result.intent else "MODIFY_CIRCUIT"

    try:
        svc.update_session(
            session_id=request.session_id,
            prompt=request.prompt,
            intent=intent_str,
            blueprint=result.blueprint or {},
            netlist=result.synthesis.netlist if result.synthesis else "",
            assistant_summary=result.summary or "",
            changes_summary=result.changes_summary,
        )
    except Exception as exc:
        log.warning("Failed to update session %s: %s", request.session_id, exc)

    return _build_response(result, session_id=request.session_id)


@router.post("/explain", response_model=ChatResponse)
def chat_explain(
    request: ChatExplainRequest,
    db: DBSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    existing_blueprint = None
    try:
        svc = SessionService(db)
        session = svc.get_session(request.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.latest_blueprint_json:
            existing_blueprint = json.loads(session.latest_blueprint_json)
    except HTTPException:
        raise
    except Exception as exc:
        log.warning("Failed to load session %s: %s", request.session_id, exc)
        raise HTTPException(status_code=503, detail="Database unavailable")

    pipeline = NetlistGenerationPipeline(
        api_key=request.api_key,
        model=request.model,
    )

    result: PipelineResult = pipeline.run(
        prompt=request.prompt,
        existing_blueprint=existing_blueprint,
        run_simulation=False,
    )

    return _build_response(result, session_id=request.session_id)


@router.get("/sessions/{session_id}", response_model=SessionInfoResponse)
def get_session_info(
    session_id: str,
    db: DBSession = Depends(get_db),
):
    try:
        svc = SessionService(db)
        session = svc.get_session(session_id)
    except Exception as exc:
        log.warning("Failed to load session %s: %s", session_id, exc)
        raise HTTPException(status_code=503, detail="Database unavailable")

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionInfoResponse(
        session_id=session.session_id,
        conversation_history=json.loads(session.conversation_history_json or "[]"),
        blueprint=json.loads(session.latest_blueprint_json) if session.latest_blueprint_json else None,
        netlist=session.latest_netlist or "",
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )
