from typing import Dict
from models.reviewModel import ReviewModel
from repositories.reviewRepository import ReviewRepository
from repositories.serviceRepository import ServiceRepository
from repositories.personRepository import PersonRepository

class ReviewService:

    @staticmethod
    def add_review(service_id: str, user_id: str, rating: str, comment: str) -> Dict:
        try:
            # Validar
            try:
                r = int(rating)
                if r < 1 or r > 5:
                    return {"success": False, "message": "La puntuación debe ser entre 1 y 5"}
            except (ValueError, TypeError):
                return {"success": False, "message": "Puntuación inválida"}

            service = ServiceRepository.find_by_id(service_id)
            if not service:
                return {"success": False, "message": "Servicio no encontrado"}

            # Un usuario solo puede dejar una reseña por servicio
            existing = ReviewRepository.find_by_user_and_service(user_id, service_id)
            if existing:
                return {"success": False, "message": "Ya has dejado una reseña para este servicio"}

            review = ReviewModel(
                service_id=service_id,
                user_id=user_id,
                rating=r,
                comment=comment.strip() if comment else ""
            )
            ReviewRepository.create(review)
            return {"success": True, "message": "Reseña publicada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al publicar reseña: {e}"}

    @staticmethod
    def get_reviews_for_service(service_id: str, current_user_id: str = None) -> Dict:
        try:
            reviews_raw = ReviewRepository.find_by_service(service_id)
            avg_result  = ReviewRepository.get_average_rating(service_id)
            avg   = avg_result[0] if isinstance(avg_result, tuple) else 0.0
            count = avg_result[1] if isinstance(avg_result, tuple) else 0
            reviews = []
            user_reviewed = False
            for r in reviews_raw:
                person = PersonRepository.find_by_user_id(r.user_id)
                reviews.append({
                    "review_id":  r.id,
                    "rating":     r.rating,
                    "comment":    r.comment,
                    "created_at": r.created_at,
                    "user_name":  f"{person.first_name} {person.last_name}" if person else "Usuario",
                    "is_own":     r.user_id == current_user_id
                })
                if current_user_id and r.user_id == current_user_id:
                    user_reviewed = True
            return {
                "success": True,
                "reviews": reviews,
                "avg_rating": avg,
                "total_reviews": count,
                "user_reviewed": user_reviewed
            }
        except Exception as e:
            return {"success": False, "reviews": [], "avg_rating": 0, "total_reviews": 0, "message": f"Error: {e}"}

    @staticmethod
    def delete_review(review_id: str, user_id: str, is_admin: bool = False) -> Dict:
        try:
            from bson import ObjectId
            collection = ReviewRepository._get_collection()
            data = collection.find_one({"_id": ObjectId(review_id)})
            if not data:
                return {"success": False, "message": "Reseña no encontrada"}
            if not is_admin and data["user_id"] != user_id:
                return {"success": False, "message": "No tienes permiso para eliminar esta reseña"}
            ReviewRepository.delete_by_id(review_id)
            return {"success": True, "message": "Reseña eliminada"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}
