import secrets

from fastapi import Header, HTTPException, status

from slicerag.config import settings


async def require_internal_access(
    x_slicerag_internal_token: str | None = Header(default=None),
) -> None:
    """Gateway와 SliceRAG 사이의 내부 호출만 허용한다."""
    expected_token = settings.internal_token
    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="내부 서비스 토큰이 설정되지 않았습니다.",
        )

    if x_slicerag_internal_token is None or not secrets.compare_digest(
        x_slicerag_internal_token, expected_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="내부 서비스 인증에 실패했습니다.",
        )
