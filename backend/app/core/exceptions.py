"""
自定义异常类

用于统一的错误处理和重试机制
"""
from typing import Optional, Any, Dict


class AppException(Exception):
    """应用基础异常"""
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class VideoProcessingError(AppException):
    """视频处理错误"""
    def __init__(self, message: str, video_id: Optional[int] = None):
        details = {"video_id": video_id} if video_id else {}
        super().__init__(
            message=message,
            code="VIDEO_PROCESSING_ERROR",
            status_code=500,
            details=details
        )


class ASRError(VideoProcessingError):
    """ASR 语音识别错误"""
    def __init__(self, message: str, video_id: Optional[int] = None):
        super().__init__(
            message=message,
            code="ASR_ERROR",
            status_code=500,
            details={"video_id": video_id} if video_id else {}
        )


class LLMParsingError(VideoProcessingError):
    """LLM 解析错误"""
    def __init__(self, message: str, raw_output: Optional[str] = None):
        super().__init__(
            message=message,
            code="LLM_PARSING_ERROR",
            status_code=500,
            details={"raw_output": raw_output[:200] if raw_output else None}
        )


class DatabaseError(AppException):
    """数据库错误"""
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation} if operation else {}
        )


class NotFoundError(AppException):
    """资源未找到错误"""
    def __init__(self, resource_type: str, resource_id: Any):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ValidationError(AppException):
    """验证错误"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field} if field else {}
        )
