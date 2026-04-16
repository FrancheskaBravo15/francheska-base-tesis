from datetime import datetime
import unicodedata
import re


def generate_slug(name: str) -> str:
    """Genera un slug URL-amigable desde un nombre de servicio."""
    # Normalizar unicode: quitar tildes y diacríticos
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = name.lower()
    # Reemplazar caracteres no alfanuméricos con guiones
    name = re.sub(r'[^a-z0-9]+', '-', name)
    name = name.strip('-')
    return name


class ServiceModel:
    # Modelo de dominio para los servicios de belleza y moda

    def __init__(self, name, description, category, price, duration_minutes,
                 image_url=None, is_active=True, id=None, slug=None):
        self.id = id
        self.name = name
        self.slug = slug if slug else generate_slug(name)
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
            is_active        = data.get("is_active", True),
            slug             = data.get("slug") or generate_slug(data["name"])
        )
        if "_id" in data:
            service.id = str(data["_id"])
        return service

    def to_dict(self) -> dict:
        return {
            "name":             self.name,
            "slug":             self.slug,
            "description":      self.description,
            "category":         self.category,
            "price":            self.price,
            "duration_minutes": self.duration_minutes,
            "image_url":        self.image_url,
            "is_active":        self.is_active,
            "created_at":       self.created_at
        }

    def __repr__(self):
        return f"ServiceModel(name={self.name}, slug={self.slug}, category={self.category}, price={self.price})"
