from database.mongoDb import DatabaseConnection
from models.testimonialModel import TestimonialModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError


class TestimonialRepository:
    COLLECTION_NAME = "testimonials"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, testimonial: TestimonialModel) -> str:
        try:
            result = cls._get_collection().insert_one(testimonial.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear testimonio: {e}")
            raise

    @classmethod
    def find_approved(cls, limit: int = 6) -> List[TestimonialModel]:
        try:
            cursor = cls._get_collection().find({"is_approved": True}).sort("created_at", -1).limit(limit)
            return [TestimonialModel.from_dict(t) for t in cursor]
        except PyMongoError as e:
            print(f"Error al obtener testimonios: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[TestimonialModel]:
        try:
            return [TestimonialModel.from_dict(t) for t in cls._get_collection().find().sort("created_at", -1)]
        except PyMongoError as e:
            print(f"Error al obtener testimonios: {e}")
            raise

    @classmethod
    def find_by_id(cls, testimonial_id: str) -> Optional[TestimonialModel]:
        try:
            data = cls._get_collection().find_one({"_id": ObjectId(testimonial_id)})
            return TestimonialModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar testimonio: {e}")
            raise

    @classmethod
    def approve(cls, testimonial_id: str) -> None:
        try:
            cls._get_collection().update_one(
                {"_id": ObjectId(testimonial_id)},
                {"$set": {"is_approved": True}}
            )
        except PyMongoError as e:
            print(f"Error al aprobar testimonio: {e}")
            raise

    @classmethod
    def delete_by_id(cls, testimonial_id: str) -> None:
        try:
            cls._get_collection().delete_one({"_id": ObjectId(testimonial_id)})
        except PyMongoError as e:
            print(f"Error al eliminar testimonio: {e}")
            raise
