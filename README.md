# Reduplicator

High-accuracy, low-latency duplicate-entity detector built on **Oracle 23ai** +
vector similarity + a tiny learned ranker.  It answers "has this person already
been seen in our system?" and is tuned for KYC/loan workflows.

## Features

* Normalises common KYC fields (name, phone, email, government id, address).
* Embeds a canonical identity string with SentenceTransformers and stores the
  512‑D vector in Oracle `VECTOR(512, FLOAT32, DENSE)`.
* Candidate generation using `VECTOR_DISTANCE` in the database.
* Lightweight logistic regression combines vector distance with a handful of
  discrete similarity signals (phone/email/gov‑id exact match, Jaro‑Winkler on
  names/city/state and token overlap on address lines).
* FastAPI service exposing:
  * `POST /customers` – ingest customers.
  * `POST /dedupe/check` – run a duplicate check for a prospective customer.
  * `POST /train` – fit/refresh the ranker (see `training/train_ranker.py`).

## Quick start

1. **Create tables** (Oracle 23ai):

   ```bash
   sqlplus users/YOURPASS@localhost/XEPDB1 @sql/01_tables.sql
   sqlplus users/YOURPASS@localhost/XEPDB1 @sql/02_indexes.sql
   ```

2. **Install & run** the API:

   ```bash
   python -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000
   ```

3. **Ingest customers** individually with HTTP or in bulk from CSV:

   ```bash
   python scripts/ingest_csv.py customers.csv
   ```

4. **Check a duplicate**:

   ```bash
   curl -X POST http://localhost:8000/dedupe/check \
        -H "Content-Type: application/json" \
        -d '{"full_name":"Rohan K.","dob":"1995-11-20","phone":"+91-9876543210"}'
   ```

5. **Train the ranker** once you have labelled pairs:

   ```bash
   python training/train_ranker.py path/to/labeled_pairs
   ```

   The path may reference a CSV file, a Parquet file, or a directory containing
   a Hugging Face dataset saved with ``datasets.save_to_disk``.

## Scripts

* `scripts/ingest_csv.py` – ingest customers from a CSV/Parquet file or a
  directory of Parquet shards.
* `scripts/smoke_check.py` – run `check_duplicate` against a JSON payload.

## Environment

Copy `.env.example` to `.env` and adjust Oracle connection and model settings as
needed.

---

This repository is a minimal but productionable reference.  Extend it with
vector indexes or additional features as required for your environment.

