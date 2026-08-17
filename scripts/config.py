from pathlib import Path

GITHUB_USERNAME = "Abhijit1102"
OUTPUT_DIR = Path("assets/github")
DATA_DIR = Path("data")
MAX_FEATURED_REPOSITORIES = 6
EXCLUDED_REPOSITORIES = []
LANGUAGE_NORMALIZATION = {
    "Jupyter Notebook": "Python",
}
LANGUAGE_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A",
    "C++": "#F34B7D", "C": "#555555", "R": "#198CE7", "HTML": "#E34C26",
    "CSS": "#563D7C", "Shell": "#89E051", "Java": "#B07219", "Go": "#00ADD8",
    "Rust": "#DEA584", "Jupyter Notebook": "#DA5B0B", "SQL": "#336791",
}
TECH_RELEVANCE = {
    "ai": 5, "ml": 5, "llm": 6, "rag": 6, "fastapi": 4, "next.js": 4,
    "nextjs": 4, "react": 3, "python": 3, "typescript": 3, "data engineering": 5,
    "big data": 5, "spark": 4, "kafka": 4, "cloud": 3, "docker": 3, "devops": 3,
    "pinecone": 4, "qdrant": 4, "langchain": 5, "huggingface": 5,
}
