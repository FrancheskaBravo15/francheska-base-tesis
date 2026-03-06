from flask import render_template, Blueprint
from services.userService import UserService

index_bp = Blueprint("index", __name__, url_prefix='/')

@index_bp.route('/', methods=['GET'])
def indexRoute():
    return render_template('/views/index.html')

@index_bp.route('/about', methods=['GET'])
def aboutRoute():
    users_data = UserService.get_all_users()
    print(users_data["users"])
    return render_template('/views/about.html')
