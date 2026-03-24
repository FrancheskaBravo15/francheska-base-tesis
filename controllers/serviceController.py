from flask import render_template, request, redirect, url_for, Blueprint, flash, session, jsonify
from services.serviceService import ServiceService
from services.reviewService import ReviewService
from services.wishlistService import WishlistService
from services.workerService import WorkerService

service_bp = Blueprint('services', __name__, url_prefix='/services')

@service_bp.route('/', methods=['GET'])
def catalog():
    category  = request.args.get('category', '')
    result    = ServiceService.get_all_services(only_active=True)
    categories = ServiceService.get_categories()
    services   = result.get("services", [])

    if category:
        services = [s for s in services if s["category"] == category]

    # Agregar rating promedio a cada servicio
    for s in services:
        try:
            from repositories.reviewRepository import ReviewRepository
            avg, count = ReviewRepository.get_average_rating(s["id"])
        except Exception:
            avg, count = 0.0, 0
        s["avg_rating"]    = avg
        s["total_reviews"] = count

    # Lista de deseos del usuario actual
    wishlist_ids = []
    user_id = session.get("user_id")
    if user_id:
        from services.wishlistService import WishlistService as WS
        wl_result = WS.get_wishlist(user_id)
        wishlist_ids = wl_result.get("service_ids", [])

    return render_template('/views/services/catalog.html',
                           services=services,
                           categories=categories,
                           selected_category=category,
                           wishlist_ids=wishlist_ids)

@service_bp.route('/<service_id>', methods=['GET'])
def detail(service_id):
    result = ServiceService.get_service_by_id(service_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('services.catalog'))

    service    = result["service"]
    user_id    = session.get("user_id")
    rev_result = ReviewService.get_reviews_for_service(service_id, current_user_id=user_id)

    in_wishlist = False
    if user_id:
        in_wishlist = WishlistService.is_in_wishlist(user_id, service_id)

    # Trabajadoras disponibles para la categoría del servicio
    workers_result = WorkerService.get_workers_by_specialty(service["category"])

    return render_template('/views/services/detail.html',
                           service=service,
                           reviews=rev_result.get("reviews", []),
                           avg_rating=rev_result.get("avg_rating", 0),
                           total_reviews=rev_result.get("total_reviews", 0),
                           user_reviewed=rev_result.get("user_reviewed", False),
                           in_wishlist=in_wishlist,
                           workers=workers_result.get("workers", []))

@service_bp.route('/<service_id>/slots', methods=['GET'])
def get_slots(service_id):
    """API para obtener slots disponibles de una trabajadora en una fecha."""
    worker_id = request.args.get('worker_id')
    date      = request.args.get('date')

    if not worker_id or not date:
        return jsonify({"success": False, "slots": [], "message": "Parámetros incompletos"})

    service_result = ServiceService.get_service_by_id(service_id)
    if not service_result["success"]:
        return jsonify({"success": False, "slots": [], "message": "Servicio no encontrado"})

    service  = service_result["service"]
    duration = service["duration_minutes"]
    category = service["category"]

    result = WorkerService.get_available_slots(worker_id, date, duration, category)
    return jsonify(result)
