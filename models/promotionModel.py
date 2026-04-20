from datetime import datetime


class PromotionModel:
    def __init__(self, name, description, service_ids, promo_price,
                 image_url=None, is_active=True, id=None):
        self.id = id
        self.name = name
        self.description = description
        self.service_ids = service_ids      # lista de str IDs
        self.promo_price = float(promo_price)
        self.image_url = image_url
        self.is_active = is_active
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'PromotionModel':
        promo = cls(
            name=data["name"],
            description=data.get("description", ""),
            service_ids=data.get("service_ids", []),
            promo_price=data.get("promo_price", 0),
            image_url=data.get("image_url"),
            is_active=data.get("is_active", True)
        )
        if "_id" in data:
            promo.id = str(data["_id"])
        return promo

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "service_ids": self.service_ids,
            "promo_price": self.promo_price,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
