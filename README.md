# E-learning synthetic data generator

Projet Python (`uv`) pour générer un écosystème réaliste de données e-learning et l’injecter dans MongoDB Atlas.

## 1) Arborescence du projet

```text
.
├── .env.example
├── main.py
├── pyproject.toml
└── src
    ├── config
    │   └── settings.py
    ├── db
    │   ├── indexes.py
    │   └── mongo.py
    ├── generators
    │   └── data_generator.py
    └── utils
        ├── ids.py
        └── logging_utils.py
```

## 2) Installation (`uv`)

```bash
uv sync
```

## 3) Configuration

Copier `.env.example` vers `.env` et renseigner les valeurs Atlas:

```bash
cp .env.example .env
```

Variables:
- `MONGODB_URI` (obligatoire hors `--dry-run`)
- `MONGODB_DB_NAME` (défaut: `elearning_synthetic`)
- `BATCH_SIZE` (défaut: `1000`)
- `DEFAULT_SEED` (optionnel)

## 4) Lancement du générateur

Dry-run local (sans insertion Mongo):

```bash
uv run python main.py --learners 1500 --seed 123 --dry-run
```

Insertion MongoDB Atlas:

```bash
uv run python main.py --learners 1500 --seed 123 --drop-existing
```

Script CLI installé:

```bash
uv run generate-elearning-data --learners 800 --instructor-ratio 0.08 --seed 99 --drop-existing
```

## 5) Collections générées

15 collections cohérentes:
- `users`
- `instructors`
- `categories`
- `courses`
- `course_modules`
- `lessons`
- `enrollments`
- `progress_events`
- `quizzes`
- `quiz_attempts`
- `payments`
- `subscriptions`
- `reviews`
- `certificates`
- `support_tickets`

Chaque document contient un `unique_id` métier unique (en plus de `_id` MongoDB natif).

## 6) Logique de cohérence relationnelle

- `instructors.user_unique_id` référence `users.unique_id`
- `courses` référence `categories` + `instructors`
- `course_modules` et `lessons` sont reliés au cours et au module parent
- `enrollments`, `progress_events`, `quiz_attempts` référencent des users/cours/leçons/quiz valides
- `payments` sont générés sur des cours payants
- `reviews` viennent d’inscriptions terminées (ou payées)
- `certificates` ne sont créés que pour des cours complétés
- les dates respectent l’ordre métier (signup < enrollment < completion/review/certificate)

## 7) Exemple de requête MongoDB

Top 10 cours les mieux notés (min 20 avis):

```javascript
db.reviews.aggregate([
  { $group: { _id: "$course_unique_id", avgRating: { $avg: "$rating" }, reviews: { $sum: 1 } } },
  { $match: { reviews: { $gte: 20 } } },
  { $sort: { avgRating: -1, reviews: -1 } },
  { $limit: 10 }
])
```
