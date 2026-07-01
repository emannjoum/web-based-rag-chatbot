from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import OperationalError, ProgrammingError

from chatbot.application.auth_service import AuthService
from chatbot.domain.exceptions import AuthError, PersistenceError
from chatbot.domain.models import User
from chatbot.presentation.api.auth_dependencies import get_current_user
from chatbot.presentation.api.dependencies import get_auth_service
from chatbot.presentation.api.schemas import AuthResponse, LoginRequest, RegisterRequest, UserSchema

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_schema(user: User) -> UserSchema:
    return UserSchema(id=user.id, email=user.email, display_name=user.display_name)


def _auth_response(user: User, token: str) -> AuthResponse:
    return AuthResponse(access_token=token, user=_user_schema(user))


def _raise_db_unavailable(exc: Exception) -> None:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="User database is unavailable. Ensure MySQL is running and migrations have been applied.",
    ) from exc


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user, token = auth_service.register(payload.email, payload.password, payload.display_name)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (PersistenceError, OperationalError, ProgrammingError) as exc:
        _raise_db_unavailable(exc)
    return _auth_response(user, token)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    try:
        user, token = auth_service.login(payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except (PersistenceError, OperationalError, ProgrammingError) as exc:
        _raise_db_unavailable(exc)
    return _auth_response(user, token)


@router.get("/me", response_model=UserSchema)
def me(current_user: User = Depends(get_current_user)) -> UserSchema:
    return _user_schema(current_user)
