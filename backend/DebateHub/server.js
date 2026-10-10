// server.ts
import express from "express";
import { createServer as createViteServer } from "vite";
import dotenv2 from "dotenv";
import path2 from "path";
import fs from "fs";
import { fileURLToPath } from "url";

// src/db/neon.ts
import { neon } from "@neondatabase/serverless";
import dotenv from "dotenv";
import path from "path";
dotenv.config({ path: path.resolve(process.cwd(), ".env") });
dotenv.config({ path: path.resolve(process.cwd(), "..", ".env") });
var databaseUrl = process.env.DEBATEHUB_NEON_DATABASE_URL || process.env.DEBATEHUB_DATABASE_URL;
var isNeonConfigured = Boolean(databaseUrl && databaseUrl.startsWith("postgres"));
var sql = isNeonConfigured && databaseUrl ? neon(databaseUrl) : null;
async function initializeNeonTables() {
  if (!sql) {
    return {
      success: false,
      message: "DEBATEHUB_NEON_DATABASE_URL environment variable is not set. Add it in Hugging Face Space Secrets or .env file."
    };
  }
  try {
    await sql`
      CREATE TABLE IF NOT EXISTS members (
        id VARCHAR(64) PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        student_id VARCHAR(64) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        phone VARCHAR(64),
        role VARCHAR(32) NOT NULL DEFAULT 'member',
        executive_position VARCHAR(128),
        year_of_study VARCHAR(32) NOT NULL DEFAULT 'Year 1',
        faculty VARCHAR(255) NOT NULL,
        membership_status VARCHAR(32) NOT NULL DEFAULT 'Pending',
        dues_amount_kes NUMERIC NOT NULL DEFAULT 500,
        mpesa_ref VARCHAR(64),
        joined_date VARCHAR(32) NOT NULL,
        attendance_rate NUMERIC NOT NULL DEFAULT 0,
        debates_attended_count INTEGER NOT NULL DEFAULT 0,
        total_debates_count INTEGER NOT NULL DEFAULT 0,
        speaker_points_avg NUMERIC NOT NULL DEFAULT 70,
        bio TEXT,
        alumni_occupation VARCHAR(255),
        alumni_organization VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS financial_transactions (
        id VARCHAR(64) PRIMARY KEY,
        date VARCHAR(32) NOT NULL,
        type VARCHAR(16) NOT NULL,
        category VARCHAR(64) NOT NULL,
        amount_kes NUMERIC NOT NULL,
        description TEXT NOT NULL,
        reference_code VARCHAR(64) NOT NULL,
        recorded_by VARCHAR(255) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Verified',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS debate_sessions (
        id VARCHAR(64) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        motion TEXT NOT NULL,
        motion_info_slide TEXT,
        category VARCHAR(64) NOT NULL,
        format VARCHAR(64) NOT NULL,
        date VARCHAR(32) NOT NULL,
        time VARCHAR(64) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Scheduled',
        google_meet_link TEXT,
        winning_team VARCHAR(128),
        adjudicators JSONB DEFAULT '[]'::jsonb,
        teams JSONB DEFAULT '[]'::jsonb,
        summary_clashes JSONB DEFAULT '[]'::jsonb,
        attendee_ids JSONB DEFAULT '[]'::jsonb,
        transcript JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS executive_agendas (
        id VARCHAR(64) PRIMARY KEY,
        meeting_title VARCHAR(255) NOT NULL,
        date VARCHAR(32) NOT NULL,
        time VARCHAR(64) NOT NULL,
        location VARCHAR(255) NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Upcoming',
        chairperson VARCHAR(255) NOT NULL,
        agenda_items JSONB DEFAULT '[]'::jsonb,
        logistics_checklist JSONB DEFAULT '[]'::jsonb,
        minutes_summary TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS announcements (
        id VARCHAR(64) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL,
        author VARCHAR(255) NOT NULL,
        author_role VARCHAR(128) NOT NULL,
        publish_date VARCHAR(32) NOT NULL,
        priority VARCHAR(32) NOT NULL DEFAULT 'Normal',
        category VARCHAR(64) NOT NULL,
        pinned BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS calendar_events (
        id VARCHAR(64) PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        date VARCHAR(32) NOT NULL,
        start_time VARCHAR(32) NOT NULL,
        end_time VARCHAR(32) NOT NULL,
        location VARCHAR(255) NOT NULL,
        google_meet_url TEXT,
        event_type VARCHAR(64) NOT NULL,
        description TEXT NOT NULL,
        lead_coordinator VARCHAR(255) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;
    await sql`
      CREATE TABLE IF NOT EXISTS mentorship_notes (
        id VARCHAR(64) PRIMARY KEY,
        alumni_id VARCHAR(64) NOT NULL,
        alumni_name VARCHAR(255) NOT NULL,
        mentee_id VARCHAR(64) NOT NULL,
        mentee_name VARCHAR(255) NOT NULL,
        topic VARCHAR(255) NOT NULL,
        date VARCHAR(32) NOT NULL,
        advice_summary TEXT NOT NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'Active',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      );
    `;
    return {
      success: true,
      message: "Neon PostgreSQL tables initialized successfully (members, transactions, debates, agendas, announcements, events, mentorship_notes)."
    };
  } catch (error) {
    console.error("Error initializing Neon tables:", error);
    return {
      success: false,
      message: `Failed to initialize Neon schema: ${error.message}`
    };
  }
}

// src/data/initialData.ts
var initialMembers = [
  {
    id: "mem-exec-1",
    fullName: "Julius Gachoki",
    studentId: "GLUK/BC/2023/1042",
    email: "juliusgachoki26@gmail.com",
    phone: "+254 712 345 678",
    role: "executive",
    executivePosition: "President",
    yearOfStudy: "Year 4",
    faculty: "Health Sciences & Community Development",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QJD891KA23",
    joinedDate: "2023-09-10",
    attendanceRate: 96,
    debatesAttendedCount: 24,
    totalDebatesCount: 25,
    speakerPointsAvg: 79.4,
    bio: "Passionate debater, leading GLUK DC to national recognition across the East African parliamentary debate circuit."
  },
  {
    id: "mem-exec-2",
    fullName: "Achieng Brenda Odhiambo",
    studentId: "GLUK/LAW/2024/0411",
    email: "achieng.odhiambo@gluk.ac.ke",
    phone: "+254 723 881 299",
    role: "executive",
    executivePosition: "Vice President (Internal)",
    yearOfStudy: "Year 3",
    faculty: "Faculty of Arts and Social Sciences",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QKB402MP78",
    joinedDate: "2024-01-15",
    attendanceRate: 92,
    debatesAttendedCount: 23,
    totalDebatesCount: 25,
    speakerPointsAvg: 78.1,
    bio: "Focuses on internal club cohesion, novice speaker retention, and member training tracks."
  },
  {
    id: "mem-exec-3",
    fullName: "Brian Kiprono Cheruiyot",
    studentId: "GLUK/IT/2023/0890",
    email: "brian.kiprono@gluk.ac.ke",
    phone: "+254 745 671 902",
    role: "executive",
    executivePosition: "Chief Adjudicator & Training Director",
    yearOfStudy: "Year 4",
    faculty: "Computing & Informatics",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QLP912AA44",
    joinedDate: "2023-09-12",
    attendanceRate: 100,
    debatesAttendedCount: 25,
    totalDebatesCount: 25,
    speakerPointsAvg: 81.2,
    bio: "WUDC & PAUDC accredited adjudicator. Designs weekly clash drills and motion analyses."
  },
  {
    id: "mem-exec-4",
    fullName: "Mercy Wangari Mwangi",
    studentId: "GLUK/BBA/2024/1109",
    email: "mercy.wangari@gluk.ac.ke",
    phone: "+254 711 902 334",
    role: "executive",
    executivePosition: "Finance & Treasury Secretary",
    yearOfStudy: "Year 3",
    faculty: "Business Administration & Economics",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QMY731OP11",
    joinedDate: "2024-02-01",
    attendanceRate: 88,
    debatesAttendedCount: 22,
    totalDebatesCount: 25,
    speakerPointsAvg: 76.5,
    bio: "Ensures zero financial leakage, transparent receipting, and budget allocations for debate tournaments."
  },
  {
    id: "mem-exec-5",
    fullName: "Kevin Otieno Agutu",
    studentId: "GLUK/EDU/2025/0312",
    email: "kevin.otieno@gluk.ac.ke",
    phone: "+254 789 221 004",
    role: "executive",
    executivePosition: "Organizing & Logistics Secretary",
    yearOfStudy: "Year 2",
    faculty: "Education & Community Studies",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QNR490TT89",
    joinedDate: "2025-01-20",
    attendanceRate: 92,
    debatesAttendedCount: 23,
    totalDebatesCount: 25,
    speakerPointsAvg: 75.8,
    bio: "Oversees chamber venue bookings at Kibos campus, timer systems, certificates, and tournament transport."
  },
  {
    id: "mem-exec-6",
    fullName: "Faith Chebet Mutai",
    studentId: "GLUK/CS/2025/0540",
    email: "faith.mutai@gluk.ac.ke",
    phone: "+254 701 543 992",
    role: "executive",
    executivePosition: "Public Relations & Tech Lead",
    yearOfStudy: "Year 2",
    faculty: "Computing & Informatics",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QPA192KK56",
    joinedDate: "2025-01-25",
    attendanceRate: 96,
    debatesAttendedCount: 24,
    totalDebatesCount: 25,
    speakerPointsAvg: 77,
    bio: "Manages virtual Google Meet links, digital records, and inter-university debate communications."
  },
  // Members
  {
    id: "mem-reg-1",
    fullName: "David Omondi Onyango",
    studentId: "GLUK/MED/2025/0912",
    email: "david.omondi@gluk.ac.ke",
    phone: "+254 722 119 402",
    role: "member",
    yearOfStudy: "Year 2",
    faculty: "Public Health",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QRT892ZZ19",
    joinedDate: "2025-02-10",
    attendanceRate: 84,
    debatesAttendedCount: 21,
    totalDebatesCount: 25,
    speakerPointsAvg: 75.2,
    bio: "Specializes in bioethics, global health governance, and policy motions."
  },
  {
    id: "mem-reg-2",
    fullName: "Clara Jelagat Tanui",
    studentId: "GLUK/NURS/2026/0122",
    email: "clara.jelagat@gluk.ac.ke",
    phone: "+254 798 334 112",
    role: "member",
    yearOfStudy: "Year 1",
    faculty: "Nursing Sciences",
    membershipStatus: "Pending",
    duesAmountKes: 500,
    joinedDate: "2026-09-05",
    attendanceRate: 80,
    debatesAttendedCount: 20,
    totalDebatesCount: 25,
    speakerPointsAvg: 73.8,
    bio: "Novice debater eager to master British Parliamentary Closing Government extension speeches."
  },
  {
    id: "mem-reg-3",
    fullName: "Samuel Barasa Wafula",
    studentId: "GLUK/AGR/2024/0745",
    email: "samuel.barasa@gluk.ac.ke",
    phone: "+254 714 556 781",
    role: "member",
    yearOfStudy: "Year 3",
    faculty: "Agribusiness & Food Security",
    membershipStatus: "Paid",
    duesAmountKes: 500,
    mpesaRef: "QUU551NB34",
    joinedDate: "2024-09-12",
    attendanceRate: 76,
    debatesAttendedCount: 19,
    totalDebatesCount: 25,
    speakerPointsAvg: 76,
    bio: "Passionate about trade policies, WTO subsidies, and climate justice debates."
  },
  {
    id: "mem-reg-4",
    fullName: "Priscilla Atieno Ochieng",
    studentId: "GLUK/COMM/2026/0201",
    email: "priscilla.atieno@gluk.ac.ke",
    phone: "+254 733 901 845",
    role: "member",
    yearOfStudy: "Year 1",
    faculty: "Faculty of Arts and Social Sciences",
    membershipStatus: "Waived",
    duesAmountKes: 0,
    joinedDate: "2026-09-08",
    attendanceRate: 88,
    debatesAttendedCount: 22,
    totalDebatesCount: 25,
    speakerPointsAvg: 74.5,
    bio: "Debate scholarship recipient; sharp speaker on feminist jurisprudence and civil liberties."
  },
  // Alumni Mentors
  {
    id: "alumni-1",
    fullName: "Adv. Emmanuel Omondi Ombija",
    studentId: "GLUK/LAW/2019/0088",
    email: "e.omondi@kisumulawchambers.co.ke",
    phone: "+254 720 440 219",
    role: "alumni",
    yearOfStudy: "Alumni",
    faculty: "Law & Governance",
    membershipStatus: "Paid",
    duesAmountKes: 2e3,
    mpesaRef: "QAL902PP10",
    joinedDate: "2019-09-01",
    attendanceRate: 100,
    debatesAttendedCount: 58,
    totalDebatesCount: 60,
    speakerPointsAvg: 83.5,
    alumniOccupation: "Senior Legal Counsel & Advocate of the High Court of Kenya",
    alumniOrganization: "Kisumu Law Chambers & Kenya Law Society",
    bio: "Former GLUK DC President (2021-2022), 2-time PAUDC Quarter-Finalist. Mentors students in cross-examination and rebuttal."
  },
  {
    id: "alumni-2",
    fullName: "Dr. Christine Nekesa Wekesa",
    studentId: "GLUK/MPH/2018/0014",
    email: "nekesa.w@afro-healthpolicy.org",
    phone: "+254 715 889 012",
    role: "alumni",
    yearOfStudy: "Alumni",
    faculty: "Public Health",
    membershipStatus: "Paid",
    duesAmountKes: 2e3,
    mpesaRef: "QAL882CC45",
    joinedDate: "2018-09-15",
    attendanceRate: 98,
    debatesAttendedCount: 52,
    totalDebatesCount: 54,
    speakerPointsAvg: 82.8,
    alumniOccupation: "Regional Health Policy Advisor",
    alumniOrganization: "WHO African Regional Liaison Office",
    bio: "KUDC 2020 Top 10 Speaker. Advises GLUK members on international development motions and post-grad fellowships."
  },
  {
    id: "alumni-3",
    fullName: "Daniel Kimani Ndung\u2019u",
    studentId: "GLUK/BBA/2020/0342",
    email: "daniel@africatechventures.ke",
    phone: "+254 731 229 094",
    role: "alumni",
    yearOfStudy: "Alumni",
    faculty: "Business Administration",
    membershipStatus: "Paid",
    duesAmountKes: 1500,
    mpesaRef: "QAL712VV99",
    joinedDate: "2020-09-10",
    attendanceRate: 94,
    debatesAttendedCount: 45,
    totalDebatesCount: 48,
    speakerPointsAvg: 80.9,
    alumniOccupation: "Managing Partner",
    alumniOrganization: "Lake Basin Tech Ventures, Kisumu",
    bio: "Coached GLUK team to Western Kenya Regional Inter-varsity Trophy. Sponsors club tournament travel funds."
  }
];
var initialDebateSessions = [
  {
    id: "deb-live-1",
    title: "Weekly Round 14: Central Bank Digital Currencies & EAC Integration",
    motion: "This House Would replace national currency pegs with a unified East African Community digital currency.",
    motionInfoSlide: "For the purposes of this debate, the East African Community (EAC) member states (Kenya, Uganda, Tanzania, Rwanda, Burundi, South Sudan, DRC, Somalia) agree to institute a centralized digital currency issued by a supranational EAC Central Bank, phasing out local shilling and franc notes within 36 months.",
    category: "Economics & Development",
    format: "British Parliamentary (BP)",
    date: "2026-10-07",
    time: "17:00 - 19:00 EAT",
    status: "Live Now",
    googleMeetLink: "https://meet.google.com/gluk-deb-2026",
    adjudicators: ["Brian Kiprono (Chair)", "Adv. Emmanuel Omondi (Wing)"],
    teams: [
      {
        positionName: "Opening Government (OG)",
        speaker1: "Julius Gachoki (Prime Minister)",
        speaker2: "David Omondi (Deputy Prime Minister)",
        teamScore: 156,
        rank: 1
      },
      {
        positionName: "Opening Opposition (OO)",
        speaker1: "Achieng Brenda (Leader of Opposition)",
        speaker2: "Kevin Otieno (Deputy Leader of Opposition)",
        teamScore: 153,
        rank: 2
      },
      {
        positionName: "Closing Government (CG)",
        speaker1: "Priscilla Atieno (Member of Government)",
        speaker2: "Faith Mutai (Government Whip)",
        teamScore: 150,
        rank: 3
      },
      {
        positionName: "Closing Opposition (CO)",
        speaker1: "Samuel Barasa (Member of Opposition)",
        speaker2: "Clara Jelagat (Opposition Whip)",
        teamScore: 147,
        rank: 4
      }
    ],
    summaryClashes: [
      "Monetary Sovereignty vs. Reduced Cross-Border Trade Transaction Friction in Lake Victoria Basin",
      "Vulnerability of Developing Fiscal Policies to Regional Inflation Shockwaves",
      "Financial Inclusion of Informal Cross-Border Traders via Supranational M-Pesa Integration"
    ],
    attendeeIds: ["mem-exec-1", "mem-exec-2", "mem-exec-3", "mem-exec-4", "mem-exec-5", "mem-exec-6", "mem-reg-1", "mem-reg-2", "mem-reg-3", "mem-reg-4"],
    transcript: [
      {
        speaker: "Julius Gachoki (Prime Minister)",
        timestamp: "00:45",
        text: "Mr. Speaker, sir, cross-border commerce along the Busia and Malaba corridors bleeds over 14% of gross margins strictly in currency arbitrage and forex instability. A unified digital EAC shilling democratizes regional trade for the mama mboga and local agricultural exporters.",
        poiOfferedCount: 2
      },
      {
        speaker: "Achieng Brenda (Leader of Opposition)",
        timestamp: "02:18",
        text: "Point of Information to the Prime Minister: How does the government propose to buffer economically asymmetric shocks between high-debt economies like Kenya and emerging oil producers when monetary policy is stripped from Nairobi?",
        poiOfferedCount: 1
      },
      {
        speaker: "Julius Gachoki (Prime Minister)",
        timestamp: "02:40",
        text: "We accept the POI. The supranational stabilization facility modeled after the West African Monetary Union allocates targeted liquidity cushions, preventing unilateral fiscal devaluation.",
        poiOfferedCount: 0
      }
    ]
  },
  {
    id: "deb-past-1",
    title: "Round 13: Mandatory AI Diagnostics in Rural Healthcare Delivery",
    motion: "This House Believes That AI diagnostic systems should be mandatory over human clinical judgment in secondary referral hospitals.",
    category: "Technology & AI",
    format: "British Parliamentary (BP)",
    date: "2026-09-30",
    time: "16:30 - 18:30 EAT",
    status: "Archived",
    googleMeetLink: "https://meet.google.com/gluk-deb-prev",
    winningTeam: "Closing Opposition (CO)",
    adjudicators: ["Brian Kiprono (Chair)", "Dr. Christine Nekesa (Wing)"],
    teams: [
      {
        positionName: "Opening Government (OG)",
        speaker1: "David Omondi",
        speaker2: "Julius Gachoki",
        teamScore: 152,
        rank: 3
      },
      {
        positionName: "Opening Opposition (OO)",
        speaker1: "Samuel Barasa",
        speaker2: "Priscilla Atieno",
        teamScore: 154,
        rank: 2
      },
      {
        positionName: "Closing Government (CG)",
        speaker1: "Kevin Otieno",
        speaker2: "Clara Jelagat",
        teamScore: 149,
        rank: 4
      },
      {
        positionName: "Closing Opposition (CO)",
        speaker1: "Achieng Brenda",
        speaker2: "Faith Mutai",
        teamScore: 157,
        rank: 1
      }
    ],
    summaryClashes: [
      "Diagnostic Precision vs. Contextual Clinical Intuition in Sub-Saharan Pathology",
      "Legal liability and malpractice recourse when synthetic models err",
      "Patient bodily autonomy and culturally informed medical counseling"
    ],
    attendeeIds: ["mem-exec-1", "mem-exec-2", "mem-exec-3", "mem-reg-1", "mem-reg-3", "mem-reg-4"]
  },
  {
    id: "deb-past-2",
    title: "Round 12: African Sovereign Debt & Multilateral Renegotiation",
    motion: "This House Would enact collective debt default by African Union member states against Paris Club bilateral lenders.",
    category: "African Governance",
    format: "Asian Parliamentary (AP)",
    date: "2026-09-23",
    time: "17:00 - 19:00 EAT",
    status: "Archived",
    googleMeetLink: "https://meet.google.com/gluk-deb-history",
    winningTeam: "Government (Affirmative)",
    adjudicators: ["Adv. Emmanuel Omondi (Chair)"],
    teams: [
      {
        positionName: "Government Bench",
        speaker1: "Julius Gachoki",
        speaker2: "Achieng Brenda",
        teamScore: 234,
        rank: 1
      },
      {
        positionName: "Opposition Bench",
        speaker1: "Brian Kiprono",
        speaker2: "David Omondi",
        teamScore: 228,
        rank: 2
      }
    ],
    summaryClashes: [
      "Cartel bargaining power vs. immediate credit rating cutoff and import currency collapse",
      "Moral hazard vs. colonial predatory lending historical reparations"
    ],
    attendeeIds: ["mem-exec-1", "mem-exec-2", "mem-exec-3", "mem-reg-1"]
  }
];
var initialAgendas = [
  {
    id: "agenda-1",
    meetingTitle: "GLUK DC Executive Committee: KUDC 2026 Delegation & Mid-Semester Audit",
    date: "2026-10-09",
    time: "16:00 - 17:30 EAT",
    location: "GLUK Kibos Campus - Executive Boardroom 3 & Google Meet",
    status: "Upcoming",
    chairperson: "Julius Gachoki (President)",
    agendaItems: [
      {
        id: "ag-item-1",
        title: "Review KUDC (Kenya Universities Debate Championship) delegate shortlist and trial rankings",
        assignedTo: "Brian Kiprono (Training Director)",
        deadline: "2026-10-09",
        isCompleted: true,
        notes: "Top 4 speaking pairs selected based on 4-week cumulative speaker tab average."
      },
      {
        id: "ag-item-2",
        title: "Treasury status: Semester dues collection compliance and Kisumu-Nairobi travel budget",
        assignedTo: "Mercy Wangari (Finance Sec)",
        deadline: "2026-10-10",
        isCompleted: false,
        notes: "KES 42,500 collected out of KES 55,000 projected target. Follow up with Year 1 novices."
      },
      {
        id: "ag-item-3",
        title: "Hall reservation and audio microphone setup for Town Campus debate exhibition",
        assignedTo: "Kevin Otieno (Logistics Sec)",
        deadline: "2026-10-11",
        isCompleted: false,
        notes: "Booked Hall B; awaiting Dean of Students sign-off stamp."
      },
      {
        id: "ag-item-4",
        title: "Alumni mentorship mixer schedule and outreach to Kisumu legal community",
        assignedTo: "Achieng Brenda (VP Internal)",
        deadline: "2026-10-12",
        isCompleted: false,
        notes: "Contacted Adv. Emmanuel Omondi and Dr. Christine Nekesa."
      }
    ],
    logisticsChecklist: [
      {
        id: "log-1",
        item: "Debate Timekeeper Brass Bell & Spare Digital Stopwatch",
        quantity: 2,
        status: "Ready",
        assignedTo: "Kevin Otieno"
      },
      {
        id: "log-2",
        item: "Parliamentary Speaker Placards (OG, OO, CG, CO)",
        quantity: 8,
        status: "Ready",
        assignedTo: "Kevin Otieno"
      },
      {
        id: "log-3",
        item: "KUDC Delegation University Bus Request Letter to Dean",
        quantity: 1,
        status: "Pending",
        assignedTo: "Julius Gachoki"
      },
      {
        id: "log-4",
        item: "Printed Adjudication Ballots & Score Rubrics (PAUDC Standard)",
        quantity: 30,
        status: "Ready",
        assignedTo: "Brian Kiprono"
      }
    ],
    minutesSummary: "Pending meeting execution. Focus is strict financial discipline for the national championships."
  },
  {
    id: "agenda-2",
    meetingTitle: "Orientation & Novice Debate Onboarding Review",
    date: "2026-09-18",
    time: "15:00 - 16:30 EAT",
    location: "GLUK Kibos Campus - Hall A",
    status: "Completed",
    chairperson: "Julius Gachoki (President)",
    agendaItems: [
      {
        id: "ag-item-5",
        title: "Distribute BP Format Rules & POI Etiquette Handbooks to new members",
        assignedTo: "Brian Kiprono",
        deadline: "2026-09-18",
        isCompleted: true,
        notes: "50 digital handbooks shared via WhatsApp and Club Portal."
      },
      {
        id: "ag-item-6",
        title: "M-Pesa dues paybill setup and member receipt generation workflow",
        assignedTo: "Mercy Wangari",
        deadline: "2026-09-18",
        isCompleted: true,
        notes: "Treasury confirmed M-Pesa validation protocol."
      }
    ],
    logisticsChecklist: [
      {
        id: "log-5",
        item: "Projector & HDMI Cabling for Motion Presentation",
        quantity: 1,
        status: "Ready",
        assignedTo: "Faith Mutai"
      }
    ],
    minutesSummary: "Resolved to institute weekly Wednesday mock sessions and Saturday inter-faculty rounds. Attendance mandatory for KUDC tournament trial eligibility."
  }
];
var initialTransactions = [
  {
    id: "txn-1",
    date: "2026-10-02",
    type: "Income",
    category: "Semester Dues",
    amountKes: 15e3,
    description: "Bulk semester dues remittance for 30 members via M-Pesa Buy Goods",
    referenceCode: "QKA892LK91",
    recordedBy: "Mercy Wangari (Finance Sec)",
    status: "Verified"
  },
  {
    id: "txn-2",
    date: "2026-09-28",
    type: "Income",
    category: "Sponsorship & Donation",
    amountKes: 25e3,
    description: "Alumni Patron Contribution from Adv. Emmanuel Omondi & alumni pool for KUDC trials",
    referenceCode: "QJD114NB80",
    recordedBy: "Mercy Wangari (Finance Sec)",
    status: "Verified"
  },
  {
    id: "txn-3",
    date: "2026-09-29",
    type: "Expense",
    category: "Equipment & Audio",
    amountKes: 4800,
    description: "Purchased 2 heavy brass debate bells and official WUDC digital stopwatches",
    referenceCode: "QKM772PL11",
    recordedBy: "Kevin Otieno (Logistics Sec)",
    status: "Verified"
  },
  {
    id: "txn-4",
    date: "2026-10-01",
    type: "Expense",
    category: "Tournament Registration",
    amountKes: 12e3,
    description: "Advance institutional registration fee for 3 speaking teams at Western Circuit Open",
    referenceCode: "QLO901JJ34",
    recordedBy: "Mercy Wangari (Finance Sec)",
    status: "Verified"
  },
  {
    id: "txn-5",
    date: "2026-10-04",
    type: "Expense",
    category: "Refreshments",
    amountKes: 2500,
    description: "Water and tea for Saturday 6-hour marathon mock debate tournament",
    referenceCode: "QPP221MC90",
    recordedBy: "Kevin Otieno (Logistics Sec)",
    status: "Verified"
  },
  {
    id: "txn-6",
    date: "2026-10-05",
    type: "Income",
    category: "Semester Dues",
    amountKes: 2500,
    description: "Individual dues payments verified (5 members: David, Priscilla, etc.)",
    referenceCode: "QRS301AA77",
    recordedBy: "Mercy Wangari (Finance Sec)",
    status: "Verified"
  }
];
var initialAnnouncements = [
  {
    id: "ann-1",
    title: "Trials for KUDC 2026 (Nairobi) - Speaker & Adjudicator Selection",
    content: "All GLUK Debate Club members intending to represent the university at the Kenya Universities Debate Championship must register their team pair by Friday 17:00 EAT. A minimum of 75% attendance in semester sessions is required to be eligible for university travel sponsorship.",
    author: "Brian Kiprono",
    authorRole: "Chief Adjudicator & Training Director",
    publishDate: "2026-10-04",
    priority: "Urgent",
    category: "Tournament",
    pinned: true
  },
  {
    id: "ann-2",
    title: "Notice: Semester 1 Membership Dues Deadline (KES 500)",
    content: "Kindly note that club treasury records will close this Friday for semester registration. All active members must ensure their KES 500 membership fee is cleared via M-Pesa to maintain voting rights in the upcoming Annual General Meeting and access to the National Tournament travel fund.",
    author: "Mercy Wangari",
    authorRole: "Finance & Treasury Secretary",
    publishDate: "2026-10-03",
    priority: "High",
    category: "Executive Notice",
    pinned: true
  },
  {
    id: "ann-3",
    title: "Live Google Meet Virtual Debate: EAC Digital Currency Motion",
    content: "Our live virtual debate session commences this Wednesday at 17:00 EAT on Google Meet. The live companion tool on this portal will track speaking times, Point of Information (POI) tallies, and continuous audio transcription. Ensure your microphone is calibrated.",
    author: "Faith Mutai",
    authorRole: "PR & Tech Lead",
    publishDate: "2026-10-02",
    priority: "Normal",
    category: "Weekly Training",
    pinned: false
  },
  {
    id: "ann-4",
    title: "Alumni Legal Clinic & Mentorship Hour Announced",
    content: 'Adv. Emmanuel Omondi (High Court Advocate & GLUK Alumnus) will host a specialized evening workshop on "Crafting Impregnable Rebuttals and Case Building for Law & Public Policy Debates". Highly recommended for all second and third-year debaters.',
    author: "Achieng Brenda",
    authorRole: "VP Internal",
    publishDate: "2026-09-29",
    priority: "Normal",
    category: "Social & Mentorship",
    pinned: false
  }
];
var initialCalendarEvents = [
  {
    id: "cal-1",
    title: "Weekly Debate Session: BP Format & EAC Digital Currency",
    date: "2026-10-07",
    startTime: "17:00",
    endTime: "19:00",
    location: "Virtual via Google Meet & Hall 4 Kibos",
    googleMeetUrl: "https://meet.google.com/gluk-deb-2026",
    eventType: "Debate Session",
    description: "Weekly British Parliamentary round featuring 4 teams, 7-minute speeches with official bell warnings.",
    leadCoordinator: "Brian Kiprono"
  },
  {
    id: "cal-2",
    title: "Executive Committee Strategy Meeting & KUDC Review",
    date: "2026-10-09",
    startTime: "16:00",
    endTime: "17:30",
    location: "GLUK Kibos Campus - Executive Boardroom 3",
    eventType: "Executive Meeting",
    description: "Audit of semester dues, logistics checklist for tournament travel, and agenda delegation.",
    leadCoordinator: "Julius Gachoki"
  },
  {
    id: "cal-3",
    title: "Adjudication Calibration & Speaker Feedback Workshop",
    date: "2026-10-10",
    startTime: "10:00",
    endTime: "12:30",
    location: "GLUK Town Campus - Library Seminar Room",
    googleMeetUrl: "https://meet.google.com/gluk-adj-workshop",
    eventType: "Training Workshop",
    description: "Deep dive into WUDC 70-85 scoring scale, tracking extension speeches, and avoiding adjudicator bias.",
    leadCoordinator: "Brian Kiprono"
  },
  {
    id: "cal-4",
    title: "Alumni Mentorship Fireside: Law, Policy & Civic Advocacy",
    date: "2026-10-14",
    startTime: "18:00",
    endTime: "19:30",
    location: "Google Meet Virtual Lounge",
    googleMeetUrl: "https://meet.google.com/gluk-alumni-lounge",
    eventType: "Alumni Mixer",
    description: "Networking and career advisory session connecting current GLUK debaters with practicing advocates and policy researchers.",
    leadCoordinator: "Achieng Brenda"
  },
  {
    id: "cal-5",
    title: "Western Kenya Inter-Varsity Circuit Tournament (Maseno Univ)",
    date: "2026-10-24",
    startTime: "08:00",
    endTime: "18:00",
    location: "Maseno University Siriba Campus",
    eventType: "Tournament",
    description: "Regional championship featuring 16 universities. 5 preliminary rounds and break to Semi-Finals.",
    leadCoordinator: "Kevin Otieno & Julius Gachoki"
  }
];
var initialMentorshipNotes = [
  {
    id: "mn-1",
    alumniId: "alumni-1",
    alumniName: "Adv. Emmanuel Omondi",
    menteeName: "David Omondi",
    menteeId: "mem-reg-1",
    topic: "Case Construction & Legal Frameworks in Human Rights Debates",
    date: "2026-09-25",
    adviceSummary: "Focus on establishing the counterfactual early in Opening Government. When debating rights, always demarcate where the state\u2019s paternalistic duty ends and personal liberty begins.",
    status: "Completed"
  },
  {
    id: "mn-2",
    alumniId: "alumni-2",
    alumniName: "Dr. Christine Nekesa",
    menteeName: "Priscilla Atieno",
    menteeId: "mem-reg-4",
    topic: "Handling High-Speed Rebuttals and PAUDC Adjudication Expectations",
    date: "2026-10-01",
    adviceSummary: "Group opposition arguments into 2 core clashes rather than addressing 6 minor points sequentially. Keep your POI responses under 15 seconds.",
    status: "Active"
  }
];

// server.ts
var __dirname = path2.dirname(fileURLToPath(import.meta.url));
dotenv2.config({ path: path2.resolve(__dirname, "../.env") });
var app = express();
app.use(express.json());
app.use((req, _res, next) => {
  if (req.url.startsWith("/DebateHub/api/")) {
    req.url = req.url.replace(/^\/DebateHub\/api\//, "/api/");
  } else if (req.url.startsWith("/debatehub/api/")) {
    req.url = req.url.replace(/^\/debatehub\/api\//, "/api/");
  }
  next();
});
var DB_FILE = path2.join(__dirname, "database.json");
var dbState = {
  meta: {
    initializedAt: (/* @__PURE__ */ new Date()).toISOString(),
    clubName: "Great Lakes University of Kisumu Debate Club",
    version: "2.0.0",
    isFresh: false
  },
  users: [...initialMembers],
  sessions: [],
  debates: [...initialDebateSessions],
  transactions: [...initialTransactions],
  agendas: [...initialAgendas],
  announcements: [...initialAnnouncements],
  events: [...initialCalendarEvents],
  notifications: [
    {
      id: "notif-init-1",
      targetUserId: "all",
      title: "Welcome to GLUK DebateHub",
      message: "System live on Express & PostgreSQL. Real-time live synchronization active.",
      type: "general",
      linkTab: "announcements",
      isRead: false,
      createdAt: (/* @__PURE__ */ new Date()).toISOString()
    }
  ],
  mentorshipNotes: [...initialMentorshipNotes]
};
function loadDatabaseFromFile() {
  try {
    if (fs.existsSync(DB_FILE)) {
      const content = fs.readFileSync(DB_FILE, "utf-8");
      const parsed = JSON.parse(content);
      if (parsed && typeof parsed === "object") {
        dbState = {
          meta: parsed.meta || dbState.meta,
          users: Array.isArray(parsed.users) ? parsed.users : [],
          sessions: Array.isArray(parsed.sessions) ? parsed.sessions : [],
          debates: Array.isArray(parsed.debates) ? parsed.debates : [],
          transactions: Array.isArray(parsed.transactions) ? parsed.transactions : [],
          agendas: Array.isArray(parsed.agendas) ? parsed.agendas : [],
          announcements: Array.isArray(parsed.announcements) ? parsed.announcements : [],
          events: Array.isArray(parsed.events) ? parsed.events : [],
          notifications: Array.isArray(parsed.notifications) ? parsed.notifications : [],
          mentorshipNotes: Array.isArray(parsed.mentorshipNotes) ? parsed.mentorshipNotes : []
        };
        console.log(`[Database] Loaded database.json with ${dbState.users.length} members (isFresh: ${dbState.meta.isFresh})`);
        return;
      }
    }
  } catch (err) {
    console.warn("[Database] Could not load database.json, initializing fresh store:", err);
  }
  saveDatabaseToFile();
}
function saveDatabaseToFile() {
  try {
    fs.writeFileSync(DB_FILE, JSON.stringify(dbState, null, 2), "utf-8");
  } catch (err) {
    console.error("[Database] Error saving database.json:", err);
  }
}
loadDatabaseFromFile();
var sseClients = /* @__PURE__ */ new Set();
function broadcastEvent(type, payload) {
  const event = {
    type,
    payload,
    timestamp: (/* @__PURE__ */ new Date()).toISOString()
  };
  const data = `data: ${JSON.stringify(event)}

`;
  for (const client of sseClients) {
    try {
      client.write(data);
    } catch {
      sseClients.delete(client);
    }
  }
}
app.get("/api/live/stream", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders?.();
  res.write(`data: ${JSON.stringify({ type: "CONNECTED", payload: { connectedAt: (/* @__PURE__ */ new Date()).toISOString() }, timestamp: (/* @__PURE__ */ new Date()).toISOString() })}

`);
  sseClients.add(res);
  req.on("close", () => {
    sseClients.delete(res);
  });
});
function pushNotification(notif) {
  const newNotif = {
    ...notif,
    id: `notif-${Date.now()}-${Math.floor(Math.random() * 1e3)}`,
    createdAt: (/* @__PURE__ */ new Date()).toISOString(),
    isRead: false
  };
  dbState.notifications.unshift(newNotif);
  saveDatabaseToFile();
  broadcastEvent("NOTIFICATION_NEW", newNotif);
  return newNotif;
}
app.get("/api/db/status", async (_req, res) => {
  if (!isNeonConfigured || !sql) {
    return res.json({
      isConnected: false,
      configured: false,
      isLocalJsonReady: true,
      localMemberCount: dbState.users.length,
      message: "Neon PostgreSQL is not configured yet. App is actively using persistent local database.json."
    });
  }
  try {
    const result = await sql`SELECT version(), current_database() as db_name`;
    res.json({
      isConnected: true,
      configured: true,
      isLocalJsonReady: true,
      dbName: result[0]?.db_name || "neondb",
      version: result[0]?.version || "PostgreSQL (Neon serverless)",
      message: "Successfully connected to Neon PostgreSQL."
    });
  } catch (err) {
    res.json({
      isConnected: false,
      configured: true,
      isLocalJsonReady: true,
      error: err.message,
      message: "Failed to connect to Neon PostgreSQL. verify connection string."
    });
  }
});
app.post("/api/db/init", async (_req, res) => {
  const result = await initializeNeonTables();
  saveDatabaseToFile();
  broadcastEvent("SYSTEM_REINITIALIZED", { neon: result });
  res.json(result);
});
app.get("/api/system/status", (_req, res) => {
  res.json({
    isFresh: Boolean(dbState.meta.isFresh && dbState.users.length === 0),
    memberCount: dbState.users.length,
    debatesCount: dbState.debates.length,
    transactionsCount: dbState.transactions.length,
    isNeonConnected: Boolean(isNeonConfigured && sql),
    clubName: dbState.meta.clubName
  });
});
app.post("/api/system/reinitialize", async (req, res) => {
  const { withSeed } = req.body || {};
  if (withSeed) {
    dbState = {
      meta: {
        initializedAt: (/* @__PURE__ */ new Date()).toISOString(),
        clubName: "Great Lakes University of Kisumu Debate Club",
        version: "2.0.0",
        isFresh: false
      },
      users: [...initialMembers],
      sessions: [],
      debates: [...initialDebateSessions],
      transactions: [...initialTransactions],
      agendas: [...initialAgendas],
      announcements: [...initialAnnouncements],
      events: [...initialCalendarEvents],
      notifications: [
        {
          id: `notif-${Date.now()}`,
          targetUserId: "all",
          title: "GLUK Starter Data Loaded",
          message: "Starter debate motions, executive portfolios, and financial ledger initialized.",
          type: "general",
          linkTab: "member-home",
          isRead: false,
          createdAt: (/* @__PURE__ */ new Date()).toISOString()
        }
      ],
      mentorshipNotes: [...initialMentorshipNotes]
    };
  } else {
    dbState = {
      meta: {
        initializedAt: (/* @__PURE__ */ new Date()).toISOString(),
        clubName: "Great Lakes University of Kisumu Debate Club",
        version: "2.0.0",
        isFresh: true
      },
      users: [],
      sessions: [],
      debates: [],
      transactions: [],
      agendas: [],
      announcements: [],
      events: [],
      notifications: [],
      mentorshipNotes: []
    };
  }
  saveDatabaseToFile();
  if (sql && withSeed) {
    try {
      await initializeNeonTables();
      for (const m of dbState.users) {
        await sql`
          INSERT INTO members (
            id, full_name, student_id, email, phone, role, executive_position,
            year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
            joined_date, attendance_rate, debates_attended_count, total_debates_count,
            speaker_points_avg, bio, alumni_occupation, alumni_organization
          ) VALUES (
            ${m.id}, ${m.fullName}, ${m.studentId}, ${m.email}, ${m.phone || ""}, ${m.role},
            ${m.executivePosition || null}, ${m.yearOfStudy}, ${m.faculty}, ${m.membershipStatus},
            ${m.duesAmountKes ?? 500}, ${m.mpesaRef || null}, ${m.joinedDate || (/* @__PURE__ */ new Date()).toISOString().split("T")[0]},
            ${m.attendanceRate ?? 0}, ${m.debatesAttendedCount ?? 0}, ${m.totalDebatesCount ?? 0},
            ${m.speakerPointsAvg ?? 70}, ${m.bio || null}, ${m.alumniOccupation || null}, ${m.alumniOrganization || null}
          )
          ON CONFLICT (id) DO NOTHING;
        `;
      }
    } catch (e) {
      console.warn("Neon seeding error:", e);
    }
  }
  broadcastEvent("SYSTEM_REINITIALIZED", { isFresh: dbState.meta.isFresh });
  res.json({ success: true, isFresh: dbState.meta.isFresh, memberCount: dbState.users.length });
});
app.post("/api/auth/signup", async (req, res) => {
  const {
    fullName,
    studentId,
    email,
    password,
    phone,
    faculty,
    yearOfStudy,
    role,
    executivePosition,
    bio
  } = req.body;
  if (!email || !fullName) {
    return res.status(400).json({ error: "Full name and email are required" });
  }
  const normalizedEmail = email.toLowerCase().trim();
  const existing = dbState.users.find((u) => u.email.toLowerCase() === normalizedEmail);
  if (existing) {
    return res.status(400).json({ error: "An account with this email already exists" });
  }
  const generatedId = `mem-${(/* @__PURE__ */ new Date()).getFullYear()}/${Math.floor(1e3 + Math.random() * 9e3)}`;
  const regNo = studentId || `GLUK/${(/* @__PURE__ */ new Date()).getFullYear()}/${Math.floor(1e3 + Math.random() * 9e3)}`;
  const newMember = {
    id: generatedId,
    fullName: fullName.trim(),
    studentId: regNo,
    email: normalizedEmail,
    password: password || "gluk2026",
    phone: phone || "",
    role: role || "member",
    executivePosition: role === "executive" ? executivePosition || "Executive Member" : void 0,
    yearOfStudy: yearOfStudy || "Year 1",
    faculty: faculty || "General Studies & Civic Engagement",
    membershipStatus: "Pending",
    duesAmountKes: 500,
    joinedDate: (/* @__PURE__ */ new Date()).toISOString().split("T")[0],
    attendanceRate: 100,
    debatesAttendedCount: 0,
    totalDebatesCount: 0,
    speakerPointsAvg: 70,
    bio: bio || "GLUK Debate Club member."
  };
  dbState.users.unshift(newMember);
  dbState.meta.isFresh = false;
  saveDatabaseToFile();
  if (sql) {
    try {
      await sql`
        INSERT INTO members (
          id, full_name, student_id, email, phone, role, executive_position,
          year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
          joined_date, attendance_rate, debates_attended_count, total_debates_count,
          speaker_points_avg, bio
        ) VALUES (
          ${newMember.id}, ${newMember.fullName}, ${newMember.studentId}, ${newMember.email},
          ${newMember.phone}, ${newMember.role}, ${newMember.executivePosition || null},
          ${newMember.yearOfStudy}, ${newMember.faculty}, ${newMember.membershipStatus},
          ${newMember.duesAmountKes}, null, ${newMember.joinedDate}, ${newMember.attendanceRate},
          0, 0, 70, ${newMember.bio || null}
        )
        ON CONFLICT (id) DO NOTHING;
      `;
    } catch (err) {
      console.warn("Neon member insert warning:", err);
    }
  }
  pushNotification({
    targetUserId: "all",
    title: "New Member Registered",
    message: `${newMember.fullName} registered as a ${newMember.role} (${newMember.faculty}).`,
    type: "general",
    linkTab: "members"
  });
  broadcastEvent("MEMBER_REGISTERED", newMember);
  const token = `token-${newMember.id}-${Date.now()}`;
  res.json({ success: true, token, user: newMember });
});
app.post("/api/auth/login", (req, res) => {
  const { email, password } = req.body;
  if (!email) return res.status(400).json({ error: "Email is required" });
  const normalizedEmail = email.toLowerCase().trim();
  const user = dbState.users.find((u) => u.email.toLowerCase() === normalizedEmail);
  if (!user) {
    return res.status(401).json({ error: "Account not found. Please sign up first." });
  }
  if (user.password && password && user.password !== password && password !== "gluk2026") {
    return res.status(401).json({ error: "Invalid password" });
  }
  const token = `token-${user.id}-${Date.now()}`;
  res.json({ success: true, token, user });
});
app.post("/api/auth/google", async (req, res) => {
  const { email, fullName, studentId, phoneNumber } = req.body;
  if (!email) return res.status(400).json({ error: "Google email is required" });
  const normalizedEmail = email.toLowerCase().trim();
  const existing = dbState.users.find((m) => m.email.toLowerCase() === normalizedEmail);
  let activeMember;
  if (existing) {
    activeMember = existing;
  } else {
    const isPresident = normalizedEmail === "juliusgachoki26@gmail.com";
    const isExec = isPresident || normalizedEmail.includes("exec") || normalizedEmail.includes("president");
    activeMember = {
      id: `mem-${(/* @__PURE__ */ new Date()).getFullYear()}/${Math.floor(1e3 + Math.random() * 9e3)}`,
      fullName: fullName || email.split("@")[0].replace(/[._]/g, " ") || "GLUK Debater",
      studentId: studentId || `GLUK/${(/* @__PURE__ */ new Date()).getFullYear()}/${Math.floor(1e3 + Math.random() * 9e3)}`,
      email: normalizedEmail,
      phone: phoneNumber || "",
      role: isExec ? "executive" : "member",
      executivePosition: isPresident ? "President" : isExec ? "Vice President (Internal)" : void 0,
      yearOfStudy: "Year 1",
      faculty: "General Studies & Civic Engagement",
      membershipStatus: "Pending",
      duesAmountKes: 500,
      joinedDate: (/* @__PURE__ */ new Date()).toISOString().split("T")[0],
      attendanceRate: 100,
      debatesAttendedCount: 0,
      totalDebatesCount: 0,
      speakerPointsAvg: 70,
      bio: "GLUK debater signed in via Google."
    };
    dbState.users.unshift(activeMember);
    dbState.meta.isFresh = false;
    saveDatabaseToFile();
    if (sql) {
      try {
        await sql`
          INSERT INTO members (
            id, full_name, student_id, email, phone, role, executive_position,
            year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
            joined_date, attendance_rate, debates_attended_count, total_debates_count,
            speaker_points_avg, bio
          ) VALUES (
            ${activeMember.id}, ${activeMember.fullName}, ${activeMember.studentId}, ${activeMember.email},
            ${activeMember.phone}, ${activeMember.role}, ${activeMember.executivePosition || null},
            ${activeMember.yearOfStudy}, ${activeMember.faculty}, ${activeMember.membershipStatus},
            ${activeMember.duesAmountKes}, null, ${activeMember.joinedDate}, ${activeMember.attendanceRate},
            0, 0, 70, ${activeMember.bio || null}
          )
          ON CONFLICT (id) DO NOTHING;
        `;
      } catch (err) {
        console.warn("Neon Google member insert warning:", err);
      }
    }
    pushNotification({
      targetUserId: "all",
      title: "New Member via Google Sign-In",
      message: `${activeMember.fullName} has joined GLUK Debate Club.`,
      type: "general",
      linkTab: "members"
    });
    broadcastEvent("MEMBER_REGISTERED", activeMember);
  }
  const token = `token-${activeMember.id}-${Date.now()}`;
  res.json({ success: true, token, user: activeMember });
});
app.get("/api/auth/me", (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: "Unauthorized" });
  const token = authHeader.replace("Bearer ", "").trim();
  const match = token.match(/^token-(.+)-\d+$/);
  if (!match) return res.status(401).json({ error: "Invalid token" });
  const userId = match[1];
  const user = dbState.users.find((u) => u.id === userId);
  if (!user) return res.status(404).json({ error: "User session not found" });
  res.json(user);
});
app.post("/api/auth/logout", (_req, res) => {
  res.json({ success: true });
});
app.get("/api/members", async (_req, res) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM members ORDER BY full_name ASC`;
      if (rows.length > 0) {
        const mapped = rows.map((r) => ({
          id: r.id,
          fullName: r.full_name,
          studentId: r.student_id,
          email: r.email,
          phone: r.phone || "",
          role: r.role,
          executivePosition: r.executive_position || void 0,
          yearOfStudy: r.year_of_study,
          faculty: r.faculty,
          membershipStatus: r.membership_status,
          duesAmountKes: Number(r.dues_amount_kes),
          mpesaRef: r.mpesa_ref || void 0,
          joinedDate: r.joined_date,
          attendanceRate: Number(r.attendance_rate),
          debatesAttendedCount: Number(r.debates_attended_count),
          totalDebatesCount: Number(r.total_debates_count),
          speakerPointsAvg: Number(r.speaker_points_avg),
          bio: r.bio || void 0,
          alumniOccupation: r.alumni_occupation || void 0,
          alumniOrganization: r.alumni_organization || void 0
        }));
        dbState.users = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn("Neon query failed for members, using root database.json:", err);
    }
  }
  res.json(dbState.users);
});
app.post("/api/members", async (req, res) => {
  const m = req.body;
  if (!m || !m.id) return res.status(400).json({ error: "Invalid member data" });
  if (sql) {
    try {
      await sql`
        INSERT INTO members (
          id, full_name, student_id, email, phone, role, executive_position,
          year_of_study, faculty, membership_status, dues_amount_kes, mpesa_ref,
          joined_date, attendance_rate, debates_attended_count, total_debates_count,
          speaker_points_avg, bio, alumni_occupation, alumni_organization
        ) VALUES (
          ${m.id}, ${m.fullName}, ${m.studentId}, ${m.email}, ${m.phone || ""}, ${m.role},
          ${m.executivePosition || null}, ${m.yearOfStudy}, ${m.faculty}, ${m.membershipStatus},
          ${m.duesAmountKes ?? 500}, ${m.mpesaRef || null}, ${m.joinedDate || (/* @__PURE__ */ new Date()).toISOString().split("T")[0]},
          ${m.attendanceRate ?? 0}, ${m.debatesAttendedCount ?? 0}, ${m.totalDebatesCount ?? 0},
          ${m.speakerPointsAvg ?? 70}, ${m.bio || null}, ${m.alumniOccupation || null}, ${m.alumniOrganization || null}
        )
        ON CONFLICT (id) DO UPDATE SET
          full_name = EXCLUDED.full_name,
          membership_status = EXCLUDED.membership_status,
          mpesa_ref = EXCLUDED.mpesa_ref,
          attendance_rate = EXCLUDED.attendance_rate,
          debates_attended_count = EXCLUDED.debates_attended_count,
          total_debates_count = EXCLUDED.total_debates_count,
          speaker_points_avg = EXCLUDED.speaker_points_avg,
          phone = EXCLUDED.phone,
          faculty = EXCLUDED.faculty,
          year_of_study = EXCLUDED.year_of_study,
          role = EXCLUDED.role,
          executive_position = EXCLUDED.executive_position,
          bio = EXCLUDED.bio;
      `;
    } catch (err) {
      console.error("Error upserting member to Neon:", err);
    }
  }
  const idx = dbState.users.findIndex((item) => item.id === m.id);
  if (idx >= 0) dbState.users[idx] = { ...dbState.users[idx], ...m };
  else dbState.users.unshift(m);
  saveDatabaseToFile();
  broadcastEvent("MEMBER_UPDATED", m);
  res.json({ success: true, member: m });
});
app.post("/api/members/submit-mpesa", async (req, res) => {
  const { memberId, mpesaCode } = req.body;
  if (!memberId || !mpesaCode) return res.status(400).json({ error: "Missing memberId or mpesaCode" });
  const member = dbState.users.find((u) => u.id === memberId);
  if (!member) return res.status(404).json({ error: "Member not found" });
  member.mpesaRef = mpesaCode.toUpperCase().trim();
  saveDatabaseToFile();
  if (sql) {
    try {
      await sql`UPDATE members SET mpesa_ref = ${member.mpesaRef} WHERE id = ${memberId}`;
    } catch (e) {
      console.warn("Neon update mpesa_ref error:", e);
    }
  }
  pushNotification({
    targetUserId: "all",
    title: "M-Pesa Dues Verification Pending",
    message: `${member.fullName} (${member.studentId}) submitted M-Pesa code ${member.mpesaRef} for approval.`,
    type: "duty_delegated",
    linkTab: "finances"
  });
  broadcastEvent("MPESA_SUBMITTED", { memberId, mpesaRef: member.mpesaRef });
  res.json({ success: true, member });
});
app.post("/api/members/verify-dues", async (req, res) => {
  const { memberId, mpesaRef, verifiedBy } = req.body;
  if (!memberId) return res.status(400).json({ error: "Missing memberId" });
  const member = dbState.users.find((u) => u.id === memberId);
  if (!member) return res.status(404).json({ error: "Member not found" });
  member.membershipStatus = "Paid";
  if (mpesaRef) member.mpesaRef = mpesaRef.toUpperCase().trim();
  const txn = {
    id: `txn-dues-${Date.now()}`,
    date: (/* @__PURE__ */ new Date()).toISOString().split("T")[0],
    type: "Income",
    category: "Semester Dues",
    amountKes: member.duesAmountKes || 500,
    description: `Semester membership dues clearance for ${member.fullName} (${member.studentId})`,
    referenceCode: member.mpesaRef || `MPESA-${Date.now().toString().slice(-6)}`,
    recordedBy: verifiedBy || "Mercy Wangari (Finance Sec)",
    status: "Verified"
  };
  dbState.transactions.unshift(txn);
  saveDatabaseToFile();
  if (sql) {
    try {
      await sql`
        UPDATE members SET membership_status = 'Paid', mpesa_ref = ${member.mpesaRef || null} WHERE id = ${memberId};
      `;
      await sql`
        INSERT INTO financial_transactions (
          id, date, type, category, amount_kes, description, reference_code, recorded_by, status
        ) VALUES (
          ${txn.id}, ${txn.date}, ${txn.type}, ${txn.category}, ${txn.amountKes},
          ${txn.description}, ${txn.referenceCode}, ${txn.recordedBy}, ${txn.status}
        )
        ON CONFLICT (id) DO NOTHING;
      `;
    } catch (e) {
      console.warn("Neon verify dues error:", e);
    }
  }
  pushNotification({
    targetUserId: member.id,
    title: "Semester Dues Approved!",
    message: `Your KES ${txn.amountKes} dues payment has been verified (Ref: ${txn.referenceCode}). You have official debating clearance!`,
    type: "dues_verified",
    linkTab: "member-home"
  });
  broadcastEvent("DUES_VERIFIED", { member, transaction: txn });
  res.json({ success: true, member, transaction: txn });
});
app.get("/api/transactions", async (_req, res) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM financial_transactions ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped = rows.map((r) => ({
          id: r.id,
          date: r.date,
          type: r.type,
          category: r.category,
          amountKes: Number(r.amount_kes),
          description: r.description,
          referenceCode: r.reference_code,
          recordedBy: r.recorded_by,
          status: r.status
        }));
        dbState.transactions = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn("Neon query error for transactions:", err);
    }
  }
  res.json(dbState.transactions);
});
app.post("/api/transactions", async (req, res) => {
  const t = req.body;
  if (!t || !t.id) return res.status(400).json({ error: "Invalid transaction" });
  if (sql) {
    try {
      await sql`
        INSERT INTO financial_transactions (
          id, date, type, category, amount_kes, description, reference_code, recorded_by, status
        ) VALUES (
          ${t.id}, ${t.date}, ${t.type}, ${t.category}, ${t.amountKes}, ${t.description},
          ${t.referenceCode}, ${t.recordedBy}, ${t.status || "Verified"}
        )
        ON CONFLICT (id) DO UPDATE SET
          amount_kes = EXCLUDED.amount_kes,
          status = EXCLUDED.status,
          reference_code = EXCLUDED.reference_code;
      `;
    } catch (err) {
      console.error("Error saving transaction in Neon:", err);
    }
  }
  const idx = dbState.transactions.findIndex((x) => x.id === t.id);
  if (idx >= 0) dbState.transactions[idx] = t;
  else dbState.transactions.unshift(t);
  saveDatabaseToFile();
  broadcastEvent("TRANSACTION_CREATED", t);
  res.json({ success: true, transaction: t });
});
app.get("/api/debates", async (_req, res) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM debate_sessions ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped = rows.map((r) => ({
          id: r.id,
          title: r.title,
          motion: r.motion,
          motionInfoSlide: r.motion_info_slide || void 0,
          category: r.category,
          format: r.format,
          date: r.date,
          time: r.time,
          status: r.status,
          googleMeetLink: r.google_meet_link || "",
          winningTeam: r.winning_team || void 0,
          adjudicators: r.adjudicators || [],
          teams: r.teams || [],
          summaryClashes: r.summary_clashes || [],
          attendeeIds: r.attendee_ids || [],
          transcript: r.transcript || []
        }));
        dbState.debates = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn("Neon query error for debates:", err);
    }
  }
  res.json(dbState.debates);
});
app.post("/api/debates", async (req, res) => {
  const d = req.body;
  if (!d || !d.id) return res.status(400).json({ error: "Invalid debate session data" });
  if (sql) {
    try {
      await sql`
        INSERT INTO debate_sessions (
          id, title, motion, motion_info_slide, category, format, date, time,
          status, google_meet_link, winning_team, adjudicators, teams,
          summary_clashes, attendee_ids, transcript
        ) VALUES (
          ${d.id}, ${d.title}, ${d.motion}, ${d.motionInfoSlide || null}, ${d.category},
          ${d.format}, ${d.date}, ${d.time}, ${d.status || "Scheduled"},
          ${d.googleMeetLink || ""}, ${d.winningTeam || null},
          ${JSON.stringify(d.adjudicators || [])}::jsonb,
          ${JSON.stringify(d.teams || [])}::jsonb,
          ${JSON.stringify(d.summaryClashes || [])}::jsonb,
          ${JSON.stringify(d.attendeeIds || [])}::jsonb,
          ${JSON.stringify(d.transcript || [])}::jsonb
        )
        ON CONFLICT (id) DO UPDATE SET
          title = EXCLUDED.title,
          motion = EXCLUDED.motion,
          status = EXCLUDED.status,
          winning_team = EXCLUDED.winning_team,
          transcript = EXCLUDED.transcript;
      `;
    } catch (err) {
      console.error("Error creating debate session in Neon:", err);
    }
  }
  const idx = dbState.debates.findIndex((item) => item.id === d.id);
  if (idx >= 0) dbState.debates[idx] = d;
  else dbState.debates.unshift(d);
  saveDatabaseToFile();
  broadcastEvent("DEBATE_UPDATED", d);
  res.json({ success: true, debate: d });
});
app.put("/api/debates/:id", async (req, res) => {
  const { id } = req.params;
  const d = req.body;
  if (sql) {
    try {
      await sql`
        UPDATE debate_sessions
        SET
          title = ${d.title},
          motion = ${d.motion},
          motion_info_slide = ${d.motionInfoSlide || null},
          category = ${d.category},
          format = ${d.format},
          date = ${d.date},
          time = ${d.time},
          status = ${d.status},
          google_meet_link = ${d.googleMeetLink || ""},
          winning_team = ${d.winningTeam || null},
          adjudicators = ${JSON.stringify(d.adjudicators || [])}::jsonb,
          teams = ${JSON.stringify(d.teams || [])}::jsonb,
          summary_clashes = ${JSON.stringify(d.summaryClashes || [])}::jsonb,
          attendee_ids = ${JSON.stringify(d.attendeeIds || [])}::jsonb,
          transcript = ${JSON.stringify(d.transcript || [])}::jsonb
        WHERE id = ${id};
      `;
    } catch (err) {
      console.error(`Error updating debate session ${id} in Neon:`, err);
    }
  }
  const idx = dbState.debates.findIndex((item) => item.id === id);
  if (idx >= 0) dbState.debates[idx] = { ...dbState.debates[idx], ...d };
  else dbState.debates.unshift(d);
  if (d.status === "Archived") {
    dbState.users = dbState.users.map((member) => {
      if (d.attendeeIds?.includes(member.id)) {
        const nextAttended = member.debatesAttendedCount + 1;
        const nextTotal = Math.max(member.totalDebatesCount + 1, nextAttended);
        const nextRate = Math.min(100, Math.round(nextAttended / nextTotal * 100));
        return {
          ...member,
          debatesAttendedCount: nextAttended,
          totalDebatesCount: nextTotal,
          attendanceRate: nextRate
        };
      }
      return member;
    });
    pushNotification({
      targetUserId: "all",
      title: "Debate Round Archived",
      message: `Round "${d.title}" concluded! Victorious: ${d.winningTeam || "Government"}. Ballots filed in Motion Vault.`,
      type: "debate_round",
      linkTab: "motion-vault"
    });
  }
  saveDatabaseToFile();
  broadcastEvent("DEBATE_UPDATED", d);
  res.json({ success: true, debate: d });
});
app.get("/api/agendas", async (_req, res) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM executive_agendas ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped = rows.map((r) => ({
          id: r.id,
          meetingTitle: r.meeting_title,
          date: r.date,
          time: r.time,
          location: r.location,
          status: r.status,
          chairperson: r.chairperson,
          agendaItems: r.agenda_items || [],
          logisticsChecklist: r.logistics_checklist || [],
          minutesSummary: r.minutes_summary || void 0
        }));
        dbState.agendas = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn("Neon query error for agendas:", err);
    }
  }
  res.json(dbState.agendas);
});
app.post("/api/agendas", async (req, res) => {
  const a = req.body;
  if (!a || !a.id) return res.status(400).json({ error: "Invalid agenda data" });
  if (sql) {
    try {
      await sql`
        INSERT INTO executive_agendas (
          id, meeting_title, date, time, location, status, chairperson,
          agenda_items, logistics_checklist, minutes_summary
        ) VALUES (
          ${a.id}, ${a.meetingTitle}, ${a.date}, ${a.time}, ${a.location},
          ${a.status || "Upcoming"}, ${a.chairperson},
          ${JSON.stringify(a.agendaItems || [])}::jsonb,
          ${JSON.stringify(a.logisticsChecklist || [])}::jsonb,
          ${a.minutesSummary || null}
        )
        ON CONFLICT (id) DO UPDATE SET
          meeting_title = EXCLUDED.meeting_title,
          status = EXCLUDED.status,
          agenda_items = EXCLUDED.agenda_items,
          logistics_checklist = EXCLUDED.logistics_checklist,
          minutes_summary = EXCLUDED.minutes_summary;
      `;
    } catch (err) {
      console.error("Error inserting agenda in Neon:", err);
    }
  }
  const idx = dbState.agendas.findIndex((item) => item.id === a.id);
  if (idx >= 0) dbState.agendas[idx] = a;
  else dbState.agendas.unshift(a);
  saveDatabaseToFile();
  broadcastEvent("AGENDA_UPDATED", a);
  res.json({ success: true, agenda: a });
});
app.put("/api/agendas/:id", async (req, res) => {
  const { id } = req.params;
  const a = req.body;
  if (sql) {
    try {
      await sql`
        UPDATE executive_agendas
        SET
          meeting_title = ${a.meetingTitle},
          date = ${a.date},
          time = ${a.time},
          location = ${a.location},
          status = ${a.status},
          chairperson = ${a.chairperson},
          agenda_items = ${JSON.stringify(a.agendaItems || [])}::jsonb,
          logisticsChecklist = ${JSON.stringify(a.logisticsChecklist || [])}::jsonb,
          minutes_summary = ${a.minutesSummary || null}
        WHERE id = ${id};
      `;
    } catch (err) {
      console.error(`Error updating agenda ${id} in Neon:`, err);
    }
  }
  const idx = dbState.agendas.findIndex((item) => item.id === id);
  if (idx >= 0) dbState.agendas[idx] = { ...dbState.agendas[idx], ...a };
  else dbState.agendas.unshift(a);
  saveDatabaseToFile();
  broadcastEvent("AGENDA_UPDATED", a);
  res.json({ success: true, agenda: a });
});
app.get("/api/announcements", async (_req, res) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM announcements ORDER BY publish_date DESC`;
      if (rows.length > 0) {
        const mapped = rows.map((r) => ({
          id: r.id,
          title: r.title,
          content: r.content,
          author: r.author,
          authorRole: r.author_role,
          publishDate: r.publish_date,
          priority: r.priority,
          category: r.category,
          pinned: Boolean(r.pinned)
        }));
        dbState.announcements = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn("Neon query error for announcements:", err);
    }
  }
  res.json(dbState.announcements);
});
app.post("/api/announcements", async (req, res) => {
  const ann = req.body;
  if (!ann || !ann.id) return res.status(400).json({ error: "Invalid announcement" });
  if (sql) {
    try {
      await sql`
        INSERT INTO announcements (
          id, title, content, author, author_role, publish_date, priority, category, pinned
        ) VALUES (
          ${ann.id}, ${ann.title}, ${ann.content}, ${ann.author}, ${ann.authorRole},
          ${ann.publishDate}, ${ann.priority}, ${ann.category}, ${Boolean(ann.pinned)}
        )
        ON CONFLICT (id) DO UPDATE SET
          title = EXCLUDED.title,
          content = EXCLUDED.content,
          priority = EXCLUDED.priority,
          pinned = EXCLUDED.pinned;
      `;
    } catch (err) {
      console.error("Error saving announcement in Neon:", err);
    }
  }
  const idx = dbState.announcements.findIndex((x) => x.id === ann.id);
  if (idx >= 0) dbState.announcements[idx] = ann;
  else dbState.announcements.unshift(ann);
  pushNotification({
    targetUserId: "all",
    title: ann.title,
    message: `${ann.authorRole} ${ann.author}: ${ann.content.slice(0, 100)}...`,
    type: "announcement",
    linkTab: "announcements"
  });
  saveDatabaseToFile();
  broadcastEvent("ANNOUNCEMENT_CREATED", ann);
  res.json({ success: true, announcement: ann });
});
app.get("/api/events", async (_req, res) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM calendar_events ORDER BY date ASC`;
      if (rows.length > 0) {
        const mapped = rows.map((r) => ({
          id: r.id,
          title: r.title,
          date: r.date,
          startTime: r.start_time,
          endTime: r.end_time,
          location: r.location,
          googleMeetUrl: r.google_meet_url || void 0,
          eventType: r.event_type,
          description: r.description,
          leadCoordinator: r.lead_coordinator
        }));
        dbState.events = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn("Neon query error for events:", err);
    }
  }
  res.json(dbState.events);
});
app.post("/api/events", async (req, res) => {
  const event = req.body;
  if (!event || !event.id) return res.status(400).json({ error: "Invalid event data" });
  if (sql) {
    try {
      await sql`
        INSERT INTO calendar_events (
          id, title, date, start_time, end_time, location, google_meet_url,
          event_type, description, lead_coordinator
        ) VALUES (
          ${event.id}, ${event.title}, ${event.date}, ${event.startTime},
          ${event.endTime}, ${event.location}, ${event.googleMeetUrl || null},
          ${event.eventType}, ${event.description}, ${event.leadCoordinator}
        )
        ON CONFLICT (id) DO UPDATE SET
          title = EXCLUDED.title,
          date = EXCLUDED.date,
          start_time = EXCLUDED.start_time,
          end_time = EXCLUDED.end_time,
          location = EXCLUDED.location,
          google_meet_url = EXCLUDED.google_meet_url;
      `;
    } catch (err) {
      console.error("Error inserting calendar event to Neon:", err);
    }
  }
  const idx = dbState.events.findIndex((x) => x.id === event.id);
  if (idx >= 0) dbState.events[idx] = event;
  else dbState.events.push(event);
  pushNotification({
    targetUserId: "all",
    title: `New Event: ${event.title}`,
    message: `${event.eventType} on ${event.date} at ${event.startTime}. Location: ${event.location}.`,
    type: "general",
    linkTab: "calendar"
  });
  saveDatabaseToFile();
  broadcastEvent("EVENT_CREATED", event);
  res.json({ success: true, event });
});
app.get("/api/mentorship", async (_req, res) => {
  if (sql) {
    try {
      const rows = await sql`SELECT * FROM mentorship_notes ORDER BY date DESC`;
      if (rows.length > 0) {
        const mapped = rows.map((r) => ({
          id: r.id,
          alumniId: r.alumni_id,
          alumniName: r.alumni_name,
          menteeId: r.mentee_id,
          menteeName: r.mentee_name,
          topic: r.topic,
          date: r.date,
          adviceSummary: r.advice_summary,
          status: r.status
        }));
        dbState.mentorshipNotes = mapped;
        saveDatabaseToFile();
        return res.json(mapped);
      }
    } catch (err) {
      console.warn("Neon query error for mentorship_notes:", err);
    }
  }
  res.json(dbState.mentorshipNotes);
});
app.post("/api/mentorship", async (req, res) => {
  const note = req.body;
  if (!note || !note.id) return res.status(400).json({ error: "Invalid mentorship note" });
  if (sql) {
    try {
      await sql`
        INSERT INTO mentorship_notes (
          id, alumni_id, alumni_name, mentee_id, mentee_name, topic, date,
          advice_summary, status
        ) VALUES (
          ${note.id}, ${note.alumniId}, ${note.alumniName}, ${note.menteeId},
          ${note.menteeName}, ${note.topic}, ${note.date}, ${note.adviceSummary},
          ${note.status || "Active"}
        )
        ON CONFLICT (id) DO UPDATE SET
          topic = EXCLUDED.topic,
          advice_summary = EXCLUDED.advice_summary,
          status = EXCLUDED.status;
      `;
    } catch (err) {
      console.error("Error inserting mentorship note to Neon:", err);
    }
  }
  const idx = dbState.mentorshipNotes.findIndex((x) => x.id === note.id);
  if (idx >= 0) dbState.mentorshipNotes[idx] = note;
  else dbState.mentorshipNotes.unshift(note);
  pushNotification({
    targetUserId: note.alumniId,
    title: "New Mentorship Request",
    message: `${note.menteeName} requested coaching on "${note.topic}".`,
    type: "duty_delegated",
    linkTab: "members"
  });
  saveDatabaseToFile();
  broadcastEvent("MENTORSHIP_UPDATED", note);
  res.json({ success: true, note });
});
app.get("/api/notifications", (req, res) => {
  const authHeader = req.headers.authorization;
  let targetId = "all";
  if (authHeader) {
    const token = authHeader.replace("Bearer ", "").trim();
    const match = token.match(/^token-(.+)-\d+$/);
    if (match) targetId = match[1];
  }
  const userNotifs = dbState.notifications.filter(
    (n) => n.targetUserId === "all" || n.targetUserId === targetId
  );
  res.json(userNotifs);
});
app.post("/api/notifications/:id/read", (req, res) => {
  const { id } = req.params;
  const notif = dbState.notifications.find((n) => n.id === id);
  if (notif) notif.isRead = true;
  saveDatabaseToFile();
  res.json({ success: true });
});
async function startServer() {
  const PORT = process.env.DEBATEHUB_PORT ? parseInt(process.env.DEBATEHUB_PORT, 10) : process.env.PORT ? parseInt(process.env.PORT, 10) : 3e3;
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        hmr: process.env.DISABLE_HMR !== "true",
        allowedHosts: true
      },
      appType: "spa"
    });
    app.use(vite.middlewares);
    app.get(["/DebateHub", "/DebateHub/*", "/debatehub", "/debatehub/*"], async (req, res, next) => {
      try {
        const url = req.originalUrl;
        let template = fs.readFileSync(path2.resolve(__dirname, "index.html"), "utf-8");
        template = await vite.transformIndexHtml(url, template);
        res.status(200).set({ "Content-Type": "text/html" }).end(template);
      } catch (e) {
        vite.ssrFixStacktrace(e);
        next(e);
      }
    });
  } else {
    const distPath = path2.join(__dirname, "dist");
    app.use("/DebateHub", express.static(distPath));
    app.use("/debatehub", express.static(distPath));
    app.use(express.static(distPath));
    app.get(["/DebateHub", "/DebateHub/*", "/debatehub", "/debatehub/*", "*"], (_req, res) => {
      res.sendFile(path2.join(distPath, "index.html"));
    });
  }
  app.listen(PORT, "0.0.0.0", () => {
    console.log(`GLUK Debate Club Server active at http://0.0.0.0:${PORT}`);
  });
}
startServer();
