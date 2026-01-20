"""
Скрипт миграции данных из OpenSearch в DynamoDB для RAG.

Использование:
    python migrate_opensearch_to_dynamodb.py --agent-id doctor_001
    или
    python migrate_opensearch_to_dynamodb.py doctor_001
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any

import boto3
from opensearchpy import AsyncOpenSearch

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация из переменных окружения
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT")
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME", "admin")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD")
DYNAMODB_TABLE = "doctor-agent-rag-documents"
AWS_REGION = os.getenv("AWS_REGION", "me-central-1")


async def export_from_opensearch(agent_id: str) -> list[dict]:
    """Экспорт всех документов агента из OpenSearch."""
    if not OPENSEARCH_ENDPOINT:
        raise ValueError("OPENSEARCH_ENDPOINT environment variable is required")
    if not OPENSEARCH_PASSWORD:
        raise ValueError("OPENSEARCH_PASSWORD environment variable is required")

    index_name = f"agent_{agent_id}_documents"
    
    # Парсинг endpoint URL
    endpoint = OPENSEARCH_ENDPOINT
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        url_parts = endpoint.replace("http://", "").replace("https://", "").split(":")
        host = url_parts[0]
        port = int(url_parts[1]) if len(url_parts) > 1 else 443
    else:
        host = endpoint.split(":")[0]
        port = int(endpoint.split(":")[1]) if ":" in endpoint else 443

    use_ssl = endpoint.startswith("https://")

    # Подключение к OpenSearch
    client = AsyncOpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
        use_ssl=use_ssl,
        verify_certs=use_ssl,
        ssl_show_warn=False,
    )

    try:
        # Проверка существования индекса
        if not await client.indices.exists(index=index_name):
            logger.warning(f"Index {index_name} does not exist")
            return []

        # Получение всех документов агента
        documents = []
        scroll_size = 100
        scroll_timeout = "5m"
        
        # Начальный запрос
        response = await client.search(
            index=index_name,
            body={
                "query": {
                    "term": {"agent_id": agent_id}
                },
                "size": scroll_size
            },
            scroll=scroll_timeout
        )
        
        scroll_id = response.get("_scroll_id")
        hits = response.get("hits", {}).get("hits", [])
        
        while hits:
            for hit in hits:
                source = hit.get("_source", {})
                documents.append({
                    "agent_id": source.get("agent_id", agent_id),
                    "document_id": source.get("document_id", hit.get("_id")),
                    "title": source.get("title", ""),
                    "content": source.get("content", ""),
                    "embedding": source.get("embedding", []),
                    "metadata": source.get("metadata", {}),
                })
            
            # Получение следующей порции
            if scroll_id:
                response = await client.scroll(
                    scroll_id=scroll_id,
                    scroll=scroll_timeout
                )
                scroll_id = response.get("_scroll_id")
                hits = response.get("hits", {}).get("hits", [])
            else:
                break
        
        # Очистка scroll context
        if scroll_id:
            await client.clear_scroll(scroll_id=scroll_id)
        
        logger.info(f"Exported {len(documents)} documents from OpenSearch")
        return documents
    
    finally:
        await client.close()


async def import_to_dynamodb(documents: list[dict]) -> int:
    """Импорт документов в DynamoDB."""
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    imported_count = 0
    failed_count = 0
    
    # Batch write для эффективности (максимум 25 items за раз)
    batch_size = 25
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        
        with table.batch_writer() as writer:
            for doc in batch:
                try:
                    item = {
                        'agent_id': doc['agent_id'],
                        'document_id': doc['document_id'],
                        'title': doc.get('title', ''),
                        'content': doc.get('content', ''),
                        'embedding': json.dumps(doc.get('embedding', [])),  # JSON строка для DynamoDB
                        'metadata': json.dumps(doc.get('metadata', {})),
                    }
                    writer.put_item(Item=item)
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Failed to import document {doc.get('document_id')}: {e}")
                    failed_count += 1
    
    logger.info(f"Imported {imported_count} documents, {failed_count} failed")
    return imported_count


async def main():
    parser = argparse.ArgumentParser(description='Migrate RAG documents from OpenSearch to DynamoDB')
    parser.add_argument('agent_id', nargs='?', default='doctor_001', help='Agent ID to migrate')
    parser.add_argument('--agent-id', dest='agent_id_arg', help='Agent ID to migrate (alternative)')
    
    args = parser.parse_args()
    agent_id = args.agent_id_arg or args.agent_id
    
    logger.info(f"Starting migration for agent: {agent_id}")
    
    try:
        # Экспорт из OpenSearch
        logger.info("Exporting documents from OpenSearch...")
        documents = await export_from_opensearch(agent_id)
        
        if not documents:
            logger.warning("No documents found to migrate")
            return
        
        logger.info(f"Found {len(documents)} documents")
        
        # Импорт в DynamoDB
        logger.info("Importing documents to DynamoDB...")
        imported = await import_to_dynamodb(documents)
        
        logger.info(f"Migration completed: {imported} documents imported")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
