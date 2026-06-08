from __future__ import annotations

import logging
from collections.abc import Iterable
from contextlib import AbstractContextManager
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

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
            logger.info("Dropped collection '%s'", name)

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
            logger.info("Indexes created for '%s'", collection_name)

    def insert_many_in_batches(self, collection_name: str, documents: list[dict[str, Any]]) -> int:
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
        logger.info("Inserted %s documents into '%s'", total, collection_name)
        return total
