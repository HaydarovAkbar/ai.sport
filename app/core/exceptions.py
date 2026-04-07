from fastapi import HTTPException, status


class CredentialsException(HTTPException):
    def __init__(self, detail: str = "Hisob ma'lumotlari noto'g'ri"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Ruxsat yo'q"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Topilmadi"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(HTTPException):
    def __init__(self, detail: str = "Allaqachon mavjud"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class SecurityException(HTTPException):
    def __init__(self, detail: str = "Xavfsizlik xatosi aniqlandi"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class RateLimitException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Juda ko'p so'rov. Biroz kuting.",
        )
