from database.mongoDb import DatabaseConnection
from models.promotionModel import PromotionModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError


class PromotionRepository:
    COLLECTION_NAME = "promotions"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, promotion: PromotionModel) -> str:
        try:
            result = cls._get_collection().insert_one(promotion.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear promoción: {e}")
            raise

    @classmethod
    def find_all(cls, only_active=False) -> List[PromotionModel]:
        try:
            query = {"is_active": True} if only_active else {}
            return [PromotionModel.from_dict(p) for p in cls._get_collection().find(query).sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener promociones: {e}")
            raise

    @classmethod
    def find_by_id(cls, promo_id: str) -> Optional[PromotionModel]:
        try:
            data = cls._get_collection().find_one({"_id": ObjectId(promo_id)})
            return PromotionModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar promoción: {e}")
            raise

    @classmethod
    def update(cls, promo_id: str, data: dict) -> None:
        try:
            cls._get_collection().update_one({"_id": ObjectId(promo_id)}, {"$set": data})
        except PyMongoError as e:
            print(f"Error al actualizar promoción: {e}")
            raise

    @classmethod
    def delete_by_id(cls, promo_id: str) -> None:
        try:
            cls._get_collection().delete_one({"_id": ObjectId(promo_id)})
        except PyMongoError as e:
            print(f"Error al eliminar promoción: {e}")
            raise
