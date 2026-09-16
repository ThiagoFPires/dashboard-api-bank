import sys
import os
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Importa a aplicação FastAPI
from app.main import app
from app.database import init_db

# Inicializa o banco no /tmp caso seja cold start no Serverless
init_db()
