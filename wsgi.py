from datetime import datetime
from app import app, db, init_db
import os

@app.context_processor
def inject_now():
    return {'now': datetime.now}

with app.app_context():
    try:
        db.create_all()
        init_db()
        with db.engine.connect() as conn:
            migracoes = [
                'ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS cheque FLOAT DEFAULT 0.0',
                'ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS cofre_opcional BOOLEAN DEFAULT FALSE',
                'ALTER TABLE movimentacao_cofre ADD COLUMN IF NOT EXISTS grupo_id VARCHAR(50)',
            ]
            for sql in migracoes:
                try:
                    conn.execute(db.text(sql))
                    conn.commit()
                except Exception as e:
                    print('Migracao ignorada:', str(e)[:80])
        print('Banco inicializado!')
    except Exception as e:
        print('ERRO:', str(e))
