
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class UnitBase(BaseModel):
    name: str
    is_active: bool = True
    category: str = "General"

class UnitCreate(UnitBase):
    owner_id: int

class UnitUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None

class LearningObjectiveResponse(BaseModel):
    id: int
    description: str
    is_completed: bool
    class Config:
        from_attributes = True

class SubtopicResponse(BaseModel):
    id: int
    name: str
    is_completed: bool
    learning_objectives: List[LearningObjectiveResponse] = []
    class Config:
        from_attributes = True

class TopicResponse(BaseModel):
    id: int
    name: str
    subtopics: List[SubtopicResponse] = []
    class Config:
        from_attributes = True

class ModuleResponse(BaseModel):
    id: int
    name: str
    topics: List[TopicResponse] = []
    class Config:
        from_attributes = True

class UnitResponse(UnitBase):
    id: int
    owner_id: int
    modules: List[ModuleResponse] = []
    class Config:
        from_attributes = True

class QuizHistoryResponse(BaseModel):
    unit_name: str
    pnl: float
    timestamp: str

class ChatMessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str

class DashboardResponse(BaseModel):
    username: str
    role: str
    sensory_mode: str
    semester_status: str
    difficulty: str
    ai_persona: str
    active_units: List[str]
    units: List[UnitResponse] = []
    average_pnl: float
    total_quizzes: int
    quiz_history: List[QuizHistoryResponse]
    chat_history: List[ChatMessageResponse]

class ChaosRequest(BaseModel):
    unit: str
    focus_area: Optional[str] = None
    difficulty: str = "Asian Parent Expectations (Extreme)"
    student_id: str

class ChaosResponse(BaseModel):
    case_study: str

class SendOtpRequest(BaseModel):
    email: str
    action: str = "signup"  # "signup" or "forgot_password"

class SendOtpResponse(BaseModel):
    status: str
    message: str
    email: str
    otp_preview: Optional[str] = None

class VerifyOtpRequest(BaseModel):
    email: str
    otp: str
    action: str = "signup"

class ForgotPasswordResetRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class GenericAuthResponse(BaseModel):
    status: str
    message: str

class UserCreate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: str
    password: str
    otp: Optional[str] = None
    role: str = "Student"
    age: Optional[int] = None
    level_of_study: Optional[str] = None
    course_pursued: Optional[str] = None
    referral_code: Optional[str] = None
    sensory_mode: str = "Standard"
    difficulty: str = "Medium (Standard)"
    ai_persona: str = "Standard Trace"
    semester_status: Optional[str] = "Year 4 - Redemption Arc"
    interests: List[str] = []
    active_units: List[str] = []

class UserUpdate(BaseModel):
    role: Optional[str] = None
    sensory_mode: Optional[str] = None
    difficulty: Optional[str] = None
    ai_persona: Optional[str] = None
    semester_status: Optional[str] = None
    interests: Optional[List[str]] = None
    active_units: Optional[List[str]] = None

class UserResponseSchema(BaseModel):
    id: int
    username: str
    role: str
    sensory_mode: str
    difficulty: str
    ai_persona: str
    semester_status: str
    interests: List[str]
    active_units: List[str] = []

    class Config:
        from_attributes = True

class UserPreferencesUpdate(BaseModel):
    sensory_mode: Optional[str] = None
    ai_persona: Optional[str] = None

# --- TEACHER PORTAL SCHEMAS ---

class StudentSummary(BaseModel):
    id: int
    username: str
    average_pnl: float
    total_quizzes: int
    semester_status: str
    active_units: List[str]
    is_at_risk: bool = False
    risk_reason: Optional[str] = None

class TeacherDashboardResponse(BaseModel):
    action_required_queue: List[StudentSummary]
    total_active_students: int
    class_health_score: float

class ClassReportResponse(BaseModel):
    report: str

# --- PARENT PORTAL SCHEMAS ---

class ParentDashboardResponse(BaseModel):
    student_name: str
    academic_status: str
    current_study_path: List[str]
    ai_progress_review: str
    teacher_remarks: Optional[str] = None
    recent_grades: List[QuizHistoryResponse]

# --- TIMETABLE SCHEMAS ---

class TimetableSlot(BaseModel):
    day: str
    time: str
    activity: str
    unit: Optional[str] = None
    type: str  # "Study", "Break", "Assessment", "Revision"

class TimetableResponse(BaseModel):
    weekly_plan: List[TimetableSlot]
    ai_brief: str

# --- AI Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    prompt: str
    user_id: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str

class QuizRequest(BaseModel):
    unit_name: str
    user_id: str
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    learning_outcomes: Optional[List[str]] = None

class QuizQuestion(BaseModel):
    question_text: str
    options: List[str]
    correct_option_index: int
    explanation: str
    learning_outcome: Optional[str] = None

class QuizResponse(BaseModel):
    quiz_title: str
    questions: List[QuizQuestion]
    learning_outcomes: Optional[List[str]] = None

class QuizRecordRequest(BaseModel):
    unit_name: str
    score: int
    total: int
    user_id: str
    timestamp: Any

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str

class RecommendationResponse(BaseModel):
    recommendation: str

class UnitProgressInfo(BaseModel):
    unit_name: str
    completed_subtopics: int = 0
    total_subtopics: int = 0
    progress_percentage: float = 0.0

class QuizAttemptInfo(BaseModel):
    unit_name: str
    score: float
    timestamp: Optional[Any] = None

class StudyContextPayload(BaseModel):
    overall_progress_percentage: Optional[float] = None
    units_progress: List[UnitProgressInfo] = []
    completed_subtopic_names: List[str] = []
    pending_subtopic_names: List[str] = []
    average_quiz_score: Optional[float] = None
    total_quizzes_taken: Optional[int] = None
    mastered_topics: List[str] = []
    weak_topics: List[str] = []
    recent_quizzes: List[QuizAttemptInfo] = []
    force_refresh: Optional[bool] = False

class BookmarkBase(BaseModel):
    type: str
    title: str
    target: str
    context: Optional[str] = None
    timestamp: float

class BookmarkCreate(BookmarkBase):
    pass

class BookmarkResponse(BookmarkBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class SyllabusProgressItem(BaseModel):
    node_id: int
    node_type: str
    status: str
    last_studied_at: Optional[float] = None

class SyncRequest(BaseModel):
    progress: List[SyllabusProgressItem] = []
    bookmarks: List[BookmarkBase] = []

class SyncResponse(BaseModel):
    success: bool = True
    status: Optional[str] = "success"
    message: str
    synced_at: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


 