from flask import render_template, request, redirect, url_for, Blueprint, flash, session
from utils.authDecorator import login_required, role_required
from services.appointmentService import AppointmentService

appointment_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointment_bp.route('/', methods=['GET'])
@login_required
def my_appointments():
    user_id = session.get("user_id")
    result  = AppointmentService.get_client_appointments(user_id)
    pending_reschedules = AppointmentService.count_pending_reschedules(user_id)
    return render_template('/views/appointments/list.html',
                           appointments=result.get("appointments", []),
                           pending_reschedules=pending_reschedules)

@appointment_bp.route('/<appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    user_id = session.get("user_id")
    result  = AppointmentService.cancel_appointment(appointment_id, user_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('appointments.my_appointments'))

@appointment_bp.route('/<appointment_id>/accept-reschedule', methods=['POST'])
@login_required
def accept_reschedule(appointment_id):
    """Cliente acepta la propuesta de reagendamiento de la trabajadora."""
    user_id = session.get("user_id")
    result  = AppointmentService.accept_reschedule(appointment_id, user_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('appointments.my_appointments'))

@appointment_bp.route('/<appointment_id>/reject-reschedule', methods=['POST'])
@login_required
def reject_reschedule(appointment_id):
    """Cliente rechaza la propuesta; la cita vuelve a su horario original."""
    user_id = session.get("user_id")
    result  = AppointmentService.reject_reschedule(appointment_id, user_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('appointments.my_appointments'))
