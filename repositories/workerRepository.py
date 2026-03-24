from database.mongoDb import DatabaseConnection
from models.workerModel import WorkerModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class WorkerRepository:
    COLLECTION_NAME = "workers"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, worker: WorkerModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(worker.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear trabajadora en la BD: {e}")
            raise

    @classmethod
    def find_all(cls, only_active=False) -> List[WorkerModel]:
        try:
            collection = cls._get_collection()
            query = {"is_active": True} if only_active else {}
            return [WorkerModel.from_dict(w) for w in collection.find(query)]
        except PyMongoError as e:
            print(f"Error al obtener trabajadoras de la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, worker_id: str) -> Optional[WorkerModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(worker_id)})
            return WorkerModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar trabajadora por Id en la BD: {e}")
            raise

    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional[WorkerModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"user_id": user_id})
            return WorkerModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar trabajadora por user_id en la BD: {e}")
            raise

    @classmethod
    def find_by_specialty(cls, specialty: str, only_active=True) -> List[WorkerModel]:
        """Busca trabajadoras que tengan una especialidad específica."""
        try:
            collection = cls._get_collection()
            query = {"specialties": specialty}
            if only_active:
                query["is_active"] = True
            return [WorkerModel.from_dict(w) for w in collection.find(query)]
        except PyMongoError as e:
            print(f"Error al buscar trabajadoras por especialidad en la BD: {e}")
            raise

    @classmethod
    def update(cls, worker_id: str, data: dict) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(worker_id)}, {"$set": data})
        except PyMongoError as e:
            print(f"Error al actualizar trabajadora en la BD: {e}")
            raise

    @classmethod
    def update_by_user_id(cls, user_id: str, data: dict) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"user_id": user_id}, {"$set": data})
        except PyMongoError as e:
            print(f"Error al actualizar trabajadora por user_id en la BD: {e}")
            raise

    @classmethod
    def exist_by_user_id(cls, user_id: str) -> bool:
        try:
            collection = cls._get_collection()
            return collection.find_one({"user_id": user_id}) is not None
        except PyMongoError as e:
            print(f"Error al verificar trabajadora por user_id en la BD: {e}")
            raise
