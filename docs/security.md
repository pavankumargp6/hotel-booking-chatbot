# Security Notes

## Least privilege

The Lambda's IAM is deliberately minimal:

- `AWSLambdaBasicExecutionRole` — CloudWatch Logs only.
- Inline statement: `dynamodb:PutItem` on `!GetAtt HotelBookingsTable.Arn`.
  Nothing else — no `GetItem`, no `Scan`, no `Resource: "*"`.

The Lex bot is granted `lambda:InvokeFunction` via a
`AWS::Lambda::Permission` scoped to `SourceArn: !Ref LexBotAliasArn`,
so no other caller can invoke the function.

## Data classification

| Data | Stored | Logged |
|---|---|---|
| `location` | DynamoDB | No — only `len(location)` in CloudWatch |
| `checkInDate` | DynamoDB | No |
| `sessionId` | DynamoDB | No |
| `total`, `tax` | DynamoDB | No |
| Tracebacks | CloudWatch | Yes |

The confirmation message tells the user this is a **simulated estimate**
and that **no real reservation has been made**. The `status` field on
every item is `SIMULATED`, so no downstream system can mistake it for a
real booking.

## Secrets

None. The application reads only `PRICING_CONFIG` and `BOOKINGS_TABLE`
from Lambda environment variables. No API keys, no passwords, no
account IDs in source or configuration. Future payment / CRM
integrations should read secrets via AWS Secrets Manager or SSM
Parameter Store, never via environment variables or the repo.

## Dependency audit scope

CI runs `pip-audit -r requirements-dev.txt`, which covers every pinned
third-party package the project explicitly depends on.

Runtime dependencies: the deployed Lambda uses the AWS-managed Python
3.12 runtime, which supplies `boto3` and `botocore`. Those are patched
by AWS as part of the runtime; this project does not pin or audit them.

Policy: if this project ever adds a third-party runtime dependency, it
belongs in `requirements.txt` **and** must be added to the audit command
in `.github/workflows/ci.yml`.
