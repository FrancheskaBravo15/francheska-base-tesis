from datetime import datetime

APPOINTMENT_STATUS = [
    "pendiente_validacion",  # voucher subido, esperando admin
    "confirmada",            # pago validado o payphone aprobado
    "en_curso",              # cita iniciada
    "completada",
    "cancelada",
    "pendiente_reagenda"
]

class AppointmentModel:
    """
    Modelo de dominio para las citas/turnos.
    date: string ISO 'YYYY-MM-DD'
    start_time / end_time: strings 'HH:MM'
    """

    def __init__(self, client_id, worker_id, service_id, date, start_time, end_time,
                 total_price, status="confirmada", notes="", id=None,
                 proposed_date=None, proposed_start_time=None,
                 proposed_end_time=None, reschedule_reason=None,
                 promotion_id=None, promotion_name=None,
                 combo_instance_id=None, created_at=None,
                 # Pago
                 payment_method=None, voucher_path=None,
                 payphone_client_tx_id=None, payphone_transaction_id=None,
                 payphone_auth_code=None,
                 # Cancelación
                 cancel_reason=None,
                 # Reseña
                 rating=None, review_comment=None, review_date=None):
        self.id = id
        self.client_id   = client_id
        self.worker_id   = worker_id
        self.service_id  = service_id
        self.date        = date
        self.start_time  = start_time
        self.end_time    = end_time
        self.total_price = float(total_price)
        self.status      = status
        self.notes       = notes
        self.proposed_date        = proposed_date
        self.proposed_start_time  = proposed_start_time
        self.proposed_end_time    = proposed_end_time
        self.reschedule_reason    = reschedule_reason
        self.promotion_id         = promotion_id
        self.promotion_name       = promotion_name
        self.combo_instance_id    = combo_instance_id
        self.created_at           = created_at if created_at is not None else datetime.now()
        # Pago
        self.payment_method         = payment_method
        self.voucher_path           = voucher_path
        self.payphone_client_tx_id  = payphone_client_tx_id
        self.payphone_transaction_id = payphone_transaction_id
        self.payphone_auth_code     = payphone_auth_code
        # Cancelación
        self.cancel_reason          = cancel_reason
        # Reseña
        self.rating                 = rating
        self.review_comment         = review_comment
        self.review_date            = review_date

    @classmethod
    def from_dict(cls, data: dict) -> 'AppointmentModel':
        appt = cls(
            client_id           = data["client_id"],
            worker_id           = data["worker_id"],
            service_id          = data["service_id"],
            date                = data["date"],
            start_time          = data["start_time"],
            end_time            = data["end_time"],
            total_price         = data["total_price"],
            status              = data.get("status", "confirmada"),
            notes               = data.get("notes", ""),
            proposed_date       = data.get("proposed_date"),
            proposed_start_time = data.get("proposed_start_time"),
            proposed_end_time   = data.get("proposed_end_time"),
            reschedule_reason   = data.get("reschedule_reason"),
            promotion_id        = data.get("promotion_id"),
            promotion_name      = data.get("promotion_name"),
            combo_instance_id   = data.get("combo_instance_id"),
            created_at          = data.get("created_at"),
            payment_method          = data.get("payment_method"),
            voucher_path            = data.get("voucher_path"),
            payphone_client_tx_id   = data.get("payphone_client_tx_id"),
            payphone_transaction_id = data.get("payphone_transaction_id"),
            payphone_auth_code      = data.get("payphone_auth_code"),
            cancel_reason           = data.get("cancel_reason"),
            rating                  = data.get("rating"),
            review_comment          = data.get("review_comment"),
            review_date             = data.get("review_date"),
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
            "created_at":         self.created_at,
            "payment_method":           self.payment_method,
            "voucher_path":             self.voucher_path,
            "payphone_client_tx_id":    self.payphone_client_tx_id,
            "payphone_transaction_id":  self.payphone_transaction_id,
            "payphone_auth_code":       self.payphone_auth_code,
            "cancel_reason":            self.cancel_reason,
            "rating":                   self.rating,
            "review_comment":           self.review_comment,
            "review_date":              self.review_date,
        }

    def __repr__(self):
        return (f"AppointmentModel(client={self.client_id}, worker={self.worker_id}, "
                f"date={self.date}, time={self.start_time}, status={self.status})")
