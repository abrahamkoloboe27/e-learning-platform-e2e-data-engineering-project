from __future__ import annotations

from pymongo import ASCENDING

INDEX_DEFINITIONS: dict[str, list[tuple[str, int] | tuple[tuple[str, int], ...]]] = {
    "users": [("unique_id", ASCENDING), ("email", ASCENDING), ("role", ASCENDING)],
    "instructors": [("unique_id", ASCENDING), ("user_unique_id", ASCENDING)],
    "categories": [("unique_id", ASCENDING), ("slug", ASCENDING)],
    "courses": [
        ("unique_id", ASCENDING),
        ("slug", ASCENDING),
        ("category_unique_id", ASCENDING),
        ("instructor_unique_id", ASCENDING),
    ],
    "course_modules": [("unique_id", ASCENDING), ("course_unique_id", ASCENDING)],
    "lessons": [
        ("unique_id", ASCENDING),
        ("course_unique_id", ASCENDING),
        ("module_unique_id", ASCENDING),
    ],
    "enrollments": [
        ("unique_id", ASCENDING),
        ("user_unique_id", ASCENDING),
        ("course_unique_id", ASCENDING),
        (("user_unique_id", ASCENDING), ("course_unique_id", ASCENDING)),
    ],
    "progress_events": [
        ("unique_id", ASCENDING),
        ("user_unique_id", ASCENDING),
        ("course_unique_id", ASCENDING),
        ("lesson_unique_id", ASCENDING),
    ],
    "quizzes": [("unique_id", ASCENDING), ("course_unique_id", ASCENDING), ("module_unique_id", ASCENDING)],
    "quiz_attempts": [("unique_id", ASCENDING), ("quiz_unique_id", ASCENDING), ("user_unique_id", ASCENDING)],
    "payments": [("unique_id", ASCENDING), ("user_unique_id", ASCENDING), ("course_unique_id", ASCENDING)],
    "subscriptions": [("unique_id", ASCENDING), ("user_unique_id", ASCENDING), ("status", ASCENDING)],
    "reviews": [("unique_id", ASCENDING), ("user_unique_id", ASCENDING), ("course_unique_id", ASCENDING)],
    "certificates": [("unique_id", ASCENDING), ("user_unique_id", ASCENDING), ("course_unique_id", ASCENDING)],
    "support_tickets": [("unique_id", ASCENDING), ("user_unique_id", ASCENDING), ("status", ASCENDING)],
}
