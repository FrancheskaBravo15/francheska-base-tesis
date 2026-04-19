import os, uuid, json, urllib.request, urllib.error
from flask import Blueprint, request, redirect, url_for, flash, session, render_template

payment_bp = Blueprint('payments', __name__, url_prefix='/payments')


@payment_bp.route('/payphone/response', methods=['GET'])
def payphone_response():
    """Payphone redirige aquí después del pago con ?id=X&clientTransactionId=Y."""
    tx_id        = request.args.get('id', 0, type=int)
    client_tx_id = request.args.get('clientTransactionId', '')

    user_id = session.get('user_id')
    if not user_id:
        flash("Tu sesión expiró. Inicia sesión e intenta de nuevo.", "danger")
        return redirect(url_for('users.login'))

    # Verificar que el clientTransactionId pertenece a esta sesión
    if client_tx_id != session.get('payphone_client_tx_id', ''):
        flash("Transacción inválida o expirada.", "danger")
        return redirect(url_for('cart.view_cart'))

    token = os.getenv('PAYPHONE_TOKEN', '')

    try:
        payload = json.dumps({"id": tx_id, "clientTxId": client_tx_id}).encode("utf-8")
        req = urllib.request.Request(
            "https://pay.payphonetodoesposible.com/api/button/V2/Confirm",
            data=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        data = json.loads(e.read().decode("utf-8"))
    except Exception as e:
        flash(f"Error al confirmar el pago con Payphone: {e}", "danger")
        return redirect(url_for('cart.view_cart'))

    session.pop('payphone_client_tx_id', None)

    if data.get('statusCode') == 3 and data.get('transactionStatus') == 'Approved':
        from services.cartService import CartService
        result = CartService.checkout(
            user_id=user_id,
            payment_method='payphone',
            payphone_client_tx_id=client_tx_id,
            payphone_transaction_id=data.get('transactionId'),
            payphone_auth_code=data.get('authorizationCode', ''),
        )
        flash(result["message"], 'success' if result["success"] else 'danger')
        if result["success"]:
            return redirect(url_for('appointments.my_appointments'))
        return redirect(url_for('cart.view_cart'))
    else:
        msg = data.get('message') or 'Pago no aprobado por Payphone.'
        flash(f"Pago rechazado: {msg}", "danger")
        return redirect(url_for('cart.view_cart'))
