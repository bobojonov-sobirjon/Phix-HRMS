"""
Application constants
"""
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1
DEFAULT_PAGE = 1

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7

DEFAULT_OTP_LENGTH = 6
DEFAULT_OTP_EXPIRE_MINUTES = 5

MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}

DEFAULT_QUERY_LIMIT = 100
MAX_QUERY_LIMIT = 1000
SLOW_QUERY_THRESHOLD_SECONDS = 1.0

WEBSOCKET_PING_INTERVAL = 20
WEBSOCKET_PING_TIMEOUT = 10

ERROR_MESSAGES = {
    "UNAUTHORIZED": "Authentication required",
    "FORBIDDEN": "You don't have permission to perform this action",
    "NOT_FOUND": "Resource not found",
    "VALIDATION_ERROR": "Invalid input data",
    "INTERNAL_ERROR": "An internal error occurred",
    "BAD_REQUEST": "Invalid request",
    "CONFLICT": "Resource already exists",
    "RATE_LIMIT": "Too many requests, please try again later",
}

SUCCESS_MESSAGES = {
    "CREATED": "Resource created successfully",
    "UPDATED": "Resource updated successfully",
    "DELETED": "Resource deleted successfully",
    "RETRIEVED": "Resource retrieved successfully",
}
