from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
import pytest

import app.main as main


@pytest.mark.asyncio
@pytest.mark.parametrize('path', ['/products', '/reservations', '/conversations'])
async def test_inventory_views_require_authentication(path):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),
                                base_url='http://test') as client:
        response = await client.get(path)
    assert response.status_code == 401


@pytest.fixture
def demo_access(monkeypatch):
    user = '11111111-1111-4111-8111-111111111111'
    token = 'test-only-token-with-at-least-24-characters'
    monkeypatch.setenv('AUTH_MODE', 'demo')
    monkeypatch.setenv('DEMO_TOKEN', token)
    monkeypatch.setenv('DEMO_USER_ID', user)
    return user, {'Authorization': 'Bearer ' + token}


@pytest.mark.asyncio
async def test_history_uses_authenticated_owner_not_query_parameter(monkeypatch, demo_access):
    user, headers = demo_access
    queries = []

    class Cursor:
        async def fetchall(self):
            return []

    class Connection:
        async def execute(self, query, params):
            queries.append((query, params))
            return Cursor()

    @asynccontextmanager
    async def fake_connect():
        yield Connection()

    monkeypatch.setattr(main, 'connect', fake_connect)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),
                                base_url='http://test', headers=headers) as client:
        response = await client.get('/reservations', params={'user_id': str(uuid4())})
    assert response.status_code == 200
    assert queries[0][1] == (user,)
    assert 'where c.user_id=%s' in queries[0][0]


@pytest.mark.asyncio
async def test_reserve_button_cannot_access_another_users_conversation(monkeypatch, demo_access):
    _, headers = demo_access

    class Cursor:
        async def fetchone(self):
            return None

    class Connection:
        async def execute(self, *args):
            return Cursor()

    @asynccontextmanager
    async def fake_connect():
        yield Connection()

    monkeypatch.setattr(main, 'connect', fake_connect)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),
                                base_url='http://test', headers=headers) as client:
        response = await client.post(f'/conversations/{uuid4()}/reserve',
                                     json={'product_id': 'TEC-01', 'quantity': 1})
    assert response.status_code == 404
