import os
from app import create_app
from app.extensions import db
from app.models import User, SiteSetting

app = create_app()


@app.cli.command('create-admin')
def create_admin():
    """Create the first admin user. Usage: flask create-admin"""
    import getpass
    email = os.environ.get('ADMIN_EMAIL') or input('Admin email: ').strip()
    name = input('Admin name [Admin]: ').strip() or 'Admin'
    password = os.environ.get('ADMIN_PASSWORD') or getpass.getpass('Password: ')
    if not email or not password:
        print('Email and password required.')
        return
    existing = User.query.filter_by(email=email).first()
    if existing:
        print(f'User {email} already exists.')
        return
    user = User(name=name, email=email, role='admin')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f'Admin created: {email}')


@app.cli.command('seed-settings')
def seed_settings():
    """Seed default site settings."""
    defaults = {
        'business_name': 'Puku Kosheli Hub',
        'business_tagline': 'घरको स्वाद, अचारको असली मज्जा',
        'phone': '',
        'email': '',
        'address': 'Urlabari, Morang, Nepal',
        'google_maps_url': 'https://maps.google.com/?q=Urlabari,Morang,Nepal',
        'tiktok_url': 'https://www.tiktok.com/@pukukoshelihuburlabari',
        'facebook_url': '',
        'instagram_url': '',
        'whatsapp_number': '',
        'delivery_enabled': '1',
        'delivery_charge': '50',
        'free_delivery_threshold': '1000',
        'pickup_enabled': '1',
        'min_order_amount': '0',
        'payment_cod': '1',
        'payment_bank': '0',
        'payment_qr': '0',
        'payment_bank_info': '',
        'payment_qr_info': '',
        'hero_title': 'घरको स्वाद, अचारको असली मज्जा',
        'hero_subtitle': 'Urlabari बाट तयार गरिएको परम्परागत नेपाली अचार',
        'about_text': 'Puku Kosheli Hub ले घरको स्वाद र गुणस्तरीय सामग्रीबाट तयार पारिएको अचार उपलब्ध गराउँछ।',
        'footer_text': 'Puku Kosheli Hub — Urlabari, Morang। घरको स्वाद, अचारको असली मज्जा।',
        'why_choose_1_title': 'असली नेपाली स्वाद',
        'why_choose_1_text': 'परम्परागत विधि र स्थानीय मसलाबाट तयार।',
        'why_choose_2_title': 'गुणस्तरीय सामग्री',
        'why_choose_2_text': 'छानिएका ताजा सामग्री मात्र प्रयोग।',
        'why_choose_3_title': 'घरको स्वाद',
        'why_choose_3_text': 'माया र हेरचाहसँग तयार गरिएको अचार।',
        'why_choose_4_title': 'मायाले तयार गरिएको',
        'why_choose_4_text': 'प्रत्येक जारमा परिवारको हेरचाह।',
    }
    for k, v in defaults.items():
        if not SiteSetting.get(k):
            SiteSetting.set(k, v)
    print('Default settings seeded.')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')
