import os
import pickle
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.logging_config import logger
from app.models.athlete import Athlete
from app.models.coach import Coach
from app.models.competition import Competition
from app.models.result import Result

# FAISS ID namespace per entity type
NS = {
    "athlete": 1_000_000,
    "coach": 2_000_000,
    "competition": 3_000_000,
    "result": 4_000_000,
}

EMBED_DIM = 1536  # text-embedding-3-small
BATCH_SIZE = 96


class EmbeddingService:
    def __init__(self, client: AsyncOpenAI) -> None:
        self.client = client
        self._index: Optional[faiss.IndexIDMap] = None
        self._id_map: list[dict] = []  # [{faiss_id, type, id, text, deleted}]
        self._faiss_dir = Path(settings.FAISS_INDEX_DIR)

    @property
    def _index_path(self) -> Path:
        return self._faiss_dir / "index.bin"

    @property
    def _map_path(self) -> Path:
        return self._faiss_dir / "id_map.pkl"

    # ── Lifecycle ──────────────────────────────────────────────

    async def initialize(self, db: AsyncSession) -> None:
        self._faiss_dir.mkdir(parents=True, exist_ok=True)
        loaded = self._load_from_disk()
        if not loaded:
            logger.info("faiss_index_not_found_building")
            await self.build_full_index(db)
        else:
            logger.info("faiss_index_loaded", docs=len(self._id_map))

    def _new_index(self) -> faiss.IndexIDMap:
        flat = faiss.IndexFlatL2(EMBED_DIM)
        return faiss.IndexIDMap(flat)

    def _load_from_disk(self) -> bool:
        if not self._index_path.exists() or not self._map_path.exists():
            return False
        self._index = faiss.read_index(str(self._index_path))
        with open(self._map_path, "rb") as f:
            self._id_map = pickle.load(f)
        return True

    def _save_to_disk(self) -> None:
        tmp_idx = self._index_path.with_suffix(".tmp")
        tmp_map = self._map_path.with_suffix(".tmp")
        faiss.write_index(self._index, str(tmp_idx))
        with open(tmp_map, "wb") as f:
            pickle.dump(self._id_map, f)
        tmp_idx.replace(self._index_path)
        tmp_map.replace(self._map_path)

    # ── Embedding ──────────────────────────────────────────────

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        for i in range(0, len(texts), BATCH_SIZE):
            chunk = texts[i : i + BATCH_SIZE]
            resp = await self.client.embeddings.create(
                model=settings.OPENAI_EMBED_MODEL,
                input=chunk,
            )
            results.extend([d.embedding for d in resp.data])
        return results

    async def embed_text(self, text: str) -> list[float]:
        resp = await self.client.embeddings.create(
            model=settings.OPENAI_EMBED_MODEL,
            input=[text],
        )
        return resp.data[0].embedding

    # ── Index building ─────────────────────────────────────────

    async def build_full_index(self, db: AsyncSession) -> None:
        records: list[tuple[str, int, str]] = []  # (type, id, text)

        coaches = (await db.execute(select(Coach))).scalars().all()
        for c in coaches:
            records.append(("coach", c.id, c.to_text()))

        athletes = (
            await db.execute(select(Athlete).options(selectinload(Athlete.coach)))
        ).scalars().all()
        for a in athletes:
            records.append(("athlete", a.id, a.to_text()))

        competitions = (await db.execute(select(Competition))).scalars().all()
        for comp in competitions:
            records.append(("competition", comp.id, comp.to_text()))

        results = (
            await db.execute(
                select(Result).options(
                    selectinload(Result.athlete),
                    selectinload(Result.competition),
                )
            )
        ).scalars().all()
        for r in results:
            records.append(("result", r.id, r.to_text()))

        if not records:
            self._index = self._new_index()
            self._id_map = []
            self._save_to_disk()
            logger.info("faiss_index_built_empty")
            return

        texts = [t for _, _, t in records]
        vectors = await self._embed_batch(texts)

        self._index = self._new_index()
        self._id_map = []

        ids_np = np.array(
            [NS[rtype] + rid for rtype, rid, _ in records], dtype=np.int64
        )
        vecs_np = np.array(vectors, dtype=np.float32)
        self._index.add_with_ids(vecs_np, ids_np)

        for (rtype, rid, text), fid in zip(records, ids_np.tolist()):
            self._id_map.append(
                {"faiss_id": fid, "type": rtype, "id": rid, "text": text, "deleted": False}
            )

        self._save_to_disk()
        logger.info("faiss_index_built", docs=len(records))

    # ── Add / Remove ───────────────────────────────────────────

    async def add_record(self, rtype: str, rid: int, text: str) -> None:
        fid = NS[rtype] + rid
        vec = await self.embed_text(text)
        vec_np = np.array([vec], dtype=np.float32)
        ids_np = np.array([fid], dtype=np.int64)
        self._index.add_with_ids(vec_np, ids_np)
        self._id_map.append(
            {"faiss_id": fid, "type": rtype, "id": rid, "text": text, "deleted": False}
        )
        self._save_to_disk()

    async def remove_record(self, rtype: str, rid: int) -> None:
        fid = NS[rtype] + rid
        ids_np = np.array([fid], dtype=np.int64)
        self._index.remove_ids(ids_np)
        for entry in self._id_map:
            if entry["faiss_id"] == fid:
                entry["deleted"] = True
        self._save_to_disk()

    # ── Search ─────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_type: Optional[str] = None,
    ) -> list[dict]:
        if self._index is None or self._index.ntotal == 0:
            return []

        vec = await self.embed_text(query)
        vec_np = np.array([vec], dtype=np.float32)
        fetch = top_k * 4 if filter_type else top_k * 2
        distances, faiss_ids = self._index.search(vec_np, min(fetch, self._index.ntotal))

        lookup = {e["faiss_id"]: e for e in self._id_map if not e["deleted"]}
        results = []
        for fid, dist in zip(faiss_ids[0], distances[0]):
            if fid < 0:
                continue
            entry = lookup.get(int(fid))
            if entry is None:
                continue
            if filter_type and entry["type"] != filter_type:
                continue
            results.append({**entry, "score": float(dist)})
            if len(results) >= top_k:
                break

        return results

    @property
    def doc_count(self) -> int:
        return self._index.ntotal if self._index else 0
