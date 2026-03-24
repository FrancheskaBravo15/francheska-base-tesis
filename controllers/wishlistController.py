from flask import render_template, request, redirect, url_for, Blueprint, flash, session, jsonify
from utils.authDecorator import login_required
from services.wishlistService import WishlistService

wishlist_bp = Blueprint('wishlist', __name__, url_prefix='/wishlist')

@wishlist_bp.route('/', methods=['GET'])
@login_required
def view():
    user_id = session.get("user_id")
    result  = WishlistService.get_wishlist(user_id)
    return render_template('/views/wishlist/wishlist.html',
                           services=result.get("services", []))

@wishlist_bp.route('/toggle', methods=['POST'])
@login_required
def toggle():
    user_id    = session.get("user_id")
    service_id = request.form.get('service_id')
    result     = WishlistService.toggle(user_id, service_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    # Volver a la página anterior o al catálogo
    return redirect(request.referrer or url_for('services.catalog'))
