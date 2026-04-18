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

    appointments = result.get("appointments", [])

    promo_groups = {}
    standalone   = []
    for appt in appointments:
        cid = appt.get("combo_instance_id")
        if cid:
            if cid not in promo_groups:
                promo_groups[cid] = {
                    "row_type":          "combo",
                    "combo_instance_id": cid,
                    "promotion_id":      appt.get("promotion_id"),
                    "promotion_name":    appt.get("promotion_name", "Promoción"),
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

    rows = []
    for g in promo_groups.values():
        g["sort_key"] = max(e["created_at"] for e in g["entries"])
        rows.append(g)
    for a in standalone:
        a["sort_key"] = a["created_at"]
        rows.append(a)
    rows.sort(key=lambda x: x["sort_key"], reverse=True)

    return render_template('/views/appointments/list.html',
                           rows=rows,
                           pending_reschedules=pending_reschedules)

@appointment_bp.route('/cancel-group/<combo_instance_id>', methods=['POST'])
@login_required
def cancel_group(combo_instance_id):
    user_id = session.get("user_id")
    result  = AppointmentService.cancel_group(combo_instance_id, user_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('appointments.my_appointments'))

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
