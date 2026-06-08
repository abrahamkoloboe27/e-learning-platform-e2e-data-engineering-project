# E-learning synthetic data generator

Projet Python (`uv`) pour générer un écosystème réaliste de données e-learning par lots et l'injecter dans MongoDB Atlas.

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
    │   ├── batch_generator.py
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
- `BATCH_SIZE` (défaut: `5000`)
- `DEFAULT_SEED` (optionnel)

## 4) Lancement du générateur

### Dry-run local (sans insertion Mongo):

```bash
uv run python main.py --users 1500 --courses 150 --seed 123 --dry-run
```

### Insertion MongoDB Atlas (avec batching):

```bash
uv run python main.py \
    --users 100000 \
    --courses 10000 \
    --seed 123 \
    --batch-size 5000 \
    --drop-existing
```

### Contrôle du volume et du batching:

```bash
uv run python main.py \
    --users 500000 \
    --courses 50000 \
    --enrollments-per-user 5 \
    --instructor-ratio 0.06 \
    --courses-per-instructor-min 2 \
    --courses-per-instructor-max 6 \
    --batch-size 10000 \
    --seed 42 \
    --drop-existing
```

### Options CLI:

- `--users` : Nombre total d'utilisateurs (inclut les instructeurs)
- `--courses` : Nombre de cours à générer
- `--enrollments-per-user` : Moyenne d'inscriptions par utilisateur (défaut: 5)
- `--instructor-ratio` : Ratio instructeurs/utilisateurs (défaut: 0.06)
- `--courses-per-instructor-min` : Min courses par instructeur (défaut: 2)
- `--courses-per-instructor-max` : Max courses par instructeur (défaut: 6)
- `--seed` : Graine aléatoire pour reproductibilité
- `--batch-size` : Taille des lots d'insertion (défaut: 5000)
- `--drop-existing` : Supprime les collections existantes
- `--dry-run` : Génère sans insérer dans MongoDB
- `--no-progress` : Désactive les barres de progression

### Script CLI installé:

```bash
uv run generate-elearning-data --users 1500 --courses 150 --dry-run
```

## 5) Collections générées

15 collections en ordre de dépendance:
1. `categories`
2. `users`
3. `instructors`
4. `courses`
5. `course_modules`
6. `lessons`
7. `enrollments`
8. `progress_events`
9. `quizzes`
10. `quiz_attempts`
11. `payments`
12. `subscriptions`
13. `reviews`
14. `certificates`
15. `support_tickets`

Chaque document contient:
- `_id` : identifiant MongoDB natif
- `unique_id` : identifiant métier unique (lisible et stable)

## 6) Traitement par lots

Le système supporte la génération et l'insertion par lots configurables:

### Caractéristiques:

- **Pas de surcharge mémoire** : Génération itérative sans charger tout en mémoire
- **Lots configurables** : `--batch-size` (défaut: 5000)
- **Insertion MongoDB optimisée** : `insert_many()` avec `ordered=False`
- **Reproductibilité** : Même seed = mêmes données
- **Progression en temps réel** : barres tqdm + logs détaillés
- **Performance** : Vitesse de génération et temps total affichés

### Pipeline:

1. Génération de lot de N documents
2. Validation et structuration
3. Insertion MongoDB via `insert_many()`
4. Libération mémoire
5. Lot suivant

### Volumes supportés:

✓ 100 documents
✓ 100 000 documents
✓ 500 000 documents
✓ 1 000 000+ documents

## 7) Logique de cohérence relationnelle

- `instructors.user_unique_id` référence `users.unique_id`
- `courses` référencent `categories` + `instructors` valides
- `course_modules` et `lessons` sont reliés au cours et module parent
- `enrollments`, `progress_events`, `quiz_attempts` référencent des entities valides
- `payments` générés pour les cours payants
- `reviews` depuis des inscriptions terminées
- `certificates` uniquement pour des cours complétés
- Dates respectent l'ordre métier (signup < enrollment < completion)

## 8) Exemple de requête MongoDB

Top 10 cours les mieux notés (min 20 avis):

```javascript
db.reviews.aggregate([
  { $group: { _id: "$course_unique_id", avgRating: { $avg: "$rating" }, reviews: { $sum: 1 } } },
  { $match: { reviews: { $gte: 20 } } },
  { $sort: { avgRating: -1, reviews: -1 } },
  { $limit: 10 }
])
```

Utilisateurs les plus actifs (nombre d'inscriptions):

```javascript
db.enrollments.aggregate([
  { $group: { _id: "$user_unique_id", enroll_count: { $sum: 1 } } },
  { $sort: { enroll_count: -1 } },
  { $limit: 20 }
])
```
