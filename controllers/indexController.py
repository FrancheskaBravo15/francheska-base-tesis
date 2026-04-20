from flask import render_template, Blueprint, request, flash, redirect, url_for
from services.serviceService import ServiceService
from services.categoryService import CategoryService
from services.testimonialService import TestimonialService
from services.promotionService import PromotionService

index_bp = Blueprint("index", __name__, url_prefix='/')

@index_bp.route('/', methods=['GET'])
def indexRoute():
    result       = ServiceService.get_all_services(only_active=True)
    services     = result.get("services", [])[:6]
    categories   = CategoryService.get_all_categories().get("categories", [])
    testimonials = TestimonialService.get_approved(limit=3).get("testimonials", [])
    promotions   = PromotionService.get_all_promotions(only_active=True).get("promotions", [])[:3]
    return render_template('/views/index.html', services=services,
                           categories=categories, testimonials=testimonials,
                           promotions=promotions)

@index_bp.route('/about', methods=['GET'])
def aboutRoute():
    return render_template('/views/about.html')

@index_bp.route('/testimonials/submit', methods=['POST'])
def submit_testimonial():
    result = TestimonialService.submit(
        author_name=request.form.get('author_name', '').strip(),
        rating=request.form.get('rating', '5'),
        comment=request.form.get('comment', '').strip()
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect('/about#testimonial-form')
