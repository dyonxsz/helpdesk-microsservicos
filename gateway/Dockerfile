FROM python:3.12-slim

# Não roda como root dentro do contêiner
RUN useradd --create-home --uid 10001 helpdesk

WORKDIR /app
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código comum (cabeçalhos de segurança) + gateway + a tela
COPY comum ./comum
COPY gateway/app ./app
COPY gateway/web ./web

USER helpdesk
ENV USUARIOS_URL=http://usuarios:8000 \
    INVENTARIO_URL=http://inventario:8000 \
    CHAMADOS_URL=http://chamados:8000 \
    NOTIFICACOES_URL=http://notificacoes:8000 \
    PROXY_TIMEOUT=10 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
