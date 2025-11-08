from fastapi import APIRouter, Depends, HTTPException
import random
 
from app.models import Word
from app.schemas import WordResponse
from sqlalchemy.orm import Session
from app.database import get_db
 
router = APIRouter()
 
@router.get("/word", response_model=WordResponse)
def get_random_word(db: Session = Depends(get_db)):
    words = db.query(Word).all()

    if not words:
        raise HTTPException(
            status_code = 404,
            detail = "No words available in database"
        )
    random_word = random.choice(words)
    return random_word
 