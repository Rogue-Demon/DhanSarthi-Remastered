"""Goal API router for DhanSarthi."""

from __future__ import annotations

from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user_id, get_goal_service
from app.models.enums import GoalStatus
from app.schemas.common import PaginatedResponse
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=PaginatedResponse[GoalResponse])
def list_goals(
    user_id: int = Depends(get_current_user_id),
    service: GoalService = Depends(get_goal_service),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    goal_status: Optional[GoalStatus] = Query(default=None, alias="status"),
    priority: Optional[int] = Query(default=None, ge=1, le=5),
) -> PaginatedResponse[GoalResponse]:
    """List financial goals for the current user with optional filtering and pagination."""
    offset = (page - 1) * page_size
    items = service.list_goals(
        user_id,
        limit=page_size,
        offset=offset,
        status=goal_status,
        priority=priority,
    )
    all_items = service.list_goals(
        user_id,
        limit=10000,
        offset=0,
        status=goal_status,
        priority=priority,
    )
    total = len(all_items)
    total_pages = max(1, ceil(total / page_size))

    serialized = [GoalResponse.model_validate(item) for item in items]
    return PaginatedResponse(
        items=serialized,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    user_id: int = Depends(get_current_user_id),
    service: GoalService = Depends(get_goal_service),
) -> GoalResponse:
    """Create a new goal record for the current user."""
    goal = service.create_goal(
        user_id,
        name=data.title,
        target_amount=data.target_amount,
        target_date=data.target_date,
        current_amount=data.current_amount,
        status=data.status,
        priority=data.priority,
    )
    return GoalResponse.model_validate(goal)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    service: GoalService = Depends(get_goal_service),
) -> GoalResponse:
    """Retrieve a single goal record by ID for the current user."""
    goal = service.get_goal(goal_id, user_id)
    return GoalResponse.model_validate(goal)


@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    data: GoalUpdate,
    user_id: int = Depends(get_current_user_id),
    service: GoalService = Depends(get_goal_service),
) -> GoalResponse:
    """Update fields on an existing goal record."""
    update_fields = data.model_dump(exclude_unset=True)
    # Map API field 'title' to ORM field 'name'
    if "title" in update_fields:
        update_fields["name"] = update_fields.pop("title")
    goal = service.update_goal(goal_id, user_id, **update_fields)
    return GoalResponse.model_validate(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    service: GoalService = Depends(get_goal_service),
) -> None:
    """Delete a goal record."""
    service.delete_goal(goal_id, user_id)
