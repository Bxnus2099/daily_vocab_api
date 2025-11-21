from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from app.database import get_db
from app.models import Word, PracticeSession
from app.schemas import ValidateSentenceRequest, ValidateSentenceResponse, HistoryItem, SummaryResponse
from app.utils import mock_ai_validation

router = APIRouter()

@router.post("/validate-sentence", response_model=ValidateSentenceResponse)
def validate_sentence(
    request: ValidateSentenceRequest,
    db: Session = Depends(get_db)
):
    word = db.query(Word).filter(Word.id == request.word_id).first()
    if not word:
        raise HTTPException(status_code=404, detail="word_id not found")

    result = mock_ai_validation(
        request.sentence,
        word.word,
        word.difficulty_level
    )

    session_entry = PracticeSession(
        user_id=1,
        word_id=request.word_id,
        user_sentence=request.sentence, 
        feedback=result["suggestion"],
        corrected_sentence=result["corrected_sentence"],
        practiced_at=datetime.utcnow() 
    )
    db.add(session_entry)
    db.commit()

    return ValidateSentenceResponse(
        score=result["score"],
        level=result["level"],
        suggestion=result["suggestion"],
        corrected_sentence=result["corrected_sentence"]
    )


@router.get("/history", response_model=List[HistoryItem])
def get_history(db: Session = Depends(get_db)):

    sessions = db.query(PracticeSession).join(Word, Word.id == PracticeSession.word_id).all()
    history = []

    for s in sessions:
        history.append(HistoryItem(
            id=s.id,
            word=s.word.word,
            user_sentence=s.user_sentence,
            score=float(s.score),
            feedback=s.feedback,
            practiced_at=s.practiced_at
        ))

    return history


@router.get("/summary", response_model=SummaryResponse)
def get_summary(db: Session = Depends(get_db)):

    total_practices = db.query(func.count(PracticeSession.id)).scalar()
    average_score = db.query(func.avg(PracticeSession.score)).scalar() or 0
    total_words_practiced = db.query(func.count(func.distinct(PracticeSession.word_id))).scalar()

    # Level distribution
    levels = db.query(Word.difficulty_level, func.count(PracticeSession.id))\
               .join(PracticeSession, PracticeSession.word_id == Word.id)\
               .group_by(Word.difficulty_level).all()

    level_distribution = {level: count for level, count in levels}

    return SummaryResponse(
        total_practices=total_practices,
        average_score=float(average_score),
        total_words_practiced=total_words_practiced,
        level_distribution=level_distribution
    )