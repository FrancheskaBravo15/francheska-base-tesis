from datetime import datetime

class ServiceModel:
    # Modelo de dominio para los servicios de belleza y moda

    def __init__(self, name, description, category, price, duration_minutes,
                 image_url=None, is_active=True, id=None):
        self.id = id
        self.name = name
        self.description = description
        self.category = category          # Ej: Manicura, Pedicura, Cabello, Maquillaje, etc.
        self.price = float(price)
        self.duration_minutes = int(duration_minutes)
        self.image_url = image_url
        self.is_active = is_active
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'ServiceModel':
        service = cls(
            name             = data["name"],
            description      = data["description"],
            category         = data["category"],
            price            = data["price"],
            duration_minutes = data["duration_minutes"],
            image_url        = data.get("image_url"),
            is_active        = data.get("is_active", True)
        )
        if "_id" in data:
            service.id = str(data["_id"])
        return service

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "description":      self.description,
            "category":         self.category,
            "price":            self.price,
            "duration_minutes": self.duration_minutes,
            "image_url":        self.image_url,
            "is_active":        self.is_active,
            "created_at":       self.created_at
        }

    def __repr__(self):
        return f"ServiceModel(name={self.name}, category={self.category}, price={self.price})"
