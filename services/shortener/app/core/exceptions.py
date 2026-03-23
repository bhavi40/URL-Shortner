from fastapi import HTTPException, status

class LinkNotFoundError(HTTPException):
    def __init__(self, short_code: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Link '{short_code}' not found."
        )

class LinkLimitReachedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Link limit reached. Upgrade to Paid for unlimited links."
        )

class CustomAliasNotAllowedError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Custom aliases require a Paid plan."
        )

class AliasAlreadyTakenError(HTTPException):
    def __init__(self, alias: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The alias '{alias}' is already taken."
        )

class ShortCodeGenerationError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate a unique short code. Please try again."
        )