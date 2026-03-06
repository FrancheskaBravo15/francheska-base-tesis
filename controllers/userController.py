from flask import render_template, request, redirect, url_for, Blueprint
from services.userService import UserService

user_bp = Blueprint('users', __name__, url_prefix='/users')

@user_bp.route('/register', methods=['GET', 'POST']) # /users/register
def register():
    # Registrar usuario

    if request.method == 'GET':
        return render_template('/views/users/register.html')
    else:        
        identification = request.form.get('identification', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        result = UserService.create_user(identification,first_name,last_name,email,password)

        if(result['success']):
            print(f"Creado correctamente {result['message']}")
            return redirect(url_for('index.indexRoute'))
        else:
            print("Existe un error")
            return render_template('/views/users/register.html')