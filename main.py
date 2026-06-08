from __future__ import annotations

import argparse
import logging
import sys
import time
from collections.abc import Iterator

from src.config.settings import Settings
from src.db.mongo import MongoService
from src.generators.batch_generator import BatchGenerator, BatchGenerationConfig
from src.utils.logging_utils import configure_logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate coherent synthetic e-learning data in batches and load to MongoDB Atlas.",
    )
    parser.add_argument("--users", type=int, default=1200, help="Number of users to generate (includes instructors).")
    parser.add_argument("--courses", type=int, default=100, help="Number of courses to generate.")
    parser.add_argument(
        "--enrollments-per-user", type=int, default=5, help="Average number of enrollments per user."
    )
    parser.add_argument("--instructor-ratio", type=float, default=0.06, help="Instructor count ratio based on users.")
    parser.add_argument("--courses-per-instructor-min", type=int, default=2, help="Minimum courses per instructor.")
    parser.add_argument("--courses-per-instructor-max", type=int, default=6, help="Maximum courses per instructor.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible generation.")
    parser.add_argument("--batch-size", type=int, default=5000, help="Batch size for MongoDB insert operations.")
    parser.add_argument("--drop-existing", action="store_true", help="Drop existing target collections before insertion.")
    parser.add_argument("--dry-run", action="store_true", help="Generate data without inserting into MongoDB.")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress bars.")
    return parser


def main() -> None:
    configure_logging()
    parser = build_parser()
    args = parser.parse_args()

    # Validate arguments
    if args.users <= 0:
        parser.error("--users must be > 0")
    if args.courses <= 0:
        parser.error("--courses must be > 0")
    if not (0.01 <= args.instructor_ratio <= 0.5):
        parser.error("--instructor-ratio must be between 0.01 and 0.5")
    if args.batch_size <= 0:
        parser.error("--batch-size must be > 0")

    settings = Settings.from_env()
    batch_size = args.batch_size or settings.batch_size

    seed = args.seed if args.seed is not None else settings.default_seed
    logger.info(f"Configuration: users={args.users}, courses={args.courses}, batch_size={batch_size}, seed={seed}")

    # Create batch generator
    config = BatchGenerationConfig(
        num_users=args.users,
        num_courses=args.courses,
        num_enrollments_per_user=args.enrollments_per_user,
        instructor_ratio=args.instructor_ratio,
        courses_per_instructor_min=args.courses_per_instructor_min,
        courses_per_instructor_max=args.courses_per_instructor_max,
        batch_size=batch_size,
        seed=seed,
    )
    generator = BatchGenerator(config)

    # Pre-cache dependencies for referenced entities
    logger.info("Pre-generating required reference data...")
    categories = list(generator.generate_categories_batch())
    logger.info(f"Generated {len(categories)} categories")

    users = list(generator.generate_users_batch())
    logger.info(f"Generated {len(users)} users")

    instructors = list(generator.generate_instructors_batch(users))
    logger.info(f"Generated {len(instructors)} instructors")

    courses = list(generator.generate_courses_batch(categories, instructors))
    logger.info(f"Generated {len(courses)} courses")

    enrollments = list(generator.generate_enrollments_batch(users, courses))
    logger.info(f"Generated {len(enrollments)} enrollments")

    quizzes = list(generator.generate_quizzes_batch(courses))
    logger.info(f"Generated {len(quizzes)} quizzes")

    if args.dry_run:
        logger.info("Dry run enabled; generated data summary:")
        logger.info(f"  - {len(categories)} categories")
        logger.info(f"  - {len(users)} users")
        logger.info(f"  - {len(instructors)} instructors")
        logger.info(f"  - {len(courses)} courses")
        logger.info(f"  - {len(enrollments)} enrollments")
        logger.info(f"  - {len(quizzes)} quizzes")
        return

    show_progress = not args.no_progress

    # MongoDB insertion with batching
    collection_order = [
        ("categories", categories),
        ("users", users),
        ("instructors", instructors),
        ("courses", courses),
        ("course_modules", generator.generate_modules_and_lessons_batch(courses)[0]),
        ("lessons", generator.generate_modules_and_lessons_batch(courses)[1]),
        ("enrollments", enrollments),
        ("progress_events", generator.generate_progress_events_batch(enrollments, courses)),
        ("quizzes", quizzes),
        ("quiz_attempts", generator.generate_quiz_attempts_batch(enrollments, quizzes)),
        ("payments", generator.generate_payments_batch(enrollments, courses)),
        ("subscriptions", generator.generate_subscriptions_batch(users)),
        ("reviews", generator.generate_reviews_batch(enrollments)),
        ("certificates", generator.generate_certificates_batch(enrollments)),
        ("support_tickets", generator.generate_support_tickets_batch(users)),
    ]

    try:
        start_time = time.time()
        with MongoService(settings.mongodb_uri, settings.mongodb_db_name, batch_size=batch_size) as mongo:
            collection_names = [name for name, _ in collection_order]

            if args.drop_existing:
                logger.info("Dropping existing collections...")
                mongo.drop_existing_collections(collection_names)

            logger.info("Creating indexes...")
            mongo.create_indexes()

            logger.info("Starting batch insertion in dependency order...")
            for collection_name, data_iterable in collection_order:
                # If data is a list, convert to iterator
                if isinstance(data_iterable, list):
                    iterable = iter(data_iterable)
                else:
                    iterable = data_iterable

                inserted = mongo.insert_from_iterable(collection_name, iterable, batch_size=batch_size, show_progress=show_progress)
                logger.info(f"Completed: {collection_name} ({inserted} documents)")

        elapsed = time.time() - start_time
        logger.info(f"Data insertion completed in {elapsed:.2f}s")

    except Exception as exc:
        logger.exception("Data generation/insertion failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
