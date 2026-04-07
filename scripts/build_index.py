"""
Build (or rebuild) the FAISS index from all DB data.
Run: python scripts/build_index.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.services.embedding_service import EmbeddingService

engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def main():
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    emb = EmbeddingService(client)

    print("🔄 FAISS indeksi qurilmoqda...")
    async with Session() as db:
        await emb.build_full_index(db)

    print(f"✅ Indeks tayyor. Hujjatlar soni: {emb.doc_count}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
