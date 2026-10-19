import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.config import settings
from backend.app.schemas.match import MatchRawFeatures
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

print(f"Testing with_structured_output on {settings.GEMINI_MODEL}...")

llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_MODEL,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.1
)

structured_llm = llm.with_structured_output(MatchRawFeatures)

prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un analista deportivo de élite. Extrae y estructura las estadísticas para el análisis predictivo."),
    ("human", "Genera las estadísticas y métricas H2H para el partido: {home_team} vs {away_team} en {competition}. Basado en datos reales recientes.")
])

chain = prompt | structured_llm

result: MatchRawFeatures = chain.invoke({
    "home_team": "Real Madrid",
    "away_team": "Barcelona",
    "competition": "La Liga"
})

print("Success! Structured result type:", type(result))
print("Home team:", result.home_team)
print("Home avg goals scored:", result.home_stats.avg_goals_scored)
print("Away team:", result.away_team)
print("H2H total matches:", result.h2h.total_matches_analyzed)
print("H2H avg total goals:", result.h2h.avg_total_goals_h2h)
print("H2H avg total corners:", result.h2h.avg_total_corners_h2h)
print("H2H avg total cards:", result.h2h.avg_total_cards_h2h)
print("Context notes count:", len(result.context_notes))
print("First note:", result.context_notes[0] if result.context_notes else "None")
