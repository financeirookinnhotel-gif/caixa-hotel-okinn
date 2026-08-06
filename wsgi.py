from datetime import datetime
from app import app, init_db, db

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Initialize database on startup
with app.app_context():
    db.create_all()
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
