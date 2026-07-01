import logging
from typing import Any
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from chatbot.application.chat_service import ChatService
from chatbot.domain.exceptions import AppError, PersistenceError, SearchError
from chatbot.domain.models import User
from chatbot.presentation.api.auth_dependencies import get_current_user
from chatbot.presentation.api.dependencies import get_chat_service, get_container
from chatbot.presentation.api.model_registry import ModelRegistry
from chatbot.presentation.api.schemas import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessageSchema,
    ImageUploadResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg"}


class ChatController:
    def __init__(self, chat_service: ChatService, current_user: User) -> None:
        self._chat_service = chat_service
        self._current_user = current_user
        self._settings = get_container().settings

    def complete(self, payload: ChatCompletionRequest) -> ChatCompletionResponse:
        search_method = payload.search_method or self._settings.default_search_method
        provider_model = ModelRegistry.resolve_provider_value(payload.model_id)
        history = self._build_history(payload.session_id)

        start_time = time.perf_counter()

        try:
            result = self._chat_service.handle_text_query(
                payload.message,
                history,
                payload.session_id,
                self._current_user.id,
                provider_model,
                search_method,
                is_drug_profile=payload.is_drug_profile,
            )
        except SearchError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc
        except PersistenceError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc
        except AppError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

        end_time = time.perf_counter()
        thoughtDurationSeconds = round(end_time - start_time, 1)

        if not result.session_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Pipeline completed without a session identifier.",
            )

        return ChatCompletionResponse(
            session_id=result.session_id,
            status=result.status,
            user_message=ChatMessageSchema(role="user", content=payload.message),
            assistant_message=ChatMessageSchema(
                role="assistant",
                content=result.response,
                sources={str(key): value for key, value in result.sources.items()},
                suggestions=result.suggestions,
                eval_status="pending" if result.sources else None,
                thoughtDurationSeconds=thoughtDurationSeconds,
            ),
        )

    async def upload_image(
        self,
        *,
        file: UploadFile,
        session_id: str | None,
        model_id: str,
        caption: str | None,
        search_method: str | None,
    ) -> ImageUploadResponse | ChatCompletionResponse:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PNG and JPEG medical images are supported.",
            )

        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        provider_model = ModelRegistry.resolve_provider_value(model_id)
        resolved_search = search_method or self._settings.default_search_method

        try:
            image_result = self._chat_service.handle_image_upload(
                image_bytes,
                file.filename or "upload.jpg",
                caption,
                provider_model,
            )
        except AppError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

        if image_result.status == "drug" and image_result.drug_query:
            message = image_result.drug_query
            if caption:
                message = f"I am asking about the drug: {image_result.drug_query}. Specifically: {caption}"

            return self.complete(
                ChatCompletionRequest(
                    message=message,
                    session_id=session_id,
                    model_id=model_id,
                    search_method=resolved_search,
                    is_drug_profile=True,
                )
            )

        assistant_content = image_result.assistant_response or ""
        try:
            new_session_id = self._chat_service.persist_simple_exchange(
                session_id,
                self._current_user.id,
                image_result.user_message,
                assistant_content,
                {
                    "model": provider_model,
                    "content_type": image_result.status,
                    "has_report_upload": image_result.status == "report",
                },
            )
        except PersistenceError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        return ImageUploadResponse(
            session_id=new_session_id,
            status=image_result.status,
            user_message=ChatMessageSchema(role="user", content=image_result.user_message),
            assistant_message=ChatMessageSchema(role="assistant", content=assistant_content),
            metadata={"content_type": image_result.status},
        )

    def _build_history(self, session_id: str | None) -> list[dict[str, Any]]:
        if not session_id:
            return []

        from chatbot.application.session_service import SessionService

        session_service = SessionService(get_container().repository)
        return session_service.get_session_messages(session_id, self._current_user.id)


def _controller(
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_current_user),
) -> ChatController:
    return ChatController(chat_service, current_user)


@router.post("/completions", response_model=ChatCompletionResponse)
def create_completion(
    payload: ChatCompletionRequest,
    controller: ChatController = Depends(_controller),
) -> ChatCompletionResponse:
    return controller.complete(payload)


@router.post("/image", response_model=ImageUploadResponse | ChatCompletionResponse)
async def upload_image(
    file: UploadFile = File(...),
    session_id: str | None = Form(default=None),
    model_id: str = Form(default=ModelRegistry.default_id()),
    caption: str | None = Form(default=None),
    search_method: str | None = Form(default=None),
    controller: ChatController = Depends(_controller),
) -> ImageUploadResponse | ChatCompletionResponse:
    return await controller.upload_image(
        file=file,
        session_id=session_id,
        model_id=model_id,
        caption=caption,
        search_method=search_method,
    )
