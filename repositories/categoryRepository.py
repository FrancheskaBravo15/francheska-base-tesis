from database.mongoDb import DatabaseConnection
from models.categoryModel import CategoryModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError


class CategoryRepository:
    COLLECTION_NAME = "categories"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, category: CategoryModel) -> str:
        try:
            result = cls._get_collection().insert_one(category.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear categoría: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[CategoryModel]:
        try:
            return [CategoryModel.from_dict(c) for c in cls._get_collection().find().sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener categorías: {e}")
            raise

    @classmethod
    def find_by_id(cls, category_id: str) -> Optional[CategoryModel]:
        try:
            data = cls._get_collection().find_one({"_id": ObjectId(category_id)})
            return CategoryModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar categoría: {e}")
            raise

    @classmethod
    def find_by_name(cls, name: str) -> Optional[CategoryModel]:
        try:
            data = cls._get_collection().find_one({"name": name})
            return CategoryModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar categoría por nombre: {e}")
            raise

    @classmethod
    def update(cls, category_id: str, data: dict) -> None:
        try:
            cls._get_collection().update_one({"_id": ObjectId(category_id)}, {"$set": data})
        except PyMongoError as e:
            print(f"Error al actualizar categoría: {e}")
            raise

    @classmethod
    def delete_by_id(cls, category_id: str) -> None:
        try:
            cls._get_collection().delete_one({"_id": ObjectId(category_id)})
        except PyMongoError as e:
            print(f"Error al eliminar categoría: {e}")
            raise

    @classmethod
    def name_exists(cls, name: str, exclude_id: str = None) -> bool:
        try:
            query = {"name": name}
            if exclude_id:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            return cls._get_collection().count_documents(query) > 0
        except PyMongoError as e:
            print(f"Error al verificar nombre de categoría: {e}")
            raise
