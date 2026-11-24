FROM python:3.12-slim

# Não roda como root dentro do contêiner
RUN useradd --create-home --uid 10001 helpdesk && mkdir /dados && chown helpdesk /dados

WORKDIR /app
COPY servicos/chamados/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código comum (tokens/erros/segurança) + código deste serviço
COPY comum ./comum
COPY servicos/chamados/app ./app

USER helpdesk
ENV DATABASE_URL=sqlite:////dados/chamados.db \
    USUARIOS_URL=http://usuarios:8000 \
    INVENTARIO_URL=http://inventario:8000 \
    REDIS_URL=redis://redis:6379/0 \
    HTTP_TIMEOUT=3 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
