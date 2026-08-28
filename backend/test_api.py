import asyncio, httpx
from app.core.database import async_session_factory
from sqlalchemy import text

async def test():
    async with async_session_factory() as db:
        res = await db.execute(text("SELECT id, name FROM repositories WHERE name LIKE '%ExpenseTracker%' LIMIT 1"))
        row = res.first()
        repo_id = str(row[0])
    
    async with httpx.AsyncClient() as client:
        payload = {'message': 'hello'}
        r = await client.post(f"http://127.0.0.1:8000/api/repositories/{repo_id}/chat", json=payload, timeout=120.0)
        print('Status:', r.status_code)

asyncio.run(test())
