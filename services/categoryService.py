from typing import Dict, List
from models.categoryModel import CategoryModel
from repositories.categoryRepository import CategoryRepository
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class CategoryService:

    @staticmethod
    def create_category(name: str, description: str,
                        image_file=None, upload_folder: str = None) -> Dict:
        if not name or len(name.strip()) < 2:
            return {"success": False, "message": "El nombre debe tener al menos 2 caracteres"}
        if CategoryRepository.name_exists(name.strip()):
            return {"success": False, "message": "Ya existe una categoría con ese nombre"}

        image_url = None
        if image_file and image_file.filename:
            if not _allowed_file(image_file.filename):
                return {"success": False, "message": "Formato de imagen no permitido (jpg, png, webp)"}
            import uuid
            ext = secure_filename(image_file.filename).rsplit(".", 1)[1].lower()
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            if upload_folder:
                image_file.save(os.path.join(upload_folder, unique_name))
            image_url = f"/img/categories/{unique_name}"

        try:
            category = CategoryModel(
                name=name.strip(),
                description=description.strip() if description else "",
                image_url=image_url
            )
            cat_id = CategoryRepository.create(category)
            return {"success": True, "message": "Categoría creada exitosamente", "category_id": cat_id}
        except Exception as e:
            return {"success": False, "message": f"Error al crear categoría: {e}"}

    @staticmethod
    def update_category(category_id: str, name: str, description: str,
                        image_file=None, upload_folder: str = None) -> Dict:
        try:
            if not CategoryRepository.find_by_id(category_id):
                return {"success": False, "message": "Categoría no encontrada"}
            if CategoryRepository.name_exists(name.strip(), exclude_id=category_id):
                return {"success": False, "message": "Ya existe una categoría con ese nombre"}

            data = {
                "name": name.strip(),
                "description": description.strip() if description else ""
            }

            if image_file and image_file.filename:
                if not _allowed_file(image_file.filename):
                    return {"success": False, "message": "Formato de imagen no permitido"}
                import uuid
                ext = secure_filename(image_file.filename).rsplit(".", 1)[1].lower()
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                if upload_folder:
                    image_file.save(os.path.join(upload_folder, unique_name))
                data["image_url"] = f"/img/categories/{unique_name}"

            CategoryRepository.update(category_id, data)
            return {"success": True, "message": "Categoría actualizada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar categoría: {e}"}

    @staticmethod
    def delete_category(category_id: str) -> Dict:
        try:
            CategoryRepository.delete_by_id(category_id)
            return {"success": True, "message": "Categoría eliminada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar categoría: {e}"}

    @staticmethod
    def get_all_categories() -> Dict:
        try:
            cats = CategoryRepository.find_all()
            return {"success": True, "categories": [c.__dict__ for c in cats]}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener categorías: {e}", "categories": []}

    @staticmethod
    def get_category_by_id(category_id: str) -> Dict:
        try:
            cat = CategoryRepository.find_by_id(category_id)
            if not cat:
                return {"success": False, "message": "Categoría no encontrada"}
            return {"success": True, "category": cat.__dict__}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener categoría: {e}"}
