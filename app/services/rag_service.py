from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import logger
from app.models.chat import ChatMessage
from app.services.embedding_service import EmbeddingService
from app.services.prompt_guard import validate_query

SYSTEM_PROMPT = """Siz O'zbekiston sport ma'lumotlari bo'yicha AI yordamchisiz.
Faqat quyida berilgan kontekst asosida javob bering.
Agar savol kontekstda yo'q ma'lumotni so'rasa, aniq aytib qo'ying: "Menda bu haqida ma'lumot yo'q."
Javobingiz aniq, qisqa va tushunarli bo'lsin. O'zbek yoki rus tilida javob bering."""

MAX_CONTEXT_CHARS = 3000
MAX_HISTORY_TURNS = 6


class RAGResult:
    __slots__ = ("answer", "chunks", "tokens_used")

    def __init__(self, answer: str, chunks: list[dict], tokens_used: int) -> None:
        self.answer = answer
        self.chunks = chunks
        self.tokens_used = tokens_used


class RAGService:
    def __init__(self, embedding_service: EmbeddingService, client: AsyncOpenAI) -> None:
        self.embeddings = embedding_service
        self.client = client

    async def answer(
        self,
        query: str,
        history: list[ChatMessage],
        db: AsyncSession,
    ) -> RAGResult:
        # [1] Guard
        clean_query = validate_query(query)

        # [2] Retrieve
        chunks = await self.embeddings.search(clean_query, top_k=settings.FAISS_TOP_K)

        # [3] Context block
        context = self._build_context(chunks)

        # [4] Messages
        messages = self._build_messages(clean_query, context, history)

        # [5] LLM call
        answer_text, tokens = await self._call_llm(messages)

        logger.info("rag_answered", query_len=len(clean_query), chunks=len(chunks), tokens=tokens)
        return RAGResult(answer=answer_text, chunks=chunks, tokens_used=tokens)

    def _build_context(self, chunks: list[dict]) -> str:
        lines = []
        total = 0
        for i, chunk in enumerate(chunks, 1):
            text = chunk["text"]
            if total + len(text) > MAX_CONTEXT_CHARS:
                remaining = MAX_CONTEXT_CHARS - total
                if remaining > 50:
                    lines.append(f"[{i}] {text[:remaining]}")
                break
            lines.append(f"[{i}] {text}")
            total += len(text)
        return "\n---\n".join(lines)

    def _build_messages(
        self,
        query: str,
        context: str,
        history: list[ChatMessage],
    ) -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Last N turns of history
        trimmed = history[-(MAX_HISTORY_TURNS * 2):]
        for msg in trimmed:
            messages.append({"role": msg.role, "content": msg.content})

        user_content = f"Ma'lumotlar:\n{context}\n\nSavol: {query}" if context else query
        messages.append({"role": "user", "content": user_content})
        return messages

    async def _call_llm(self, messages: list[dict]) -> tuple[str, int]:
        response = await self.client.chat.completions.create(
            model=settings.OPENAI_LLM_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=800,
        )
        text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return text, tokens
