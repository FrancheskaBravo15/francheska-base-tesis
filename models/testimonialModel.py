from datetime import datetime


class TestimonialModel:
    def __init__(self, author_name, rating, comment, is_approved=False, id=None):
        self.id = id
        self.author_name = author_name
        self.rating = int(rating)           # 1 a 5
        self.comment = comment
        self.is_approved = is_approved
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'TestimonialModel':
        t = cls(
            author_name=data["author_name"],
            rating=data["rating"],
            comment=data.get("comment", ""),
            is_approved=data.get("is_approved", False)
        )
        if "_id" in data:
            t.id = str(data["_id"])
        if "created_at" in data:
            t.created_at = data["created_at"]
        return t

    def to_dict(self) -> dict:
        return {
            "author_name": self.author_name,
            "rating": self.rating,
            "comment": self.comment,
            "is_approved": self.is_approved,
            "created_at": self.created_at
        }
