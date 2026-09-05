from flask import render_template, request, redirect, url_for, flash
from app.main import bp
from app.models import Product, Category, Review, GalleryImage, SiteSetting
from app.extensions import db


@bp.route('/')
def home():
    featured, categories, reviews, gallery = [], [], [], []
    try:
        featured = Product.query.filter_by(active=True, featured=True).order_by(Product.created_at.desc()).limit(8).all()
        if not featured:
            featured = Product.query.filter_by(active=True).order_by(Product.created_at.desc()).limit(8).all()
        categories = Category.query.filter_by(active=True).order_by(Category.name).all()
        reviews = Review.query.filter_by(approved=True).order_by(Review.created_at.desc()).limit(6).all()
        gallery = GalleryImage.query.filter_by(active=True).order_by(GalleryImage.created_at.desc()).limit(8).all()
    except Exception as e:
        print(f'Home query error: {e}')
    return render_template(
        'home.html',
        featured_products=featured,
        categories=categories,
        reviews=reviews,
        gallery_images=gallery,
    )


@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/gallery')
def gallery():
    images = GalleryImage.query.filter_by(active=True).order_by(GalleryImage.created_at.desc()).all()
    return render_template('gallery.html', images=images)


@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()
        if name and message:
            # Store as unapproved review-style feedback or just flash
            flash('तपाईंको सन्देश प्राप्त भयो। धन्यवाद!', 'success')
            return redirect(url_for('main.contact'))
        flash('कृपया नाम र सन्देश भर्नुहोस्।', 'warning')
    return render_template('contact.html')


@bp.route('/track-order', methods=['GET', 'POST'])
def track_order():
    order = None
    error = None
    if request.method == 'POST':
        order_number = request.form.get('order_number', '').strip().upper()
        phone = request.form.get('phone', '').strip()
        from app.models import Order
        if order_number and phone:
            order = Order.query.filter_by(order_number=order_number, phone=phone).first()
            if not order:
                error = 'अर्डर फेला परेन। कृपया अर्डर नम्बर र मोबाइल जाँच गर्नुहोस्।'
        else:
            error = 'अर्डर नम्बर र मोबाइल नम्बर आवश्यक छ।'
    return render_template('track_order.html', order=order, error=error)
