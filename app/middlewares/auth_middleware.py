from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import JWT_SECRET, X_API_KEY

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer()

    async def dispatch(self, request: Request, call_next):
        # Bỏ qua xác thực cho một số endpoint nếu cần
        if request.url.path == "/" or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi"):
            return await call_next(request)

        # Kiểm tra x-api-key trong header
        api_key = request.headers.get("x-api-key")
        if api_key and api_key == X_API_KEY:
            return await call_next(request)

        # Kiểm tra JWT token
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(status_code=401, detail="Missing Authorization header")

            # Lấy token từ header
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=401, detail="Invalid authentication scheme")

            # Giải mã token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            
            # Kiểm tra thời gian hết hạn
            if "exp" in payload:
                exp = datetime.fromtimestamp(payload["exp"])
                if exp < datetime.now():
                    raise HTTPException(status_code=401, detail="Token has expired")

            # Lưu thông tin user vào request state
            request.state.user = payload
            return await call_next(request)

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))

        # Nếu không có cả API key và JWT token
        raise HTTPException(status_code=401, detail="Unauthorized")