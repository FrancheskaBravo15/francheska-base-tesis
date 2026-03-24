from datetime import datetime

class WishlistModel:
    """Lista de deseos de servicios por usuario."""

    def __init__(self, user_id, service_ids=None, id=None):
        self.id         = id
        self.user_id    = user_id
        self.service_ids = service_ids or []   # list[str]  (ObjectId as str)
        self.updated_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'WishlistModel':
        wl = cls(
            user_id     = data["user_id"],
            service_ids = data.get("service_ids", [])
        )
        if "_id" in data:
            wl.id = str(data["_id"])
        return wl

    def to_dict(self) -> dict:
        return {
            "user_id":     self.user_id,
            "service_ids": self.service_ids,
            "updated_at":  self.updated_at
        }

    def __repr__(self):
        return f"WishlistModel(user_id={self.user_id}, services={len(self.service_ids)})"
