from flask import render_template, request, redirect, url_for, Blueprint, flash, session, jsonify
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

@worker_bp.route('/appointments/<appointment_id>/reschedule', methods=['POST'])
@role_required('worker')
def reschedule_appointment(appointment_id):
    """La trabajadora propone un nuevo horario para una cita confirmada."""
    user_id        = session.get("user_id")
    proposed_date  = request.form.get('proposed_date', '').strip()
    proposed_start = request.form.get('proposed_start_time', '').strip()
    reason         = request.form.get('reason', '').strip()

    result = AppointmentService.propose_reschedule(
        appointment_id    = appointment_id,
        worker_user_id    = user_id,
        proposed_date     = proposed_date,
        proposed_start_time = proposed_start,
        reason            = reason
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('worker.appointments'))

@worker_bp.route('/appointments/<appointment_id>/slots', methods=['GET'])
@role_required('worker')
def reschedule_slots(appointment_id):
    """
    API interna: devuelve slots disponibles para una cita específica en una fecha dada.
    Usado por el modal de reagendamiento (evita exponer service_slug al template).
    """
    from repositories.appointmentRepository import AppointmentRepository
    from repositories.serviceRepository import ServiceRepository

    date = request.args.get('date', '').strip()
    if not date:
        return jsonify({"success": False, "slots": [], "message": "Fecha requerida"})

    try:
        appt = AppointmentRepository.find_by_id(appointment_id)
        if not appt:
            return jsonify({"success": False, "slots": [], "message": "Cita no encontrada"})

        service = ServiceRepository.find_by_id(appt.service_id)
        if not service:
            return jsonify({"success": False, "slots": [], "message": "Servicio no encontrado"})

        result = WorkerService.get_available_slots(
            appt.worker_id, date, service.duration_minutes, service.category
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "slots": [], "message": f"Error: {e}"})
