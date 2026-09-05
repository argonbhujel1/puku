from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import func
from app.admin import bp
from app.models import (
    Product, Category, Order, OrderItem, Review, GalleryImage, SiteSetting, User
)
from app.extensions import db
from app.utils import admin_required, slugify, upload_to_cloudinary, delete_from_cloudinary, allowed_file


@bp.route('/')
@login_required
@admin_required
def dashboard():
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())

    total_orders = Order.query.count()
    today_orders = Order.query.filter(Order.created_at >= today_start).count()
    pending = Order.query.filter_by(status='pending').count()

    total_sales = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.status != 'cancelled'
    ).scalar() or 0
    today_sales = db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.created_at >= today_start,
        Order.status != 'cancelled'
    ).scalar() or 0

    low_stock = Product.query.filter(
        Product.active == True,
        Product.stock > 0,
        Product.stock <= Product.low_stock_threshold
    ).all()
    out_of_stock = Product.query.filter(Product.active == True, Product.stock <= 0).count()

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()

    return render_template(
        'admin/dashboard.html',
        total_orders=total_orders,
        today_orders=today_orders,
        pending=pending,
        total_sales=total_sales,
        today_sales=today_sales,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
        recent_orders=recent_orders,
    )


# ─── Products ───────────────────────────────────────────────
@bp.route('/products')
@login_required
@admin_required
def products():
    q = request.args.get('q', '')
    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f'%{q}%'))
    products = query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products, q=q)


@bp.route('/products/new', methods=['GET', 'POST'])
@login_required
@admin_required
def product_new():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('नाम आवश्यक छ।', 'danger')
            return render_template('admin/product_form.html', categories=categories, product=None)
        slug = slugify(request.form.get('slug') or name)
        # ensure unique slug
        base_slug = slug
        i = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{i}'
            i += 1

        image_url = None
        public_id = None
        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename and allowed_file(f.filename):
                image_url, public_id = upload_to_cloudinary(f, folder='puku-kosheli/products')

        product = Product(
            name=name,
            slug=slug,
            category_id=request.form.get('category_id') or None,
            description=request.form.get('description', ''),
            ingredients=request.form.get('ingredients', ''),
            weight=request.form.get('weight', ''),
            price=Decimal(request.form.get('price', '0') or '0'),
            stock=int(request.form.get('stock', 0) or 0),
            low_stock_threshold=int(request.form.get('low_stock_threshold', 5) or 5),
            featured=bool(request.form.get('featured')),
            active=bool(request.form.get('active', True)),
            why_special=request.form.get('why_special', ''),
            image_url=image_url,
            cloudinary_public_id=public_id,
        )
        db.session.add(product)
        db.session.commit()
        flash('उत्पादन थपियो।', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', categories=categories, product=None)


@bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def product_edit(id):
    product = Product.query.get_or_404(id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip() or product.name
        new_slug = slugify(request.form.get('slug') or product.name)
        if new_slug != product.slug:
            if not Product.query.filter(Product.slug == new_slug, Product.id != id).first():
                product.slug = new_slug
        product.category_id = request.form.get('category_id') or None
        product.description = request.form.get('description', '')
        product.ingredients = request.form.get('ingredients', '')
        product.weight = request.form.get('weight', '')
        product.price = Decimal(request.form.get('price', '0') or '0')
        product.stock = int(request.form.get('stock', 0) or 0)
        product.low_stock_threshold = int(request.form.get('low_stock_threshold', 5) or 5)
        product.featured = bool(request.form.get('featured'))
        product.active = bool(request.form.get('active'))
        product.why_special = request.form.get('why_special', '')

        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename and allowed_file(f.filename):
                if product.cloudinary_public_id:
                    delete_from_cloudinary(product.cloudinary_public_id)
                url, pid = upload_to_cloudinary(f, folder='puku-kosheli/products')
                if url:
                    product.image_url = url
                    product.cloudinary_public_id = pid

        db.session.commit()
        flash('उत्पादन अपडेट भयो।', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', categories=categories, product=product)


@bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def product_delete(id):
    product = Product.query.get_or_404(id)
    if product.cloudinary_public_id:
        delete_from_cloudinary(product.cloudinary_public_id)
    db.session.delete(product)
    db.session.commit()
    flash('उत्पादन मेटियो।', 'success')
    return redirect(url_for('admin.products'))


# ─── Categories ─────────────────────────────────────────────
@bp.route('/categories')
@login_required
@admin_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=cats)


@bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def category_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('नाम आवश्यक छ।', 'danger')
            return render_template('admin/category_form.html', category=None)
        slug = slugify(request.form.get('slug') or name)
        base = slug
        i = 1
        while Category.query.filter_by(slug=slug).first():
            slug = f'{base}-{i}'
            i += 1
        cat = Category(
            name=name,
            slug=slug,
            description=request.form.get('description', ''),
            active=bool(request.form.get('active', True)),
        )
        db.session.add(cat)
        db.session.commit()
        flash('श्रेणी थपियो।', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=None)


@bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def category_edit(id):
    cat = Category.query.get_or_404(id)
    if request.method == 'POST':
        cat.name = request.form.get('name', '').strip() or cat.name
        new_slug = slugify(request.form.get('slug') or cat.name)
        if new_slug != cat.slug and not Category.query.filter(Category.slug == new_slug, Category.id != id).first():
            cat.slug = new_slug
        cat.description = request.form.get('description', '')
        cat.active = bool(request.form.get('active'))
        db.session.commit()
        flash('श्रेणी अपडेट भयो।', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', category=cat)


@bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def category_delete(id):
    cat = Category.query.get_or_404(id)
    Product.query.filter_by(category_id=id).update({'category_id': None})
    db.session.delete(cat)
    db.session.commit()
    flash('श्रेणी मेटियो।', 'success')
    return redirect(url_for('admin.categories'))


# ─── Orders ─────────────────────────────────────────────────
@bp.route('/orders')
@login_required
@admin_required
def orders():
    status = request.args.get('status', '')
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders, current_status=status)


@bp.route('/orders/<int:id>')
@login_required
@admin_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)


@bp.route('/orders/<int:id>/status', methods=['POST'])
@login_required
@admin_required
def order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status', '')
    if new_status in Order.STATUS_LABELS:
        order.status = new_status
        db.session.commit()
        flash('स्टेटस अपडेट भयो।', 'success')
    return redirect(url_for('admin.order_detail', id=id))


# ─── Reviews ────────────────────────────────────────────────
@bp.route('/reviews')
@login_required
@admin_required
def reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)


@bp.route('/reviews/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def review_approve(id):
    r = Review.query.get_or_404(id)
    r.approved = True
    db.session.commit()
    flash('समीक्षा स्वीकृत।', 'success')
    return redirect(url_for('admin.reviews'))


@bp.route('/reviews/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def review_reject(id):
    r = Review.query.get_or_404(id)
    r.approved = False
    db.session.commit()
    flash('समीक्षा अस्वीकृत।', 'success')
    return redirect(url_for('admin.reviews'))


@bp.route('/reviews/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def review_delete(id):
    r = Review.query.get_or_404(id)
    db.session.delete(r)
    db.session.commit()
    flash('समीक्षा मेटियो।', 'success')
    return redirect(url_for('admin.reviews'))


@bp.route('/reviews/add', methods=['POST'])
@login_required
@admin_required
def review_add():
    name = request.form.get('customer_name', '').strip()
    rating = int(request.form.get('rating', 5) or 5)
    message = request.form.get('message', '').strip()
    if name and message:
        r = Review(customer_name=name, rating=min(5, max(1, rating)), message=message, approved=True)
        db.session.add(r)
        db.session.commit()
        flash('समीक्षा थपियो।', 'success')
    return redirect(url_for('admin.reviews'))


# ─── Gallery ────────────────────────────────────────────────
@bp.route('/gallery')
@login_required
@admin_required
def gallery():
    images = GalleryImage.query.order_by(GalleryImage.created_at.desc()).all()
    return render_template('admin/gallery.html', images=images)


@bp.route('/gallery/upload', methods=['POST'])
@login_required
@admin_required
def gallery_upload():
    if 'image' not in request.files:
        flash('फाइल छान्नुहोस्।', 'warning')
        return redirect(url_for('admin.gallery'))
    f = request.files['image']
    if f and f.filename and allowed_file(f.filename):
        url, pid = upload_to_cloudinary(f, folder='puku-kosheli/gallery')
        if url:
            img = GalleryImage(
                title=request.form.get('title', ''),
                image_url=url,
                cloudinary_public_id=pid,
                active=True,
            )
            db.session.add(img)
            db.session.commit()
            flash('तस्बिर अपलोड भयो।', 'success')
        else:
            flash('अपलोड असफल। Cloudinary सेटिङ जाँच गर्नुहोस्।', 'danger')
    return redirect(url_for('admin.gallery'))


@bp.route('/gallery/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def gallery_delete(id):
    img = GalleryImage.query.get_or_404(id)
    if img.cloudinary_public_id:
        delete_from_cloudinary(img.cloudinary_public_id)
    db.session.delete(img)
    db.session.commit()
    flash('तस्बिर मेटियो।', 'success')
    return redirect(url_for('admin.gallery'))


# ─── Settings ───────────────────────────────────────────────
@bp.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    keys = [
        'business_name', 'business_tagline', 'phone', 'email', 'address',
        'google_maps_url', 'tiktok_url', 'facebook_url', 'instagram_url',
        'whatsapp_number', 'delivery_enabled', 'delivery_charge',
        'free_delivery_threshold', 'pickup_enabled', 'min_order_amount',
        'payment_cod', 'payment_bank', 'payment_qr', 'payment_bank_info',
        'payment_qr_info', 'hero_title', 'hero_subtitle', 'about_text',
        'footer_text',
        'why_choose_1_title', 'why_choose_1_text',
        'why_choose_2_title', 'why_choose_2_text',
        'why_choose_3_title', 'why_choose_3_text',
        'why_choose_4_title', 'why_choose_4_text',
    ]
    if request.method == 'POST':
        for k in keys:
            val = request.form.get(k, '')
            SiteSetting.set(k, val)
        flash('सेटिङ सेभ भयो।', 'success')
        return redirect(url_for('admin.settings'))
    current = SiteSetting.get_all_dict()
    return render_template('admin/settings.html', settings=current, keys=keys)
