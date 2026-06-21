from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import ChallengeCreate, ChallengeUpdate, ChallengeResponse, ChallengeWithStats
from app.services import (
    get_current_user,
    create_challenge,
    get_challenges_with_stats,
    get_challenge_by_id,
    calculate_challenge_progress,
    update_challenge,
    delete_challenge,
)

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.get("/", response_model=List[ChallengeWithStats])
def list_challenges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_challenges_with_stats(db, current_user.id)


@router.post("/", response_model=ChallengeWithStats)
def create_new_challenge(
    challenge_create: ChallengeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    challenge = create_challenge(db, challenge_create, current_user.id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Habit not found",
        )
    return calculate_challenge_progress(db, challenge)


@router.get("/{challenge_id}", response_model=ChallengeWithStats)
def get_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    challenge = get_challenge_by_id(db, challenge_id, current_user.id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    return calculate_challenge_progress(db, challenge)


@router.put("/{challenge_id}", response_model=ChallengeWithStats)
def update_existing_challenge(
    challenge_id: int,
    challenge_update: ChallengeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    challenge = update_challenge(db, challenge_id, challenge_update, current_user.id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    return calculate_challenge_progress(db, challenge)


@router.delete("/{challenge_id}")
def delete_existing_challenge(
    challenge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = delete_challenge(db, challenge_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    return {"message": "Challenge deleted successfully"}
