# 🏨 Hotel Booking Chatbot using Amazon Lex

![AWS Lex](https://img.shields.io/badge/Amazon%20Lex-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)
![NLP](https://img.shields.io/badge/NLP-Powered-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 📌 Project Overview

This project demonstrates the development of a **Hotel Booking Chatbot** using **Amazon Lex**, a service by Amazon Web Services (AWS) for building conversational interfaces.

The chatbot interacts with users to collect booking details such as location, check-in date, number of nights, and room type, and provides a confirmation message.

---

## 🎯 Objectives

- Build a conversational chatbot for hotel booking
- Understand intent and slot handling in Amazon Lex
- Implement a cost-efficient serverless solution
- Provide a user-friendly booking experience

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Amazon Lex (V2) | Chatbot / NLP engine |
| AWS Management Console | Bot configuration & testing |
| Natural Language Processing | Intent & slot recognition |

---

## ⚙️ Features

- 🗣️ Natural language interaction
- 📍 Captures user location
- 📅 Handles check-in date
- 🌙 Collects number of nights
- 🛏️ Supports multiple room types (Classic, Deluxe, Duplex, Suite)
- ✅ Booking confirmation summary

---

## 🧠 Bot Design

### Intent

- **BookHotel**

### Slots

| Slot Name   | Type          | Description            |
|-------------|---------------|------------------------|
| Location    | AMAZON.City   | City for hotel booking |
| CheckInDate | AMAZON.Date   | Check-in date          |
| Nights      | AMAZON.Number | Number of nights       |
| RoomType    | Custom        | Type of room           |

### Sample Utterances

- `I want to book a hotel`
- `Book a room in {Location}`
- `I need a hotel for {Nights} nights`

---

## 💬 Sample Conversation

```
User: Book a hotel
Bot:  Which city do you want to stay in?
User: Bangalore
Bot:  What is your check-in date?
User: April 1
Bot:  How many nights will you stay?
User: 2
Bot:  Which room type? Classic, Deluxe, Duplex, or Suite?
User: Deluxe
```

**Bot Response:**

```
✅ Your booking is confirmed!

📍 Location    : Bangalore
📅 Check-in    : 2026-04-01
🌙 Nights      : 2
🛏️ Room Type   : Deluxe

💰 Price per night:
   Classic  → ₹2,000
   Deluxe   → ₹3,000
   Duplex   → ₹5,000
   Suite    → ₹7,000

🎉 Thank you! Have a great stay!
```

---

## 📸 Screenshots

| | |
|---|---|
| ![Screenshot 1](screenshots/major%20ss1.png) | ![Screenshot 2](screenshots/major%20ss2.png) |
| ![Screenshot 3](screenshots/major%20ss3.png) | ![Screenshot 4](screenshots/major%20ss4.png) |

---

## 📹 Demo Video

> See `demo/20260330_002246.mp4` in this repository for a full walkthrough.

---

## 🚀 Implementation Steps

1. Created AWS account and accessed Amazon Lex
2. Built a bot named `HotelBookingBot`
3. Created intent `BookHotel`
4. Defined slots and prompts
5. Added sample utterances
6. Configured fulfillment with simple response (no Lambda)
7. Built and tested the chatbot

---

## 💰 Cost Optimization

- Used **AWS Free Tier** to keep costs at zero
- Avoided AWS Lambda to prevent additional charges
- Limited usage to testing and demonstration purposes

---

## ⚠️ Challenges Faced

- Understanding slot type creation in Lex V2
- Fixing slot name mismatches
- Resolving fulfillment and build errors

---

## 📈 Future Enhancements

- [ ] Integrate AWS Lambda for dynamic pricing
- [ ] Add payment gateway support
- [ ] Store bookings in a database (e.g., DynamoDB)
- [ ] Improve conversation flow with validations
- [ ] Deploy as a web widget

---

## 🔗 Author

**Pavan Kumar G P**

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 📢 Conclusion

This project showcases how **Amazon Lex** can be used to build a scalable and interactive chatbot for real-world applications like hotel booking, while maintaining a cost-efficient, serverless architecture.
