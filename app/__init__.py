import os
from flask import Flask, render_template, request
from app.extensions import db, migrate, login_manager, csrf
from config import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Handle Neon / Heroku style postgres:// URLs
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url and db_url.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace('postgres://', 'postgresql://', 1)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Cloudinary
    cloud_name = app.config.get('CLOUDINARY_CLOUD_NAME')
    if cloud_name:
        import cloudinary
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=app.config.get('CLOUDINARY_API_KEY'),
            api_secret=app.config.get('CLOUDINARY_API_SECRET'),
            secure=True
        )

    # Blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.products import bp as products_bp
    app.register_blueprint(products_bp, url_prefix='/products')

    from app.cart import bp as cart_bp
    app.register_blueprint(cart_bp, url_prefix='/cart')

    from app.orders import bp as orders_bp
    app.register_blueprint(orders_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Context processors
    @app.context_processor
    def inject_globals():
        from app.models import SiteSetting, Category
        from flask import session
        settings = {}
        try:
            settings = SiteSetting.get_all_dict()
        except Exception:
            pass
        cart = session.get('cart', {})
        cart_count = sum(item.get('quantity', 0) for item in cart.values())
        categories = []
        try:
            categories = Category.query.filter_by(active=True).order_by(Category.name).all()
        except Exception:
            pass
        return {
            'site_settings': settings,
            'cart_count': cart_count,
            'nav_categories': categories,
            'business_name': settings.get('business_name', 'Puku Kosheli Hub'),
        }

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    # SEO routes
    @app.route('/robots.txt')
    def robots():
        return app.send_static_file('robots.txt')

    @app.route('/sitemap.xml')
    def sitemap():
        from flask import make_response
        from app.models import Product, Category
        from datetime import datetime
        base = request.url_root.rstrip('/')
        urls = [
            {'loc': f'{base}/', 'priority': '1.0'},
            {'loc': f'{base}/products', 'priority': '0.9'},
            {'loc': f'{base}/about', 'priority': '0.8'},
            {'loc': f'{base}/gallery', 'priority': '0.7'},
            {'loc': f'{base}/contact', 'priority': '0.8'},
            {'loc': f'{base}/track-order', 'priority': '0.6'},
        ]
        try:
            for p in Product.query.filter_by(active=True).all():
                urls.append({'loc': f'{base}/products/{p.slug}', 'priority': '0.8'})
            for c in Category.query.filter_by(active=True).all():
                urls.append({'loc': f'{base}/products?category={c.slug}', 'priority': '0.7'})
        except Exception:
            pass
        xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for u in urls:
            xml.append(f'<url><loc>{u["loc"]}</loc><priority>{u["priority"]}</priority></url>')
        xml.append('</urlset>')
        resp = make_response('\n'.join(xml))
        resp.headers['Content-Type'] = 'application/xml'
        return resp

    return app
