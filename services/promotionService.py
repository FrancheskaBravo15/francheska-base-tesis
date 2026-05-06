from typing import Dict, List, Optional
from datetime import datetime
from models.promotionModel import PromotionModel
from repositories.promotionRepository import PromotionRepository
from repositories.serviceRepository import ServiceRepository
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_datetime(value: str) -> Optional[datetime]:
    """Convierte 'YYYY-MM-DDTHH:MM' (input datetime-local) a datetime. Retorna None si vacío."""
    if not value or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _promo_to_dict(p: PromotionModel, services: list) -> dict:
    d = p.__dict__.copy()
    d["services"]       = [s.__dict__ for s in services]
    d["original_price"] = sum(s.price for s in services)
    d["vigencia_status"]    = p.vigencia_status
    d["is_currently_valid"] = p.is_currently_valid
    return d


class PromotionService:

    @staticmethod
    def create_promotion(name: str, description: str, service_ids: List[str],
                         promo_price: str, image_file=None, upload_folder: str = None,
                         start_datetime: str = None, end_datetime: str = None) -> Dict:
        if not name or len(name.strip()) < 2:
            return {"success": False, "message": "El nombre debe tener al menos 2 caracteres"}
        if not service_ids or len(service_ids) < 2:
            return {"success": False, "message": "Un combo debe incluir al menos 2 servicios"}
        try:
            price = float(promo_price)
            if price <= 0:
                return {"success": False, "message": "El precio promocional debe ser mayor a 0"}
        except (TypeError, ValueError):
            return {"success": False, "message": "El precio debe ser un número válido"}

        # Validar descuento mínimo del 5%
        services = ServiceRepository.find_by_ids(service_ids)
        original_total = sum(s.price for s in services)
        max_allowed = round(original_total * 0.95, 2)
        if price > max_allowed:
            return {
                "success": False,
                "message": f"El precio promocional (${price:.2f}) debe tener al menos 5% de descuento. Máximo permitido: ${max_allowed:.2f}"
            }

        start_dt = _parse_datetime(start_datetime)
        end_dt   = _parse_datetime(end_datetime)
        if start_dt and end_dt and start_dt >= end_dt:
            return {"success": False, "message": "La fecha de inicio debe ser anterior a la fecha de fin"}

        image_url = None
        if image_file and image_file.filename:
            if not _allowed_file(image_file.filename):
                return {"success": False, "message": "Formato de imagen no permitido (jpg, png, webp)"}
            import uuid
            ext = secure_filename(image_file.filename).rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            if upload_folder:
                image_file.save(os.path.join(upload_folder, unique_name))
            image_url = f"/img/promotions/{unique_name}"

        try:
            promo = PromotionModel(
                name           = name.strip(),
                description    = description.strip() if description else "",
                service_ids    = service_ids,
                promo_price    = price,
                image_url      = image_url,
                start_datetime = start_dt,
                end_datetime   = end_dt,
            )
            promo_id = PromotionRepository.create(promo)
            return {"success": True, "message": "Promoción creada exitosamente", "promo_id": promo_id}
        except Exception as e:
            return {"success": False, "message": f"Error al crear promoción: {e}"}

    @staticmethod
    def update_promotion(promo_id: str, name: str, description: str, service_ids: List[str],
                         promo_price: str, is_active: bool,
                         image_file=None, upload_folder: str = None,
                         start_datetime: str = None, end_datetime: str = None) -> Dict:
        try:
            if not PromotionRepository.find_by_id(promo_id):
                return {"success": False, "message": "Promoción no encontrada"}
            if not service_ids or len(service_ids) < 2:
                return {"success": False, "message": "Un combo debe incluir al menos 2 servicios"}

            price = float(promo_price)
            services = ServiceRepository.find_by_ids(service_ids)
            original_total = sum(s.price for s in services)
            max_allowed = round(original_total * 0.95, 2)
            if price > max_allowed:
                return {
                    "success": False,
                    "message": f"El precio promocional (${price:.2f}) debe tener al menos 5% de descuento. Máximo permitido: ${max_allowed:.2f}"
                }

            start_dt = _parse_datetime(start_datetime)
            end_dt   = _parse_datetime(end_datetime)
            if start_dt and end_dt and start_dt >= end_dt:
                return {"success": False, "message": "La fecha de inicio debe ser anterior a la fecha de fin"}

            data = {
                "name":           name.strip(),
                "description":    description.strip() if description else "",
                "service_ids":    service_ids,
                "promo_price":    price,
                "is_active":      is_active,
                "start_datetime": start_dt,
                "end_datetime":   end_dt,
            }
            if image_file and image_file.filename:
                if not _allowed_file(image_file.filename):
                    return {"success": False, "message": "Formato de imagen no permitido"}
                import uuid
                ext = secure_filename(image_file.filename).rsplit(".", 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                if upload_folder:
                    image_file.save(os.path.join(upload_folder, unique_name))
                data["image_url"] = f"/img/promotions/{unique_name}"

            PromotionRepository.update(promo_id, data)
            return {"success": True, "message": "Promoción actualizada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar promoción: {e}"}

    @staticmethod
    def delete_promotion(promo_id: str) -> Dict:
        try:
            PromotionRepository.delete_by_id(promo_id)
            return {"success": True, "message": "Promoción eliminada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar promoción: {e}"}

    @staticmethod
    def get_all_promotions(only_active=False) -> Dict:
        try:
            promos = PromotionRepository.find_all(only_active=only_active)
            # Filtro adicional por vigencia cuando se pide solo las activas (vista cliente)
            if only_active:
                promos = [p for p in promos if p.is_currently_valid]
            result = []
            for p in promos:
                services = ServiceRepository.find_by_ids(p.service_ids) if p.service_ids else []
                result.append(_promo_to_dict(p, services))
            return {"success": True, "promotions": result}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener promociones: {e}", "promotions": []}

    @staticmethod
    def get_promotion_by_id(promo_id: str) -> Dict:
        try:
            promo = PromotionRepository.find_by_id(promo_id)
            if not promo:
                return {"success": False, "message": "Promoción no encontrada"}
            services = ServiceRepository.find_by_ids(promo.service_ids) if promo.service_ids else []
            return {"success": True, "promotion": _promo_to_dict(promo, services)}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener promoción: {e}"}
