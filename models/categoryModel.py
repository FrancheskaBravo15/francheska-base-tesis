from datetime import datetime


class CategoryModel:
    def __init__(self, name, description, image_url=None, is_active=True, id=None):
        self.id = id
        self.name = name
        self.description = description
        self.image_url = image_url
        self.is_active = is_active
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'CategoryModel':
        cat = cls(
            name=data["name"],
            description=data.get("description", ""),
            image_url=data.get("image_url"),
            is_active=data.get("is_active", True)
        )
        if "_id" in data:
            cat.id = str(data["_id"])
        return cat

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
