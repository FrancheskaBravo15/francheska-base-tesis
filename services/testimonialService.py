from typing import Dict
from models.testimonialModel import TestimonialModel
from repositories.testimonialRepository import TestimonialRepository


class TestimonialService:

    @staticmethod
    def submit(author_name: str, rating: str, comment: str) -> Dict:
        if not author_name or len(author_name.strip()) < 2:
            return {"success": False, "message": "El nombre debe tener al menos 2 caracteres"}
        if not comment or len(comment.strip()) < 10:
            return {"success": False, "message": "El comentario debe tener al menos 10 caracteres"}
        try:
            r = int(rating)
            if r < 1 or r > 5:
                return {"success": False, "message": "La puntuación debe ser entre 1 y 5"}
        except (TypeError, ValueError):
            return {"success": False, "message": "Puntuación inválida"}

        try:
            t = TestimonialModel(
                author_name=author_name.strip(),
                rating=r,
                comment=comment.strip(),
                is_approved=True
            )
            TestimonialRepository.create(t)
            return {"success": True, "message": "¡Gracias por tu comentario! Será revisado pronto."}
        except Exception as e:
            return {"success": False, "message": f"Error al guardar tu comentario: {e}"}

    @staticmethod
    def get_approved(limit: int = 6) -> Dict:
        try:
            testimonials = TestimonialRepository.find_approved(limit=limit)
            return {"success": True, "testimonials": [t.__dict__ for t in testimonials]}
        except Exception as e:
            return {"success": False, "testimonials": [], "message": str(e)}

    @staticmethod
    def get_all() -> Dict:
        try:
            testimonials = TestimonialRepository.find_all()
            return {"success": True, "testimonials": [t.__dict__ for t in testimonials]}
        except Exception as e:
            return {"success": False, "testimonials": [], "message": str(e)}

    @staticmethod
    def approve(testimonial_id: str) -> Dict:
        try:
            TestimonialRepository.approve(testimonial_id)
            return {"success": True, "message": "Testimonio aprobado"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def delete(testimonial_id: str) -> Dict:
        try:
            TestimonialRepository.delete_by_id(testimonial_id)
            return {"success": True, "message": "Testimonio eliminado"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}
