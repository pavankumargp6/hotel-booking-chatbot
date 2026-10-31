# Deployment verification runbook

The exact sequence to move this project from "locally verified" to
"verified in AWS". Each step produces evidence for the README's
`### Verification status` section.

## Prerequisites

- AWS CLI installed: `pip install awscli` (or `apt install awscli`)
- `aws sts get-caller-identity` succeeds (credentials configured)
- A Lex V2 bot with a `BookHotel` intent exists in that account
- AWS SAM CLI installed: `sam --version` prints `1.x`

## Step 1 — Deploy

```bash
cp samconfig.toml.example samconfig.toml
# Edit samconfig.toml:
#   region = your region
#   parameter_overrides = LexBotAliasArn="arn:aws:lex:...:bot-alias/<botId>/<aliasId>"
sam validate --lint
sam build
sam deploy --guided
cat > docs/deployment-verification.md <<'EOF'
# Deployment verification runbook

Prerequisites: `pip install awscli`, working `aws sts get-caller-identity`,
an existing Lex V2 bot with `BookHotel` intent, and SAM CLI 1.x.

## Steps

### 1. Deploy

    cp samconfig.toml.example samconfig.toml
    # edit region + LexBotAliasArn
    sam validate --lint && sam build && sam deploy --guided

Evidence: sam deploy success output.

### 2. Wire to Lex

Lex console → BookHotel intent → Fulfillment → attach hotel-booking-fulfilment
to both Dialog and Fulfillment hooks → Build bot.
Evidence: screenshots/lambda/01-lex-fulfillment.png.

### 3. Test booking

Lex chat, future date, complete all four slots.
Confirmation ends with "Reference: <hex>".
Evidence: screenshots/lambda/02-lex-chat.png.

### 4. CloudWatch

    aws logs tail "/aws/lambda/hotel-booking-fulfilment" --since 10m

Expect "Persisted booking <id>" and "Fulfilled BookHotel: room=...".
Evidence: screenshots/lambda/03-cloudwatch.png.

### 5. DynamoDB

    aws dynamodb scan --table-name "$(aws cloudformation describe-stacks \
      --stack-name hotel-booking-chatbot \
      --query 'Stacks[0].Outputs[?OutputKey==`BookingsTableName`].OutputValue' \
      --output text)" --max-items 3

Confirm status = SIMULATED, expiresAt ~30 days out.
Evidence: screenshots/lambda/04-dynamodb.png.

### 6. Update README

In ### Verification status, replace "Not yet deployed" with
"Deployed and verified in <region> on <date>" + evidence paths.

Do NOT change `| Real hotel reservation | Not implemented |`.

    git add screenshots/lambda/ README.md
    git commit -m "docs: verified deployment in <region>"
    git push

### 7. Cleanup

    sam delete --stack-name hotel-booking-chatbot
