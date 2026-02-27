"""PostgreSQL-based RAG client (JSONB embeddings, cosine similarity in Python)."""

import json
import logging
import math
from functools import lru_cache
from typing import Any, Optional

from app.config import Settings, get_settings

from app.storage.postgres import get_pool

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        logger.warning(f"Vector length mismatch: {len(vec1)} vs {len(vec2)}")
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    m1 = math.sqrt(sum(a * a for a in vec1))
    m2 = math.sqrt(sum(a * a for a in vec2))
    if m1 == 0 or m2 == 0:
        return 0.0
    return dot / (m1 * m2)


class PostgresRAGClient:
    """PostgreSQL RAG client with JSONB embeddings."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def connect(self) -> "PostgresRAGClient":
        return self

    async def create_index(
        self,
        index_name: str,
        vector_dimension: int = 1536,
        shards: int = 1,
        replicas: int = 0,
    ) -> bool:
        logger.info(f"Index creation requested for {index_name} (table already exists)")
        return True

    async def index_document(
        self,
        index_name: str,
        agent_id: str,
        document_id: str,
        title: str,
        content: str,
        embedding: list[float],
    ) -> bool:
        emb_json = json.dumps(embedding)
        meta_json = json.dumps({})
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO rag_documents (agent_id, document_id, title, content, embedding, metadata)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb)
                    ON CONFLICT (agent_id, document_id) DO UPDATE SET
                        title = EXCLUDED.title, content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
                    """,
                    agent_id,
                    document_id,
                    title,
                    content,
                    emb_json,
                    meta_json,
                )
            return True
        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}", exc_info=True)
            return False

    async def bulk_index_documents(
        self,
        index_name: str,
        documents: list[dict[str, Any]],
    ) -> tuple[int, int]:
        success_count = 0
        failed_count = 0
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                for doc in documents:
                    try:
                        emb = doc.get("embedding", [])
                        emb_json = json.dumps(emb)
                        meta_json = json.dumps(doc.get("metadata", {}))
                        await conn.execute(
                            """
                            INSERT INTO rag_documents (agent_id, document_id, title, content, embedding, metadata)
                            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb)
                            ON CONFLICT (agent_id, document_id) DO UPDATE SET
                                title = EXCLUDED.title, content = EXCLUDED.content,
                                embedding = EXCLUDED.embedding, metadata = EXCLUDED.metadata
                            """,
                            doc["agent_id"],
                            doc["document_id"],
                            doc.get("title", ""),
                            doc.get("content", ""),
                            emb_json,
                            meta_json,
                        )
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to index document {doc.get('document_id')}: {e}", exc_info=True)
                        failed_count += 1
        return success_count, failed_count

    async def search(
        self,
        index_name: str,
        query_embedding: list[float],
        agent_id: str,
        top_k: int = 6,
        score_threshold: float = 0.2,
    ) -> list[dict[str, Any]]:
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT agent_id, document_id, title, content, embedding FROM rag_documents WHERE agent_id = $1",
                    agent_id,
                )
            results = []
            for row in rows:
                try:
                    emb_raw = row.get("embedding")
                    if isinstance(emb_raw, str):
                        emb = json.loads(emb_raw)
                    elif isinstance(emb_raw, list):
                        emb = emb_raw
                    else:
                        emb = []
                    if not emb:
                        continue
                    sim = cosine_similarity(query_embedding, emb)
                    if sim >= score_threshold:
                        results.append({
                            "document_id": row["document_id"],
                            "title": row.get("title", ""),
                            "content": row.get("content", ""),
                            "score": sim,
                        })
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.warning(f"Error processing document {row.get('document_id')}: {e}")
                    continue
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]
        except Exception as e:
            logger.error(f"Error searching RAG: {e}", exc_info=True)
            return []

    async def delete_documents_by_agent(self, index_name: str, agent_id: str) -> int:
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM rag_documents WHERE agent_id = $1",
                    agent_id,
                )
            # Parse "DELETE N" from result
            if result and result.startswith("DELETE "):
                return int(result.split()[1])
            return 0
        except Exception as e:
            logger.error(f"Error deleting RAG documents: {e}", exc_info=True)
            return 0

    async def close(self) -> None:
        pass


@lru_cache()
def get_postgres_rag_client() -> PostgresRAGClient:
    settings = get_settings()
    return PostgresRAGClient(settings)
