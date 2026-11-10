from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    representative_color = Column(String(20), default="#58FF9C", nullable=False)
    client_instagram_url = Column(String(500), nullable=False)
    # Lista de URLs de competidores almacenada como JSON string
    competitor_urls = Column(Text, nullable=False, default="[]")
    brand_voice_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_analyzed_at = Column(DateTime, nullable=True)

    # Relación 1 a N con reportes de análisis
    reports = relationship(
        "AnalysisReport",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisReport.created_at)"
    )

    def get_competitor_urls_list(self) -> list:
        try:
            return json.loads(self.competitor_urls) if self.competitor_urls else []
        except Exception:
            return []

    def set_competitor_urls_list(self, urls: list):
        self.competitor_urls = json.dumps(urls)


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    profile = relationship("Profile", back_populates="reports")
    proposals = relationship(
        "ScriptProposal",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ScriptProposal.id"
    )


class ScriptProposal(Base):
    __tablename__ = "script_proposals"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    competitor_source_info = Column(String(500), nullable=True)
    virality_badge = Column(String(100), nullable=True)
    # Escaleta por bloques de tiempo en formato JSON string
    escalation_timeline = Column(Text, nullable=False, default="[]")
    full_script = Column(Text, nullable=False)
    original_reel_url = Column(String(500), nullable=True)
    original_transcript = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("AnalysisReport", back_populates="proposals")

    def get_timeline_list(self) -> list:
        try:
            return json.loads(self.escalation_timeline) if self.escalation_timeline else []
        except Exception:
            return []

    def set_timeline_list(self, timeline: list):
        self.escalation_timeline = json.dumps(timeline)
