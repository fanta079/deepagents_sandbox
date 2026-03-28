"""
国际化 (i18n) 核心模块
"""

import json
from pathlib import Path

LOCALE_DIR = Path(__file__).parent / "locales"


def get_message(lang: str, key: str, default: str = "") -> str:
    """获取翻译消息"""
    try:
        locale_file = LOCALE_DIR / f"{lang}.json"
        if not locale_file.exists():
            locale_file = LOCALE_DIR / "zh_CN.json"
        with open(locale_file, "r", encoding="utf-8") as f:
            messages = json.load(f)
        # 支持嵌套 key 如 "auth.login_success"
        keys = key.split(".")
        result = messages
        for k in keys:
            result = result.get(k, default)
        return result
    except Exception:
        return default
