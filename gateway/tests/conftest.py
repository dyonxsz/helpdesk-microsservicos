import os
import sys
from pathlib import Path

# Permite importar o pacote comum/ do repositório sem confundir com o app/ do monólito.
sys.path.append(str(Path(__file__).resolve().parents[2]))

os.environ.setdefault("USUARIOS_URL", "http://usuarios-teste:8000")
os.environ.setdefault("INVENTARIO_URL", "http://inventario-teste:8000")
os.environ.setdefault("CHAMADOS_URL", "http://chamados-teste:8000")
os.environ.setdefault("NOTIFICACOES_URL", "http://notificacoes-teste:8000")

import pytest
from fastapi.testclient import TestClient

from app import main as gateway


@pytest.fixture
def cliente():
    return TestClient(gateway.app)


@pytest.fixture
def chamadas(monkeypatch):
    """Substitui a chamada HTTP real e registra o que o gateway tentou encaminhar."""
    registro = []

    async def falso(url, metodo, cabecalhos, corpo, parametros):
        import httpx

        registro.append({
            "url": url, "metodo": metodo, "cabecalhos": cabecalhos,
            "corpo": corpo, "parametros": parametros,
        })
        return httpx.Response(200, json={"ok": True}, headers={"content-type": "application/json"})

    monkeypatch.setattr(gateway, "repassar", falso)
    return registro
