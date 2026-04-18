from datetime import datetime

# Estados posibles de una cita
APPOINTMENT_STATUS = ["pendiente", "confirmada", "cancelada", "completada", "pendiente_reagenda"]

class AppointmentModel:
    """
    Modelo de dominio para las citas/turnos.
    date: string ISO 'YYYY-MM-DD'
    start_time / end_time: strings 'HH:MM'

    Campos de reagendamiento (solo presentes cuando status == 'pendiente_reagenda'):
      proposed_date, proposed_start_time, proposed_end_time, reschedule_reason
    """

    def __init__(self, client_id, worker_id, service_id, date, start_time, end_time,
                 total_price, status="confirmada", notes="", id=None,
                 proposed_date=None, proposed_start_time=None,
                 proposed_end_time=None, reschedule_reason=None,
                 promotion_id=None, promotion_name=None,
                 combo_instance_id=None):
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
        # Propuesta de reagendamiento (solo cuando status == 'pendiente_reagenda')
        self.proposed_date       = proposed_date
        self.proposed_start_time = proposed_start_time
        self.proposed_end_time   = proposed_end_time
        self.reschedule_reason   = reschedule_reason
        # Referencia a promoción (opcional)
        self.promotion_id       = promotion_id
        self.promotion_name     = promotion_name
        self.combo_instance_id  = combo_instance_id  # UUID único por cada compra del combo
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'AppointmentModel':
        appt = cls(
            client_id          = data["client_id"],
            worker_id          = data["worker_id"],
            service_id         = data["service_id"],
            date               = data["date"],
            start_time         = data["start_time"],
            end_time           = data["end_time"],
            total_price        = data["total_price"],
            status             = data.get("status", "confirmada"),
            notes              = data.get("notes", ""),
            proposed_date      = data.get("proposed_date"),
            proposed_start_time= data.get("proposed_start_time"),
            proposed_end_time  = data.get("proposed_end_time"),
            reschedule_reason  = data.get("reschedule_reason"),
            promotion_id       = data.get("promotion_id"),
            promotion_name     = data.get("promotion_name"),
            combo_instance_id  = data.get("combo_instance_id")
        )
        if "_id" in data:
            appt.id = str(data["_id"])
        return appt

    def to_dict(self) -> dict:
        return {
            "client_id":          self.client_id,
            "worker_id":          self.worker_id,
            "service_id":         self.service_id,
            "date":               self.date,
            "start_time":         self.start_time,
            "end_time":           self.end_time,
            "total_price":        self.total_price,
            "status":             self.status,
            "notes":              self.notes,
            "proposed_date":      self.proposed_date,
            "proposed_start_time":self.proposed_start_time,
            "proposed_end_time":  self.proposed_end_time,
            "reschedule_reason":  self.reschedule_reason,
            "promotion_id":       self.promotion_id,
            "promotion_name":     self.promotion_name,
            "combo_instance_id":  self.combo_instance_id,
            "created_at":         self.created_at
        }

    def __repr__(self):
        return (f"AppointmentModel(client={self.client_id}, worker={self.worker_id}, "
                f"date={self.date}, time={self.start_time}, status={self.status})")
