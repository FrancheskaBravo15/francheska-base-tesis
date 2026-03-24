from database.mongoDb import DatabaseConnection
from models.serviceModel import ServiceModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class ServiceRepository:
    COLLECTION_NAME = "services"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, service: ServiceModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(service.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear servicio en la BD: {e}")
            raise

    @classmethod
    def find_all(cls, only_active=False) -> List[ServiceModel]:
        try:
            collection = cls._get_collection()
            query = {"is_active": True} if only_active else {}
            return [ServiceModel.from_dict(s) for s in collection.find(query).sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener servicios de la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, service_id: str) -> Optional[ServiceModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(service_id)})
            return ServiceModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar servicio por Id en la BD: {e}")
            raise

    @classmethod
    def find_by_category(cls, category: str, only_active=True) -> List[ServiceModel]:
        try:
            collection = cls._get_collection()
            query = {"category": category}
            if only_active:
                query["is_active"] = True
            return [ServiceModel.from_dict(s) for s in collection.find(query)]
        except PyMongoError as e:
            print(f"Error al buscar servicios por categoría en la BD: {e}")
            raise

    @classmethod
    def find_by_ids(cls, ids: List[str]) -> List[ServiceModel]:
        try:
            collection = cls._get_collection()
            object_ids = [ObjectId(i) for i in ids]
            return [ServiceModel.from_dict(s) for s in collection.find({"_id": {"$in": object_ids}})]
        except PyMongoError as e:
            print(f"Error al buscar servicios por ids en la BD: {e}")
            raise

    @classmethod
    def update(cls, service_id: str, data: dict) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(service_id)}, {"$set": data})
        except PyMongoError as e:
            print(f"Error al actualizar servicio en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, service_id: str) -> None:
        try:
            collection = cls._get_collection()
            collection.delete_one({"_id": ObjectId(service_id)})
        except PyMongoError as e:
            print(f"Error al eliminar servicio en la BD: {e}")
            raise

    @classmethod
    def get_categories(cls) -> List[str]:
        try:
            collection = cls._get_collection()
            return collection.distinct("category", {"is_active": True})
        except PyMongoError as e:
            print(f"Error al obtener categorías en la BD: {e}")
            raise
