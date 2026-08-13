"""Profile service for DhanSarthi."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError, handle_db_exceptions
from app.models.enums import Persona, RiskProfile
from app.models.profile import Profile
from app.repositories.profile_repository import ProfileRepository


class ProfileService:
    """Coordinates Profile business logic and persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = ProfileRepository(db)

    def get_profile(self, user_id: int) -> Profile:
        """Retrieve Profile for user_id, or raise ResourceNotFoundError."""
        profile = self._repo.get_by_user_id(user_id)
        if profile is None:
            raise ResourceNotFoundError(resource="Profile", identifier=user_id)
        return profile

    def get_or_create_profile(
        self,
        user_id: int,
        *,
        persona: Persona = Persona.PROFESSIONAL,
        display_name: str | None = None,
        country: str = "IN",
        currency: str = "INR",
        risk_profile: RiskProfile | None = RiskProfile.MODERATE,
    ) -> Profile:
        """Retrieve existing Profile or create a default Profile for user_id."""
        profile = self._repo.get_by_user_id(user_id)
        if profile is not None:
            return profile

        new_profile = Profile(
            user_id=user_id,
            persona=persona,
            display_name=display_name or f"User {user_id}",
            country=country,
            currency=currency,
            risk_profile=risk_profile,
        )
        with handle_db_exceptions(resource="Profile"):
            self._repo.add(new_profile)
            self._db.commit()
        self._db.refresh(new_profile)
        return new_profile

    def update_profile(self, user_id: int, **fields: object) -> Profile:
        """Update fields on existing user Profile or create if missing."""
        profile = self._repo.get_by_user_id(user_id)
        if profile is None:
            # Create if updating a non-existent profile
            persona = fields.get("persona") or Persona.PROFESSIONAL
            profile = Profile(user_id=user_id, persona=persona)
            self._repo.add(profile)

        allowed = {"persona", "display_name", "country", "currency", "risk_profile", "phone", "occupation"}
        for key, value in fields.items():
            if key in allowed:
                setattr(profile, key, value)

        with handle_db_exceptions(resource="Profile"):
            self._db.commit()
        self._db.refresh(profile)
        return profile
