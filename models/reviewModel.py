from datetime import datetime

class ReviewModel:
    """Reseña y puntuación de un servicio por un cliente."""

    def __init__(self, service_id, user_id, rating, comment="", id=None):
        self.id         = id
        self.service_id = service_id
        self.user_id    = user_id
        self.rating     = int(rating)     # 1 a 5
        self.comment    = comment
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'ReviewModel':
        review = cls(
            service_id = data["service_id"],
            user_id    = data["user_id"],
            rating     = data["rating"],
            comment    = data.get("comment", "")
        )
        if "_id" in data:
            review.id = str(data["_id"])
        return review

    def to_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "user_id":    self.user_id,
            "rating":     self.rating,
            "comment":    self.comment,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"ReviewModel(service={self.service_id}, user={self.user_id}, rating={self.rating})"
