# AdServer Frequency Capping

Redis-backed frequency capping microservice for programmatic advertising. Tracks user impression counts across hourly, daily, weekly, and lifetime windows for campaign, line item, creative, and advertiser dimensions. Falls back to in-memory storage when Redis is not configured (dev/test).

## Features

- **4 Window Types** — hour, day, week, lifetime; auto-expiring Redis keys
- **4 Cap Dimensions** — line_item, campaign, creative, advertiser
- **Bulk Check API** — check multiple dimensions in one call with a single `any_capped` signal (optimised for bid evaluation)
- **Atomic Counters** — Redis `INCR` + `EXPIRE` for race-free distributed counting
- **Named Cap Rules** — define reusable rules by name and check users against them
- **Dual Backend** — Redis in production, in-memory dict in dev/test (no config change needed)
- **OpenRTB Friendly** — check-before-bid + record-on-win pattern matches OpenRTB win notice flow

## Architecture

```
Bid Evaluator (DSP)
    │
    ├── POST /v1/check/bulk   ← fast multi-dimension check (no side effects)
    │     { user_id, checks: [{dimension, dimension_id, window, max},...] }
    │     → { any_capped: true/false, results: [...] }
    │
Win Notice Handler
    │
    └── POST /v1/record       ← increments counters across ALL windows at once
          { user_id, dimension, dimension_id }
          → { counts: {hour: 1, day: 1, week: 1, lifetime: 1} }

Redis Key Format:
  freq:{dimension}:{dimension_id}:{user_id}:{window_bucket}
  e.g. freq:line_item:li_abc:usr_123:20260525   (day window)
       freq:campaign:cmp_xyz:usr_123:global      (lifetime)
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8006 --reload
# No Redis needed — falls back to in-memory store
```

API docs: http://localhost:8006/docs

## Docker (with Redis)

```bash
docker compose up
```

Starts the service on port 8006 wired to Redis 7 on port 6379.

## API Reference

### Frequency Cap Checks & Recording

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/check` | Check a single user/dimension cap |
| `POST` | `/v1/check/bulk` | Check multiple dimensions at once |
| `POST` | `/v1/record` | Record an impression (all windows) |
| `POST` | `/v1/record/bulk` | Record impressions for multiple dimensions |
| `POST` | `/v1/reset` | Admin reset for a specific counter |

### Named Cap Rules

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/rules` | Create a named cap rule |
| `GET` | `/v1/rules` | List rules |
| `GET` | `/v1/rules/{id}` | Get rule by ID |
| `PATCH` | `/v1/rules/{id}/active` | Activate / deactivate rule |
| `DELETE` | `/v1/rules/{id}` | Delete rule |
| `POST` | `/v1/rules/{id}/check` | Check a user against a named rule |

## Example: OpenRTB Bid Evaluation Flow

```bash
# On each bid request — check before bidding (no counter increment)
curl -X POST http://localhost:8006/v1/check/bulk \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "usr_abc123",
    "checks": [
      {"user_id": "usr_abc123", "dimension": "line_item",  "dimension_id": "li_001", "window": "day",      "max_impressions": 3},
      {"user_id": "usr_abc123", "dimension": "campaign",   "dimension_id": "cmp_01", "window": "day",      "max_impressions": 10},
      {"user_id": "usr_abc123", "dimension": "advertiser", "dimension_id": "adv_01", "window": "lifetime", "max_impressions": 50}
    ]
  }'
# → { "any_capped": false, "results": [...] }  → bid
# → { "any_capped": true,  "results": [...] }  → no-bid

# On win notice — record the impression
curl -X POST http://localhost:8006/v1/record \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "usr_abc123",
    "dimension": "line_item",
    "dimension_id": "li_001"
  }'
# → { "counts": {"hour": 1, "day": 1, "week": 1, "lifetime": 1} }
```

## Example: Named Rules

```bash
# Create a 3-per-day rule for a line item
curl -X POST http://localhost:8006/v1/rules \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "3/day for LI-001",
    "dimension": "line_item",
    "dimension_id": "li_001",
    "window": "day",
    "max_impressions": 3
  }'
# → { "id": "rule_abc...", ... }

# Check a user against the rule
curl -X POST http://localhost:8006/v1/rules/rule_abc.../check \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "usr_abc123", "rule_id": "rule_abc..."}'
# → { "capped": false, "current_count": 1, "ttl_seconds": 43200 }
```

## Window Buckets & TTLs

| Window | Redis key bucket | TTL |
|--------|-----------------|-----|
| `hour` | `YYYYMMDDHH` | 1 hour (3,600s) |
| `day` | `YYYYMMDD` | 24 hours (86,400s) |
| `week` | `YYYYwWW` | 7 days (604,800s) |
| `lifetime` | `global` | No expiry |

## Running Tests

```bash
pytest tests/ -v
```

Tests run entirely in-memory — no Redis required.

## Production Considerations

| Concern | Notes |
|---------|-------|
| **Atomicity** | Redis `INCR` is atomic — no race conditions under concurrent writes |
| **TTL race** | `EXPIRE` is set only if key is new; double-fire on same second is safe |
| **Redis failure** | Service should fail open (allow impressions) rather than block delivery |
| **Cluster mode** | Keys are already user-sharded — compatible with Redis Cluster |
| **Sliding windows** | Current fixed-window approach; upgrade to sorted-set sliding window for exact counts |

## Tech Stack

- **FastAPI** — async REST
- **Pydantic v2** — model validation
- **Redis 7** — atomic counters with auto-expiry
- Python 3.12+

<!-- Last updated: 2026-05-29 -->

<!-- Last updated: 2026-05-31 -->

<!-- Last updated: 2026-06-01 -->

<!-- Last updated: 2026-06-03 -->

<!-- Last updated: 2026-06-05 -->

<!-- Last updated: 2026-06-07 -->

<!-- Last updated: 2026-06-09 -->

<!-- Last updated: 2026-06-11 -->

<!-- Last updated: 2026-06-13 -->

<!-- Last updated: 2026-06-15 -->

<!-- Last updated: 2026-06-17 -->

<!-- Last updated: 2026-06-19 -->

<!-- Last updated: 2026-06-21 -->

<!-- Last updated: 2026-06-23 -->

<!-- Last updated: 2026-06-25 -->

<!-- Last updated: 2026-06-27 -->

<!-- Last updated: 2026-06-29 -->
