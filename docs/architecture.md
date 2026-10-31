# Architecture

## Request flow

1. User sends an utterance to `HotelBookingBot` in Lex V2.
2. Lex invokes the Lambda with `invocationSource = DialogCodeHook`
   on each turn where a slot was filled:
   - Validate filled slots only.
   - Invalid filled slot → `ElicitSlot` with a user message.
   - Otherwise → `Delegate`.
3. Once all four slots are filled, Lex invokes with
   `invocationSource = FulfillmentCodeHook`:
   - Re-validate everything.
   - Missing or invalid slot → `ElicitSlot`.
   - Otherwise calculate the estimate, write one DynamoDB record
     (idempotent), and return `Close`, state `Fulfilled`, with a
     formatted summary.
4. Unhandled exception → `Close`, state `Failed`, generic user
   message; full traceback logged to CloudWatch.

## Modules

| Module | Responsibility |
|---|---|
| `config` | Load and validate `PRICING_CONFIG`. |
| `validation` | Per-slot validators returning `SlotError` or `None`. |
| `pricing` | Decimal-based estimate calculation. |
| `storage` | Idempotent DynamoDB `PutItem` for booking records. |
| `lex` | Build Lex V2 response objects. |
| `lambda_handler` | Orchestration only. |

## Non-goals

- Making a real reservation (every record carries `status=SIMULATED`).
- Payment or identity verification.
- Reading, updating, or deleting booking records after they are written
  (no `GetItem` / `UpdateItem` / `DeleteItem` flows yet).
- Calling any AWS service other than DynamoDB from inside the handler.
