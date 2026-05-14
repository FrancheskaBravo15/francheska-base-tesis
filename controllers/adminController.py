from flask import render_template, request, redirect, url_for, Blueprint, flash, jsonify
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
    import json
    from collections import defaultdict
    from datetime import datetime, date

    AppointmentService.expire_overdue_pending()

    users_result    = UserService.get_all_users_with_persons()
    appts_result    = AppointmentService.get_all_appointments()
    workers_result  = WorkerService.get_all_workers()
    services_result = ServiceService.get_all_services()

    appointments = appts_result.get("appointments", [])

    stats = {
        "total_users":    len(users_result.get("users", [])),
        "total_workers":  len(workers_result.get("workers", [])),
        "total_services": len(services_result.get("services", [])),
        "total_appts":    len(appointments),
        "pending_appts":  sum(1 for a in appointments if a["status"] == "confirmada"),
        "total_revenue":  sum(a["total_price"] for a in appointments if a["status"] == "completada"),
    }

    # ── Datos crudos para Chart.js (JS filtrará por período) ──────────────────
    chart_rows = []
    for a in appointments:
        dt = a.get("created_at")
        if dt is None:
            continue
        if hasattr(dt, "strftime"):
            date_str = dt.strftime("%Y-%m-%d")
        else:
            date_str = str(dt)[:10]
        chart_rows.append({
            "date":     date_str,
            "status":   a["status"],
            "payment":  a.get("payment_method") or "otro",
            "price":    float(a["total_price"]) if a["status"] == "completada" else 0,
            "category": a.get("service_category") or "N/A",
            "worker":   a.get("worker_name") or "N/A",
        })

    return render_template('/views/admin/panel.html',
                           stats=stats,
                           chart_data=json.dumps(chart_rows, ensure_ascii=False))


@admin_bp.route('/reports', methods=['GET'])
@role_required('admin')
def reports():
    from datetime import datetime, date, timedelta
    from collections import defaultdict

    period = request.args.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30

    appts_result    = AppointmentService.get_all_appointments()
    workers_result  = WorkerService.get_all_workers()
    users_result    = UserService.get_all_users_with_persons()
    services_result = ServiceService.get_all_services()
    all_appts       = appts_result.get("appointments", [])

    if days > 0:
        cutoff = date.today() - timedelta(days=days)
        appts = [a for a in all_appts if a.get("created_at") and
                 (a["created_at"].date() if hasattr(a["created_at"], "date") else
                  date.fromisoformat(str(a["created_at"])[:10])) >= cutoff]
    else:
        appts = all_appts

    # Conteo por estado
    by_status = defaultdict(int)
    for a in appts:
        by_status[a["status"]] += 1

    # Ingresos y citas por trabajadora
    by_worker = defaultdict(lambda: {"citas": 0, "ingresos": 0.0})
    for a in appts:
        w = a.get("worker_name") or "N/A"
        by_worker[w]["citas"] += 1
        if a["status"] == "completada":
            by_worker[w]["ingresos"] += a["total_price"]

    # Citas por categoría
    by_category = defaultdict(int)
    for a in appts:
        by_category[a.get("service_category") or "N/A"] += 1

    # Ingresos por mes
    by_month = defaultdict(float)
    for a in appts:
        if a["status"] == "completada" and a.get("created_at"):
            dt = a["created_at"]
            key = dt.strftime("%Y-%m") if hasattr(dt, "strftime") else str(dt)[:7]
            by_month[key] += a["total_price"]

    total_revenue   = sum(a["total_price"] for a in appts if a["status"] == "completada")
    total_completed = by_status.get("completada", 0)
    total_cancelled = by_status.get("cancelada", 0)
    total_no_show   = by_status.get("no_asistio", 0)

    return render_template('/views/admin/reports.html',
        period=days,
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total_appts=len(appts),
        total_revenue=total_revenue,
        total_completed=total_completed,
        total_cancelled=total_cancelled,
        total_no_show=total_no_show,
        total_users=len([u for u in users_result.get("users", []) if u["role"] == "client"]),
        total_workers=len(workers_result.get("workers", [])),
        total_services=len(services_result.get("services", [])),
        by_status=dict(by_status),
        by_worker=dict(by_worker),
        by_category=dict(by_category),
        by_month=dict(sorted(by_month.items())),
    )


@admin_bp.route('/reports/daily', methods=['GET'])
@role_required('admin')
def daily_report():
    from datetime import date as _date, datetime
    from collections import defaultdict
    from repositories.appointmentRepository import AppointmentRepository
    from repositories.personRepository import PersonRepository
    from repositories.userRepository import UserRepository as UR
    from repositories.serviceRepository import ServiceRepository
    from repositories.workerRepository import WorkerRepository

    date_str = request.args.get('date', _date.today().isoformat())

    raw = AppointmentRepository.find_by_date(date_str)
    appts = [a for a in raw if a.status not in ('cancelada', 'pendiente_reagenda', 'pendiente_validacion')]

    by_worker = defaultdict(list)
    for appt in appts:
        worker     = WorkerRepository.find_by_id(appt.worker_id)
        w_person   = PersonRepository.find_by_user_id(worker.user_id) if worker else None
        c_person   = PersonRepository.find_by_user_id(appt.client_id)
        c_user     = UR.find_by_id(appt.client_id)
        service    = ServiceRepository.find_by_id(appt.service_id)

        worker_name = f"{w_person.first_name} {w_person.last_name}" if w_person else "N/A"
        by_worker[worker_name].append({
            "appointment_id": appt.id,
            "start_time":     appt.start_time,
            "end_time":       appt.end_time,
            "client_name":    f"{c_person.first_name} {c_person.last_name}" if c_person else "N/A",
            "client_phone":   c_person.phone if c_person else "—",
            "client_email":   c_user.email if c_user else "—",
            "service_name":   service.name if service else "N/A",
            "service_category": service.category if service else "N/A",
            "promotion_name": appt.promotion_name,
            "notes":          appt.notes or "",
            "status":         appt.status,
            "total_price":    appt.total_price,
        })

    for worker_name in by_worker:
        by_worker[worker_name].sort(key=lambda x: x["start_time"])

    return render_template('/views/admin/reports_daily.html',
        date_str=date_str,
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        by_worker=dict(sorted(by_worker.items())),
        total_appts=len(appts),
    )


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
@admin_bp.route('/appointments/new', methods=['GET', 'POST'])
@role_required('admin')
def new_appointment():
    if request.method == 'POST':
        client_id      = request.form.get('client_id', '').strip()
        service_id     = request.form.get('service_id', '').strip()
        worker_id      = request.form.get('worker_id', '').strip()
        date           = request.form.get('date', '').strip()
        start_time     = request.form.get('start_time', '').strip()
        payment_method = request.form.get('payment_method', 'efectivo').strip()
        notes          = request.form.get('notes', '').strip()

        if not all([client_id, service_id, worker_id, date, start_time]):
            flash("Todos los campos son obligatorios.", 'danger')
            return redirect(url_for('admin.new_appointment'))

        result = AppointmentService.admin_create_appointment(
            client_id=client_id, worker_id=worker_id, service_id=service_id,
            date=date, start_time=start_time, notes=notes,
            payment_method=payment_method
        )
        flash(result["message"], 'success' if result["success"] else 'danger')
        if result["success"]:
            return redirect(url_for('admin.appointment_detail',
                                    appointment_id=result["appointment_id"]))
        return redirect(url_for('admin.new_appointment'))

    from datetime import date as _date
    clients  = [u for u in UserService.get_all_users_with_persons().get("users", [])
                if u["role"] == "client" and u["is_active"]]
    services = ServiceService.get_all_services(only_active=True).get("services", [])
    workers  = [w for w in WorkerService.get_all_workers().get("workers", [])
                if w["is_active"]]

    return render_template('/views/admin/appointment_new.html',
                           clients=clients, services=services, workers=workers,
                           today_str=_date.today().isoformat())


@admin_bp.route('/appointments/slots', methods=['GET'])
@role_required('admin')
def appointment_slots():
    from repositories.serviceRepository import ServiceRepository
    worker_id  = request.args.get('worker_id', '').strip()
    service_id = request.args.get('service_id', '').strip()
    date       = request.args.get('date', '').strip()
    if not all([worker_id, service_id, date]):
        return jsonify({"success": False, "slots": []})
    try:
        service = ServiceRepository.find_by_id(service_id)
        if not service:
            return jsonify({"success": False, "slots": []})
        result = WorkerService.get_available_slots(
            worker_id, date, service.duration_minutes, service.category
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "slots": [], "message": str(e)})


@admin_bp.route('/appointments', methods=['GET'])
@role_required('admin')
def appointments():
    expired = AppointmentService.expire_overdue_pending()
    if expired.get("expired", 0) > 0:
        flash(
            f"{expired['expired']} reagendamiento(s) vencido(s) cancelado(s) automáticamente "
            f"(el cliente no respondió). Se notificó a los clientes.",
            "warning"
        )
    if expired.get("overdue_paid", 0) > 0:
        flash(
            f"⚠ {expired['overdue_paid']} cita(s) con comprobante pendiente tienen fecha pasada. "
            f"El cliente ya pagó — revísalas y decide si validar o rechazar con devolución.",
            "danger"
        )

    all_appts = AppointmentService.get_all_appointments().get("appointments", [])

    STATUS_PRIORITY = {
        'no_asistio': 0, 'cancelada': 1, 'pendiente_reagenda': 2,
        'completada': 3, 'en_curso': 4, 'pendiente_validacion': 5, 'confirmada': 6,
    }

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
            # Update combo status to reflect worst-case entry status
            current_priority = STATUS_PRIORITY.get(promo_groups[cid]["status"], 99)
            entry_priority   = STATUS_PRIORITY.get(appt["status"], 99)
            if entry_priority < current_priority:
                promo_groups[cid]["status"] = appt["status"]
        else:
            appt["row_type"] = "standalone"
            standalone.append(appt)

    def _dt_str(dt):
        if dt is None: return "0000-00-00 00:00:00"
        return dt.strftime("%Y-%m-%d %H:%M:%S") if hasattr(dt, 'strftime') else str(dt)

    def _sort_key(dt):
        if dt is None or not hasattr(dt, 'strftime'):
            return __import__('datetime').datetime.min
        return dt

    rows = []
    for g in promo_groups.values():
        dts = [e["created_at"] for e in g["entries"] if e.get("created_at") and hasattr(e["created_at"], 'strftime')]
        g["sort_key"]       = max(dts) if dts else __import__('datetime').datetime.min
        g["sort_order_str"] = _dt_str(g["sort_key"])
        g["sort_appt_str"]  = min(f"{e['date']} {e['start_time']}" for e in g["entries"])
        g["detail_id"]      = g["entries"][0]["appointment_id"]
        rows.append(g)
    for a in standalone:
        a["sort_key"]       = _sort_key(a["created_at"])
        a["sort_order_str"] = _dt_str(a["created_at"])
        a["sort_appt_str"]  = f"{a['date']} {a['start_time']}"
        a["detail_id"]      = a["appointment_id"]
        rows.append(a)
    rows.sort(key=lambda x: x["sort_key"], reverse=True)

    from repositories.appointmentRepository import AppointmentRepository
    from datetime import date as _date
    pending_count = AppointmentRepository.count_pending_validation()
    today_str     = _date.today().isoformat()

    return render_template('/views/admin/appointments.html',
                           rows=rows, pending_count=pending_count, today_str=today_str)


@admin_bp.route('/appointments/detail/<appointment_id>', methods=['GET'])
@role_required('admin')
def appointment_detail(appointment_id):
    from services.appointmentService import AppointmentService
    result = AppointmentService.get_appointment_detail(appointment_id, is_admin=True)
    if not result["success"]:
        flash(result["message"], "danger")
        return redirect(url_for('admin.appointments'))
    return render_template('/views/admin/appointment_detail.html',
                           appt=result["appointment"],
                           siblings=result.get("siblings", []))


@admin_bp.route('/appointments/<appointment_id>/validate', methods=['POST'])
@role_required('admin')
def validate_payment(appointment_id):
    from services.appointmentService import AppointmentService
    result = AppointmentService.validate_payment(appointment_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))


@admin_bp.route('/appointments/<appointment_id>/reject', methods=['POST'])
@role_required('admin')
def reject_payment(appointment_id):
    from services.appointmentService import AppointmentService
    result = AppointmentService.reject_payment(appointment_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.appointments'))


@admin_bp.route('/appointments/<appointment_id>/start', methods=['POST'])
@role_required('admin')
def start_appointment(appointment_id):
    from services.appointmentService import AppointmentService
    result = AppointmentService.start_appointment(appointment_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))


@admin_bp.route('/appointments/<appointment_id>/complete', methods=['POST'])
@role_required('admin')
def complete_appointment(appointment_id):
    from services.appointmentService import AppointmentService
    result = AppointmentService.complete_appointment(appointment_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))


@admin_bp.route('/appointments/<appointment_id>/cancel', methods=['POST'])
@role_required('admin')
def cancel_appointment(appointment_id):
    from services.appointmentService import AppointmentService
    from flask import request
    reason = request.form.get('cancel_reason', '')
    result = AppointmentService.cancel_by_admin(appointment_id, reason)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('admin.appointment_detail', appointment_id=appointment_id))


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
        name           = request.form.get('name', '').strip(),
        description    = request.form.get('description', '').strip(),
        service_ids    = request.form.getlist('service_ids'),
        promo_price    = request.form.get('promo_price', '0'),
        image_file     = request.files.get('image'),
        upload_folder  = upload_folder,
        start_datetime = request.form.get('start_datetime', '').strip(),
        end_datetime   = request.form.get('end_datetime', '').strip(),
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
        promo_id       = promo_id,
        name           = request.form.get('name', '').strip(),
        description    = request.form.get('description', '').strip(),
        service_ids    = request.form.getlist('service_ids'),
        promo_price    = request.form.get('promo_price', '0'),
        is_active      = is_active,
        image_file     = request.files.get('image'),
        upload_folder  = upload_folder,
        start_datetime = request.form.get('start_datetime', '').strip(),
        end_datetime   = request.form.get('end_datetime', '').strip(),
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
