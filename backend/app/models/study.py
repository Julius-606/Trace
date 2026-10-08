
# ==========================================
# IDENTITY: The Syllabus Vault / Models
# FILEPATH: backend/app/models/study.py
# COMPONENT: Database Schema
# ROLE: Defines what a Study Task and Syllabus look like in the DB.
# VIBE: The harsh reality of how much Anatomy you haven't read yet. 💀🩺
# ==========================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class BrainRotLevel(enum.Enum):
    CHILL = "chill"           # Just highlighting notes
    MID = "mid"               # Actually trying to understand Pharmacology
    COOKED = "cooked"         # 3 AM before the exam, straight panic

class StudyTask(Base):
    __tablename__ = "study_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    subject = Column(String, index=True, nullable=False) # e.g., "Internal Medicine"
    
    # Scheduling & Sync
    due_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)

    # New metadata for Orbit Life-OS v4.0.0
    remarks = Column(Text, nullable=True)
    is_reminder = Column(Boolean, default=False)

    # Chronotype-based scheduling hint
    brain_rot_level = Column(Enum(BrainRotLevel), default=BrainRotLevel.CHILL)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<StudyTask(title='{self.title}', subject='{self.subject}', completed={self.completed})>"


