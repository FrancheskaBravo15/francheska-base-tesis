from flask import request, redirect, url_for, Blueprint, flash, session
from utils.authDecorator import login_required
from services.reviewService import ReviewService

review_bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@review_bp.route('/add', methods=['POST'])
@login_required
def add():
    user_id    = session.get("user_id")
    service_id = request.form.get('service_id')
    rating     = request.form.get('rating')
    comment    = request.form.get('comment', '')

    result = ReviewService.add_review(service_id, user_id, rating, comment)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('services.detail', service_id=service_id))

@review_bp.route('/<review_id>/delete', methods=['POST'])
@login_required
def delete(review_id):
    from repositories.userRepository import UserRepository
    user_id   = session.get("user_id")
    user      = UserRepository.find_by_id(user_id)
    is_admin  = user and user.role == 'admin'
    service_id = request.form.get('service_id')

    result = ReviewService.delete_review(review_id, user_id, is_admin=is_admin)
    flash(result["message"], 'success' if result["success"] else 'danger')
    if service_id:
        return redirect(url_for('services.detail', service_id=service_id))
    return redirect(url_for('services.catalog'))
