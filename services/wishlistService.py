from typing import Dict
from models.wishlistModel import WishlistModel
from repositories.wishlistRepository import WishlistRepository
from repositories.serviceRepository import ServiceRepository

class WishlistService:

    @staticmethod
    def get_wishlist(user_id: str) -> Dict:
        try:
            wl = WishlistRepository.find_by_user_id(user_id)
            service_ids = wl.service_ids if wl else []
            services = []
            if service_ids:
                found = ServiceRepository.find_by_ids(service_ids)
                services = [s.__dict__ for s in found]
            return {"success": True, "services": services, "service_ids": service_ids}
        except Exception as e:
            return {"success": False, "services": [], "service_ids": [], "message": f"Error: {e}"}

    @staticmethod
    def toggle(user_id: str, service_id: str) -> Dict:
        """Agrega o quita un servicio de la lista de deseos."""
        try:
            service = ServiceRepository.find_by_id(service_id)
            if not service:
                return {"success": False, "message": "Servicio no encontrado", "in_wishlist": False}

            wl = WishlistRepository.find_by_user_id(user_id) or WishlistModel(user_id=user_id)

            if service_id in wl.service_ids:
                wl.service_ids.remove(service_id)
                added = False
                msg = f"'{service.name}' eliminado de la lista de deseos"
            else:
                wl.service_ids.append(service_id)
                added = True
                msg = f"'{service.name}' agregado a la lista de deseos"

            WishlistRepository.upsert(wl)
            return {"success": True, "message": msg, "in_wishlist": added}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}", "in_wishlist": False}

    @staticmethod
    def is_in_wishlist(user_id: str, service_id: str) -> bool:
        try:
            wl = WishlistRepository.find_by_user_id(user_id)
            return wl is not None and service_id in wl.service_ids
        except Exception:
            return False
