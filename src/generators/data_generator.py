from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from faker import Faker

from src.utils.ids import make_unique_id

POPULAR_CATEGORIES = [
    ("Data Science", 0.18),
    ("Web Development", 0.17),
    ("Business", 0.13),
    ("Cloud Computing", 0.11),
    ("Cybersecurity", 0.10),
    ("AI & Machine Learning", 0.10),
    ("Design", 0.08),
    ("Marketing", 0.07),
    ("Language Learning", 0.06),
]

COUNTRY_LANGUAGE = [
    ("France", "fr_FR", "EUR", "French"),
    ("Canada", "en_CA", "CAD", "English"),
    ("United States", "en_US", "USD", "English"),
    ("United Kingdom", "en_GB", "GBP", "English"),
    ("Germany", "de_DE", "EUR", "German"),
    ("Spain", "es_ES", "EUR", "Spanish"),
    ("India", "en_IN", "INR", "English"),
    ("Nigeria", "en_NG", "NGN", "English"),
]


@dataclass(slots=True)
class GenerationConfig:
    learners: int = 1200
    instructor_ratio: float = 0.06
    courses_per_instructor_min: int = 2
    courses_per_instructor_max: int = 6
    max_enrollments_per_user: int = 10


def _weighted_choice(options: list[tuple[Any, float]]) -> Any:
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


def _slugify(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def generate_dataset(seed: int | None, config: GenerationConfig) -> dict[str, list[dict[str, Any]]]:
    if seed is not None:
        random.seed(seed)
    faker = Faker()
    if seed is not None:
        Faker.seed(seed)

    now = datetime.now(UTC)

    users: list[dict[str, Any]] = []
    instructors: list[dict[str, Any]] = []
    categories: list[dict[str, Any]] = []
    courses: list[dict[str, Any]] = []
    modules: list[dict[str, Any]] = []
    lessons: list[dict[str, Any]] = []
    enrollments: list[dict[str, Any]] = []
    progress_events: list[dict[str, Any]] = []
    quizzes: list[dict[str, Any]] = []
    quiz_attempts: list[dict[str, Any]] = []
    payments: list[dict[str, Any]] = []
    subscriptions: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    support_tickets: list[dict[str, Any]] = []

    total_instructors = max(5, int(config.learners * config.instructor_ratio))
    total_users = config.learners + total_instructors

    for i in range(1, total_users + 1):
        country, locale, _, language = random.choice(COUNTRY_LANGUAGE)
        local_faker = Faker(locale)
        gender = random.choice(["male", "female", "other"])
        first_name = local_faker.first_name_male() if gender == "male" else local_faker.first_name_female()
        if gender == "other":
            first_name = local_faker.first_name()
        last_name = local_faker.last_name()

        signup_date = now - timedelta(days=random.randint(7, 1200))
        role = "learner"
        if i <= total_instructors:
            role = random.choices(["instructor", "instructor_learner"], weights=[0.7, 0.3], k=1)[0]

        users.append(
            {
                "unique_id": make_unique_id("USR", i),
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{_slugify(first_name)}.{_slugify(last_name)}.{i}@example.com",
                "phone": local_faker.phone_number(),
                "gender": gender,
                "date_of_birth": local_faker.date_of_birth(minimum_age=18, maximum_age=70),
                "country": country,
                "city": local_faker.city(),
                "language": language,
                "role": role,
                "signup_date": signup_date,
                "status": random.choices(["active", "inactive", "suspended"], weights=[0.84, 0.12, 0.04], k=1)[0],
                "last_login_at": signup_date + timedelta(days=random.randint(0, max(1, (now - signup_date).days))),
            }
        )

    instructor_users = users[:total_instructors]
    for i, user in enumerate(instructor_users, start=1):
        expertise_domain = random.choice(["Python", "Data Engineering", "AWS", "SQL", "Power BI", "AI", "DevOps"])
        created_at = user["signup_date"] + timedelta(days=random.randint(0, 60))
        instructors.append(
            {
                "unique_id": make_unique_id("INS", i),
                "user_unique_id": user["unique_id"],
                "headline": f"Senior {expertise_domain} Instructor",
                "bio": faker.paragraph(nb_sentences=4),
                "expertise": random.sample(
                    ["Python", "SQL", "Spark", "Airflow", "MongoDB", "Docker", "Kubernetes", "dbt", "Pandas"],
                    k=random.randint(3, 6),
                ),
                "years_experience": random.randint(2, 20),
                "rating_avg": round(random.triangular(3.1, 5.0, 4.4), 2),
                "total_students": max(50, int(abs(random.gauss(2000, 1800)))),
                "social_links": {
                    "linkedin": faker.url(),
                    "x": faker.url(),
                },
                "verification_status": random.choices(["verified", "pending", "rejected"], weights=[0.8, 0.16, 0.04], k=1)[0],
                "created_at": created_at,
            }
        )

    for idx, (name, _) in enumerate(POPULAR_CATEGORIES, start=1):
        categories.append(
            {
                "unique_id": make_unique_id("CAT", idx),
                "name": name,
                "slug": _slugify(name),
                "description": faker.sentence(nb_words=14),
                "parent_category_unique_id": None,
                "is_active": random.choices([True, False], weights=[0.97, 0.03], k=1)[0],
                "created_at": now - timedelta(days=random.randint(400, 1300)),
            }
        )

    category_ids = [c["unique_id"] for c in categories]
    instructor_ids = [ins["unique_id"] for ins in instructors]

    course_idx = 1
    module_idx = 1
    lesson_idx = 1
    quiz_idx = 1

    lessons_by_course: dict[str, list[str]] = defaultdict(list)
    modules_by_course: dict[str, list[str]] = defaultdict(list)
    quizzes_by_course: dict[str, list[str]] = defaultdict(list)

    for instructor_unique_id in instructor_ids:
        course_count = random.randint(config.courses_per_instructor_min, config.courses_per_instructor_max)
        for _ in range(course_count):
            category_unique_id = _weighted_choice([(c["unique_id"], w) for c, (_, w) in zip(categories, POPULAR_CATEGORIES)])
            title = faker.sentence(nb_words=random.randint(4, 8)).rstrip(".")
            published_at = now - timedelta(days=random.randint(1, 1000))
            price = round(max(0, random.lognormvariate(3.4, 0.5)), 2)
            is_free = random.random() < 0.18
            discount = round(price * random.uniform(0.1, 0.6), 2)
            discount_price = 0.0 if is_free else max(0.0, round(price - discount, 2))

            course_unique_id = make_unique_id("CRS", course_idx)
            courses.append(
                {
                    "unique_id": course_unique_id,
                    "category_unique_id": category_unique_id,
                    "instructor_unique_id": instructor_unique_id,
                    "title": title,
                    "slug": f"{_slugify(title)}-{course_idx}",
                    "description": faker.paragraph(nb_sentences=5),
                    "level": random.choices(["beginner", "intermediate", "advanced"], weights=[0.5, 0.34, 0.16], k=1)[0],
                    "language": random.choice(["English", "French", "Spanish", "German"]),
                    "price": 0.0 if is_free else price,
                    "discount_price": discount_price,
                    "duration_hours": round(random.triangular(2, 70, 18), 1),
                    "thumbnail_url": faker.image_url(),
                    "tags": random.sample(
                        ["python", "sql", "etl", "analytics", "aws", "docker", "ml", "bi", "api", "mongodb"],
                        k=random.randint(3, 6),
                    ),
                    "status": random.choices(["published", "draft", "archived"], weights=[0.87, 0.1, 0.03], k=1)[0],
                    "published_at": published_at,
                    "updated_at": published_at + timedelta(days=random.randint(0, 180)),
                }
            )

            module_count = random.randint(3, 10)
            for mod_order in range(1, module_count + 1):
                module_unique_id = make_unique_id("MOD", module_idx)
                module_created = published_at + timedelta(days=random.randint(0, 30))
                modules.append(
                    {
                        "unique_id": module_unique_id,
                        "course_unique_id": course_unique_id,
                        "title": f"Module {mod_order}: {faker.sentence(nb_words=4).rstrip('.')}",
                        "order_index": mod_order,
                        "is_free_preview": mod_order == 1,
                        "created_at": module_created,
                    }
                )
                modules_by_course[course_unique_id].append(module_unique_id)
                module_idx += 1

                lesson_count = random.randint(3, 9)
                for lesson_order in range(1, lesson_count + 1):
                    lesson_unique_id = make_unique_id("LES", lesson_idx)
                    lessons.append(
                        {
                            "unique_id": lesson_unique_id,
                            "course_unique_id": course_unique_id,
                            "module_unique_id": module_unique_id,
                            "title": faker.sentence(nb_words=5).rstrip("."),
                            "lesson_type": random.choices(
                                ["video", "article", "exercise", "live_session"],
                                weights=[0.66, 0.18, 0.12, 0.04],
                                k=1,
                            )[0],
                            "duration_minutes": max(3, int(abs(random.gauss(18, 9)))),
                            "resource_urls": [faker.url() for _ in range(random.randint(0, 2))],
                            "order_index": lesson_order,
                            "is_free_preview": mod_order == 1 and lesson_order <= 2,
                            "created_at": module_created + timedelta(hours=lesson_order),
                        }
                    )
                    lessons_by_course[course_unique_id].append(lesson_unique_id)
                    lesson_idx += 1

                if random.random() < 0.72:
                    quiz_unique_id = make_unique_id("QZ", quiz_idx)
                    quizzes.append(
                        {
                            "unique_id": quiz_unique_id,
                            "course_unique_id": course_unique_id,
                            "module_unique_id": module_unique_id,
                            "title": f"{faker.word().title()} Assessment",
                            "quiz_type": random.choice(["mcq", "coding", "mixed"]),
                            "total_questions": random.randint(5, 35),
                            "passing_score": random.choice([60, 65, 70, 75]),
                            "time_limit_minutes": random.choice([10, 15, 20, 30, 45]),
                            "created_at": module_created + timedelta(days=random.randint(0, 20)),
                        }
                    )
                    quizzes_by_course[course_unique_id].append(quiz_unique_id)
                    quiz_idx += 1

            course_idx += 1

    learner_users = users[total_instructors:]
    course_ids = [course["unique_id"] for course in courses]
    course_weights = [random.uniform(0.3, 3.0) for _ in course_ids]

    enrollment_idx = 1
    progress_idx = 1
    payment_idx = 1
    review_idx = 1
    certificate_idx = 1
    attempt_idx = 1
    subscription_idx = 1
    ticket_idx = 1

    completed_enrollments: list[dict[str, Any]] = []
    paid_enrollments: list[dict[str, Any]] = []

    for user in learner_users:
        enrollment_count = random.randint(0, config.max_enrollments_per_user)
        picked_courses = set(random.choices(course_ids, weights=course_weights, k=enrollment_count))
        for course_unique_id in picked_courses:
            course = next(c for c in courses if c["unique_id"] == course_unique_id)
            enrollment_date = max(
                user["signup_date"],
                course["published_at"] + timedelta(days=random.randint(0, 180)),
            )
            progress_percent = min(100, max(0, int(random.betavariate(1.4, 1.8) * 120)))
            completion_status = "completed" if progress_percent >= random.randint(85, 100) else "in_progress"
            completed_at = (
                enrollment_date + timedelta(days=random.randint(7, 180))
                if completion_status == "completed"
                else None
            )

            enroll_doc = {
                "unique_id": make_unique_id("ENR", enrollment_idx),
                "user_unique_id": user["unique_id"],
                "course_unique_id": course_unique_id,
                "enrollment_date": enrollment_date,
                "enrollment_source": random.choices(
                    ["organic", "ads", "referral", "affiliate", "partner"],
                    weights=[0.46, 0.22, 0.16, 0.10, 0.06],
                    k=1,
                )[0],
                "progress_percent": progress_percent,
                "completion_status": completion_status,
                "completed_at": completed_at,
                "last_accessed_at": enrollment_date + timedelta(days=random.randint(0, max(1, (now - enrollment_date).days))),
            }
            enrollments.append(enroll_doc)

            if completion_status == "completed":
                completed_enrollments.append(enroll_doc)

            if course["price"] > 0:
                payment_status = random.choices(["paid", "failed", "refunded"], weights=[0.9, 0.06, 0.04], k=1)[0]
                payments.append(
                    {
                        "unique_id": make_unique_id("PAY", payment_idx),
                        "user_unique_id": user["unique_id"],
                        "course_unique_id": course_unique_id,
                        "payment_method": random.choice(["card", "paypal", "bank_transfer", "mobile_money"]),
                        "amount": course["discount_price"] if course["discount_price"] else course["price"],
                        "currency": random.choice(["USD", "EUR", "GBP", "CAD", "INR", "NGN"]),
                        "payment_status": payment_status,
                        "transaction_reference": faker.uuid4(),
                        "payment_date": enrollment_date + timedelta(minutes=random.randint(1, 180)),
                        "provider": random.choice(["stripe", "paypal", "adyen", "flutterwave"]),
                    }
                )
                payment_idx += 1
                if payment_status == "paid":
                    paid_enrollments.append(enroll_doc)

            lesson_candidates = lessons_by_course[course_unique_id]
            if lesson_candidates:
                for _ in range(random.randint(1, 12)):
                    event_time = enrollment_date + timedelta(days=random.randint(0, max(1, (now - enrollment_date).days)))
                    progress_events.append(
                        {
                            "unique_id": make_unique_id("PRG", progress_idx),
                            "user_unique_id": user["unique_id"],
                            "course_unique_id": course_unique_id,
                            "lesson_unique_id": random.choice(lesson_candidates),
                            "event_type": random.choice(["started", "paused", "resumed", "completed_lesson", "seek"]),
                            "progress_percent": min(100, max(0, progress_percent + random.randint(-20, 8))),
                            "event_timestamp": event_time,
                            "device_type": random.choice(["web", "android", "ios", "tablet"]),
                        }
                    )
                    progress_idx += 1

            for quiz_unique_id in random.sample(quizzes_by_course.get(course_unique_id, []), k=min(2, len(quizzes_by_course.get(course_unique_id, [])))):
                max_score = 100
                score = max(0, min(100, int(random.gauss(72, 18))))
                started_at = enrollment_date + timedelta(days=random.randint(1, 200))
                submitted_at = started_at + timedelta(minutes=random.randint(5, 50))
                quiz_attempts.append(
                    {
                        "unique_id": make_unique_id("QZA", attempt_idx),
                        "quiz_unique_id": quiz_unique_id,
                        "user_unique_id": user["unique_id"],
                        "attempt_number": random.randint(1, 3),
                        "score": score,
                        "max_score": max_score,
                        "passed": score >= random.choice([60, 65, 70]),
                        "started_at": started_at,
                        "submitted_at": submitted_at,
                        "duration_seconds": int((submitted_at - started_at).total_seconds()),
                    }
                )
                attempt_idx += 1

            enrollment_idx += 1

    subscribed_users = random.sample(learner_users, k=max(1, int(len(learner_users) * 0.25)))
    for user in subscribed_users:
        start_date = user["signup_date"] + timedelta(days=random.randint(0, 120))
        billing_period = random.choice(["monthly", "yearly"])
        duration_days = 30 if billing_period == "monthly" else 365
        status = random.choices(["active", "paused", "cancelled", "expired"], weights=[0.7, 0.08, 0.12, 0.10], k=1)[0]
        end_date = start_date + timedelta(days=duration_days)
        subscriptions.append(
            {
                "unique_id": make_unique_id("SUB", subscription_idx),
                "user_unique_id": user["unique_id"],
                "plan_name": random.choice(["starter", "pro", "team"]),
                "billing_period": billing_period,
                "start_date": start_date,
                "end_date": end_date,
                "auto_renew": status == "active",
                "status": status,
                "monthly_price": round(random.choice([12.0, 19.0, 24.0, 39.0]), 2),
                "currency": random.choice(["USD", "EUR", "GBP", "CAD"]),
            }
        )
        subscription_idx += 1

    review_sources = completed_enrollments if completed_enrollments else paid_enrollments
    for enroll in random.sample(review_sources, k=min(len(review_sources), max(1, int(len(review_sources) * 0.55)))):
        rating = random.choices([1, 2, 3, 4, 5], weights=[0.04, 0.07, 0.14, 0.33, 0.42], k=1)[0]
        reviews.append(
            {
                "unique_id": make_unique_id("REV", review_idx),
                "user_unique_id": enroll["user_unique_id"],
                "course_unique_id": enroll["course_unique_id"],
                "rating": rating,
                "review_title": faker.sentence(nb_words=6).rstrip("."),
                "review_text": faker.paragraph(nb_sentences=2),
                "helpful_votes": max(0, int(abs(random.gauss(7, 12)))),
                "created_at": (enroll["completed_at"] or enroll["enrollment_date"]) + timedelta(days=random.randint(1, 40)),
                "verified_purchase": any(
                    p["user_unique_id"] == enroll["user_unique_id"] and p["course_unique_id"] == enroll["course_unique_id"] and p["payment_status"] == "paid"
                    for p in payments
                ),
            }
        )
        review_idx += 1

    for enroll in completed_enrollments:
        if random.random() < 0.78:
            certificates.append(
                {
                    "unique_id": make_unique_id("CRT", certificate_idx),
                    "user_unique_id": enroll["user_unique_id"],
                    "course_unique_id": enroll["course_unique_id"],
                    "issued_at": enroll["completed_at"] + timedelta(hours=random.randint(6, 72)),
                    "certificate_url": faker.url(),
                    "verification_code": faker.bothify(text="CERT-#####-????").upper(),
                    "status": random.choices(["active", "revoked"], weights=[0.98, 0.02], k=1)[0],
                    "score_final": random.randint(60, 100),
                }
            )
            certificate_idx += 1

    ticket_users = random.sample(users, k=max(1, int(len(users) * 0.15)))
    for user in ticket_users:
        created_at = user["signup_date"] + timedelta(days=random.randint(0, max(1, (now - user["signup_date"]).days)))
        resolved = random.random() < 0.68
        resolved_at = created_at + timedelta(hours=random.randint(2, 240)) if resolved else None
        support_tickets.append(
            {
                "unique_id": make_unique_id("TKT", ticket_idx),
                "user_unique_id": user["unique_id"],
                "ticket_type": random.choice(["billing", "technical", "content", "account", "refund"]),
                "priority": random.choices(["low", "medium", "high", "urgent"], weights=[0.42, 0.34, 0.18, 0.06], k=1)[0],
                "subject": faker.sentence(nb_words=7).rstrip("."),
                "message": faker.paragraph(nb_sentences=3),
                "status": "resolved" if resolved else random.choice(["open", "pending"]),
                "created_at": created_at,
                "resolved_at": resolved_at,
                "channel": random.choice(["email", "chat", "web_form"]),
            }
        )
        ticket_idx += 1

    return {
        "users": users,
        "instructors": instructors,
        "categories": categories,
        "courses": courses,
        "course_modules": modules,
        "lessons": lessons,
        "enrollments": enrollments,
        "progress_events": progress_events,
        "quizzes": quizzes,
        "quiz_attempts": quiz_attempts,
        "payments": payments,
        "subscriptions": subscriptions,
        "reviews": reviews,
        "certificates": certificates,
        "support_tickets": support_tickets,
    }
