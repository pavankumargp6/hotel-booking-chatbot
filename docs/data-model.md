# Data Model — DynamoDB `bookings` table

## Table

- **Name:** `${AWS::StackName}-bookings` (created by `template.yaml`)
- **PK:** `bookingId` (string, 32 hex chars)
- **Billing:** `PAY_PER_REQUEST`
- **TTL:** `expiresAt` (unix epoch)
- **PITR:** disabled (demo tier; enable for production)

## Item schema

| Attribute | Type | Example | Purpose |
|---|---|---|---|
| `bookingId` | S | `3f8a…` | PK, derived (see below) |
| `createdAt` | S | `2026-10-31T06:12:03+00:00` | Audit trail |
| `sessionId` | S | `lex-sess-abc` | Correlates retries |
| `location` | S | `Bangalore` | User-entered city |
| `checkInDate` | S | `2099-04-01` | ISO date |
| `nights` | N | `2` | 1..maxNights |
| `roomType` | S | `deluxe` | Lowercase room key |
| `subtotal`, `tax`, `total` | S | `6000.00` | Decimal strings |
| `currency` | S | `INR` | From `PRICING_CONFIG` |
| `status` | S | `SIMULATED` | Never `CONFIRMED` |
| `expiresAt` | N | `…` | TTL, now + 30 days |

## Why strings for money

DynamoDB `N` supports arbitrary precision, but the *client* is what
turns a `Decimal` into a wire value. Writing `"6000.00"` as a string is
trivial to inspect and cannot drift across languages. A future query
that sums by `total` would need it as `N`; that is a deliberate trade
for a demo that never sums.

## Access patterns covered

| Pattern | Supported? |
|---|---|
| Write one booking (idempotent) | Yes — `PutItem` with condition |
| Read one booking by ID | Yes (not exposed in the Lambda) |
| List by date / room / session | No — would need a GSI |

## Cost

At demo traffic (< 1k writes/day), with `PAY_PER_REQUEST` and TTL on,
monthly cost is ≈ $0.00. Free tier: 25 WCU / 25 RCU and 25 GB storage,
orders of magnitude above this project's usage.
