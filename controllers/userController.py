from flask import render_template, request, redirect, url_for, Blueprint, session, flash, current_app
from services.userService import UserService
from utils.authDecorator import login_required, guest_only
import os

user_bp = Blueprint('users', __name__, url_prefix='/users')

@user_bp.app_context_processor
def inject_current_user():
    user_id = session.get("user_id")
    if user_id:
        result = UserService.get_user_by_id(user_id)
        if result["success"]:
            return {"current_user": result["user"]}
        session.pop("user_id", None)
    return {"current_user": None}

@user_bp.app_context_processor
def inject_cart_count():
    user_id = session.get("user_id")
    if user_id:
        try:
            from services.cartService import CartService
            cart = CartService.get_cart(user_id)
            return {"cart_count": cart.get("count", 0)}
        except Exception:
            pass
    return {"cart_count": 0}

@user_bp.app_context_processor
def inject_wishlist_count():
    user_id = session.get("user_id")
    if user_id:
        try:
            from repositories.wishlistRepository import WishlistRepository
            wl = WishlistRepository.find_by_user_id(user_id)
            return {"wishlist_count": len(wl.service_ids) if wl else 0}
        except Exception:
            pass
    return {"wishlist_count": 0}

@user_bp.app_context_processor
def inject_reschedule_count():
    """Inyecta en todos los templates el nro. de reagendamientos pendientes del cliente."""
    user_id = session.get("user_id")
    if user_id:
        try:
            from services.appointmentService import AppointmentService
            result = UserService.get_user_by_id(user_id)
            if result["success"] and result["user"].get("role") == "client":
                count = AppointmentService.count_pending_reschedules(user_id)
                return {"reschedule_count": count}
        except Exception:
            pass
    return {"reschedule_count": 0}

@user_bp.route('/register', methods=['GET', 'POST'])
@guest_only
def register():
    if request.method == 'GET':
        return render_template('/views/users/register.html')

    identification = request.form.get('identification', '').strip()
    first_name     = request.form.get('first_name', '').strip()
    last_name      = request.form.get('last_name', '').strip()
    phone          = request.form.get('phone', '').strip()
    email          = request.form.get('email', '').strip()
    password       = request.form.get('password', '')

    result = UserService.create_user(identification, first_name, last_name, phone, email, password)

    if result['success']:
        flash(result['message'], 'success')
        return redirect(url_for('users.login'))
    else:
        flash(result['message'], 'danger')
        return render_template('/views/users/register.html',
                               identification=identification,
                               first_name=first_name,
                               last_name=last_name,
                               phone=phone,
                               email=email)

@user_bp.route('/login', methods=['GET', 'POST'])
@guest_only
def login():
    if request.method == 'GET':
        return render_template('/views/users/login.html')

    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    result = UserService.login_user(email, password)

    if result["success"]:
        session["user_id"] = result["user_id"]
        flash(result["message"], 'success')
        # Redirección según rol
        user_result = UserService.get_user_by_id(result["user_id"])
        if user_result["success"]:
            role = user_result["user"].get("role")
            if role == "admin":
                return redirect(url_for('admin.panel'))
            if role == "worker":
                return redirect(url_for('worker.dashboard'))
        return redirect(url_for('index.indexRoute'))
    else:
        flash(result["message"], 'danger')
        return render_template('/views/users/login.html', email=email)

@user_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop("user_id", None)
    flash("Sesión cerrada exitosamente", 'info')
    return redirect(url_for('users.login'))

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session.get("user_id")
    if request.method == 'GET':
        return render_template('/views/users/profile.html')

    first_name  = request.form.get('first_name', '').strip()
    last_name   = request.form.get('last_name', '').strip()
    phone       = request.form.get('phone', '').strip()
    photo_file  = request.files.get('profile_photo')
    upload_folder = os.path.join(current_app.static_folder, 'img', 'profiles')

    result = UserService.update_profile(user_id, first_name, last_name, phone,
                                        photo_file=photo_file,
                                        upload_folder=upload_folder)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('users.profile'))


@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    user_id          = session.get("user_id")
    current_password = request.form.get('current_password', '')
    new_password     = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    result = UserService.change_password(user_id, current_password, new_password, confirm_password)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('users.profile'))


@user_bp.route('/forgot-password', methods=['GET', 'POST'])
@guest_only
def forgot_password():
    if request.method == 'GET':
        return render_template('/views/users/forgot_password.html')

    email     = request.form.get('email', '').strip().lower()
    reset_url = url_for('users.reset_password', token='__TOKEN__', _external=True)
    result    = UserService.request_password_reset(email, reset_url)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return render_template('/views/users/forgot_password.html', sent=True)


@user_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@guest_only
def reset_password(token):
    if request.method == 'GET':
        return render_template('/views/users/reset_password.html', token=token)

    new_password     = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    result = UserService.reset_password(token, new_password, confirm_password)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('users.login'))

    flash(result["message"], 'danger')
    return render_template('/views/users/reset_password.html', token=token)
