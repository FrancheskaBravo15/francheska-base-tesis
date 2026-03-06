from flask import render_template, request, redirect, url_for, Blueprint, session, flash
from services.userService import UserService
from utils.authDecorator import login_required, guest_only

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

@user_bp.route('/register', methods=['GET', 'POST']) # /users/register
@guest_only
def register():
    # Registrar usuario

    if request.method == 'GET':
        return render_template('/views/users/register.html')
    else:        
        identification = request.form.get('identification', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        result = UserService.create_user(identification,first_name,last_name,email,password)

        if(result['success']):
            print(f"Creado correctamente {result['message']}")
            return redirect(url_for('index.indexRoute'))
        else:
            print("Existe un error")
            return render_template('/views/users/register.html')

@user_bp.route('/login', methods=['GET', 'POST']) # /users/login
@guest_only   
def login():
    #Login de usuario
    if request.method == 'GET':
        return render_template('/views/users/login.html')
    else:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        result = UserService.login_user(email, password)

        if result["success"]:
            session["user_id"] = result["user_id"]
            flash(result["message"], 'success')
            return redirect(url_for('index.indexRoute'))
        else:
            flash(result["message"], 'danger')
            return render_template('/views/users/login.html', email=email)

@user_bp.route('/logout', methods=['POST']) # /users/logout
@login_required
def logout():
    #Cerrar sesión
    session.pop("user_id", None)
    flash("Sesión cerrada exitosamente", 'info')
    return redirect(url_for('users.login'))

@user_bp.route('/profile', methods=['GET']) # /users/profile
@login_required
def profile():
    # Perfil del usuario
    if request.method == 'GET':
        return render_template('/views/users/profile.html')