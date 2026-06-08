from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    mongodb_uri: str
    mongodb_db_name: str
    batch_size: int = 5000
    default_seed: int | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        mongodb_uri = os.getenv("MONGODB_URI", "").strip()
        mongodb_db_name = os.getenv("MONGODB_DB_NAME", "elearning_synthetic").strip()
        batch_size = int(os.getenv("BATCH_SIZE", "1000"))

        default_seed_raw = os.getenv("DEFAULT_SEED", "").strip()
        default_seed = int(default_seed_raw) if default_seed_raw else None

        return cls(
            mongodb_uri=mongodb_uri,
            mongodb_db_name=mongodb_db_name,
            batch_size=max(1, batch_size),
            default_seed=default_seed,
        )
