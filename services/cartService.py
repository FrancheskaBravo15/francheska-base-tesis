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
        - Combos: verifica TODOS los conflictos antes de crear cualquiera (todo-o-nada).
        - Individuales: crea cada uno independientemente.
        """
        from models.appointmentModel import AppointmentModel
        from repositories.appointmentRepository import AppointmentRepository as AR

        try:
            cart = CartRepository.find_by_user_id(user_id)
            if not cart or not cart.items:
                return {"success": False, "message": "El carrito está vacío"}

            # Separar combos de individuales
            promo_groups     = {}
            standalone_items = []
            for item in cart.items:
                if item.promotion_id:
                    if item.promotion_id not in promo_groups:
                        promo_groups[item.promotion_id] = {
                            "name":  item.promotion_name,
                            "items": []
                        }
                    promo_groups[item.promotion_id]["items"].append(item)
                else:
                    standalone_items.append(item)

            created = []
            failed  = []

            # ── Combos: todo-o-nada ──────────────────────────────────────────
            for promo_id, group in promo_groups.items():
                conflicts = [
                    f"'{i.service_name}' con {i.worker_name} el {i.date} a las {i.start_time}"
                    for i in group["items"]
                    if AR.has_conflict(i.worker_id, i.date, i.start_time, i.end_time)
                ]
                if conflicts:
                    failed.append(
                        f"Combo '{group['name']}' no confirmado: "
                        + "; ".join(conflicts)
                        + " ya no está disponible"
                    )
                    continue

                for item in group["items"]:
                    AR.create(AppointmentModel(
                        client_id=user_id,
                        worker_id=item.worker_id,
                        service_id=item.service_id,
                        date=item.date,
                        start_time=item.start_time,
                        end_time=item.end_time,
                        total_price=item.price,
                        promotion_id=item.promotion_id,
                        promotion_name=item.promotion_name
                    ))
                created.append(f"Combo '{group['name']}'")

            # ── Individuales ─────────────────────────────────────────────────
            for item in standalone_items:
                if AR.has_conflict(item.worker_id, item.date, item.start_time, item.end_time):
                    failed.append(
                        f"'{item.service_name}' con {item.worker_name} "
                        f"el {item.date} a las {item.start_time} ya no está disponible"
                    )
                    continue
                AR.create(AppointmentModel(
                    client_id=user_id,
                    worker_id=item.worker_id,
                    service_id=item.service_id,
                    date=item.date,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    total_price=item.price
                ))
                created.append(item.service_name)

            if failed and not created:
                return {"success": False, "message": "No se pudo confirmar ninguna cita: " + "; ".join(failed)}

            CartRepository.clear(user_id)

            msg = f"{len(created)} elemento(s) confirmado(s)."
            if failed:
                msg += " No se pudo confirmar: " + "; ".join(failed)

            return {"success": True, "message": msg, "created": created, "failed": failed}
        except Exception as e:
            return {"success": False, "message": f"Error en checkout: {e}"}

    @staticmethod
    def add_promotion_to_cart(user_id: str, promotion_id: str, promo_name: str,
                              promo_price: float, selections: list) -> Dict:
        """
        Agrega todos los servicios de una promoción al carrito como grupo.
        selections: [{"service_id": ..., "worker_id": ..., "date": ..., "start_time": ...}, ...]
        El precio se distribuye proporcionalmente entre los ítems.
        """
        try:
            if not selections:
                return {"success": False, "message": "No hay selecciones"}

            n = len(selections)
            per_item = round(promo_price / n, 2)
            first_item_price = round(promo_price - per_item * (n - 1), 2)

            cart = CartRepository.find_by_user_id(user_id) or CartModel(user_id=user_id)

            for existing in cart.items:
                if existing.promotion_id == promotion_id:
                    return {"success": False, "message": "Esta promoción ya está en el carrito"}

            new_items = []
            for i, sel in enumerate(selections):
                service = ServiceRepository.find_by_id(sel["service_id"])
                if not service or not service.is_active:
                    return {"success": False, "message": "Un servicio de la promoción no está disponible"}

                worker = WorkerRepository.find_by_id(sel["worker_id"])
                if not worker or not worker.is_active:
                    return {"success": False, "message": "Una especialista seleccionada no está disponible"}

                start_mins = _time_to_minutes(sel["start_time"])
                end_time   = _minutes_to_time(start_mins + service.duration_minutes)

                if AppointmentRepository.has_conflict(sel["worker_id"], sel["date"], sel["start_time"], end_time):
                    return {"success": False, "message": f"La especialista no tiene disponibilidad para '{service.name}' en ese horario"}

                worker_person = PersonRepository.find_by_user_id(worker.user_id)
                worker_name   = f"{worker_person.first_name} {worker_person.last_name}" if worker_person else "N/A"

                new_items.append(CartItemModel(
                    service_id     = sel["service_id"],
                    service_name   = service.name,
                    worker_id      = sel["worker_id"],
                    worker_name    = worker_name,
                    date           = sel["date"],
                    start_time     = sel["start_time"],
                    end_time       = end_time,
                    price          = first_item_price if i == 0 else per_item,
                    promotion_id   = promotion_id,
                    promotion_name = promo_name
                ))

            cart.items.extend(new_items)
            CartRepository.upsert(cart)
            return {"success": True, "message": f"Promoción '{promo_name}' agregada al carrito", "count": len(cart.items)}
        except Exception as e:
            return {"success": False, "message": f"Error al agregar promoción: {e}"}

    @staticmethod
    def remove_promotion_from_cart(user_id: str, promotion_id: str) -> Dict:
        try:
            cart = CartRepository.find_by_user_id(user_id)
            if not cart:
                return {"success": False, "message": "Carrito no encontrado"}
            original = len(cart.items)
            cart.items = [i for i in cart.items if i.promotion_id != promotion_id]
            if len(cart.items) == original:
                return {"success": False, "message": "Promoción no encontrada en el carrito"}
            CartRepository.upsert(cart)
            return {"success": True, "message": "Promoción eliminada del carrito"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def clear_cart(user_id: str) -> Dict:
        try:
            CartRepository.clear(user_id)
            return {"success": True, "message": "Carrito vaciado"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}
