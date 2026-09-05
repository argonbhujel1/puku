from flask import render_template, request, jsonify, abort
from app.products import bp
from app.models import Product, Category
from app.extensions import db
from sqlalchemy import or_


@bp.route('/')
def list_products():
    q = request.args.get('q', '').strip()
    category_slug = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    availability = request.args.get('availability', '')

    query = Product.query.filter_by(active=True)

    if q:
        query = query.filter(or_(
            Product.name.ilike(f'%{q}%'),
            Product.description.ilike(f'%{q}%')
        ))

    if category_slug:
        cat = Category.query.filter_by(slug=category_slug, active=True).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    if availability == 'in_stock':
        query = query.filter(Product.stock > 0)

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'popular':
        query = query.order_by(Product.featured.desc(), Product.created_at.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    page = request.args.get('page', 1, type=int)
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    categories = Category.query.filter_by(active=True).order_by(Category.name).all()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'html': render_template('products/_grid.html', products=pagination.items),
            'has_next': pagination.has_next,
            'page': pagination.page,
            'total': pagination.total,
        })

    return render_template(
        'products/list.html',
        products=pagination.items,
        pagination=pagination,
        categories=categories,
        current_category=category_slug,
        q=q,
        sort=sort,
        availability=availability,
    )


@bp.route('/<slug>')
def detail(slug):
    product = Product.query.filter_by(slug=slug, active=True).first_or_404()
    related = Product.query.filter(
        Product.active == True,
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    if not related:
        related = Product.query.filter(
            Product.active == True,
            Product.id != product.id
        ).order_by(Product.featured.desc()).limit(4).all()
    return render_template('products/detail.html', product=product, related=related)
