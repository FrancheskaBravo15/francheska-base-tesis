import json
from flask import render_template, Blueprint, flash, redirect, url_for, request, jsonify
from services.promotionService import PromotionService
from services.workerService import WorkerService
from repositories.serviceRepository import ServiceRepository

promotion_bp = Blueprint('promotions', __name__, url_prefix='/promotions')


@promotion_bp.route('/', methods=['GET'])
def list_promotions():
    result = PromotionService.get_all_promotions(only_active=True)
    return render_template('/views/promotions/list.html',
                           promotions=result.get("promotions", []))


@promotion_bp.route('/<promo_id>', methods=['GET'])
def detail(promo_id):
    result = PromotionService.get_promotion_by_id(promo_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('promotions.list_promotions'))
    promo = result["promotion"]
    services_json = json.dumps([{
        "id":               s["id"],
        "name":             s["name"],
        "category":         s["category"],
        "duration_minutes": s["duration_minutes"],
        "price":            s["price"]
    } for s in promo["services"]])
    return render_template('/views/promotions/detail.html',
                           promotion=promo,
                           services_json=services_json)


# ── API para el modal de reserva ──────────────────────────────────────────────

@promotion_bp.route('/api/workers/<service_id>', methods=['GET'])
def api_workers(service_id):
    """Devuelve las especialistas disponibles para la categoría de un servicio."""
    svc = ServiceRepository.find_by_id(service_id)
    if not svc:
        return jsonify({"success": False, "workers": [], "message": "Servicio no encontrado"})
    result = WorkerService.get_workers_by_specialty(svc.category)
    return jsonify(result)


@promotion_bp.route('/api/slots', methods=['GET'])
def api_slots():
    """Devuelve los horarios disponibles para especialista+fecha+servicio."""
    service_id = request.args.get('service_id')
    worker_id  = request.args.get('worker_id')
    date       = request.args.get('date')
    if not all([service_id, worker_id, date]):
        return jsonify({"success": False, "slots": [], "message": "Parámetros incompletos"})
    svc = ServiceRepository.find_by_id(service_id)
    if not svc:
        return jsonify({"success": False, "slots": [], "message": "Servicio no encontrado"})
    result = WorkerService.get_available_slots(worker_id, date, svc.duration_minutes, svc.category)
    return jsonify(result)
