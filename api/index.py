# Ponto de entrada da função serverless do Vercel.
#
# Diferente do Render (um processo Flask/waitress de longa duração), o
# Vercel roda cada requisição numa função isolada. Este arquivo só importa o
# `app` já existente em app.py (mesma lógica de rotas, autenticação e banco
# do projeto original) e delega pra ele — nada de regra de negócio é
# duplicada aqui.
#
# vercel.json manda todo tráfego de /api/* pra esta função; o resto (HTML,
# JS, CSS do frontend compilado) é servido direto pelo CDN do Vercel a
# partir de frontend/dist/spa, sem passar por aqui.
import sys
from pathlib import Path

# api/ fica um nível abaixo da raiz do projeto — garante que "import app",
# "import auth", "import database" (tudo em caminho absoluto a partir da
# raiz) funcione dentro da função, igual funciona hoje rodando localmente.
RAIZ_DO_PROJETO = Path(__file__).resolve().parent.parent
if str(RAIZ_DO_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_DO_PROJETO))

from app import app  # noqa: E402 (import depende do sys.path acima)

# O runtime Python do Vercel espera encontrar uma variável WSGI chamada
# "app" neste módulo — é só isso, o resto é o Flask de sempre.
