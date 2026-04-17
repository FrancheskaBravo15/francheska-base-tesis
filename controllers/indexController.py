from flask import render_template, Blueprint
from services.serviceService import ServiceService
from services.reviewService import ReviewService

index_bp = Blueprint("index", __name__, url_prefix='/')

@index_bp.route('/', methods=['GET'])
def indexRoute():
    # Mostrar servicios destacados en el inicio (primeros 6 activos)
    result    = ServiceService.get_all_services(only_active=True)
    services  = result.get("services", [])[:6]
    categories = ServiceService.get_categories()
    return render_template('/views/index.html', services=services, categories=categories)

@index_bp.route('/about', methods=['GET'])
def aboutRoute():
    return render_template('/views/about.html')
