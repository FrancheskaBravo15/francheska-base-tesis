from datetime import datetime

class CartItemModel:
    """
    Ítem dentro del carrito de compras.
    Representa un servicio reservado para una fecha/hora específica con una trabajadora.
    """
    def __init__(self, service_id, service_name, worker_id, worker_name,
                 date, start_time, end_time, price):
        self.service_id   = service_id
        self.service_name = service_name
        self.worker_id    = worker_id
        self.worker_name  = worker_name
        self.date         = date        # 'YYYY-MM-DD'
        self.start_time   = start_time  # 'HH:MM'
        self.end_time     = end_time    # 'HH:MM'
        self.price        = float(price)

    @classmethod
    def from_dict(cls, data: dict) -> 'CartItemModel':
        return cls(
            service_id   = data["service_id"],
            service_name = data["service_name"],
            worker_id    = data["worker_id"],
            worker_name  = data["worker_name"],
            date         = data["date"],
            start_time   = data["start_time"],
            end_time     = data["end_time"],
            price        = data["price"]
        )

    def to_dict(self) -> dict:
        return {
            "service_id":   self.service_id,
            "service_name": self.service_name,
            "worker_id":    self.worker_id,
            "worker_name":  self.worker_name,
            "date":         self.date,
            "start_time":   self.start_time,
            "end_time":     self.end_time,
            "price":        self.price
        }


class CartModel:
    """Carrito de compras por usuario. Un carrito por cliente."""

    def __init__(self, user_id, items=None, id=None):
        self.id      = id
        self.user_id = user_id
        self.items   = items or []   # list[CartItemModel]
        self.updated_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'CartModel':
        cart = cls(
            user_id = data["user_id"],
            items   = [CartItemModel.from_dict(i) for i in data.get("items", [])]
        )
        if "_id" in data:
            cart.id = str(data["_id"])
        return cart

    def to_dict(self) -> dict:
        return {
            "user_id":    self.user_id,
            "items":      [i.to_dict() for i in self.items],
            "updated_at": self.updated_at
        }

    @property
    def total(self) -> float:
        return sum(i.price for i in self.items)

    def __repr__(self):
        return f"CartModel(user_id={self.user_id}, items={len(self.items)}, total={self.total})"
