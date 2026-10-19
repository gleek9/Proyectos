"""
Pydantic schemas for API requests, responses, and agent data structures.
"""
from backend.app.schemas.match import (
    MatchSearchQuery, PreviousMatch, TeamFormStats, HeadToHeadStats, MatchRawFeatures
)
from backend.app.schemas.prediction import (
    PredictRequest,
    WinnerPrediction, GoalsPrediction, CornersPrediction, CardsPrediction,
    MatchPredictionDetails, GoalDistributionItem, TopScoreItem, ChartData,
    MatchMeta, PredictionResponse
)

__all__ = [
    "MatchSearchQuery", "PreviousMatch", "TeamFormStats", "HeadToHeadStats", "MatchRawFeatures",
    "PredictRequest",
    "WinnerPrediction", "GoalsPrediction", "CornersPrediction", "CardsPrediction",
    "MatchPredictionDetails", "GoalDistributionItem", "TopScoreItem", "ChartData",
    "MatchMeta", "PredictionResponse"
]
