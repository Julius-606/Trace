
export type Role = 'executive' | 'member' | 'alumni' | 'adjudicator';

export type ExecutivePosition = 
  | 'President'
  | 'Vice President (Internal)'
  | 'Vice President (External)'
  | 'Chief Adjudicator & Training Director'
  | 'Finance & Treasury Secretary'
  | 'Organizing & Logistics Secretary'
  | 'Public Relations & Tech Lead';

export type DebateFormat = 'British Parliamentary (BP)' | 'Asian Parliamentary (AP)' | 'World Schools (WSDC)';

export type PaymentStatus = 'Paid' | 'Pending' | 'Waived';

export interface Member {
  id: string;
  fullName: string;
  studentId: string;
  email: string;
  phone: string;
  role: Role;
  executivePosition?: ExecutivePosition;
  yearOfStudy: 'Year 1' | 'Year 2' | 'Year 3' | 'Year 4' | 'Postgraduate' | 'Alumni';
  faculty: string;
  membershipStatus: PaymentStatus;
  duesAmountKes: number;
  mpesaRef?: string;
  joinedDate: string;
  attendanceRate: number; // 0 - 100%
  debatesAttendedCount: number;
  totalDebatesCount: number;
  speakerPointsAvg: number;
  bio?: string;
  alumniOccupation?: string;
  alumniOrganization?: string;
}

export interface ClubNotification {
  id: string;
  targetUserId: string; // 'all' or specific user ID
  title: string;
  message: string;
  type: 'duty_delegated' | 'announcement' | 'dues_verified' | 'debate_round' | 'general';
  linkTab?: string;
  isRead: boolean;
  createdAt: string;
}

export interface AgendaItem {
  id: string;
  meetingTitle: string;
  date: string;
  time: string;
  location: string;
  status: 'Upcoming' | 'Completed' | 'In Progress';
  chairperson: string;
  agendaItems: {
    id: string;
    title: string;
    assignedTo: string;
    assignedUserId?: string;
    deadline: string;
    isCompleted: boolean;
    notes?: string;
  }[];
  logisticsChecklist: {
    id: string;
    item: string;
    quantity: number;
    status: 'Ready' | 'Pending' | 'Not Started';
    assignedTo: string;
  }[];
  minutesSummary?: string;
}

export interface FinancialTransaction {
  id: string;
  date: string;
  type: 'Income' | 'Expense';
  category: 'Semester Dues' | 'Tournament Registration' | 'Logistics & Transport' | 'Equipment & Audio' | 'Merchandise' | 'Sponsorship & Donation' | 'Refreshments';
  amountKes: number;
  description: string;
  referenceCode: string; // M-Pesa / Bank ref
  recordedBy: string;
  status: 'Verified' | 'Pending Approval';
}

export interface SpeakerScore {
  speakerName: string;
  role: string;
  matterScore: number;
  mannerScore: number;
  methodScore: number;
  totalScore: number;
  feedback: string;
}

export interface DebateSession {
  id: string;
  title: string;
  motion: string;
  motionInfoSlide?: string;
  category: 'Geopolitics & IR' | 'Economics & Development' | 'Technology & AI' | 'Law & Human Rights' | 'Environmental & Climate' | 'African Governance';
  format: DebateFormat;
  date: string;
  time: string;
  status: 'Scheduled' | 'Live Now' | 'Archived';
  googleMeetLink: string;
  adjudicators: string[];
  winningTeam?: string;
  teams: {
    positionName: string;
    speaker1: string;
    speaker2?: string;
    teamScore?: number;
    rank?: number;
  }[];
  speakerScores?: SpeakerScore[];
  transcript?: {
    speaker: string;
    timestamp: string;
    text: string;
    poiOfferedCount?: number;
  }[];
  summaryClashes?: string[];
  attendeeIds: string[];
}

export interface Announcement {
  id: string;
  title: string;
  content: string;
  author: string;
  authorRole: string;
  publishDate: string;
  priority: 'High' | 'Normal' | 'Urgent';
  category: 'Tournament' | 'Weekly Training' | 'Executive Notice' | 'Social & Mentorship';
  pinned: boolean;
}

export interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  startTime: string;
  endTime: string;
  location: string;
  googleMeetUrl?: string;
  eventType: 'Debate Session' | 'Training Workshop' | 'Executive Meeting' | 'Tournament' | 'Alumni Mixer';
  description: string;
  leadCoordinator: string;
}

export interface AlumniMentorshipNote {
  id: string;
  alumniId: string;
  alumniName: string;
  menteeName: string;
  menteeId: string;
  topic: string;
  date: string;
  adviceSummary: string;
  status: 'Active' | 'Completed' | 'Pending Request';
}


