from fastapi import HTTPException, status

class LinkNotFoundError(HTTPException):
    def __init__(self, short_code: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link '{short_code}' not found or has been deleted."
        )

class LinkInactiveError(HTTPException):
    def __init__(self, short_code: str):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail=f"Link '{short_code}' is no longer active."
        )

class RedisConnectionError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service temporarily unavailable."
        )