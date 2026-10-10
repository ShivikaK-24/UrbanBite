# 🍔 OrderIQ — AI-Powered Restaurant Chatbot

**OrderIQ** is an AI-powered restaurant ordering chatbot built for *UrbanBite*, a fictional restaurant. It enables customers to explore menus, place orders, and modify their carts using natural language, while providing restaurant managers with business analytics and AI-generated insights.

🔗 **Live Demo:** [Try OrderIQ](https://orderiq-urbanbite.streamlit.app/)

## ✨ Features

- **Conversational Ordering:** Understands natural-language requests to help customers find and order menu items.
- **Smart Menu Search:** Retrieves relevant dishes and beverages based on customer requests, preferences, and price ranges.
- **Cart Management:** Supports adding items, removing products, and updating quantities through conversation.
- **Automated Checkout:** Calculates subtotals, GST, and final order totals using Python-based business logic.
- **Alcohol Age Confirmation:** Requires customers to confirm they are 25 or older before checking out with alcoholic beverages.
- **Order Management:** Generates order IDs and stores confirmed orders.
- **Manager Dashboard:** Displays total orders, revenue, average order value, items sold, top-selling products, order mix, and recent orders.
- **AI Manager Insights:** Uses AI to summarize business data, identify observations, and generate actionable recommendations with relevant data caveats.
- **Staff Login:** Provides a separate authenticated interface for managerial analytics.

## ⚙️ How It Works

1. A customer submits a request through the Streamlit chatbot.
2. A menu retrieval layer identifies relevant products from the restaurant catalog.
3. The Groq API-powered language model interprets the request and generates a structured action.
4. Python validates the requested action and handles cart operations, pricing, GST, and checkout.
5. Confirmed orders are stored and used by the analytics service.
6. The manager can review dashboard metrics and generate AI-powered business insights.

**Design principle:** AI handles language understanding and business interpretation, while deterministic Python logic controls product validation, financial calculations, and order processing.

## 🛠️ Tech Stack

- **Language:** Python
- **Frontend:** Streamlit
- **LLM Integration:** Groq API — `openai/gpt-oss-20b`
- **Data Processing:** Pandas
- **Storage:** JSON-based order records
- **Deployment:** Streamlit Community Cloud
- **Development:** VS Code, with ChatGPT-assisted vibe coding

## 💼 Business Use Cases

- Conversational restaurant ordering and menu discovery
- Reducing friction in digital ordering workflows
- Automating repetitive menu-related customer queries
- Monitoring sales and order performance
- Identifying popular menu items
- Supporting managerial decisions through AI-generated insights

## 🚀 Future Scope

- Database integration with PostgreSQL or Supabase
- Payment gateway and POS integration
- Multilingual and voice-based ordering
- Customer segmentation and personalized recommendations
- Demand forecasting and inventory analytics

## ⚠️ Note

OrderIQ is an educational prototype built to demonstrate practical applications of generative AI in restaurant operations and managerial decision support. It uses sample restaurant data and is not a production-grade ordering or payment system.

## 👩‍💻 Built By

**Shivika Khanna**  
PGDM — Big Data Analytics | FORE School of Management

Built using Python, Streamlit, Groq API, and ChatGPT-assisted vibe coding.
