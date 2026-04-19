from typing import Dict, List
from models.appointmentModel import AppointmentModel
from repositories.appointmentRepository import AppointmentRepository
from repositories.serviceRepository import ServiceRepository
from repositories.workerRepository import WorkerRepository
from repositories.personRepository import PersonRepository
from services.workerService import WorkerService

class AppointmentService:

    @staticmethod
    def create_appointment(client_id: str, worker_id: str, service_id: str,
                           date: str, start_time: str) -> Dict:
        try:
            service = ServiceRepository.find_by_id(service_id)
            if not service:
                return {"success": False, "message": "Servicio no encontrado"}
            worker = WorkerRepository.find_by_id(worker_id)
            if not worker or not worker.is_active:
                return {"success": False, "message": "Trabajadora no disponible"}

            from services.workerService import _time_to_minutes, _minutes_to_time
            start_mins = _time_to_minutes(start_time)
            end_mins   = start_mins + service.duration_minutes
            end_time   = _minutes_to_time(end_mins)

            if AppointmentRepository.has_conflict(worker_id, date, start_time, end_time):
                return {"success": False, "message": "La trabajadora ya tiene una cita en ese horario"}

            appointment = AppointmentModel(
                client_id=client_id,
                worker_id=worker_id,
                service_id=service_id,
                date=date,
                start_time=start_time,
                end_time=end_time,
                total_price=service.price
            )
            appt_id = AppointmentRepository.create(appointment)
            return {"success": True, "message": "Cita creada exitosamente", "appointment_id": appt_id}
        except Exception as e:
            return {"success": False, "message": f"Error al crear cita: {e}"}

    @staticmethod
    def cancel_appointment(appointment_id: str, client_id: str, reason: str = "") -> Dict:
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.client_id != client_id:
                return {"success": False, "message": "No tienes permiso para cancelar esta cita"}
            if appt.status == "cancelada":
                return {"success": False, "message": "La cita ya está cancelada"}
            AppointmentRepository.update_data(appointment_id, {
                "status": "cancelada",
                "cancel_reason": reason.strip() if reason else ""
            })
            return {"success": True, "message": "Cita cancelada. No se realizan devoluciones."}
        except Exception as e:
            return {"success": False, "message": f"Error al cancelar cita: {e}"}

    @staticmethod
    def complete_appointment(appointment_id: str) -> Dict:
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.status not in ("confirmada", "en_curso"):
                return {"success": False, "message": "Solo se pueden completar citas confirmadas o en curso"}
            AppointmentRepository.update_status(appointment_id, "completada")
            return {"success": True, "message": "Cita marcada como completada"}
        except Exception as e:
            return {"success": False, "message": f"Error al completar cita: {e}"}

    @staticmethod
    def start_appointment(appointment_id: str) -> Dict:
        """Marca la cita como en curso (trabajadora/admin)."""
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.status != "confirmada":
                return {"success": False, "message": "Solo se puede iniciar una cita confirmada"}
            AppointmentRepository.update_status(appointment_id, "en_curso")
            return {"success": True, "message": "Cita marcada como en curso"}
        except Exception as e:
            return {"success": False, "message": f"Error al iniciar cita: {e}"}

    # ─── Validación de pago ──────────────────────────────────────────────────────

    @staticmethod
    def validate_payment(appointment_id: str) -> Dict:
        """Admin valida el comprobante → confirmada (individual o todo el combo)."""
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.status != "pendiente_validacion":
                return {"success": False, "message": "La cita no está pendiente de validación"}
            if appt.combo_instance_id:
                AppointmentRepository.update_status_by_combo_instance(appt.combo_instance_id, "confirmada")
            else:
                AppointmentRepository.update_status(appointment_id, "confirmada")
            return {"success": True, "message": "Pago validado. Cita(s) confirmada(s)."}
        except Exception as e:
            return {"success": False, "message": f"Error al validar pago: {e}"}

    @staticmethod
    def reject_payment(appointment_id: str) -> Dict:
        """Admin rechaza el comprobante → cancelada (individual o todo el combo)."""
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.status != "pendiente_validacion":
                return {"success": False, "message": "La cita no está pendiente de validación"}
            if appt.combo_instance_id:
                AppointmentRepository.update_status_by_combo_instance(appt.combo_instance_id, "cancelada")
            else:
                AppointmentRepository.update_status(appointment_id, "cancelada")
            return {"success": True, "message": "Comprobante rechazado. Cita(s) cancelada(s)."}
        except Exception as e:
            return {"success": False, "message": f"Error al rechazar pago: {e}"}

    # ─── Reagendamiento ──────────────────────────────────────────────────────────

    @staticmethod
    def propose_reschedule(appointment_id: str, worker_user_id: str,
                           proposed_date: str, proposed_start_time: str,
                           reason: str) -> Dict:
        try:
            from services.workerService import _time_to_minutes, _minutes_to_time

            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}

            worker = WorkerRepository.find_by_user_id(worker_user_id)
            if not worker or worker.id != appt.worker_id:
                return {"success": False, "message": "No tienes permiso para reagendar esta cita"}

            if appt.status != "confirmada":
                return {"success": False, "message": "Solo se pueden reagendar citas confirmadas"}

            if not proposed_date or not proposed_start_time:
                return {"success": False, "message": "Debe indicar la nueva fecha y hora"}

            service = ServiceRepository.find_by_id(appt.service_id)
            if not service:
                return {"success": False, "message": "Servicio no encontrado"}

            start_mins        = _time_to_minutes(proposed_start_time)
            proposed_end_time = _minutes_to_time(start_mins + service.duration_minutes)

            if AppointmentRepository.has_conflict(appt.worker_id, proposed_date,
                                                  proposed_start_time, proposed_end_time,
                                                  exclude_id=appointment_id):
                return {"success": False,
                        "message": "Ya tienes otra cita en ese horario. Elige un horario diferente."}

            AppointmentRepository.update_data(appointment_id, {
                "status":              "pendiente_reagenda",
                "proposed_date":       proposed_date,
                "proposed_start_time": proposed_start_time,
                "proposed_end_time":   proposed_end_time,
                "reschedule_reason":   reason.strip() if reason else ""
            })
            return {"success": True,
                    "message": "Propuesta de reagendamiento enviada. El cliente debe confirmarla."}
        except Exception as e:
            return {"success": False, "message": f"Error al proponer reagendamiento: {e}"}

    @staticmethod
    def accept_reschedule(appointment_id: str, client_id: str) -> Dict:
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.client_id != client_id:
                return {"success": False, "message": "No tienes permiso para responder esta cita"}
            if appt.status != "pendiente_reagenda":
                return {"success": False, "message": "No hay reagendamiento pendiente para esta cita"}
            if not appt.proposed_date or not appt.proposed_start_time:
                return {"success": False, "message": "Datos de reagendamiento incompletos"}

            if AppointmentRepository.has_conflict(appt.worker_id, appt.proposed_date,
                                                  appt.proposed_start_time, appt.proposed_end_time,
                                                  exclude_id=appointment_id):
                return {"success": False,
                        "message": "El horario propuesto ya no está disponible. "
                                   "Solicita un nuevo reagendamiento a la especialista."}

            AppointmentRepository.update_data(appointment_id, {
                "date":               appt.proposed_date,
                "start_time":         appt.proposed_start_time,
                "end_time":           appt.proposed_end_time,
                "status":             "confirmada",
                "proposed_date":      None,
                "proposed_start_time":None,
                "proposed_end_time":  None,
                "reschedule_reason":  None
            })
            return {"success": True,
                    "message": "Reagendamiento aceptado. Tu cita ha sido actualizada al nuevo horario."}
        except Exception as e:
            return {"success": False, "message": f"Error al aceptar reagendamiento: {e}"}

    @staticmethod
    def reject_reschedule(appointment_id: str, client_id: str) -> Dict:
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.client_id != client_id:
                return {"success": False, "message": "No tienes permiso para responder esta cita"}
            if appt.status != "pendiente_reagenda":
                return {"success": False, "message": "No hay reagendamiento pendiente para esta cita"}

            AppointmentRepository.update_data(appointment_id, {
                "status":             "confirmada",
                "proposed_date":      None,
                "proposed_start_time":None,
                "proposed_end_time":  None,
                "reschedule_reason":  None
            })
            return {"success": True,
                    "message": "Reagendamiento rechazado. Tu cita se mantiene en el horario original."}
        except Exception as e:
            return {"success": False, "message": f"Error al rechazar reagendamiento: {e}"}

    @staticmethod
    def cancel_group(combo_instance_id: str, client_id: str, reason: str = "") -> Dict:
        try:
            count = AppointmentRepository.cancel_by_combo_instance(combo_instance_id, client_id,
                                                                    reason=reason)
            if count == 0:
                return {"success": False, "message": "No hay citas activas para cancelar en este combo"}
            return {"success": True,
                    "message": f"Combo cancelado ({count} cita(s)). No se realizan devoluciones."}
        except Exception as e:
            return {"success": False, "message": f"Error al cancelar combo: {e}"}

    @staticmethod
    def submit_review(appointment_id: str, client_id: str,
                      rating: int, comment: str) -> Dict:
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if appt.client_id != client_id:
                return {"success": False, "message": "No tienes permiso para calificar esta cita"}
            if appt.status != "completada":
                return {"success": False, "message": "Solo puedes calificar citas completadas"}
            if appt.rating is not None:
                return {"success": False, "message": "Ya has calificado esta cita"}
            if not (1 <= int(rating) <= 5):
                return {"success": False, "message": "La calificación debe ser entre 1 y 5"}
            from datetime import datetime
            AppointmentRepository.update_data(appointment_id, {
                "rating":         int(rating),
                "review_comment": comment.strip() if comment else "",
                "review_date":    datetime.now(),
            })
            return {"success": True, "message": "¡Gracias por tu calificación!"}
        except Exception as e:
            return {"success": False, "message": f"Error al enviar calificación: {e}"}

    @staticmethod
    def count_pending_reschedules(client_id: str) -> int:
        try:
            return len(AppointmentRepository.find_pending_reschedule_by_client(client_id))
        except Exception:
            return 0

    # ─── Detalle ─────────────────────────────────────────────────────────────────

    @staticmethod
    def get_appointment_detail(appointment_id: str, user_id: str = None,
                               is_admin: bool = False) -> Dict:
        """Detalle completo de una cita, con hermanos del combo si aplica."""
        try:
            appt = AppointmentRepository.find_by_id(appointment_id)
            if not appt:
                return {"success": False, "message": "Cita no encontrada"}
            if not is_admin and user_id and appt.client_id != user_id:
                return {"success": False, "message": "No tienes permiso para ver esta cita"}

            service       = ServiceRepository.find_by_id(appt.service_id)
            worker        = WorkerRepository.find_by_id(appt.worker_id)
            worker_person = PersonRepository.find_by_user_id(worker.user_id) if worker else None
            client_person = PersonRepository.find_by_user_id(appt.client_id)

            appt_dict = {
                "appointment_id":        appt.id,
                "date":                  appt.date,
                "start_time":            appt.start_time,
                "end_time":              appt.end_time,
                "service_name":          service.name if service else "N/A",
                "service_category":      service.category if service else "N/A",
                "worker_name":           (f"{worker_person.first_name} {worker_person.last_name}"
                                          if worker_person else "N/A"),
                "client_name":           (f"{client_person.first_name} {client_person.last_name}"
                                          if client_person else "N/A"),
                "total_price":           appt.total_price,
                "status":                appt.status,
                "notes":                 appt.notes,
                "payment_method":        appt.payment_method,
                "voucher_path":          appt.voucher_path,
                "payphone_transaction_id": appt.payphone_transaction_id,
                "payphone_auth_code":    appt.payphone_auth_code,
                "promotion_id":          appt.promotion_id,
                "promotion_name":        appt.promotion_name,
                "combo_instance_id":     appt.combo_instance_id,
                "created_at":            appt.created_at,
                "proposed_date":         appt.proposed_date,
                "proposed_start_time":   appt.proposed_start_time,
                "proposed_end_time":     appt.proposed_end_time,
                "reschedule_reason":     appt.reschedule_reason,
                "cancel_reason":         appt.cancel_reason,
                "rating":                appt.rating,
                "review_comment":        appt.review_comment,
                "review_date":           appt.review_date,
            }

            # Hermanos del combo (excluye la cita principal)
            siblings = []
            if appt.combo_instance_id:
                for sibling in AppointmentRepository.find_by_combo_instance(appt.combo_instance_id):
                    if sibling.id == appt.id:
                        continue
                    svc = ServiceRepository.find_by_id(sibling.service_id)
                    wkr = WorkerRepository.find_by_id(sibling.worker_id)
                    wkr_p = PersonRepository.find_by_user_id(wkr.user_id) if wkr else None
                    siblings.append({
                        "appointment_id": sibling.id,
                        "service_name":   svc.name if svc else "N/A",
                        "worker_name":    (f"{wkr_p.first_name} {wkr_p.last_name}" if wkr_p else "N/A"),
                        "date":           sibling.date,
                        "start_time":     sibling.start_time,
                        "end_time":       sibling.end_time,
                        "total_price":    sibling.total_price,
                        "status":         sibling.status,
                    })

            return {"success": True, "appointment": appt_dict, "siblings": siblings}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener detalle: {e}"}

    # ─── Consultas ───────────────────────────────────────────────────────────────

    @staticmethod
    def get_client_appointments(client_id: str) -> Dict:
        try:
            appointments = AppointmentRepository.find_by_client(client_id)
            result = []
            for a in appointments:
                service       = ServiceRepository.find_by_id(a.service_id)
                worker        = WorkerRepository.find_by_id(a.worker_id)
                worker_person = PersonRepository.find_by_user_id(worker.user_id) if worker else None
                result.append({
                    "appointment_id":    a.id,
                    "date":              a.date,
                    "start_time":        a.start_time,
                    "end_time":          a.end_time,
                    "service_name":      service.name if service else "N/A",
                    "service_category":  service.category if service else "N/A",
                    "worker_name":       (f"{worker_person.first_name} {worker_person.last_name}"
                                         if worker_person else "N/A"),
                    "total_price":       a.total_price,
                    "status":            a.status,
                    "notes":             a.notes,
                    "proposed_date":       a.proposed_date,
                    "proposed_start_time": a.proposed_start_time,
                    "proposed_end_time":   a.proposed_end_time,
                    "reschedule_reason":   a.reschedule_reason,
                    "promotion_id":        a.promotion_id,
                    "promotion_name":      a.promotion_name,
                    "combo_instance_id":   a.combo_instance_id,
                    "created_at":          a.created_at,
                    "payment_method":      a.payment_method,
                    "voucher_path":        a.voucher_path,
                    "cancel_reason":       a.cancel_reason,
                    "rating":              a.rating,
                    "review_comment":      a.review_comment,
                    "review_date":         a.review_date,
                })
            return {"success": True, "appointments": result}
        except Exception as e:
            return {"success": False, "appointments": [], "message": f"Error: {e}"}

    @staticmethod
    def get_all_appointments() -> Dict:
        try:
            appointments = AppointmentRepository.find_all()
            result = []
            for a in appointments:
                service       = ServiceRepository.find_by_id(a.service_id)
                worker        = WorkerRepository.find_by_id(a.worker_id)
                worker_person = PersonRepository.find_by_user_id(worker.user_id) if worker else None
                client_person = PersonRepository.find_by_user_id(a.client_id)
                result.append({
                    "appointment_id":    a.id,
                    "client_id":         a.client_id,
                    "date":              a.date,
                    "start_time":        a.start_time,
                    "end_time":          a.end_time,
                    "service_name":      service.name if service else "N/A",
                    "client_name":       (f"{client_person.first_name} {client_person.last_name}"
                                         if client_person else "N/A"),
                    "worker_name":       (f"{worker_person.first_name} {worker_person.last_name}"
                                         if worker_person else "N/A"),
                    "total_price":       a.total_price,
                    "status":            a.status,
                    "promotion_id":      a.promotion_id,
                    "promotion_name":    a.promotion_name,
                    "combo_instance_id": a.combo_instance_id,
                    "created_at":        a.created_at,
                    "payment_method":    a.payment_method,
                    "voucher_path":      a.voucher_path,
                })
            return {"success": True, "appointments": result}
        except Exception as e:
            return {"success": False, "appointments": [], "message": f"Error: {e}"}
