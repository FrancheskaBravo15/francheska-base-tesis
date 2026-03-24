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
