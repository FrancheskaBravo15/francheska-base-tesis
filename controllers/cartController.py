from flask import render_template, request, redirect, url_for, Blueprint, flash, session, jsonify
from utils.authDecorator import login_required
from services.cartService import CartService

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


@cart_bp.route('/', methods=['GET'])
@login_required
def view_cart():
    user_id = session.get("user_id")
    result  = CartService.get_cart(user_id)
    items   = result.get("items", [])
    total   = result.get("total", 0)

    # Agrupar ítems para visualización
    promo_groups  = {}
    standalone    = []

    for idx, item in enumerate(items):
        pid = item.get("promotion_id")
        if pid:
            if pid not in promo_groups:
                promo_groups[pid] = {
                    "promotion_id":   pid,
                    "promotion_name": item.get("promotion_name", "Promoción"),
                    "entries":        [],
                    "group_total":    0.0
                }
            promo_groups[pid]["entries"].append({"index": idx, "item": item})
            promo_groups[pid]["group_total"] = round(
                promo_groups[pid]["group_total"] + item["price"], 2
            )
        else:
            standalone.append({"index": idx, "item": item})

    return render_template('/views/cart/cart.html',
                           items=items,
                           total=total,
                           promo_groups=list(promo_groups.values()),
                           standalone_items=standalone)


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


@cart_bp.route('/add-promotion', methods=['POST'])
@login_required
def add_promotion():
    user_id = session.get("user_id")
    data    = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Datos inválidos"}), 400

    result = CartService.add_promotion_to_cart(
        user_id      = user_id,
        promotion_id = data.get("promotion_id"),
        promo_name   = data.get("promo_name"),
        promo_price  = float(data.get("promo_price", 0)),
        selections   = data.get("selections", [])
    )
    return jsonify(result)


@cart_bp.route('/remove/<int:item_index>', methods=['POST'])
@login_required
def remove(item_index):
    user_id = session.get("user_id")
    result  = CartService.remove_from_cart(user_id, item_index)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove-promotion/<promotion_id>', methods=['POST'])
@login_required
def remove_promotion(promotion_id):
    user_id = session.get("user_id")
    result  = CartService.remove_promotion_from_cart(user_id, promotion_id)
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
