from sqlalchemy.orm import Session
from models.rating import Rating
from sqlalchemy import func


def create_rating(db: Session, delivery_id: int, from_user_id: int, to_user_id: int, score: float, review: str = None) -> Rating:
    r = Rating(delivery_id=delivery_id, from_user_id=from_user_id, to_user_id=to_user_id, score=score, review=review)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_driver_rating_stats(db: Session, driver_id: int) -> dict:
    stats = db.query(func.avg(Rating.score), func.count(Rating.id)).filter(Rating.to_user_id == driver_id).first()
    return {"average_score": round(stats[0] or 0, 2), "total_ratings": stats[1] or 0}
