import random

# Predefined questions
QUESTIONS = [
    {
        "question": "Which of the following best describes *structured data*?",
        "options": [
            "Tweets and blog posts",
            "Tables in a relational database",
            "Photos and videos",
            "Audio recordings"
        ],
        "answer": "Tables in a relational database"
    },
    {
        "question": "What is the main purpose of a data visualization?",
        "options": [
            "To make datasets larger",
            "To store data securely",
            "To reveal insights and patterns in data",
            "To eliminate missing values"
        ],
        "answer": "To reveal insights and patterns in data"
    },
    {
        "question": "In the context of AI agents, what does the perception-action loop describe?",
        "options": [
            "The cycle of sensing the environment, reasoning, and acting",
            "A debugging process for fixing agent code",
            "How humans interact with robots socially",
            "The process of labeling training data"
        ],
        "answer": "The cycle of sensing the environment, reasoning, and acting"
    },
    {
        "question": "Which of the following is an example of a reactive agent?",
        "options": [
            "A chess-playing AI that plans several moves ahead",
            "A thermostat that turns on heating when the temperature drops",
            "A recommender system that uses collaborative filtering",
            "A search engine that ranks results based on relevance"
        ],
        "answer": "A thermostat that turns on heating when the temperature drops"
    },
    {
        "question": "In a Markov Decision Process (MDP), what does the policy represent?",
        "options": [
            "The sequence of rewards",
            "The mapping from states to actions",
            "The set of possible states",
            "The agent’s memory of past states"
        ],
        "answer": "The mapping from states to actions"
    }
]

def generate_question(index=None):
    """Return a question by index or random if None."""
    if index is not None and 0 <= index < len(QUESTIONS):
        return QUESTIONS[index]
    return random.choice(QUESTIONS)

def total_questions():
    return len(QUESTIONS)
