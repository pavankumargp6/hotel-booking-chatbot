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
   - Otherwise → `Close`, state `Fulfilled`, formatted summary.
4. Unhandled exception → `Close`, state `Failed`, generic user message;
   full traceback logged to CloudWatch.

## Modules

| Module | Responsibility |
|---|---|
| `config` | Load and validate `PRICING_CONFIG`. |
| `validation` | Per-slot validators returning `SlotError` or `None`. |
| `pricing` | Decimal-based estimate calculation. |
| `lex` | Build Lex V2 response objects. |
| `lambda_handler` | Orchestration only. |
