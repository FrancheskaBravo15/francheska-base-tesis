from datetime import datetime


class PromotionModel:
    def __init__(self, name, description, service_ids, promo_price,
                 image_url=None, is_active=True, id=None,
                 start_datetime=None, end_datetime=None, created_at=None):
        self.id           = id
        self.name         = name
        self.description  = description
        self.service_ids  = service_ids      # lista de str IDs
        self.promo_price  = float(promo_price)
        self.image_url    = image_url
        self.is_active    = is_active
        self.start_datetime = start_datetime  # datetime | None
        self.end_datetime   = end_datetime    # datetime | None
        self.created_at   = created_at if created_at is not None else datetime.now()

    # ── Estado de vigencia ────────────────────────────────────────────────────

    @property
    def vigencia_status(self) -> str:
        """'vigente' | 'por_iniciar' | 'expirada' | 'sin_fecha'"""
        now = datetime.now()
        if self.start_datetime is None and self.end_datetime is None:
            return "sin_fecha"
        if self.start_datetime and now < self.start_datetime:
            return "por_iniciar"
        if self.end_datetime and now > self.end_datetime:
            return "expirada"
        return "vigente"

    @property
    def is_currently_valid(self) -> bool:
        return self.vigencia_status in ("vigente", "sin_fecha")

    # ── Serialización ─────────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> 'PromotionModel':
        promo = cls(
            name           = data["name"],
            description    = data.get("description", ""),
            service_ids    = data.get("service_ids", []),
            promo_price    = data.get("promo_price", 0),
            image_url      = data.get("image_url"),
            is_active      = data.get("is_active", True),
            start_datetime = data.get("start_datetime"),
            end_datetime   = data.get("end_datetime"),
            created_at     = data.get("created_at"),
        )
        if "_id" in data:
            promo.id = str(data["_id"])
        return promo

    def to_dict(self) -> dict:
        return {
            "name":           self.name,
            "description":    self.description,
            "service_ids":    self.service_ids,
            "promo_price":    self.promo_price,
            "image_url":      self.image_url,
            "is_active":      self.is_active,
            "start_datetime": self.start_datetime,
            "end_datetime":   self.end_datetime,
            "created_at":     self.created_at,
        }
