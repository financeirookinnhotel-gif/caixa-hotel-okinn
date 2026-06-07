from datetime import datetime
from app import app, db, init_db

@app.context_processor
def inject_now():
    return {'now': datetime.now}

with app.app_context():
    db.create_all()
    init_db()
