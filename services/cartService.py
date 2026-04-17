from typing import Dict
from models.cartModel import CartModel, CartItemModel
from repositories.cartRepository import CartRepository
from repositories.serviceRepository import ServiceRepository
from repositories.workerRepository import WorkerRepository
from repositories.personRepository import PersonRepository
from repositories.appointmentRepository import AppointmentRepository
from services.workerService import _time_to_minutes, _minutes_to_time, WorkerService

class CartService:

    @staticmethod
    def get_cart(user_id: str) -> Dict:
        try:
            cart = CartRepository.find_by_user_id(user_id)
            if not cart:
                cart = CartModel(user_id=user_id)
            return {
                "success": True,
                "items":   [i.to_dict() for i in cart.items],
                "total":   cart.total,
                "count":   len(cart.items)
            }
        except Exception as e:
            return {"success": False, "items": [], "total": 0, "count": 0, "message": f"Error: {e}"}

    @staticmethod
    def add_to_cart(user_id: str, service_id: str, worker_id: str,
                    date: str, start_time: str) -> Dict:
        try:
            service = ServiceRepository.find_by_id(service_id)
            if not service or not service.is_active:
                return {"success": False, "message": "Servicio no disponible"}

            worker = WorkerRepository.find_by_id(worker_id)
            if not worker or not worker.is_active:
                return {"success": False, "message": "Trabajadora no disponible"}

            # Calcular end_time
            start_mins = _time_to_minutes(start_time)
            end_mins   = start_mins + service.duration_minutes
            end_time   = _minutes_to_time(end_mins)

            # Verificar disponibilidad en tiempo real
            if AppointmentRepository.has_conflict(worker_id, date, start_time, end_time):
                return {"success": False, "message": "La trabajadora ya tiene una cita en ese horario"}

            worker_person = PersonRepository.find_by_user_id(worker.user_id)
            worker_name   = f"{worker_person.first_name} {worker_person.last_name}" if worker_person else "N/A"

            item = CartItemModel(
                service_id=service_id,
                service_name=service.name,
                worker_id=worker_id,
                worker_name=worker_name,
                date=date,
                start_time=start_time,
                end_time=end_time,
                price=service.price
            )

            cart = CartRepository.find_by_user_id(user_id) or CartModel(user_id=user_id)

            # Evitar duplicados (mismo servicio+trabajadora+fecha+hora)
            for existing in cart.items:
                if (existing.service_id == service_id and
                        existing.worker_id == worker_id and
                        existing.date == date and
                        existing.start_time == start_time):
                    return {"success": False, "message": "Este servicio ya está en el carrito"}

            cart.items.append(item)
            CartRepository.upsert(cart)
            return {"success": True, "message": f"'{service.name}' agregado al carrito", "count": len(cart.items)}
        except Exception as e:
            return {"success": False, "message": f"Error al agregar al carrito: {e}"}

    @staticmethod
    def remove_from_cart(user_id: str, item_index: int) -> Dict:
        try:
            cart = CartRepository.find_by_user_id(user_id)
            if not cart or item_index < 0 or item_index >= len(cart.items):
                return {"success": False, "message": "Ítem no encontrado en el carrito"}
            removed = cart.items.pop(item_index)
            CartRepository.upsert(cart)
            return {"success": True, "message": f"'{removed.service_name}' eliminado del carrito"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar del carrito: {e}"}

    @staticmethod
    def checkout(user_id: str) -> Dict:
        """
        Convierte los ítems del carrito en citas confirmadas.
        Verifica conflictos antes de crear cada cita.
        """
        from models.appointmentModel import AppointmentModel
        from repositories.appointmentRepository import AppointmentRepository as AR

        try:
            cart = CartRepository.find_by_user_id(user_id)
            if not cart or not cart.items:
                return {"success": False, "message": "El carrito está vacío"}

            created = []
            failed  = []

            for item in cart.items:
                # Re-verificar conflicto en el momento del checkout
                if AR.has_conflict(item.worker_id, item.date, item.start_time, item.end_time):
                    failed.append(f"'{item.service_name}' con {item.worker_name} el {item.date} a las {item.start_time} ya no está disponible")
                    continue

                appt = AppointmentModel(
                    client_id=user_id,
                    worker_id=item.worker_id,
                    service_id=item.service_id,
                    date=item.date,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    total_price=item.price
                )
                AR.create(appt)
                created.append(item.service_name)

            if failed and not created:
                return {"success": False, "message": "No se pudo confirmar ninguna cita: " + "; ".join(failed)}

            # Vaciar carrito
            CartRepository.clear(user_id)

            msg = f"{len(created)} cita(s) confirmada(s)."
            if failed:
                msg += f" {len(failed)} no se pudo confirmar: " + "; ".join(failed)

            return {"success": True, "message": msg, "created": created, "failed": failed}
        except Exception as e:
            return {"success": False, "message": f"Error en checkout: {e}"}

    @staticmethod
    def clear_cart(user_id: str) -> Dict:
        try:
            CartRepository.clear(user_id)
            return {"success": True, "message": "Carrito vaciado"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}
