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
                "ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS sistema_pms VARCHAR(10) DEFAULT 'hmax'",
                'ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS hits_stone_total FLOAT DEFAULT 0.0',
                'ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS hits_transferencia_bancaria FLOAT DEFAULT 0.0',
                'ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS hits_pix_cnpj FLOAT DEFAULT 0.0',
                'ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS hits_virada_sistema FLOAT DEFAULT 0.0',
                'ALTER TABLE fechamento_caixa ADD COLUMN IF NOT EXISTS hits_total_caixa FLOAT DEFAULT 0.0',
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
