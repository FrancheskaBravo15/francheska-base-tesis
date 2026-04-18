from typing import Dict, List
from models.promotionModel import PromotionModel
from repositories.promotionRepository import PromotionRepository
from repositories.serviceRepository import ServiceRepository
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class PromotionService:

    @staticmethod
    def create_promotion(name: str, description: str, service_ids: List[str],
                         promo_price: str, image_file=None, upload_folder: str = None) -> Dict:
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
                name=name.strip(),
                description=description.strip() if description else "",
                service_ids=service_ids,
                promo_price=price,
                image_url=image_url
            )
            promo_id = PromotionRepository.create(promo)
            return {"success": True, "message": "Promoción creada exitosamente", "promo_id": promo_id}
        except Exception as e:
            return {"success": False, "message": f"Error al crear promoción: {e}"}

    @staticmethod
    def update_promotion(promo_id: str, name: str, description: str, service_ids: List[str],
                         promo_price: str, is_active: bool,
                         image_file=None, upload_folder: str = None) -> Dict:
        try:
            if not PromotionRepository.find_by_id(promo_id):
                return {"success": False, "message": "Promoción no encontrada"}
            if not service_ids or len(service_ids) < 2:
                return {"success": False, "message": "Un combo debe incluir al menos 2 servicios"}

            data = {
                "name": name.strip(),
                "description": description.strip() if description else "",
                "service_ids": service_ids,
                "promo_price": float(promo_price),
                "is_active": is_active
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
            result = []
            for p in promos:
                promo_dict = p.__dict__.copy()
                services = ServiceRepository.find_by_ids(p.service_ids) if p.service_ids else []
                promo_dict["services"] = [s.__dict__ for s in services]
                promo_dict["original_price"] = sum(s.price for s in services)
                result.append(promo_dict)
            return {"success": True, "promotions": result}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener promociones: {e}", "promotions": []}

    @staticmethod
    def get_promotion_by_id(promo_id: str) -> Dict:
        try:
            promo = PromotionRepository.find_by_id(promo_id)
            if not promo:
                return {"success": False, "message": "Promoción no encontrada"}
            promo_dict = promo.__dict__.copy()
            services = ServiceRepository.find_by_ids(promo.service_ids) if promo.service_ids else []
            promo_dict["services"] = [s.__dict__ for s in services]
            promo_dict["original_price"] = sum(s.price for s in services)
            return {"success": True, "promotion": promo_dict}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener promoción: {e}"}
