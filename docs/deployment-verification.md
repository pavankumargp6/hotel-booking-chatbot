# AWS Deployment Verification Runbook

Use this runbook to move the project from **locally verified** to **verified in AWS**. Do not describe the project as deployed until all verification steps have succeeded.

## Prerequisites

- AWS CLI configured with credentials for the target account.
- `aws sts get-caller-identity` succeeds.
- AWS SAM CLI installed.
- An Amazon Lex V2 bot with a `BookHotel` intent and an alias.
- Permission to create Lambda, IAM, DynamoDB, and Lambda permissions through CloudFormation.

## 1. Configure and deploy

From the repository root:

```bash
cp samconfig.toml.example samconfig.toml
```

Edit `samconfig.toml` and set the deployment region and the `LexBotAliasArn` parameter override for your existing Lex V2 bot alias.

Then run:

```bash
sam validate --lint
sam build
sam deploy --guided
```

Save the successful deployment output. The stack should create the fulfillment Lambda, DynamoDB table, and permission allowing the Lex bot alias to invoke the Lambda.

## 2. Connect the Lambda to Lex V2

In the Amazon Lex V2 console:

1. Open the `BookHotel` intent.
2. Configure the deployed Lambda as the **Dialog code hook**.
3. Configure the same Lambda as the **Fulfillment code hook**.
4. Build the bot and ensure the alias uses the updated bot version.

Capture evidence showing the configured hooks.

## 3. Test a simulated booking

Use the Lex test console and provide all four slots:

- Location
- Check-in date (use a valid future date)
- Number of nights
- Room type

Confirm that the bot returns an estimate and a reference. The response must make clear that **no real hotel reservation was made**.

Capture the completed conversation.

## 4. Verify CloudWatch logs

After a successful test, inspect the Lambda log group:

```bash
aws logs tail "/aws/lambda/hotel-booking-fulfilment" --since 10m
```

Check for the persistence and fulfillment log entries. Confirm that free-text location values are not written to logs.

Capture the relevant log output, taking care not to expose account IDs or other sensitive information.

## 5. Verify the DynamoDB record

Retrieve the table name from the CloudFormation stack outputs:

```bash
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name hotel-booking-chatbot \
  --query "Stacks[0].Outputs[?OutputKey=='BookingsTableName'].OutputValue" \
  --output text)

echo "$TABLE_NAME"
aws dynamodb scan --table-name "$TABLE_NAME" --max-items 3
```

Verify that a record was written and that:

- `status` is `SIMULATED`.
- The booking reference matches the chatbot response.
- `expiresAt` is set for the configured 30-day TTL period.

Capture the result without exposing unnecessary personal data.

## 6. Add deployment evidence

Add verified screenshots under `screenshots/lambda/`, for example:

- `01-lex-fulfillment.png` — Lex hook configuration.
- `02-lex-chat.png` — successful simulated estimate.
- `03-cloudwatch.png` — relevant Lambda logs.
- `04-dynamodb.png` — persisted simulated record.

Only include screenshots from a deployment you actually tested.

Then update the README's **Verification status** section with the AWS region, verification date, and links to the evidence.

Keep the project limitations accurate: this workflow stores a **simulated estimate record**; it does not reserve a real hotel room or process a payment.

## 7. Clean up AWS resources

When you have finished testing and no longer need the deployment:

```bash
sam delete --stack-name hotel-booking-chatbot
```

Confirm in the AWS console that the stack and its resources have been removed. Check the account for any separately created Lex resources, which may not be part of this SAM stack.
