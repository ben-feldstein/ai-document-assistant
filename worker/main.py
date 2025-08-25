"""Main worker module for background tasks."""

import asyncio
import logging
import signal
import sys
from typing import Optional
import redis.asyncio as redis
from sqlalchemy.orm import Session

from api.models.db import get_db_session
from api.models.entities import Doc, Embedding
from api.services.vectorizer import vectorizer_service
from api.services.cache import cache_service
from api.utils.config import get_redis_url, settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Worker:
    """Background worker for processing tasks."""
    
    def __init__(self):
        self.redis_url = get_redis_url()
        self.redis: Optional[redis.Redis] = None
        self.running = False
        self.tasks = []
        
    async def start(self):
        """Start the worker."""
        logger.info("Starting AI Voice Policy Assistant Worker...")
        
        try:
            # Connect to Redis
            await self._connect_redis()
            
            # Initialize vectorizer
            await vectorizer_service.get_model_info()
            logger.info("Vectorizer initialized successfully")
            
            # Start task processing
            self.running = True
            await self._process_tasks()
            
        except Exception as e:
            logger.error(f"Error starting worker: {e}")
            await self.stop()
            sys.exit(1)
    
    async def stop(self):
        """Stop the worker."""
        logger.info("Stopping worker...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close connections
        if self.redis:
            await self.redis.close()
        
        await vectorizer_service.close()
        logger.info("Worker stopped")
    
    async def _connect_redis(self):
        """Connect to Redis."""
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        await self.redis.ping()
        logger.info("Connected to Redis")
    
    async def _process_tasks(self):
        """Main task processing loop."""
        logger.info("Starting task processing loop...")
        
        while self.running:
            try:
                # Check for new tasks
                task_data = await self.redis.blpop("worker:embed_tasks", timeout=1)
                
                if task_data:
                    task_type, task_id = task_data
                    logger.info(f"Processing task: {task_id}")
                    
                    # Process the task
                    task = asyncio.create_task(self._process_embed_task(task_id))
                    self.tasks.append(task)
                    
                    # Clean up completed tasks
                    self.tasks = [t for t in self.tasks if not t.done()]
                
                # Process any pending embedding jobs
                await self._process_pending_embeddings()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_embed_task(self, task_id: str):
        """Process an embedding task."""
        try:
            # Get task details from Redis
            task_data = await self.redis.hgetall(f"worker:task:{task_id}")
            
            if not task_data:
                logger.warning(f"Task {task_id} not found")
                return
            
            task_type = task_data.get("type")
            
            if task_type == "embed_doc":
                doc_id = int(task_data.get("doc_id"))
                await self._embed_document(doc_id)
            elif task_type == "reindex_org":
                org_id = int(task_data.get("org_id"))
                await self._reindex_organization(org_id)
            else:
                logger.warning(f"Unknown task type: {task_type}")
            
            # Mark task as completed
            await self.redis.hset(f"worker:task:{task_id}", "status", "completed")
            await self.redis.expire(f"worker:task:{task_id}", 3600)  # 1 hour TTL
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            
            # Mark task as failed
            await self.redis.hset(f"worker:task:{task_id}", "status", "failed")
            await self.redis.hset(f"worker:task:{task_id}", "error", str(e))
            await self.redis.expire(f"worker:task:{task_id}", 3600)  # 1 hour TTL
    
    async def _process_pending_embeddings(self):
        """Process any documents that need embeddings."""
        try:
            db = get_db_session()
            
            # Find documents without embeddings
            docs_without_embeddings = db.query(Doc).outerjoin(Embedding).filter(
                Embedding.id.is_(None)
            ).limit(10).all()  # Process in batches
            
            for doc in docs_without_embeddings:
                await self._embed_document(doc.id)
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error processing pending embeddings: {e}")
    
    async def _embed_document(self, doc_id: int):
        """Generate embeddings for a document."""
        try:
            db = get_db_session()
            
            # Get the document
            doc = db.query(Doc).filter(Doc.id == doc_id).first()
            if not doc:
                logger.warning(f"Document {doc_id} not found")
                return
            
            # Check if document already has embeddings
            existing_embeddings = db.query(Embedding).filter(Embedding.doc_id == doc_id).count()
            if existing_embeddings > 0:
                logger.info(f"Document {doc_id} already has embeddings, skipping")
                return
            
            # Chunk the document
            chunks = self._chunk_text(doc.text, chunk_size=800, overlap=100)
            
            # Generate embeddings for each chunk
            embeddings = []
            for i, chunk in enumerate(chunks):
                embedding_vector = await vectorizer_service.get_embedding(chunk)
                
                if embedding_vector:
                    embedding = Embedding(
                        doc_id=doc_id,
                        chunk_text=chunk,
                        chunk_start=i * 800,
                        chunk_end=min((i + 1) * 800, len(doc.text)),
                        vector=embedding_vector,
                        model=settings.embed_model
                    )
                    embeddings.append(embedding)
            
            # Save embeddings to database
            if embeddings:
                db.add_all(embeddings)
                db.commit()
                logger.info(f"Generated {len(embeddings)} embeddings for document {doc_id}")
                
                # Clear document cache
                await cache_service.invalidate_cache(f"doc:{doc_id}:*")
            else:
                logger.warning(f"No embeddings generated for document {doc_id}")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error embedding document {doc_id}: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
    
    async def _reindex_organization(self, org_id: int):
        """Reindex all documents for an organization."""
        try:
            db = get_db_session()
            
            # Get all documents for the organization
            docs = db.query(Doc).filter(Doc.org_id == org_id).all()
            
            logger.info(f"Reindexing {len(docs)} documents for organization {org_id}")
            
            # Delete existing embeddings
            db.query(Embedding).join(Doc).filter(Doc.org_id == org_id).delete()
            
            # Regenerate embeddings
            for doc in docs:
                await self._embed_document(doc.id)
            
            # Clear organization cache
            await cache_service.invalidate_cache(f"org:{org_id}:*")
            
            logger.info(f"Reindexing completed for organization {org_id}")
            db.close()
            
        except Exception as e:
            logger.error(f"Error reindexing organization {org_id}: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
    
    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> list:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at word boundary
            if end < len(text):
                # Find last space before chunk_size
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - overlap)
        
        return chunks


async def main():
    """Main entry point."""
    worker = Worker()
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(worker.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
