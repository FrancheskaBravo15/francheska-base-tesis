from flask import render_template, request, redirect, url_for, Blueprint, flash, session
from utils.authDecorator import role_required
from services.workerService import WorkerService
from services.appointmentService import AppointmentService
from models.workerModel import DAYS_OF_WEEK

worker_bp = Blueprint('worker', __name__, url_prefix='/worker')

@worker_bp.route('/dashboard', methods=['GET'])
@role_required('worker')
def dashboard():
    user_id = session.get("user_id")
    result  = WorkerService.get_worker_by_user_id(user_id)
    history = WorkerService.get_worker_history(user_id)
    today_appts = [a for a in history.get("appointments", []) if a["status"] == "confirmada"]
    return render_template('/views/worker/dashboard.html',
                           worker=result.get("worker"),
                           today_appointments=today_appts,
                           total_earned=history.get("total_earned", 0))

@worker_bp.route('/schedule', methods=['GET', 'POST'])
@role_required('worker')
def schedule():
    user_id = session.get("user_id")
    result  = WorkerService.get_worker_by_user_id(user_id)
    if not result["success"]:
        flash("Perfil de trabajadora no encontrado", 'danger')
        return redirect(url_for('index.indexRoute'))

    worker = result["worker"]
    if request.method == 'GET':
        return render_template('/views/worker/schedule.html',
                               worker=worker, days=DAYS_OF_WEEK)

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

    res = WorkerService.update_availability(user_id, availability)
    flash(res["message"], 'success' if res["success"] else 'danger')
    return redirect(url_for('worker.schedule'))

@worker_bp.route('/appointments', methods=['GET'])
@role_required('worker')
def appointments():
    user_id = session.get("user_id")
    history = WorkerService.get_worker_history(user_id)
    return render_template('/views/worker/appointments.html',
                           appointments=history.get("appointments", []),
                           total_earned=history.get("total_earned", 0))

@worker_bp.route('/appointments/<appointment_id>/complete', methods=['POST'])
@role_required('worker')
def complete_appointment(appointment_id):
    result = AppointmentService.complete_appointment(appointment_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('worker.appointments'))
