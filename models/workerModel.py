from datetime import datetime

DAYS_OF_WEEK = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

class WorkerModel:
    """
    Modelo de dominio para los trabajadores (especialistas).
    availability: dict con días como clave y lista de franjas horarias como valor.
    Ejemplo:
      {
        "Lunes":   [{"start": "09:00", "end": "13:00"}, {"start": "14:00", "end": "18:00"}],
        "Martes":  [{"start": "09:00", "end": "18:00"}],
        ...
      }
    specialties: lista de categorías de servicios que puede realizar.
    """

    def __init__(self, user_id, specialties, bio="", availability=None, is_active=True, id=None):
        self.id = id
        self.user_id = user_id
        self.specialties = specialties      # list[str]
        self.bio = bio
        self.availability = availability or {}   # dict day -> list[{start, end}]
        self.is_active = is_active
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkerModel':
        worker = cls(
            user_id      = data["user_id"],
            specialties  = data.get("specialties", []),
            bio          = data.get("bio", ""),
            availability = data.get("availability", {}),
            is_active    = data.get("is_active", True)
        )
        if "_id" in data:
            worker.id = str(data["_id"])
        return worker

    def to_dict(self) -> dict:
        return {
            "user_id":      self.user_id,
            "specialties":  self.specialties,
            "bio":          self.bio,
            "availability": self.availability,
            "is_active":    self.is_active,
            "created_at":   self.created_at
        }

    def __repr__(self):
        return f"WorkerModel(user_id={self.user_id}, specialties={self.specialties})"
