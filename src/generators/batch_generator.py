from __future__ import annotations

import random
from collections.abc import Iterator
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
class BatchGenerationConfig:
    """Configuration for batch data generation."""
    num_users: int = 1200
    num_courses: int = 100
    num_enrollments_per_user: int = 5
    instructor_ratio: float = 0.06
    courses_per_instructor_min: int = 2
    courses_per_instructor_max: int = 6
    batch_size: int = 5000
    seed: int | None = None


def _weighted_choice(options: list[tuple[Any, float]]) -> Any:
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


def _slugify(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


class BatchGenerator:
    """Main batch generator orchestrating the generation pipeline."""

    def __init__(self, config: BatchGenerationConfig) -> None:
        self.config = config
        self.seed = config.seed
        self._setup_random()
        self.now = datetime.now(UTC)
        self._id_counters: dict[str, int] = {
            "users": 0,
            "instructors": 0,
            "categories": 0,
            "courses": 0,
            "modules": 0,
            "lessons": 0,
            "enrollments": 0,
            "progress_events": 0,
            "quizzes": 0,
            "quiz_attempts": 0,
            "payments": 0,
            "subscriptions": 0,
            "reviews": 0,
            "certificates": 0,
            "support_tickets": 0,
        }
        self._cached_data: dict[str, list[dict[str, Any]]] = {}

    def _setup_random(self) -> None:
        if self.seed is not None:
            random.seed(self.seed)
            Faker.seed(self.seed)

    def _increment_id(self, entity_type: str) -> int:
        self._id_counters[entity_type] += 1
        return self._id_counters[entity_type]

    def generate_categories_batch(self) -> Iterator[dict[str, Any]]:
        """Generate all categories (no batching, small collection)."""
        for idx, (name, _) in enumerate(POPULAR_CATEGORIES, start=1):
            self._increment_id("categories")
            yield {
                "unique_id": make_unique_id("CAT", idx),
                "name": name,
                "slug": _slugify(name),
                "description": Faker().sentence(nb_words=14),
                "parent_category_unique_id": None,
                "is_active": random.choices([True, False], weights=[0.97, 0.03], k=1)[0],
                "created_at": self.now - timedelta(days=random.randint(400, 1300)),
            }

    def generate_users_batch(self) -> Iterator[dict[str, Any]]:
        """Generate users in batches."""
        total_instructors = max(5, int(self.config.num_users * self.config.instructor_ratio))
        total_users = self.config.num_users + total_instructors

        for i in range(1, total_users + 1):
            self._increment_id("users")
            country, locale, _, language = random.choice(COUNTRY_LANGUAGE)
            local_faker = Faker(locale)
            gender = random.choice(["male", "female", "other"])
            first_name = (
                local_faker.first_name_male()
                if gender == "male"
                else local_faker.first_name_female() if gender == "female"
                else local_faker.first_name()
            )
            last_name = local_faker.last_name()

            signup_date = self.now - timedelta(days=random.randint(7, 1200))
            role = "learner"
            if i <= total_instructors:
                role = random.choices(["instructor", "instructor_learner"], weights=[0.7, 0.3], k=1)[0]

            yield {
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
                "last_login_at": signup_date + timedelta(days=random.randint(0, max(1, (self.now - signup_date).days))),
            }

    def generate_instructors_batch(self, users_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate instructors from instructor users."""
        total_instructors = max(5, int(self.config.num_users * self.config.instructor_ratio))
        instructor_users = users_data[:total_instructors]

        for i, user in enumerate(instructor_users, start=1):
            self._increment_id("instructors")
            expertise_domain = random.choice(["Python", "Data Engineering", "AWS", "SQL", "Power BI", "AI", "DevOps"])
            created_at = user["signup_date"] + timedelta(days=random.randint(0, 60))

            yield {
                "unique_id": make_unique_id("INS", i),
                "user_unique_id": user["unique_id"],
                "headline": f"Senior {expertise_domain} Instructor",
                "bio": Faker().paragraph(nb_sentences=4),
                "expertise": random.sample(
                    ["Python", "SQL", "Spark", "Airflow", "MongoDB", "Docker", "Kubernetes", "dbt", "Pandas"],
                    k=random.randint(3, 6),
                ),
                "years_experience": random.randint(2, 20),
                "rating_avg": round(random.triangular(3.1, 5.0, 4.4), 2),
                "total_students": max(50, int(abs(random.gauss(2000, 1800)))),
                "social_links": {"linkedin": Faker().url(), "x": Faker().url()},
                "verification_status": random.choices(["verified", "pending", "rejected"], weights=[0.8, 0.16, 0.04], k=1)[0],
                "created_at": created_at,
            }

    def generate_courses_batch(self, categories_data: list[dict[str, Any]], instructors_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate courses in batches."""
        category_ids = [c["unique_id"] for c in categories_data]
        instructor_ids = [ins["unique_id"] for ins in instructors_data]

        course_count = 0
        for instructor_unique_id in instructor_ids:
            courses_per_instructor = random.randint(self.config.courses_per_instructor_min, self.config.courses_per_instructor_max)
            for _ in range(courses_per_instructor):
                if course_count >= self.config.num_courses:
                    return

                self._increment_id("courses")
                category_unique_id = _weighted_choice([(c["unique_id"], w) for c, (_, w) in zip(categories_data, POPULAR_CATEGORIES)])
                title = Faker().sentence(nb_words=random.randint(4, 8)).rstrip(".")
                published_at = self.now - timedelta(days=random.randint(1, 1000))
                price = round(max(0, random.lognormvariate(3.4, 0.5)), 2)
                is_free = random.random() < 0.18
                discount = round(price * random.uniform(0.1, 0.6), 2) if not is_free else 0
                discount_price = 0.0 if is_free else max(0.0, round(price - discount, 2))

                course_unique_id = make_unique_id("CRS", course_count + 1)
                yield {
                    "unique_id": course_unique_id,
                    "category_unique_id": category_unique_id,
                    "instructor_unique_id": instructor_unique_id,
                    "title": title,
                    "slug": f"{_slugify(title)}-{course_count + 1}",
                    "description": Faker().paragraph(nb_sentences=5),
                    "level": random.choices(["beginner", "intermediate", "advanced"], weights=[0.5, 0.34, 0.16], k=1)[0],
                    "language": random.choice(["English", "French", "Spanish", "German"]),
                    "price": 0.0 if is_free else price,
                    "discount_price": discount_price,
                    "duration_hours": round(random.triangular(2, 70, 18), 1),
                    "thumbnail_url": Faker().image_url(),
                    "tags": random.sample(
                        ["python", "sql", "etl", "analytics", "aws", "docker", "ml", "bi", "api", "mongodb"],
                        k=random.randint(3, 6),
                    ),
                    "status": random.choices(["published", "draft", "archived"], weights=[0.87, 0.1, 0.03], k=1)[0],
                    "published_at": published_at,
                    "updated_at": published_at + timedelta(days=random.randint(0, 180)),
                }
                course_count += 1

    def generate_modules_and_lessons_batch(self, courses_data: list[dict[str, Any]]) -> tuple[Iterator[dict[str, Any]], Iterator[dict[str, Any]]]:
        """Generate modules and lessons (interdependent)."""

        def modules_gen() -> Iterator[dict[str, Any]]:
            for course in courses_data:
                module_count = random.randint(3, 10)
                for mod_order in range(1, module_count + 1):
                    self._increment_id("modules")
                    module_created = course["published_at"] + timedelta(days=random.randint(0, 30))
                    yield {
                        "unique_id": make_unique_id("MOD", self._id_counters["modules"]),
                        "course_unique_id": course["unique_id"],
                        "title": f"Module {mod_order}: {Faker().sentence(nb_words=4).rstrip('.')}",
                        "order_index": mod_order,
                        "is_free_preview": mod_order == 1,
                        "created_at": module_created,
                    }

        def lessons_gen() -> Iterator[dict[str, Any]]:
            for course in courses_data:
                module_count = random.randint(3, 10)
                for mod_order in range(1, module_count + 1):
                    module_created = course["published_at"] + timedelta(days=random.randint(0, 30))
                    lesson_count = random.randint(3, 9)
                    for lesson_order in range(1, lesson_count + 1):
                        self._increment_id("lessons")
                        yield {
                            "unique_id": make_unique_id("LES", self._id_counters["lessons"]),
                            "course_unique_id": course["unique_id"],
                            "module_unique_id": make_unique_id("MOD", self._id_counters["modules"]),
                            "title": Faker().sentence(nb_words=5).rstrip("."),
                            "lesson_type": random.choices(
                                ["video", "article", "exercise", "live_session"],
                                weights=[0.66, 0.18, 0.12, 0.04],
                                k=1,
                            )[0],
                            "duration_minutes": max(3, int(abs(random.gauss(18, 9)))),
                            "resource_urls": [Faker().url() for _ in range(random.randint(0, 2))],
                            "order_index": lesson_order,
                            "is_free_preview": mod_order == 1 and lesson_order <= 2,
                            "created_at": module_created + timedelta(hours=lesson_order),
                        }

        return modules_gen(), lessons_gen()

    def generate_enrollments_batch(self, users_data: list[dict[str, Any]], courses_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate enrollments in batches."""
        learner_users = users_data[int(len(users_data) * self.config.instructor_ratio) :]
        course_ids = [course["unique_id"] for course in courses_data]
        course_weights = [random.uniform(0.3, 3.0) for _ in course_ids]

        for user in learner_users:
            enrollment_count = random.randint(0, self.config.num_enrollments_per_user)
            picked_courses = set(random.choices(course_ids, weights=course_weights, k=enrollment_count))
            for course_unique_id in picked_courses:
                course = next((c for c in courses_data if c["unique_id"] == course_unique_id), None)
                if not course:
                    continue

                self._increment_id("enrollments")
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

                yield {
                    "unique_id": make_unique_id("ENR", self._id_counters["enrollments"]),
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
                    "last_accessed_at": enrollment_date + timedelta(days=random.randint(0, max(1, (self.now - enrollment_date).days))),
                }

    def generate_progress_events_batch(self, enrollments_data: list[dict[str, Any]], courses_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate progress events in batches."""
        for enrollment in enrollments_data:
            for _ in range(random.randint(1, 12)):
                self._increment_id("progress_events")
                course = next((c for c in courses_data if c["unique_id"] == enrollment["course_unique_id"]), None)
                if not course:
                    continue

                event_time = enrollment["enrollment_date"] + timedelta(days=random.randint(0, max(1, (self.now - enrollment["enrollment_date"]).days)))
                yield {
                    "unique_id": make_unique_id("PRG", self._id_counters["progress_events"]),
                    "user_unique_id": enrollment["user_unique_id"],
                    "course_unique_id": enrollment["course_unique_id"],
                    "lesson_unique_id": make_unique_id("LES", random.randint(1, 1000)),
                    "event_type": random.choice(["started", "paused", "resumed", "completed_lesson", "seek"]),
                    "progress_percent": min(100, max(0, enrollment["progress_percent"] + random.randint(-20, 8))),
                    "event_timestamp": event_time,
                    "device_type": random.choice(["web", "android", "ios", "tablet"]),
                }

    def generate_quizzes_batch(self, courses_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate quizzes for courses."""
        for course in courses_data:
            module_count = random.randint(3, 10)
            for mod_idx in range(1, module_count + 1):
                if random.random() < 0.72:
                    self._increment_id("quizzes")
                    yield {
                        "unique_id": make_unique_id("QZ", self._id_counters["quizzes"]),
                        "course_unique_id": course["unique_id"],
                        "module_unique_id": make_unique_id("MOD", mod_idx),
                        "title": f"{Faker().word().title()} Assessment",
                        "quiz_type": random.choice(["mcq", "coding", "mixed"]),
                        "total_questions": random.randint(5, 35),
                        "passing_score": random.choice([60, 65, 70, 75]),
                        "time_limit_minutes": random.choice([10, 15, 20, 30, 45]),
                        "created_at": course["published_at"] + timedelta(days=random.randint(0, 20)),
                    }

    def generate_quiz_attempts_batch(self, enrollments_data: list[dict[str, Any]], quizzes_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate quiz attempts."""
        for enrollment in enrollments_data:
            quiz_candidates = [q for q in quizzes_data if q["course_unique_id"] == enrollment["course_unique_id"]]
            for quiz in random.sample(quiz_candidates, k=min(2, len(quiz_candidates))):
                max_score = 100
                score = max(0, min(100, int(random.gauss(72, 18))))
                started_at = enrollment["enrollment_date"] + timedelta(days=random.randint(1, 200))
                submitted_at = started_at + timedelta(minutes=random.randint(5, 50))
                self._increment_id("quiz_attempts")
                yield {
                    "unique_id": make_unique_id("QZA", self._id_counters["quiz_attempts"]),
                    "quiz_unique_id": quiz["unique_id"],
                    "user_unique_id": enrollment["user_unique_id"],
                    "attempt_number": random.randint(1, 3),
                    "score": score,
                    "max_score": max_score,
                    "passed": score >= random.choice([60, 65, 70]),
                    "started_at": started_at,
                    "submitted_at": submitted_at,
                    "duration_seconds": int((submitted_at - started_at).total_seconds()),
                }

    def generate_payments_batch(self, enrollments_data: list[dict[str, Any]], courses_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate payments for paid courses."""
        for enrollment in enrollments_data:
            course = next((c for c in courses_data if c["unique_id"] == enrollment["course_unique_id"]), None)
            if course and course["price"] > 0:
                self._increment_id("payments")
                payment_status = random.choices(["paid", "failed", "refunded"], weights=[0.9, 0.06, 0.04], k=1)[0]
                yield {
                    "unique_id": make_unique_id("PAY", self._id_counters["payments"]),
                    "user_unique_id": enrollment["user_unique_id"],
                    "course_unique_id": enrollment["course_unique_id"],
                    "payment_method": random.choice(["card", "paypal", "bank_transfer", "mobile_money"]),
                    "amount": course["discount_price"] if course["discount_price"] else course["price"],
                    "currency": random.choice(["USD", "EUR", "GBP", "CAD", "INR", "NGN"]),
                    "payment_status": payment_status,
                    "transaction_reference": Faker().uuid4(),
                    "payment_date": enrollment["enrollment_date"] + timedelta(minutes=random.randint(1, 180)),
                    "provider": random.choice(["stripe", "paypal", "adyen", "flutterwave"]),
                }

    def generate_subscriptions_batch(self, users_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate subscriptions."""
        subscribed_users = random.sample(users_data, k=max(1, int(len(users_data) * 0.25)))
        for user in subscribed_users:
            start_date = user["signup_date"] + timedelta(days=random.randint(0, 120))
            billing_period = random.choice(["monthly", "yearly"])
            duration_days = 30 if billing_period == "monthly" else 365
            status = random.choices(["active", "paused", "cancelled", "expired"], weights=[0.7, 0.08, 0.12, 0.10], k=1)[0]
            end_date = start_date + timedelta(days=duration_days)
            self._increment_id("subscriptions")
            yield {
                "unique_id": make_unique_id("SUB", self._id_counters["subscriptions"]),
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

    def generate_reviews_batch(self, enrollments_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate reviews from completed enrollments."""
        completed_enrollments = [e for e in enrollments_data if e["completion_status"] == "completed"]
        for enrollment in random.sample(completed_enrollments, k=min(len(completed_enrollments), max(1, int(len(completed_enrollments) * 0.55)))):
            self._increment_id("reviews")
            rating = random.choices([1, 2, 3, 4, 5], weights=[0.04, 0.07, 0.14, 0.33, 0.42], k=1)[0]
            yield {
                "unique_id": make_unique_id("REV", self._id_counters["reviews"]),
                "user_unique_id": enrollment["user_unique_id"],
                "course_unique_id": enrollment["course_unique_id"],
                "rating": rating,
                "review_title": Faker().sentence(nb_words=6).rstrip("."),
                "review_text": Faker().paragraph(nb_sentences=2),
                "helpful_votes": max(0, int(abs(random.gauss(7, 12)))),
                "created_at": (enrollment["completed_at"] or enrollment["enrollment_date"]) + timedelta(days=random.randint(1, 40)),
                "verified_purchase": random.random() < 0.8,
            }

    def generate_certificates_batch(self, enrollments_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate certificates for completed courses."""
        completed_enrollments = [e for e in enrollments_data if e["completion_status"] == "completed"]
        for enrollment in completed_enrollments:
            if random.random() < 0.78:
                self._increment_id("certificates")
                yield {
                    "unique_id": make_unique_id("CRT", self._id_counters["certificates"]),
                    "user_unique_id": enrollment["user_unique_id"],
                    "course_unique_id": enrollment["course_unique_id"],
                    "issued_at": enrollment["completed_at"] + timedelta(hours=random.randint(6, 72)),
                    "certificate_url": Faker().url(),
                    "verification_code": Faker().bothify(text="CERT-#####-????").upper(),
                    "status": random.choices(["active", "revoked"], weights=[0.98, 0.02], k=1)[0],
                    "score_final": random.randint(60, 100),
                }

    def generate_support_tickets_batch(self, users_data: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Generate support tickets."""
        ticket_users = random.sample(users_data, k=max(1, int(len(users_data) * 0.15)))
        for user in ticket_users:
            created_at = user["signup_date"] + timedelta(days=random.randint(0, max(1, (self.now - user["signup_date"]).days)))
            resolved = random.random() < 0.68
            resolved_at = created_at + timedelta(hours=random.randint(2, 240)) if resolved else None
            self._increment_id("support_tickets")
            yield {
                "unique_id": make_unique_id("TKT", self._id_counters["support_tickets"]),
                "user_unique_id": user["unique_id"],
                "ticket_type": random.choice(["billing", "technical", "content", "account", "refund"]),
                "priority": random.choices(["low", "medium", "high", "urgent"], weights=[0.42, 0.34, 0.18, 0.06], k=1)[0],
                "subject": Faker().sentence(nb_words=7).rstrip("."),
                "message": Faker().paragraph(nb_sentences=3),
                "status": "resolved" if resolved else random.choice(["open", "pending"]),
                "created_at": created_at,
                "resolved_at": resolved_at,
                "channel": random.choice(["email", "chat", "web_form"]),
            }
