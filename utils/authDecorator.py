from functools import wraps
from flask import session, flash, redirect, url_for, abort
from repositories.userRepository import UserRepository

def login_required(f):
    #Requiere que el usuario tenga una sesión activa para acceder a una ruta
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            flash('Debes iniciar sesión para acceder a esta página','warning')
            return redirect(url_for('users.login')) #login
        return f(*args, **kwargs)
    return decorated_function

def guest_only(f):
    #Solo permite acceso a usuarios que No tienen una sesión activa
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id'):
            return redirect(url_for('index.indexRoute'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    #Requiere que el usuario tenga el rol indicado
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                flash('Debes iniciar sesión para acceder a esta página','warning')
                return redirect(url_for('users.login')) #login
            user = UserRepository.find_by_id(user_id)
            if not user or user.role not in roles:
                abort(401)
            return f(*args, **kwargs)
        return decorated_function
    return decorator