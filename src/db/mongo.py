from __future__ import annotations

import logging
import time
from collections.abc import Iterable, Iterator
from contextlib import AbstractContextManager
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from tqdm import tqdm

from src.db.indexes import INDEX_DEFINITIONS

logger = logging.getLogger(__name__)


class MongoService(AbstractContextManager["MongoService"]):
    def __init__(self, uri: str, database_name: str, batch_size: int = 1000) -> None:
        self._uri = uri
        self._database_name = database_name
        self._batch_size = batch_size
        self._client: MongoClient[Any] | None = None
        self.db: Database[Any] | None = None

    def __enter__(self) -> "MongoService":
        if not self._uri:
            raise ValueError("MONGODB_URI is missing. Configure it in .env or environment.")

        self._client = MongoClient(self._uri)
        self.db = self._client[self._database_name]
        self._client.admin.command("ping")
        logger.info("Connected to MongoDB Atlas database '%s'", self._database_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._client:
            self._client.close()
            logger.info("MongoDB connection closed")

    def drop_existing_collections(self, collection_names: Iterable[str]) -> None:
        if not self.db:
            raise RuntimeError("Database is not initialized")
        for name in collection_names:
            self.db[name].drop()
            logger.info("Dropped target collection")

    def create_indexes(self) -> None:
        if not self.db:
            raise RuntimeError("Database is not initialized")

        for collection_name, indexes in INDEX_DEFINITIONS.items():
            collection = self.db[collection_name]
            for index_def in indexes:
                if index_def and isinstance(index_def[0], tuple):
                    collection.create_index(list(index_def), background=True)
                else:
                    field, direction = index_def  # type: ignore[misc]
                    unique = field in {"unique_id", "email", "slug"}
                    collection.create_index([(field, direction)], unique=unique, background=True)
            logger.info("Indexes created for target collection")

    def insert_from_iterable(self, collection_name: str, iterable: Iterable[dict[str, Any]], batch_size: int = 5000, show_progress: bool = True) -> int:
        """Insert documents from an iterable/generator into collection in batches.
        
        Args:
            collection_name: Name of the collection
            iterable: Iterator/iterable of documents
            batch_size: Size of each batch
            show_progress: Whether to show tqdm progress bar
        
        Returns:
            Total number of documents inserted
        """
        if not self.db:
            raise RuntimeError("Database is not initialized")

        collection = self.db[collection_name]
        total = 0
        batch: list[dict[str, Any]] = []
        start_time = time.time()

        # Wrap iterable in tqdm if progress tracking enabled
        iterator: Iterator[dict[str, Any]] = (
            tqdm(iterable, desc=f"Generating {collection_name}", unit=" docs")
            if show_progress
            else iter(iterable)
        )

        for doc in iterator:
            batch.append(doc)
            if len(batch) >= batch_size:
                collection.insert_many(batch, ordered=False)
                total += len(batch)
                batch = []

        # Insert remaining documents
        if batch:
            collection.insert_many(batch, ordered=False)
            total += len(batch)

        elapsed = time.time() - start_time
        speed = total / elapsed if elapsed > 0 else 0
        logger.info("Batch insertion completed successfully.")
        return total

    def insert_many_in_batches(self, collection_name: str, documents: list[dict[str, Any]]) -> int:
        """Insert a list of documents into collection in batches (legacy method)."""
        if not self.db:
            raise RuntimeError("Database is not initialized")
        if not documents:
            return 0

        total = 0
        collection = self.db[collection_name]
        for start in range(0, len(documents), self._batch_size):
            chunk = documents[start : start + self._batch_size]
            collection.insert_many(chunk, ordered=False)
            total += len(chunk)
        logger.info("Batch insert completed")
        return total
