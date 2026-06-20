from fastapi import APIRouter, Depends, HTTPException, status

from chatbot.application.session_service import SessionService
from chatbot.presentation.api.dependencies import get_session_service
from chatbot.presentation.api.schemas import (
    DeleteAllSessionsResponse,
    DeleteSessionResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionSummarySchema,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionController:
    def __init__(self, session_service: SessionService) -> None:
        self._session_service = session_service

    def list_sessions(self) -> SessionListResponse:
        sessions = [
            SessionSummarySchema(**session)
            for session in self._session_service.list_sessions()
        ]
        return SessionListResponse(sessions=sessions)

    def get_session(self, session_id: str) -> SessionDetailResponse:
        messages = self._session_service.get_session_messages(session_id)
        if not messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )
        return SessionDetailResponse(session_id=session_id, messages=messages)

    def delete_session(self, session_id: str) -> DeleteSessionResponse:
        deleted = self._session_service.delete_session(session_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found.",
            )
        return DeleteSessionResponse(deleted=True, session_id=session_id)

    def delete_all_sessions(self) -> DeleteAllSessionsResponse:
        deleted_count = self._session_service.delete_all_sessions()
        return DeleteAllSessionsResponse(deleted_count=deleted_count)


def _controller(
    session_service: SessionService = Depends(get_session_service),
) -> SessionController:
    return SessionController(session_service)


@router.get("", response_model=SessionListResponse)
def list_sessions(controller: SessionController = Depends(_controller)) -> SessionListResponse:
    return controller.list_sessions()


@router.get("/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: str,
    controller: SessionController = Depends(_controller),
) -> SessionDetailResponse:
    return controller.get_session(session_id)


@router.delete("/{session_id}", response_model=DeleteSessionResponse)
def delete_session(
    session_id: str,
    controller: SessionController = Depends(_controller),
) -> DeleteSessionResponse:
    return controller.delete_session(session_id)


@router.delete("", response_model=DeleteAllSessionsResponse)
def delete_all_sessions(
    controller: SessionController = Depends(_controller),
) -> DeleteAllSessionsResponse:
    return controller.delete_all_sessions()
