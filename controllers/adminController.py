from flask import render_template, request, redirect, url_for, Blueprint, flash
from utils.authDecorator import role_required
from services.userService import UserService
from services.serviceService import ServiceService
from services.workerService import WorkerService
from services.appointmentService import AppointmentService
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def _upload_folder_services(app):
    return os.path.join(app.static_folder, 'img', 'services')

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
        categories = ServiceService.get_categories()
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
    categories = ServiceService.get_categories()
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
        categories = ServiceService.get_categories()
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
    return redirect(url_for('admin.services'))

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
    categories = ServiceService.get_categories()
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
    result = AppointmentService.get_all_appointments()
    return render_template('/views/admin/appointments.html',
                           appointments=result.get("appointments", []))
