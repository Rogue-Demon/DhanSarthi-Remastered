"""Profile API router for DhanSarthi."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user_id, get_profile_service
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    user_id: int = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Retrieve financial profile for the current user."""
    profile = service.get_or_create_profile(user_id)
    return ProfileResponse.model_validate(profile)


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ProfileCreate,
    user_id: int = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Create or initialize profile for the current user."""
    profile = service.get_or_create_profile(
        user_id,
        persona=data.persona,
        display_name=data.display_name,
        country=data.country,
        currency=data.currency,
        risk_profile=data.risk_profile,
    )
    return ProfileResponse.model_validate(profile)


@router.patch("", response_model=ProfileResponse)
def update_profile(
    data: ProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Update fields on the current user's profile."""
    update_data = data.model_dump(exclude_unset=True)
    profile = service.update_profile(user_id, **update_data)
    return ProfileResponse.model_validate(profile)
