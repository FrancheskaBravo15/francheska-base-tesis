from typing import Dict, List
from models.workerModel import WorkerModel, DAYS_OF_WEEK
from models.userModel import UserModel
from models.personModel import PersonModel
from repositories.workerRepository import WorkerRepository
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository
from repositories.appointmentRepository import AppointmentRepository
from werkzeug.security import generate_password_hash
from utils.userUtil import validate_cedula, validate_email, validate_phone_number
from datetime import datetime, timedelta

def _time_to_minutes(t: str) -> int:
    """Convierte 'HH:MM' a minutos desde medianoche."""
    h, m = map(int, t.split(":"))
    return h * 60 + m

def _minutes_to_time(mins: int) -> str:
    h = mins // 60
    m = mins % 60
    return f"{h:02d}:{m:02d}"

class WorkerService:

    @staticmethod
    def create_worker(identification: str, first_name: str, last_name: str,
                      phone: str, email: str, password: str,
                      specialties: List[str], bio: str) -> Dict:
        """Crea un usuario con rol worker y su perfil de trabajadora."""
        errors = []
        err = validate_cedula(identification)
        if err: errors.append(err)
        err = validate_email(email)
        if err: errors.append(err)
        err = validate_phone_number(phone)
        if err: errors.append(err)
        if not first_name or len(first_name.strip()) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        if not last_name or len(last_name.strip()) < 2:
            errors.append("El apellido debe tener al menos 2 caracteres")
        if not specialties:
            errors.append("Debe seleccionar al menos una especialidad")
        if errors:
            return {"success": False, "message": ", ".join(errors)}

        user_id = None
        try:
            if UserRepository.exist_by_email(email):
                return {"success": False, "message": "Ya existe un usuario con ese correo"}
            if PersonRepository.exist_by_identification(identification):
                return {"success": False, "message": "Ya existe un usuario con esa cédula"}

            hashed = generate_password_hash(password)
            user = UserModel(email=email, password=hashed, role="worker")
            user_id = UserRepository.create(user)

            person = PersonModel(user_id=user_id, identification=identification,
                                 first_name=first_name.strip(), last_name=last_name.strip(),
                                 phone=phone)
            PersonRepository.create(person)

            worker = WorkerModel(user_id=user_id, specialties=specialties, bio=bio.strip() if bio else "")
            WorkerRepository.create(worker)

            return {"success": True, "message": "Trabajadora creada exitosamente", "user_id": user_id}
        except Exception as e:
            if user_id:
                UserRepository.delete_by_id(user_id)
            return {"success": False, "message": f"Error al crear trabajadora: {e}"}

    @staticmethod
    def update_worker_profile(worker_id: str, specialties: List[str], bio: str) -> Dict:
        try:
            WorkerRepository.update(worker_id, {"specialties": specialties, "bio": bio.strip() if bio else ""})
            return {"success": True, "message": "Perfil de trabajadora actualizado"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar perfil: {e}"}

    @staticmethod
    def update_worker_full(worker_id: str, first_name: str, last_name: str,
                           phone: str, specialties: List[str], bio: str,
                           new_password: str = None) -> Dict:
        """
        Actualiza datos personales y perfil de una trabajadora.
        Uso exclusivo del administrador.
        Si new_password se proporciona (≥ 8 caracteres), actualiza la contraseña.
        """
        errors = []
        err = validate_phone_number(phone)
        if err: errors.append(err)
        if not first_name or len(first_name.strip()) < 2:
            errors.append("El nombre debe tener al menos 2 caracteres")
        if not last_name or len(last_name.strip()) < 2:
            errors.append("El apellido debe tener al menos 2 caracteres")
        if not specialties:
            errors.append("Debe seleccionar al menos una especialidad")
        if new_password and len(new_password) < 8:
            errors.append("La nueva contraseña debe tener al menos 8 caracteres")
        if errors:
            return {"success": False, "message": ", ".join(errors)}

        try:
            worker = WorkerRepository.find_by_id(worker_id)
            if not worker:
                return {"success": False, "message": "Trabajadora no encontrada"}

            # Actualizar datos personales (persons collection)
            PersonRepository.update_by_user_id(worker.user_id, {
                "first_name": first_name.strip(),
                "last_name":  last_name.strip(),
                "phone":      phone.strip()
            })

            # Actualizar perfil de trabajadora (workers collection)
            WorkerRepository.update(worker_id, {
                "specialties": specialties,
                "bio":         bio.strip() if bio else ""
            })

            # Actualizar contraseña si se proporcionó una nueva
            if new_password:
                hashed = generate_password_hash(new_password)
                UserRepository.update(worker.user_id, {"password": hashed})

            return {"success": True, "message": "Trabajadora actualizada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar trabajadora: {e}"}

    @staticmethod
    def update_availability(user_id: str, availability: dict) -> Dict:
        """
        availability: dict  {day: [{"start": "HH:MM", "end": "HH:MM"}, ...], ...}
        """
        try:
            # Validar que start < end en cada franja
            for day, slots in availability.items():
                for slot in slots:
                    if _time_to_minutes(slot["start"]) >= _time_to_minutes(slot["end"]):
                        return {"success": False,
                                "message": f"La hora de inicio debe ser anterior a la hora de fin en {day}"}
            WorkerRepository.update_by_user_id(user_id, {"availability": availability})
            return {"success": True, "message": "Disponibilidad actualizada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar disponibilidad: {e}"}

    @staticmethod
    def get_all_workers() -> Dict:
        """Retorna lista de trabajadoras con su info de persona."""
        try:
            workers = WorkerRepository.find_all()
            result = []
            for w in workers:
                person = PersonRepository.find_by_user_id(w.user_id)
                user   = UserRepository.find_by_id(w.user_id)
                result.append({
                    "worker_id":    w.id,
                    "user_id":      w.user_id,
                    "first_name":   person.first_name if person else "",
                    "last_name":    person.last_name if person else "",
                    "email":        user.email if user else "",
                    "phone":        person.phone if person else "",
                    "specialties":  w.specialties,
                    "bio":          w.bio,
                    "availability": w.availability,
                    "is_active":    w.is_active,
                    "profile_photo": person.profile_photo if person else None
                })
            return {"success": True, "workers": result}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener trabajadoras: {e}", "workers": []}

    @staticmethod
    def get_worker_by_id(worker_id: str) -> Dict:
        try:
            w = WorkerRepository.find_by_id(worker_id)
            if not w:
                return {"success": False, "message": "Trabajadora no encontrada"}
            person = PersonRepository.find_by_user_id(w.user_id)
            user   = UserRepository.find_by_id(w.user_id)
            return {
                "success": True,
                "worker": {
                    "worker_id":    w.id,
                    "user_id":      w.user_id,
                    "first_name":   person.first_name if person else "",
                    "last_name":    person.last_name if person else "",
                    "email":        user.email if user else "",
                    "phone":        person.phone if person else "",
                    "specialties":  w.specialties,
                    "bio":          w.bio,
                    "availability": w.availability,
                    "is_active":    w.is_active,
                    "profile_photo": person.profile_photo if person else None
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Error al obtener trabajadora: {e}"}

    @staticmethod
    def get_worker_by_user_id(user_id: str) -> Dict:
        try:
            w = WorkerRepository.find_by_user_id(user_id)
            if not w:
                return {"success": False, "message": "Trabajadora no encontrada"}
            person = PersonRepository.find_by_user_id(user_id)
            user   = UserRepository.find_by_id(user_id)
            return {
                "success": True,
                "worker": {
                    "worker_id":    w.id,
                    "user_id":      w.user_id,
                    "first_name":   person.first_name if person else "",
                    "last_name":    person.last_name if person else "",
                    "email":        user.email if user else "",
                    "phone":        person.phone if person else "",
                    "specialties":  w.specialties,
                    "bio":          w.bio,
                    "availability": w.availability,
                    "is_active":    w.is_active,
                    "profile_photo": person.profile_photo if person else None
                }
            }
        except Exception as e:
            return {"success": False, "message": f"Error al obtener trabajadora: {e}"}

    @staticmethod
    def get_available_slots(worker_id: str, date_str: str, duration_minutes: int, service_category: str) -> Dict:
        """
        Calcula los slots disponibles para una trabajadora en una fecha dada.
        Retorna lista de {'start': 'HH:MM', 'end': 'HH:MM'} disponibles.
        """
        try:
            worker = WorkerRepository.find_by_id(worker_id)
            if not worker or not worker.is_active:
                return {"success": False, "slots": [], "message": "Trabajadora no disponible"}

            # Verificar que la trabajadora tiene la especialidad
            if service_category not in worker.specialties:
                return {"success": False, "slots": [], "message": "La trabajadora no tiene esa especialidad"}

            # Obtener el día de la semana
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            # 0=Lunes, 1=Martes ... 6=Domingo
            day_index = date_obj.weekday()
            day_name  = DAYS_OF_WEEK[day_index]

            if day_name not in worker.availability or not worker.availability[day_name]:
                return {"success": True, "slots": [], "message": "La trabajadora no labora ese día"}

            # Citas ya reservadas ese día
            booked = AppointmentRepository.find_by_worker_and_date(worker_id, date_str)
            booked_ranges = [(_time_to_minutes(a.start_time), _time_to_minutes(a.end_time)) for a in booked]

            slots = []
            step  = 30  # granularidad en minutos

            for time_range in worker.availability[day_name]:
                range_start = _time_to_minutes(time_range["start"])
                range_end   = _time_to_minutes(time_range["end"])
                t = range_start
                while t + duration_minutes <= range_end:
                    slot_start = t
                    slot_end   = t + duration_minutes
                    # Verificar que no choca con ninguna cita reservada
                    conflict = any(
                        not (slot_end <= bs or slot_start >= be)
                        for bs, be in booked_ranges
                    )
                    if not conflict:
                        slots.append({
                            "start": _minutes_to_time(slot_start),
                            "end":   _minutes_to_time(slot_end)
                        })
                    t += step

            return {"success": True, "slots": slots}
        except Exception as e:
            return {"success": False, "slots": [], "message": f"Error al calcular slots: {e}"}

    @staticmethod
    def get_workers_by_specialty(specialty: str) -> Dict:
        try:
            workers = WorkerRepository.find_by_specialty(specialty)
            result = []
            for w in workers:
                person = PersonRepository.find_by_user_id(w.user_id)
                result.append({
                    "worker_id":   w.id,
                    "user_id":     w.user_id,
                    "first_name":  person.first_name if person else "",
                    "last_name":   person.last_name if person else "",
                    "specialties": w.specialties,
                    "bio":         w.bio,
                    "availability": w.availability,
                    "profile_photo": person.profile_photo if person else None
                })
            return {"success": True, "workers": result}
        except Exception as e:
            return {"success": False, "workers": [], "message": f"Error: {e}"}

    @staticmethod
    def get_worker_history(user_id: str) -> Dict:
        """Historial de citas completadas y monto recaudado para la trabajadora."""
        try:
            worker = WorkerRepository.find_by_user_id(user_id)
            if not worker:
                return {"success": False, "appointments": [], "total_earned": 0}

            appointments = AppointmentRepository.find_by_worker(worker.id)
            history = []
            total_earned = 0.0

            from repositories.serviceRepository import ServiceRepository
            from repositories.personRepository import PersonRepository as PR

            for a in appointments:
                service = ServiceRepository.find_by_id(a.service_id)
                client_person = PR.find_by_user_id(a.client_id)
                entry = {
                    "appointment_id": a.id,
                    "date":           a.date,
                    "start_time":     a.start_time,
                    "end_time":       a.end_time,
                    "service_name":   service.name if service else "N/A",
                    "client_name":    f"{client_person.first_name} {client_person.last_name}" if client_person else "N/A",
                    "total_price":    a.total_price,
                    "status":         a.status
                }
                history.append(entry)
                if a.status == "completada":
                    total_earned += a.total_price

            return {"success": True, "appointments": history, "total_earned": total_earned}
        except Exception as e:
            return {"success": False, "appointments": [], "total_earned": 0, "message": f"Error: {e}"}

    @staticmethod
    def toggle_active(worker_id: str) -> Dict:
        try:
            worker = WorkerRepository.find_by_id(worker_id)
            if not worker:
                return {"success": False, "message": "Trabajadora no encontrada"}
            new_status = not worker.is_active
            WorkerRepository.update(worker_id, {"is_active": new_status})
            # También actualizar el usuario
            UserRepository.update(worker.user_id, {"is_active": new_status})
            msg = "activada" if new_status else "desactivada"
            return {"success": True, "message": f"Trabajadora {msg} exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}
