from database.mongoDb import DatabaseConnection
from models.reviewModel import ReviewModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class ReviewRepository:
    COLLECTION_NAME = "reviews"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, review: ReviewModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(review.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear reseña en la BD: {e}")
            raise

    @classmethod
    def find_by_service(cls, service_id: str) -> List[ReviewModel]:
        try:
            collection = cls._get_collection()
            return [ReviewModel.from_dict(r) for r in
                    collection.find({"service_id": service_id}).sort("created_at", -1)]
        except PyMongoError as e:
            print(f"Error al buscar reseñas por servicio en la BD: {e}")
            raise

    @classmethod
    def find_by_user_and_service(cls, user_id: str, service_id: str) -> Optional[ReviewModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"user_id": user_id, "service_id": service_id})
            return ReviewModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar reseña de usuario y servicio en la BD: {e}")
            raise

    @classmethod
    def get_average_rating(cls, service_id: str) -> float:
        """Calcula la puntuación promedio de un servicio."""
        try:
            collection = cls._get_collection()
            pipeline = [
                {"$match": {"service_id": service_id}},
                {"$group": {"_id": "$service_id", "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
            ]
            result = list(collection.aggregate(pipeline))
            if result:
                return round(result[0]["avg"], 1), result[0]["count"]
            return 0.0, 0
        except PyMongoError as e:
            print(f"Error al calcular rating promedio en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, review_id: str) -> None:
        try:
            collection = cls._get_collection()
            collection.delete_one({"_id": ObjectId(review_id)})
        except PyMongoError as e:
            print(f"Error al eliminar reseña en la BD: {e}")
            raise
