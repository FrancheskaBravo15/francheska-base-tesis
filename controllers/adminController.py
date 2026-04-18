from flask import render_template, request, redirect, url_for, Blueprint, flash
from utils.authDecorator import role_required
from services.userService import UserService
from services.serviceService import ServiceService
from services.categoryService import CategoryService
from services.promotionService import PromotionService
from services.testimonialService import TestimonialService
from services.workerService import WorkerService
from services.appointmentService import AppointmentService
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def _upload_folder_services(app):
    return os.path.join(app.static_folder, 'img', 'services')

def _upload_folder_categories(app):
    return os.path.join(app.static_folder, 'img', 'categories')

# ──────────────────────────────────────────
# PANEL PRINCIPAL
# ──────────────────────────────────────────
@admin_bp.route('/', methods=['GET'])
@role_required('admin')
def panel():
    users_result  = UserService.get_all_users_with_persons()
    appts_result  = AppointmentService.get_all_appointments()
    workers_result = WorkerService.get_all_workers()
    services_result = ServiceService.get_all_services()

    stats = {
        "total_users":    len(users_result.get("users", [])),
        "total_workers":  len(workers_result.get("workers", [])),
        "total_services": len(services_result.get("services", [])),
        "total_appts":    len(appts_result.get("appointments", [])),
        "pending_appts":  sum(1 for a in appts_result.get("appointments", []) if a["status"] == "confirmada"),
        "total_revenue":  sum(a["total_price"] for a in appts_result.get("appointments", []) if a["status"] == "completada")
    }
    return render_template('/views/admin/panel.html', stats=stats)


# ──────────────────────────────────────────
# GESTIÓN DE USUARIOS
# ──────────────────────────────────────────
@admin_bp.route('/users', methods=['GET'])
@role_required('admin')
def users():
    result = UserService.get_all_users_with_persons()
    return render_template('/views/admin/users.html', users=result.get("users", []))

@admin_bp.route('/users/<user_id>/toggle', methods=['POST'])
@role_required('admin')
def toggle_user(user_id):
    result = UserService.toggle_user_active(user_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.users'))


# ──────────────────────────────────────────
# GESTIÓN DE SERVICIOS
# ──────────────────────────────────────────
# ──────────────────────────────────────────
# GESTIÓN DE CATEGORÍAS
# ──────────────────────────────────────────
@admin_bp.route('/categories', methods=['GET'])
@role_required('admin')
def categories():
    result = CategoryService.get_all_categories()
    return render_template('/views/admin/categories.html', categories=result.get("categories", []))

@admin_bp.route('/categories/new', methods=['GET', 'POST'])
@role_required('admin')
def create_category():
    from flask import current_app
    if request.method == 'GET':
        return render_template('/views/admin/category_form.html', category=None)

    upload_folder = _upload_folder_categories(current_app)
    os.makedirs(upload_folder, exist_ok=True)
    result = CategoryService.create_category(
        name=request.form.get('name', '').strip(),
        description=request.form.get('description', '').strip(),
        image_file=request.files.get('image'),
        upload_folder=upload_folder
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('admin.categories'))
    return render_template('/views/admin/category_form.html', category=None, form_data=request.form)

@admin_bp.route('/categories/<category_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_category(category_id):
    from flask import current_app
    result = CategoryService.get_category_by_id(category_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('admin.categories'))

    category = result["category"]
    if request.method == 'GET':
        return render_template('/views/admin/category_form.html', category=category)

    upload_folder = _upload_folder_categories(current_app)
    os.makedirs(upload_folder, exist_ok=True)
    result = CategoryService.update_category(
        category_id=category_id,
        name=request.form.get('name', '').strip(),
        description=request.form.get('description', '').strip(),
        image_file=request.files.get('image'),
        upload_folder=upload_folder
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('admin.categories'))
    return render_template('/views/admin/category_form.html', category=category, form_data=request.form)

@admin_bp.route('/categories/<category_id>/delete', methods=['POST'])
@role_required('admin')
def delete_category(category_id):
    result = CategoryService.delete_category(category_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.categories'))


# ──────────────────────────────────────────
# GESTIÓN DE SERVICIOS
# ──────────────────────────────────────────
@admin_bp.route('/services', methods=['GET'])
@role_required('admin')
def services():
    result = ServiceService.get_all_services()
    return render_template('/views/admin/services.html', services=result.get("services", []))

@admin_bp.route('/services/new', methods=['GET', 'POST'])
@role_required('admin')
def create_service():
    from flask import current_app
    if request.method == 'GET':
        categories = CategoryService.get_all_categories().get("categories", [])
        return render_template('/views/admin/service_form.html', service=None, categories=categories)

    image_file    = request.files.get('image')
    upload_folder = _upload_folder_services(current_app)
    result = ServiceService.create_service(
        name             = request.form.get('name', '').strip(),
        description      = request.form.get('description', '').strip(),
        category         = request.form.get('category', '').strip(),
        price            = request.form.get('price', '0'),
        duration_minutes = request.form.get('duration_minutes', '60'),
        image_file       = image_file,
        upload_folder    = upload_folder
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('admin.services'))
    categories = CategoryService.get_all_categories().get("categories", [])
    return render_template('/views/admin/service_form.html', service=None,
                           categories=categories, form_data=request.form)

@admin_bp.route('/services/<service_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_service(service_id):
    from flask import current_app
    result = ServiceService.get_service_by_id(service_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('admin.services'))

    service = result["service"]
    if request.method == 'GET':
        categories = CategoryService.get_all_categories().get("categories", [])
        return render_template('/views/admin/service_form.html', service=service, categories=categories)

    image_file    = request.files.get('image')
    upload_folder = _upload_folder_services(current_app)
    is_active     = request.form.get('is_active') == 'on'
    result = ServiceService.update_service(
        service_id       = service_id,
        name             = request.form.get('name', '').strip(),
        description      = request.form.get('description', '').strip(),
        category         = request.form.get('category', '').strip(),
        price            = request.form.get('price', '0'),
        duration_minutes = request.form.get('duration_minutes', '60'),
        is_active        = is_active,
        image_file       = image_file,
        upload_folder    = upload_folder
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('admin.services'))
    categories = CategoryService.get_all_categories().get("categories", [])
    return render_template('/views/admin/service_form.html', service=service,
                           categories=categories, form_data=request.form)

@admin_bp.route('/services/<service_id>/delete', methods=['POST'])
@role_required('admin')
def delete_service(service_id):
    result = ServiceService.delete_service(service_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.services'))


# ──────────────────────────────────────────
# GESTIÓN DE TRABAJADORAS
# ──────────────────────────────────────────
@admin_bp.route('/workers', methods=['GET'])
@role_required('admin')
def workers():
    result = WorkerService.get_all_workers()
    return render_template('/views/admin/workers.html', workers=result.get("workers", []))

@admin_bp.route('/workers/new', methods=['GET', 'POST'])
@role_required('admin')
def create_worker():
    categories = CategoryService.get_all_categories().get("categories", [])
    if request.method == 'GET':
        return render_template('/views/admin/worker_form.html', worker=None, categories=categories)

    specialties = request.form.getlist('specialties')
    result = WorkerService.create_worker(
        identification = request.form.get('identification', '').strip(),
        first_name     = request.form.get('first_name', '').strip(),
        last_name      = request.form.get('last_name', '').strip(),
        phone          = request.form.get('phone', '').strip(),
        email          = request.form.get('email', '').strip(),
        password       = request.form.get('password', ''),
        specialties    = specialties,
        bio            = request.form.get('bio', '').strip()
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('admin.workers'))
    return render_template('/views/admin/worker_form.html', worker=None,
                           categories=categories, form_data=request.form)

@admin_bp.route('/workers/<worker_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_worker(worker_id):
    categories = CategoryService.get_all_categories().get("categories", [])
    result = WorkerService.get_worker_by_id(worker_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('admin.workers'))

    worker = result["worker"]

    if request.method == 'GET':
        return render_template('/views/admin/worker_form.html',
                               worker=worker, categories=categories, is_edit=True)

    specialties  = request.form.getlist('specialties')
    new_password = request.form.get('new_password', '').strip()

    res = WorkerService.update_worker_full(
        worker_id    = worker_id,
        first_name   = request.form.get('first_name', '').strip(),
        last_name    = request.form.get('last_name', '').strip(),
        phone        = request.form.get('phone', '').strip(),
        specialties  = specialties,
        bio          = request.form.get('bio', '').strip(),
        new_password = new_password if new_password else None
    )
    flash(res["message"], 'success' if res["success"] else 'danger')
    if res["success"]:
        return redirect(url_for('admin.workers'))
    return render_template('/views/admin/worker_form.html',
                           worker=worker, categories=categories, is_edit=True,
                           form_data=request.form)

@admin_bp.route('/workers/<worker_id>/toggle', methods=['POST'])
@role_required('admin')
def toggle_worker(worker_id):
    result = WorkerService.toggle_active(worker_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.workers'))

@admin_bp.route('/workers/<worker_id>/schedule', methods=['GET', 'POST'])
@role_required('admin')
def worker_schedule(worker_id):
    from models.workerModel import DAYS_OF_WEEK
    result = WorkerService.get_worker_by_id(worker_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('admin.workers'))

    worker = result["worker"]
    if request.method == 'GET':
        return render_template('/views/admin/worker_schedule.html',
                               worker=worker, days=DAYS_OF_WEEK)

    # Reconstruir availability desde el form
    availability = {}
    for day in DAYS_OF_WEEK:
        starts = request.form.getlist(f"{day}_start[]")
        ends   = request.form.getlist(f"{day}_end[]")
        slots  = []
        for s, e in zip(starts, ends):
            if s and e:
                slots.append({"start": s, "end": e})
        if slots:
            availability[day] = slots

    res = WorkerService.update_availability(worker["user_id"], availability)
    flash(res["message"], 'success' if res["success"] else 'danger')
    return redirect(url_for('admin.workers'))


# ──────────────────────────────────────────
# GESTIÓN DE CITAS
# ──────────────────────────────────────────
@admin_bp.route('/appointments', methods=['GET'])
@role_required('admin')
def appointments():
    all_appts = AppointmentService.get_all_appointments().get("appointments", [])

    promo_groups = {}
    standalone   = []
    for appt in all_appts:
        cid = appt.get("combo_instance_id")
        if cid:
            if cid not in promo_groups:
                promo_groups[cid] = {
                    "row_type":          "combo",
                    "combo_instance_id": cid,
                    "promotion_id":      appt.get("promotion_id"),
                    "promotion_name":    appt.get("promotion_name", "Promoción"),
                    "client_name":       appt["client_name"],
                    "status":            appt["status"],
                    "group_total":       0.0,
                    "entries":           []
                }
            promo_groups[cid]["entries"].append(appt)
            promo_groups[cid]["group_total"] = round(
                promo_groups[cid]["group_total"] + appt["total_price"], 2
            )
        else:
            appt["row_type"] = "standalone"
            standalone.append(appt)

    def _dt_str(dt):
        if dt is None: return "0000-00-00 00:00:00"
        return dt.strftime("%Y-%m-%d %H:%M:%S") if hasattr(dt, 'strftime') else str(dt)

    rows = []
    for g in promo_groups.values():
        g["sort_key"]       = max(e["created_at"] for e in g["entries"] if e["created_at"])
        g["sort_order_str"] = _dt_str(g["sort_key"])
        g["sort_appt_str"]  = min(f"{e['date']} {e['start_time']}" for e in g["entries"])
        rows.append(g)
    for a in standalone:
        a["sort_key"]       = a["created_at"]
        a["sort_order_str"] = _dt_str(a["created_at"])
        a["sort_appt_str"]  = f"{a['date']} {a['start_time']}"
        rows.append(a)
    rows.sort(key=lambda x: x["sort_key"], reverse=True)

    return render_template('/views/admin/appointments.html', rows=rows)


# ──────────────────────────────────────────
# GESTIÓN DE PROMOCIONES
# ──────────────────────────────────────────
def _upload_folder_promotions(app):
    return os.path.join(app.static_folder, 'img', 'promotions')

@admin_bp.route('/promotions', methods=['GET'])
@role_required('admin')
def promotions():
    result = PromotionService.get_all_promotions()
    return render_template('/views/admin/promotions.html', promotions=result.get("promotions", []))

@admin_bp.route('/promotions/new', methods=['GET', 'POST'])
@role_required('admin')
def create_promotion():
    import json
    from flask import current_app
    services = ServiceService.get_all_services(only_active=True).get("services", [])
    if request.method == 'GET':
        services_json = json.dumps([
            {"id": s["id"], "name": s["name"], "category": s["category"],
             "price": s["price"], "duration": s["duration_minutes"]}
            for s in services
        ])
        return render_template('/views/admin/promotion_form.html',
                               promotion=None, services=services, services_json=services_json)

    upload_folder = _upload_folder_promotions(current_app)
    os.makedirs(upload_folder, exist_ok=True)
    result = PromotionService.create_promotion(
        name=request.form.get('name', '').strip(),
        description=request.form.get('description', '').strip(),
        service_ids=request.form.getlist('service_ids'),
        promo_price=request.form.get('promo_price', '0'),
        image_file=request.files.get('image'),
        upload_folder=upload_folder
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('admin.promotions'))
    services_json = json.dumps([
        {"id": s["id"], "name": s["name"], "category": s["category"],
         "price": s["price"], "duration": s["duration_minutes"]}
        for s in services
    ])
    return render_template('/views/admin/promotion_form.html', promotion=None,
                           services=services, services_json=services_json,
                           form_data=request.form)

@admin_bp.route('/promotions/<promo_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_promotion(promo_id):
    import json
    from flask import current_app
    result = PromotionService.get_promotion_by_id(promo_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('admin.promotions'))

    promotion = result["promotion"]
    services = ServiceService.get_all_services(only_active=True).get("services", [])
    services_json = json.dumps([
        {"id": s["id"], "name": s["name"], "category": s["category"],
         "price": s["price"], "duration": s["duration_minutes"]}
        for s in services
    ])

    if request.method == 'GET':
        return render_template('/views/admin/promotion_form.html',
                               promotion=promotion, services=services,
                               services_json=services_json)

    upload_folder = _upload_folder_promotions(current_app)
    os.makedirs(upload_folder, exist_ok=True)
    is_active = request.form.get('is_active') == 'on'
    result = PromotionService.update_promotion(
        promo_id=promo_id,
        name=request.form.get('name', '').strip(),
        description=request.form.get('description', '').strip(),
        service_ids=request.form.getlist('service_ids'),
        promo_price=request.form.get('promo_price', '0'),
        is_active=is_active,
        image_file=request.files.get('image'),
        upload_folder=upload_folder
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('admin.promotions'))
    return render_template('/views/admin/promotion_form.html', promotion=promotion,
                           services=services, services_json=services_json,
                           form_data=request.form)

@admin_bp.route('/promotions/<promo_id>/delete', methods=['POST'])
@role_required('admin')
def delete_promotion(promo_id):
    result = PromotionService.delete_promotion(promo_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.promotions'))


# ──────────────────────────────────────────
# GESTIÓN DE TESTIMONIOS
# ──────────────────────────────────────────
@admin_bp.route('/testimonials', methods=['GET'])
@role_required('admin')
def testimonials():
    result = TestimonialService.get_all()
    return render_template('/views/admin/testimonials.html',
                           testimonials=result.get("testimonials", []))

@admin_bp.route('/testimonials/<testimonial_id>/approve', methods=['POST'])
@role_required('admin')
def approve_testimonial(testimonial_id):
    result = TestimonialService.approve(testimonial_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.testimonials'))

@admin_bp.route('/testimonials/<testimonial_id>/delete', methods=['POST'])
@role_required('admin')
def delete_testimonial(testimonial_id):
    result = TestimonialService.delete(testimonial_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.testimonials'))
