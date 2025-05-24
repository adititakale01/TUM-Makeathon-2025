# VERA: AI-Powered Hotel Recommendation Engine

**Developed at TUM.ai Makeathon 2025** in collaboration with **CHECK24**  

## What is VERA?
VERA is an LLM-driven hotel search engine we made, that eliminates the hassle of browsing hundreds of tabs. It uses OpenAI LLM, offering ideal sorted recommendations based on the human prompt.

It uses OpenAI's GPT-4 to:
Understand natural language queries (e.g., "stylish modern hotel with great breakfast").
- Dynamically filter and rank hotels based on amenities, pricing, and user preferences.
- Reduce ambiguity in hotel data by classifying columns into rankable features (price, rating) vs. constraints (amenities).

## Features
- Natural language understanding for hotel searches - It interprets free-text requests like a human travel agent.
- Smart ranking combining price, amenities, and user preferences - Separates rankable (price, distance) from descriptive (pool, pet-friendly) features.
- Chain-of-Thought Ranking - Mimics human logic: prioritizes family-friendly options, extra beds, and budget.
- Fast filtering of 100K+ hotel offers
- Real-World Demo - Streamlit web app for live queries and email-based results.
- Email-based results delivery (demo implementation)

## Tech Stack
- Backend: Python, OpenAI GPT-4
- Data Processing: Pandas, JSON normalization
- Frontend: Streamlit (demo)
- Deployment: Localhost (with scalability plans for CHECK24’s high-traffic ecosystem)


## How It Works

### Example User Input:

"Family-friendly hotel near the beach with a pool and breakfast under €200/night"

### Data Preprocessing:
- Normalizes 50+ raw columns (e.g., distancetobeach → distance_to_beach).
- Drops irrelevant metadata (e.g., searchid, timestamp).

### LLM Pipeline:

- Step 1: Validates query relevance.
- Step 2: Classifies columns into rankable vs. amenities.
- Step 3: Filters and ranks hotels using a hybrid rule-based + LLM approach.

### Example Output:

json file similar to:  
[  
    {  
    "name": "Copenhagen Island Hotel",  
    "price": "€196/night",  
    "features": ["Good breakfast", "Pool", "Family-friendly"]  
    }  
]  


## Why It Matters for CHECK24

### Solves High-Traffic Challenges:
- Scalable filtering avoids full-database searches.
- Modular design fits CHECK24’s comparison engine (100K+ offers, 10K+ concurrent reads).
### User-Centric:
- Eliminates outdated offers with real-time LLM processing.
- Demo mimics CHECK24’s push-update subscription model.


## Tech Stack
| Component       | Technology |
|-----------------|------------|
| Backend         | Python 3.9 |
| LLM             | OpenAI GPT-4 |
| Data Processing | Pandas |
| Web Interface   | Streamlit |
