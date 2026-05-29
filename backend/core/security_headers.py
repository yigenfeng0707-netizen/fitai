"""
安全响应头中间件
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """为所有响应添加安全头"""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # 防止 MIME 类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"

        # 启用浏览器 XSS 过滤器
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 控制 Referrer 信息泄露
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content-Security-Policy（API 服务，严格限制）
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
        )

        # 隐藏服务器版本信息
        try:
            del response.headers["Server"]
        except KeyError:
            pass

        # 禁用浏览器缓存敏感 API 响应
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        return response
