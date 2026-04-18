from flask import render_template, Blueprint
from services.promotionService import PromotionService

promotion_bp = Blueprint('promotions', __name__, url_prefix='/promotions')


@promotion_bp.route('/', methods=['GET'])
def list_promotions():
    result = PromotionService.get_all_promotions(only_active=True)
    return render_template('/views/promotions/list.html',
                           promotions=result.get("promotions", []))


@promotion_bp.route('/<promo_id>', methods=['GET'])
def detail(promo_id):
    result = PromotionService.get_promotion_by_id(promo_id)
    if not result["success"]:
        from flask import flash, redirect, url_for
        flash(result["message"], 'danger')
        return redirect(url_for('promotions.list_promotions'))
    return render_template('/views/promotions/detail.html',
                           promotion=result["promotion"])
