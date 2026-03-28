"""
统一错误码定义

格式: ERROR_CODES = { "CODE": "描述" }
"""

ERROR_CODES = {
    # ——— 认证类 ——————————————————————————————————————————————
    "AUTH_001": "Invalid credentials",
    "AUTH_002": "Token expired",
    "AUTH_003": "Token invalid",
    # ——— 用户类 ——————————————————————————————————————————————
    "USER_001": "User not found",
    "USER_002": "User already exists",
    # ——— 任务类 ——————————————————————————————————————————————
    "TASK_001": "Task not found",
    "TASK_002": "Invalid task status",
    # ——— 通用 ——————————————————————————————————————————————
    "VALIDATION_001": "Validation error",
}


def get_error_message(code: str) -> str:
    """根据错误码获取描述，未知码返回原始码"""
    return ERROR_CODES.get(code, code)
