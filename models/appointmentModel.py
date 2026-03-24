from datetime import datetime

# Estados posibles de una cita
APPOINTMENT_STATUS = ["pendiente", "confirmada", "cancelada", "completada"]

class AppointmentModel:
    """
    Modelo de dominio para las citas/turnos.
    date: string ISO 'YYYY-MM-DD'
    start_time / end_time: strings 'HH:MM'
    """

    def __init__(self, client_id, worker_id, service_id, date, start_time, end_time,
                 total_price, status="confirmada", notes="", id=None):
        self.id = id
        self.client_id  = client_id
        self.worker_id  = worker_id
        self.service_id = service_id
        self.date       = date           # 'YYYY-MM-DD'
        self.start_time = start_time     # 'HH:MM'
        self.end_time   = end_time       # 'HH:MM'
        self.total_price = float(total_price)
        self.status     = status
        self.notes      = notes
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'AppointmentModel':
        appt = cls(
            client_id   = data["client_id"],
            worker_id   = data["worker_id"],
            service_id  = data["service_id"],
            date        = data["date"],
            start_time  = data["start_time"],
            end_time    = data["end_time"],
            total_price = data["total_price"],
            status      = data.get("status", "confirmada"),
            notes       = data.get("notes", "")
        )
        if "_id" in data:
            appt.id = str(data["_id"])
        return appt

    def to_dict(self) -> dict:
        return {
            "client_id":   self.client_id,
            "worker_id":   self.worker_id,
            "service_id":  self.service_id,
            "date":        self.date,
            "start_time":  self.start_time,
            "end_time":    self.end_time,
            "total_price": self.total_price,
            "status":      self.status,
            "notes":       self.notes,
            "created_at":  self.created_at
        }

    def __repr__(self):
        return f"AppointmentModel(client={self.client_id}, worker={self.worker_id}, date={self.date}, time={self.start_time})"
