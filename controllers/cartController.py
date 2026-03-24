from flask import render_template, request, redirect, url_for, Blueprint, flash, session, jsonify
from utils.authDecorator import login_required
from services.cartService import CartService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/', methods=['GET'])
@login_required
def view_cart():
    user_id = session.get("user_id")
    result  = CartService.get_cart(user_id)
    return render_template('/views/cart/cart.html',
                           items=result.get("items", []),
                           total=result.get("total", 0))

@cart_bp.route('/add', methods=['POST'])
@login_required
def add():
    user_id    = session.get("user_id")
    service_id = request.form.get('service_id')
    worker_id  = request.form.get('worker_id')
    date       = request.form.get('date')
    start_time = request.form.get('start_time')

    result = CartService.add_to_cart(user_id, service_id, worker_id, date, start_time)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remove/<int:item_index>', methods=['POST'])
@login_required
def remove(item_index):
    user_id = session.get("user_id")
    result  = CartService.remove_from_cart(user_id, item_index)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    user_id = session.get("user_id")
    result  = CartService.checkout(user_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('appointments.my_appointments'))
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/clear', methods=['POST'])
@login_required
def clear():
    user_id = session.get("user_id")
    CartService.clear_cart(user_id)
    flash("Carrito vaciado", 'info')
    return redirect(url_for('cart.view_cart'))
