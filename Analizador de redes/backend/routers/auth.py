from fastapi import APIRouter, HTTPException, status
from schemas import AuthLoginRequest, AuthLoginResponse
from config import settings

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=AuthLoginResponse)
def login(credentials: AuthLoginRequest):
    """
    Autenticación administrativa de Social Analyzer contra variables de entorno.
    """
    if credentials.username != settings.ADMIN_USER or credentials.password != settings.ADMIN_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de acceso incorrectas. Verifique usuario y contraseña."
        )

    # Token de sesión local dev/prod
    return AuthLoginResponse(
        access_token=f"social_session_{settings.ADMIN_USER.lower()}_token",
        token_type="bearer",
        username=settings.ADMIN_USER
    )

@router.get("/verify")
def verify_session():
    """
    Verifica si el servidor de autenticación está operativo.
    """
    return {"status": "active", "admin_user": settings.ADMIN_USER}
