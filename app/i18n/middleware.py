"""
i18n 中间件 — 自动检测语言并注入到 request.state
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

SUPPORTED_LANGUAGES = ["zh_CN", "en_US", "ja_JP", "ko_KR"]
DEFAULT_LANGUAGE = "zh_CN"


class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        lang = request.headers.get("Accept-Language", DEFAULT_LANGUAGE)
        # 简化处理，实际可用更复杂的语言检测
        request.state.lang = lang[:5] if lang else DEFAULT_LANGUAGE
        if request.state.lang not in SUPPORTED_LANGUAGES:
            request.state.lang = DEFAULT_LANGUAGE
        return await call_next(request)


def get_translations(lang: str):
    """加载翻译文件"""
    from app.i18n import get_message, LOCALE_DIR
    import json

    try:
        locale_file = LOCALE_DIR / f"{lang}.json"
        if not locale_file.exists():
            locale_file = LOCALE_DIR / "zh_CN.json"
        with open(locale_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
