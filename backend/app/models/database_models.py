
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(200), nullable=True)
    role = Column(String(50), default="Student")
    sensory_mode = Column(String(50), default="Standard")
    difficulty = Column(String(50), default="Medium (Standard)")
    ai_persona = Column(String(100), default="Standard Trace")
    semester_status = Column(String(100), default="Year 4 - Redemption Arc")
    full_name = Column(String(150), nullable=True)
    age = Column(Integer, nullable=True)
    level_of_study = Column(String(100), nullable=True)
    course_pursued = Column(String(150), nullable=True)
    referral_code = Column(String(100), nullable=True)
    is_email_verified = Column(Boolean, default=False)
    interests = Column(JSON, default=list)
    trace_coins = Column(Integer, default=200)

    # Multi-platform channels & account linking
    phone_number = Column(String(50), unique=True, index=True, nullable=True)
    telegram_chat_id = Column(String(50), unique=True, index=True, nullable=True)
    magic_token = Column(String(100), unique=True, index=True, nullable=True)
    magic_token_expires_at = Column(Float, nullable=True)

    # Relationships
    channels = relationship("UserChannel", back_populates="user", cascade="all, delete-orphan")
    units = relationship("Unit", back_populates="owner", cascade="all, delete-orphan")
    quiz_history = relationship("QuizHistory", back_populates="owner", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="owner", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="owner", cascade="all, delete-orphan")
    performance_logs = relationship("PerformanceLog", back_populates="owner", cascade="all, delete-orphan")
    timetables = relationship("Timetable", back_populates="owner", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="owner", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="owner", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        active_units_data = kwargs.pop("active_units", None)
        super().__init__(**kwargs)
        if active_units_data:
            for u_name in active_units_data:
                self.units.append(Unit(name=u_name, is_active=True))

    @property
    def neurons(self) -> int:
        return self.trace_coins or 0

    @neurons.setter
    def neurons(self, val: int):
        self.trace_coins = val

    @property
    def active_units_list(self):
        return [u.name for u in self.units if u.is_active]


class UserChannel(Base):
    """Normalized multi-platform channel mapping table for Telegram, WhatsApp, Web, and Android."""
    __tablename__ = "user_channels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_type = Column(String(50), nullable=False) # "telegram", "whatsapp", "web", "android"
    channel_identifier = Column(String(100), nullable=False, index=True) # telegram chat_id or phone number
    linked_at = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="channels")

class Unit(Base):

    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    is_active = Column(Boolean, default=True)
    category = Column(String(100), default="General")
    course = Column(String(100), default="General")
    unit_group = Column(String(100), nullable=True)
    learning_outcomes = Column(Text, nullable=True)
    price_t_coins = Column(Integer, default=20)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="units")

    # Relationships to lower levels
    modules = relationship("Module", back_populates="unit", cascade="all, delete-orphan")

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)

    unit_id = Column(Integer, ForeignKey("units.id"))
    unit = relationship("Unit", back_populates="modules")

    # NEW: Module -> Topic
    topics = relationship("Topic", back_populates="module", cascade="all, delete-orphan")

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)

    module_id = Column(Integer, ForeignKey("modules.id"))
    module = relationship("Module", back_populates="topics")

    # Topic -> Subtopic
    subtopics = relationship("Subtopic", back_populates="topic", cascade="all, delete-orphan")

class Subtopic(Base):
    __tablename__ = "subtopics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True)
    is_completed = Column(Boolean, default=False)
    content = Column(Text, nullable=True) # Full expansive syllabus notes & lecture breakdowns

    topic_id = Column(Integer, ForeignKey("topics.id"))
    topic = relationship("Topic", back_populates="subtopics")

    # Subtopic -> LearningObjective
    learning_objectives = relationship("LearningObjective", back_populates="subtopic", cascade="all, delete-orphan")

class LearningObjective(Base):
    __tablename__ = "learning_objectives"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text)
    is_completed = Column(Boolean, default=False)
    content = Column(Text, nullable=True) # Detailed objective-level markdown content

    subtopic_id = Column(Integer, ForeignKey("subtopics.id"))
    subtopic = relationship("Subtopic", back_populates="learning_objectives")

class UserSyllabusProgress(Base):
    __tablename__ = "user_syllabus_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    node_id = Column(Integer) # Can be Unit, Module, Topic, or Subtopic ID
    node_type = Column(String(50)) # "unit", "module", "topic", "subtopic"
    status = Column(String(50), default="Locked") # "Locked", "Unlocked", "In_Progress", "Completed"
    last_studied_at = Column(Float, nullable=True)
    version = Column(Integer, default=1)
    updated_at = Column(Float, nullable=True)

    user = relationship("User")

class QuizHistory(Base):
    __tablename__ = "quiz_history"

    id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(200))
    score = Column(Integer)
    total = Column(Integer)
    pnl = Column(Float)
    timestamp = Column(String(100))

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="quiz_history")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default="New Consultation")
    description = Column(Text, nullable=True)
    timestamp = Column(Float)
    is_archived = Column(Boolean, default=False)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20)) # "user" or "model"
    content = Column(Text)
    timestamp = Column(String(100))

    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    owner = relationship("User", back_populates="chat_messages")

    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=True, index=True)
    session = relationship("ChatSession", back_populates="messages")

class PerformanceLog(Base):
    __tablename__ = "performance_logs"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(200))
    grade = Column(Float)
    timestamp = Column(String(100))

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="performance_logs")

class Timetable(Base):
    __tablename__ = "timetables"

    id = Column(Integer, primary_key=True, index=True)
    weekly_plan_json = Column(JSON)
    ai_brief = Column(Text)
    timestamp = Column(Float) # Time of generation

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="timetables")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation = Column(Text)
    timestamp = Column(Float) # Time of generation

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="recommendations")

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50)) # 'learn' | 'chat' | 'browser' | 'quiz' | 'general'
    title = Column(String(200))
    target = Column(String(500)) # path or target reference
    context = Column(Text, nullable=True) # text content or excerpt
    timestamp = Column(Float) # epoch time

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="bookmarks")


class AdminNotification(Base):
    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True) # "NEW_USER", "BACKEND_ERROR", "BUG_REPORT", "SYSTEM_ALERT", "SECURITY"
    level = Column(String(20), default="info") # "info", "warning", "error", "critical"
    title = Column(String(200))
    message = Column(Text)
    details = Column(Text, nullable=True) # JSON, URL or stacktrace
    is_read = Column(Boolean, default=False)
    timestamp = Column(Float) # epoch time


class SystemRelease(Base):
    __tablename__ = "system_releases"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50))
    version_code = Column(Integer, default=1)
    artifact_type = Column(String(100), default="Trace Mobile App")
    download_url = Column(String(500), nullable=True)
    release_notes = Column(Text, nullable=True)
    is_current = Column(Boolean, default=False)
    is_mandatory = Column(Boolean, default=False)
    min_supported_version_code = Column(Integer, default=1)
    file_size = Column(String(50), default="14.8 MB")
    timestamp = Column(Float)


class CanvasSession(Base):
    __tablename__ = "canvas_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default="New Ingestion Session")
    chat_history = Column(JSON, default=list) # List of dicts: [{"role": "user" | "model", "content": "..."}]
    canvas_content = Column(Text, default="")  # Course structure/syllabus Markdown
    field_name = Column(String(100), default="Clinical Medicine")
    course_name = Column(String(100), default="MBChB")
    unit_group_name = Column(String(100), nullable=True)
    last_updated = Column(Float)


class EmailVerificationOTP(Base):
    __tablename__ = "email_verification_otps"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), index=True)
    otp = Column(String(10), index=True)
    action = Column(String(50), default="signup")  # "signup" or "forgot_password"
    created_at = Column(Float)
    expires_at = Column(Float)
    is_used = Column(Boolean, default=False)


# ==============================================================================
# Trace Rich Library Engine Models (Pre-generation Pools & Auditing)
# ==============================================================================

class GeneratedQuizBank(Base):
    """Pre-built quiz questions tagged by node/topic for instant cached serving."""
    __tablename__ = "generated_quiz_bank"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="CASCADE"), nullable=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=True, index=True)
    subtopic_id = Column(Integer, ForeignKey("subtopics.id", ondelete="CASCADE"), nullable=True, index=True)

    unit_name = Column(String(200), index=True, nullable=False)
    topic_name = Column(String(200), index=True, nullable=True)
    subtopic_name = Column(String(200), index=True, nullable=True)

    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=False) # List of 4 string options
    correct_answer = Column(String(500), nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(50), default="Medium")
    clinical_scenario = Column(Text, nullable=True)
    learning_outcomes = Column(JSON, default=list)
    created_at = Column(Float, nullable=True)

    unit = relationship("Unit")
    subtopic = relationship("Subtopic")


class NodeEnrichment(Base):
    """Alternative explanations, multi-perspective clinical notes, and inline visual diagrams."""
    __tablename__ = "node_enrichments"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, index=True, nullable=False) # Subtopic, Topic, or Unit ID
    node_type = Column(String(50), index=True, nullable=False) # "subtopic", "topic", "unit"
    node_name = Column(String(200), index=True, nullable=False)

    intuitive_explanation = Column(Text, nullable=True)
    technical_explanation = Column(Text, nullable=True)
    clinical_takeaway = Column(Text, nullable=True)

    diagram_type = Column(String(50), default="mermaid") # "mermaid", "svg", "ascii"
    diagram_code = Column(Text, nullable=True) # Mermaid chart syntax or SVG element
    diagram_caption = Column(String(250), nullable=True)

    metadata_json = Column(JSON, default=dict)
    created_at = Column(Float, nullable=True)
    updated_at = Column(Float, nullable=True)


class ContentAuditLog(Base):
    """Verification status, factual accuracy score, and quality audit flags."""
    __tablename__ = "content_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(50), index=True, nullable=False) # "quiz", "enrichment", "subtopic"
    target_id = Column(Integer, index=True, nullable=False)
    verification_status = Column(String(50), default="pending", index=True) # "verified", "flagged", "pending", "rejected"
    accuracy_score = Column(Float, default=1.0) # 0.0 to 1.0 (or percentage)
    flags = Column(JSON, default=list) # Issues, hallucinations, or formatting errors
    audit_pass = Column(Integer, default=1) # Pass 1 or Pass 2 double-check
    audited_by = Column(String(100), default="Trace Audit Cron")
    auditor_notes = Column(Text, nullable=True)
    created_at = Column(Float, nullable=True)


class UnitPipelineProgress(Base):
    """Tracks real-time background content build-up (quizzes, enrichments, diagrams) per unit."""
    __tablename__ = "unit_pipeline_progress"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), unique=True, index=True)
    unit_name = Column(String(200), index=True)
    status = Column(String(50), default="queued", index=True) # "queued", "processing", "completed", "failed", "idle"
    total_subtopics = Column(Integer, default=0)
    completed_subtopics = Column(Integer, default=0)
    quizzes_generated = Column(Integer, default=0)
    diagrams_generated = Column(Integer, default=0)
    current_step = Column(String(250), nullable=True)
    progress_percent = Column(Float, default=0.0)
    started_at = Column(Float, nullable=True)
    completed_at = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)






 