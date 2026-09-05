import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_gbl4YnKaM0Hr@ep-twilight-rice-aej8rri4-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"
os.environ["SECRET_KEY"] = "setup-secret"

from app import create_app
from app.extensions import db
from app.models import User, SiteSetting

app = create_app()
with app.app_context():
    db.create_all()
    print("OK tables")

    defaults = {
        "business_name": "Puku Kosheli Hub",
        "hero_title": "घरको स्वाद, अचारको असली मज्जा",
        "address": "Urlabari, Morang, Nepal",
        "delivery_enabled": "1",
        "delivery_charge": "50",
        "pickup_enabled": "1",
        "payment_cod": "1",
    }
    for k, v in defaults.items():
        if not SiteSetting.get(k):
            SiteSetting.set(k, v)

    u = User.query.filter_by(email="admin@puku.com").first()
    if not u:
        u = User(name="Admin", email="admin@puku.com", role="admin")
        u.set_password("admin123")
        db.session.add(u)
        db.session.commit()
        print("Admin created: admin@puku.com / admin123")
    else:
        u.set_password("admin123")
        db.session.commit()
        print("Password reset: admin123")

    print("Done")
