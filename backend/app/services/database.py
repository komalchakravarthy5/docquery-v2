"""
Database Service
Manages SQLite database for document and chunk metadata.
"""

import aiosqlite
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from app.config import get_settings

settings = get_settings()


class DatabaseService:
    """Manages SQLite database operations"""
    
    def __init__(self):
        """Initialize database service"""
        self.db_path = settings.database_path
        self._initialized = False
        self._init_lock = asyncio.Lock()
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Create database tables if they don't exist"""
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            async with aiosqlite.connect(self.db_path) as db:
                # Create documents table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        upload_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        num_pages INTEGER NOT NULL,
                        num_chunks INTEGER NOT NULL,
                        file_path TEXT NOT NULL
                    )
                """)
                
                # Create chunks table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id TEXT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        page_number INTEGER NOT NULL,
                        source_file TEXT,
                        source_page_number INTEGER,
                        text TEXT NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                    )
                """)

                # Backward-compatible lightweight migration for existing databases
                async with db.execute("PRAGMA table_info(chunks)") as cursor:
                    columns = {row[1] for row in await cursor.fetchall()}

                if "source_file" not in columns:
                    await db.execute("ALTER TABLE chunks ADD COLUMN source_file TEXT")
                if "source_page_number" not in columns:
                    await db.execute("ALTER TABLE chunks ADD COLUMN source_page_number INTEGER")
                
                # Create index for faster queries
                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_document_id 
                    ON chunks(document_id)
                """)

                # Query metrics persistence for longitudinal benchmarking
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS query_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        latency_ms REAL NOT NULL,
                        avg_relevance_score REAL NOT NULL,
                        num_citations INTEGER NOT NULL,
                        answer_found INTEGER NOT NULL,
                        grounding_score REAL NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                    )
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query_metrics_document_id
                    ON query_metrics(document_id)
                """)
                
                await db.commit()
                self._initialized = True
    
    async def create_document(
        self,
        document_id: str,
        filename: str,
        num_pages: int,
        num_chunks: int,
        file_path: str
    ) -> bool:
        """
        Insert a new document into the database.
        
        Args:
            document_id: Unique document identifier
            filename: Original filename
            num_pages: Number of pages in document
            num_chunks: Number of chunks created
            file_path: Path to stored file
            
        Returns:
            True if successful
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO documents (id, filename, num_pages, num_chunks, file_path)
                VALUES (?, ?, ?, ?, ?)
            """, (document_id, filename, num_pages, num_chunks, file_path))
            await db.commit()
        return True
    
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """
        Retrieve document metadata.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document dictionary or None if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM documents WHERE id = ?",
                (document_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        return None
    
    async def list_documents(self) -> List[Dict]:
        """
        List all documents in the database.
        
        Returns:
            List of document dictionaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM documents ORDER BY upload_timestamp DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document and its chunks.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if deleted
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Delete chunks first (foreign key constraint)
            await db.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            # Delete document
            await db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            await db.commit()
        return True
    
    async def insert_chunks(self, document_id: str, chunks: List[Dict]) -> bool:
        """
        Insert chunks for a document.
        
        Args:
            document_id: Document identifier
            chunks: List of chunk dictionaries with 'chunk_id', 'text', 'page_number'
            
        Returns:
            True if successful
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Prepare data for batch insert
            chunk_data = [
                (
                    document_id,
                    chunk["chunk_id"],
                    chunk["page_number"],
                    chunk.get("source_file"),
                    chunk.get("source_page_number", chunk["page_number"]),
                    chunk["text"],
                )
                for chunk in chunks
            ]
            
            await db.executemany("""
                INSERT INTO chunks (
                    document_id,
                    chunk_index,
                    page_number,
                    source_file,
                    source_page_number,
                    text
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, chunk_data)
            
            await db.commit()
        return True
    
    async def get_chunks_by_indices(
        self,
        document_id: str,
        chunk_indices: List[int]
    ) -> List[Dict]:
        """
        Retrieve specific chunks by their indices.
        
        Args:
            document_id: Document identifier
            chunk_indices: List of chunk indices to retrieve
            
        Returns:
            List of chunk dictionaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Create placeholders for IN clause
            placeholders = ','.join('?' * len(chunk_indices))
            query = f"""
                SELECT * FROM chunks 
                WHERE document_id = ? AND chunk_index IN ({placeholders})
            """
            
            params = [document_id] + chunk_indices
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_all_chunks(self, document_id: str) -> List[Dict]:
        """
        Retrieve all chunks for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of chunk dictionaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
                (document_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def document_exists(self, document_id: str) -> bool:
        """
        Check if document exists in database.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if exists, False otherwise
        """
        doc = await self.get_document(document_id)
        return doc is not None

    async def insert_query_metric(
        self,
        document_id: str,
        latency_ms: float,
        avg_relevance_score: float,
        num_citations: int,
        answer_found: bool,
        grounding_score: float,
    ) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO query_metrics (
                    document_id,
                    latency_ms,
                    avg_relevance_score,
                    num_citations,
                    answer_found,
                    grounding_score
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    latency_ms,
                    avg_relevance_score,
                    num_citations,
                    1 if answer_found else 0,
                    grounding_score,
                ),
            )
            await db.commit()
        return True

    async def get_query_metrics(self, document_id: str, limit: int = 100) -> List[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM query_metrics
                WHERE document_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (document_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


# Singleton instance
database_service = DatabaseService()
