from __future__ import annotations

import argparse
import logging
import sys

from src.config.settings import Settings
from src.db.mongo import MongoService
from src.generators.data_generator import GenerationConfig, generate_dataset
from src.utils.logging_utils import configure_logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate coherent synthetic e-learning data and optionally load it to MongoDB Atlas.",
    )
    parser.add_argument("--learners", type=int, default=1200, help="Number of learner profiles to generate.")
    parser.add_argument("--instructor-ratio", type=float, default=0.06, help="Instructor count ratio based on learners.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible generation.")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size for MongoDB insert operations.")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing target collections before insertion.")
    parser.add_argument("--dry-run", action="store_true", help="Generate data without inserting into MongoDB.")
    return parser


def main() -> None:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    if args.learners <= 0:
        parser.error("--learners must be > 0")
    if not (0.01 <= args.instructor_ratio <= 0.5):
        parser.error("--instructor-ratio must be between 0.01 and 0.5")

    settings = Settings.from_env()

    seed = args.seed if args.seed is not None else settings.default_seed
    generation_config = GenerationConfig(
        learners=args.learners,
        instructor_ratio=args.instructor_ratio,
    )
    dataset = generate_dataset(seed=seed, config=generation_config)

    logger.info("Synthetic data generated with seed=%s", seed)
    for name, records in dataset.items():
        logger.info("%s: %s", name, len(records))

    if args.dry_run:
        logger.info("Dry run enabled; no MongoDB write executed.")
        return

    batch_size = args.batch_size or settings.batch_size

    try:
        with MongoService(settings.mongodb_uri, settings.mongodb_db_name, batch_size=batch_size) as mongo:
            collection_names = list(dataset.keys())
            if args.drop_existing:
                mongo.drop_existing_collections(collection_names)

            mongo.create_indexes()
            for collection_name, documents in dataset.items():
                mongo.insert_many_in_batches(collection_name, documents)
    except Exception as exc:  # pragma: no cover - operational safety
        logger.exception("Data generation/insertion failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
