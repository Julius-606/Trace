export type UserRole = 'Student' | 'Teacher' | 'Parent' | 'Admin';

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  difficulty: string;
  semesterStatus: string;
  aiPersona: string;
  sensoryMode?: string;
  activeUnits: string[];
  traceCoins?: number;
}

export interface SubtopicObjective {
  id: string;
  title: string;
  description: string;
  content: string;
}

export interface Subtopic {
  id: number;
  topicId: number;
  name: string;
  isCompleted: boolean;
  objectives: SubtopicObjective[];
}

export interface Topic {
  id: number;
  moduleId: number;
  name: string;
  description?: string;
  subtopics: Subtopic[];
}

export interface Module {
  id: number;
  unitId: number;
  name: string;
  description?: string;
  topics: Topic[];
}

export interface Unit {
  id: number;
  unitName: string;
  category: string;
  description: string;
  isActive: boolean;
  modules: Module[];
}

export interface Bookmark {
  id: string;
  userId: string;
  subtopicId: number;
  subtopicName: string;
  objectiveDescription: string;
  excerpt: string;
  timestamp: number;
  notes?: string;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
  unitName: string;
  topicName?: string;
  learningOutcome?: string;
}

export interface QuizHistoryItem {
  id: string;
  userId: string;
  unitName: string;
  topicName?: string;
  score: number;
  total: number;
  pnlScore: number; // percentage score 0-100%
  timestamp: number;
  questions?: QuizQuestion[];
  userAnswers?: Record<number, number>;
  status?: 'Completed' | 'Unfinished';
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: number;
}

export interface ChatSession {
  id: string;
  userId: string;
  title: string;
  description?: string;
  timestamp: number;
  messages: ChatMessage[];
}

export interface TimetableSlot {
  id: string;
  day: 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';
  startTime: string;
  endTime: string;
  type: 'study' | 'break' | 'assessment' | 'revision';
  title: string;
  unitName?: string;
  notes?: string;
}

export interface PeerMessage {
  id: string;
  senderId: string;
  senderName: string;
  recipientId: string;
  content: string;
  timestamp: number;
}

export interface StudentProgressSummary {
  id: string;
  username: string;
  semesterStatus: string;
  activeUnits: string[];
  averagePnl: number;
  totalQuizzes: number;
  completedSubtopics: number;
  totalSubtopics: number;
  isAtRisk: boolean;
  riskReason?: string;
}


export interface SystemLogEntry {
  id: string;
  timestamp: number;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  source: 'FastAPI Backend' | 'Express Node' | 'AI Engine' | 'Database Engine';
  method: string;
  endpoint: string;
  statusCode: number;
  durationMs: number;
  ip: string;
  message: string;
  payloadSnippet?: string;
  errorStack?: string;
}
