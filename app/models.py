from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, login_manager
import secrets


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    image = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    ingredients = db.Column(db.Text)
    weight = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    image_url = db.Column(db.String(500))
    cloudinary_public_id = db.Column(db.String(300))
    featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    why_special = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_in_stock(self):
        return self.stock > 0 and self.active

    def is_low_stock(self):
        return 0 < self.stock <= self.low_stock_threshold

    def __repr__(self):
        return f'<Product {self.name}>'


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    customer_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(300))
    ward = db.Column(db.String(20))
    locality = db.Column(db.String(100))
    city = db.Column(db.String(100), default='Urlabari')
    delivery_method = db.Column(db.String(30), default='delivery')  # delivery / pickup
    payment_method = db.Column(db.String(30), default='cod')  # cod / bank / qr
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    delivery_charge = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy='joined', cascade='all, delete-orphan')

    STATUS_LABELS = {
        'pending': 'अर्डर प्राप्त',
        'confirmed': 'पुष्टि भयो',
        'preparing': 'तयारी हुँदैछ',
        'ready': 'तयार छ',
        'out_for_delivery': 'डेलिभरीका लागि निस्कियो',
        'delivered': 'डेलिभर भयो',
        'cancelled': 'रद्द भयो'
    }

    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @staticmethod
    def generate_order_number():
        year = datetime.utcnow().year
        # Find last order of the year
        last = Order.query.filter(
            Order.order_number.like(f'PKH-{year}-%')
        ).order_by(Order.id.desc()).first()
        if last:
            try:
                seq = int(last.order_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f'PKH-{year}-{seq:05d}'


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    product = db.relationship('Product')


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    message = db.Column(db.Text)
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class GalleryImage(db.Model):
    __tablename__ = 'gallery_images'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    image_url = db.Column(db.String(500), nullable=False)
    cloudinary_public_id = db.Column(db.String(300))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)

    @staticmethod
    def get(key, default=None):
        setting = SiteSetting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        setting = SiteSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = SiteSetting(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
        return setting

    @staticmethod
    def get_all_dict():
        return {s.key: s.value for s in SiteSetting.query.all()}
