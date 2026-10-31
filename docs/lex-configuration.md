# Lex V2 Bot Configuration

The handler assumes the following bot configuration.

## Bot

- **Name:** `HotelBookingBot` (any name — handler checks intent name).
- **Locale:** `en_US`.
- **Voice:** none / text only.

## Intent: `BookHotel`

Sample utterances:

- `I want to book a hotel`
- `Book a room in {Location}`
- `I need a {RoomType} room for {Nights} nights`
- `Book a hotel in {Location} from {CheckInDate}`

Slots (all required, in this order):

| Slot | Type | Notes |
|---|---|---|
| `Location` | `AMAZON.City` | Free-form city name. |
| `CheckInDate` | `AMAZON.Date` | Lex normalizes to `YYYY-MM-DD`. |
| `Nights` | `AMAZON.Number` | Handler enforces 1..`maxNights`. |
| `RoomType` | Custom `RoomType` | Handler is case-insensitive. |

## Custom slot type `RoomType`

Values: `Classic`, `Deluxe`, `Duplex`, `Suite`.
Set **Slot value resolution** to `Restrict to slot values`.

## Fulfillment

- Lambda function: the deployed `hotel-booking-fulfilment` ARN.
- Enable **Use a Lambda function for initialization and validation**
  (Dialog code hook).
- Enable **Use a Lambda function for fulfillment**
  (FulfillmentCodeHook).

## Fallback

`FallbackIntent` is not handled by this Lambda. Configure a static
response in the console, e.g. "Sorry, I can only help with hotel
bookings right now."
