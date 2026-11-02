import { User, QuizQuestion, QuizHistoryItem, TimetableSlot, StudentProgressSummary, ChatSession } from '../types';

export const INITIAL_USERS: User[] = [
  {
    id: "1",
    username: "Alex Kim",
    email: "student@trace.edu",
    role: "Student",
    difficulty: "Medium (Standard)",
    semesterStatus: "Year 4 - Clinical Rotations",
    aiPersona: "Socratic Tutor",
    sensoryMode: "Standard",
    activeUnits: ["Biochemistry II", "General Surgery", "Internal Medicine"],
    traceCoins: 200
  },
  {
    id: "2",
    username: "Dr. Neema Ongaga",
    email: "teacher@trace.edu",
    role: "Teacher",
    difficulty: "Advanced Faculty",
    semesterStatus: "Department of Clinical Sciences",
    aiPersona: "Pedagogical Report Assistant",
    sensoryMode: "Faculty",
    activeUnits: ["Biochemistry II", "General Surgery", "Internal Medicine"],
    traceCoins: 200
  },
  {
    id: "3",
    username: "Eleanor Kim",
    email: "parent@trace.edu",
    role: "Parent",
    difficulty: "Standard",
    semesterStatus: "Guardian Dashboard",
    aiPersona: "Supportive Education Consultant",
    sensoryMode: "Standard",
    activeUnits: ["Biochemistry II", "General Surgery", "Internal Medicine"],
    traceCoins: 200
  },
  {
    id: "4",
    username: "Admin Root",
    email: "admin@trace.edu",
    role: "Admin",
    difficulty: "Superuser",
    semesterStatus: "System Administration & Oversight",
    aiPersona: "System Architect & Lead Consultant",
    sensoryMode: "Standard",
    activeUnits: ["Biochemistry II", "General Surgery", "Internal Medicine", "Pathology & Diagnostics"],
    traceCoins: 500
  }
];

export const INITIAL_TEACHER_STUDENTS: StudentProgressSummary[] = [
  {
    id: "1",
    username: "Alex Kim",
    semesterStatus: "Year 4 - Clinical Rotations",
    activeUnits: ["Biochemistry II", "General Surgery", "Internal Medicine"],
    averagePnl: 84.5,
    totalQuizzes: 6,
    completedSubtopics: 4,
    totalSubtopics: 8,
    isAtRisk: false
  },
  {
    id: "102",
    username: "Grace Naliaka",
    semesterStatus: "Year 3 - Rotations",
    activeUnits: ["Biochemistry II", "General Surgery"],
    averagePnl: 58.2,
    totalQuizzes: 4,
    completedSubtopics: 2,
    totalSubtopics: 6,
    isAtRisk: true,
    riskReason: "Performance drop: 58.2% avg score on Acute Abdomen assessments. Targeted remediation recommended."
  },
  {
    id: "103",
    username: "Rayvins Otieno",
    semesterStatus: "Year 4 - Pre-med",
    activeUnits: ["Internal Medicine", "Biochemistry II"],
    averagePnl: 79.8,
    totalQuizzes: 7,
    completedSubtopics: 5,
    totalSubtopics: 7,
    isAtRisk: false
  },
  {
    id: "104",
    username: "Hillary Lweya",
    semesterStatus: "Final Year",
    activeUnits: ["General Surgery", "Internal Medicine"],
    averagePnl: 48.0,
    totalQuizzes: 2,
    completedSubtopics: 1,
    totalSubtopics: 7,
    isAtRisk: true,
    riskReason: "Stalled progress: Only 1 subtopic completed this term and quiz scores are below passing rubric."
  },
  {
    id: "105",
    username: "Tatiana A.",
    semesterStatus: "Year 4 - Honors",
    activeUnits: ["Biochemistry II", "Clinical Pharmacology"],
    averagePnl: 94.0,
    totalQuizzes: 9,
    completedSubtopics: 6,
    totalSubtopics: 6,
    isAtRisk: false
  }
];

export const INITIAL_TIMETABLE: TimetableSlot[] = [
  {
    id: "slot-1",
    day: "Monday",
    startTime: "08:30",
    endTime: "10:00",
    type: "study",
    title: "Enzyme Kinetics & Lineweaver-Burk Analysis",
    unitName: "Biochemistry II",
    notes: "Focus on competitive vs non-competitive inhibitor shifts on Km & Vmax."
  },
  {
    id: "slot-2",
    day: "Monday",
    startTime: "10:30",
    endTime: "12:00",
    type: "assessment",
    title: "Glycolysis & ETC Retrieval Quiz",
    unitName: "Biochemistry II",
    notes: "Timed 10-question retrieval session to reinforce Mitchell hypothesis."
  },
  {
    id: "slot-3",
    day: "Tuesday",
    startTime: "09:00",
    endTime: "11:00",
    type: "study",
    title: "Acute Abdomen Differential Roadmap",
    unitName: "General Surgery",
    notes: "Evaluate Alvarado score criteria & small bowel air-fluid level patterns."
  },
  {
    id: "slot-4",
    day: "Tuesday",
    startTime: "11:30",
    endTime: "12:30",
    type: "break",
    title: "Cognitive Consolidation & Hydration",
    notes: "Active mental rest to enhance neuroplastic memory consolidation."
  },
  {
    id: "slot-5",
    day: "Wednesday",
    startTime: "13:00",
    endTime: "14:30",
    type: "study",
    title: "Acute Coronary Syndromes (STEMI / NSTEMI)",
    unitName: "Internal Medicine",
    notes: "Correlate ST elevations in reciprocal leads with coronary arterial branches."
  },
  {
    id: "slot-6",
    day: "Thursday",
    startTime: "10:00",
    endTime: "11:30",
    type: "revision",
    title: "ATLS Shock Classes & Resuscitation",
    unitName: "General Surgery",
    notes: "Spaced review of Class I-IV blood loss and 1:1:1 MTP transfusion ratios."
  },
  {
    id: "slot-7",
    day: "Friday",
    startTime: "14:00",
    endTime: "15:30",
    type: "assessment",
    title: "Weekly Integrative Clinical Synthesis",
    unitName: "Internal Medicine",
    notes: "High-yield multi-system case study synthesis with Socratic Consultant."
  }
];

export const INITIAL_QUIZ_BANK: Record<string, QuizQuestion[]> = {
  "Biochemistry II": [
    {
      id: "q-bio-1",
      unitName: "Biochemistry II",
      topicName: "Glycolysis & Pyruvate Fate",
      question: "Which of the following compounds is the most potent positive allosteric activator of Phosphofructokinase-1 (PFK-1), effectively overriding high-ATP negative feedback in hepatocytes?",
      options: [
        "Fructose 2,6-bisphosphate",
        "Fructose 1,6-bisphosphate",
        "Citrate",
        "Glucose 6-phosphate"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Fructose 2,6-bisphosphate (F2,6-BP) is synthesized by the bifunctional enzyme PFK-2 in response to elevated insulin/glucagon ratios. F2,6-BP binds allosterically to PFK-1, shifting the enzyme from the low-affinity T state to the high-affinity R state, even in the presence of physiologic inhibitory ATP concentrations."
    },
    {
      id: "q-bio-2",
      unitName: "Biochemistry II",
      topicName: "Enzymology & Kinetic Models",
      question: "In the presence of a pure competitive inhibitor, how do the apparent Michaelis constant (Km) and maximal reaction velocity (Vmax) change on a Lineweaver-Burk plot?",
      options: [
        "Km increases (moves closer to zero on the 1/[S] axis), while Vmax remains unchanged",
        "Km remains unchanged, while Vmax decreases",
        "Both Km and Vmax decrease proportionally with parallel slope",
        "Km decreases, while Vmax increases"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Competitive inhibitors reversibly bind the active substrate-binding site. High substrate concentrations displace the inhibitor, meaning Vmax remains achievable. However, higher substrate is required to reach half-maximal velocity, resulting in an increased apparent Km."
    },
    {
      id: "q-bio-3",
      unitName: "Biochemistry II",
      topicName: "Electron Transport Chain",
      question: "A researcher administers 2,4-dinitrophenol (DNP) to isolated hepatocyte mitochondria. What immediate physiological alteration occurs?",
      options: [
        "Proton gradient dissipates as heat, decreasing ATP synthesis while oxygen consumption continues or accelerates",
        "Complex I is irreversibly blocked, halting all oxygen uptake",
        "ATP Synthase (Complex V) rotor accelerates ATP production",
        "Cytochrome c is released, triggering immediate caspase-3 cleavage"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: 2,4-DNP acts as an uncoupling agent by shuttling protons directly across the inner mitochondrial membrane, collapsing the electrochemical proton motive force without passing through ATP synthase (Complex V). Energy is lost as heat (hyperthermia), while the respiratory chain accelerates oxygen consumption in an attempt to restore the gradient."
    },
    {
      id: "q-bio-4",
      unitName: "Biochemistry II",
      topicName: "Beta-Oxidation & Ketogenesis",
      question: "Which metabolite directly inhibits Carnitine Palmitoyltransferase-1 (CPT-1), thereby preventing futile fatty acid oxidation during de novo lipogenesis?",
      options: [
        "Malonyl-CoA",
        "Acetyl-CoA",
        "Citrate",
        "Acetoacetate"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Malonyl-CoA, produced by Acetyl-CoA carboxylase (ACC) during fatty acid synthesis, allosterically inhibits CPT-1 on the outer mitochondrial membrane. This reciprocal regulation prevents newly synthesized fatty acids from being instantly transported into mitochondria for beta-oxidation."
    }
  ],
  "General Surgery": [
    {
      id: "q-surg-1",
      unitName: "General Surgery",
      topicName: "Appendicitis, Peritonitis & Perforation",
      question: "A 22-year-old male presents with 14 hours of periumbilical discomfort that has now localized to the right lower quadrant as severe, sharp pain worsened by coughing. Which physical exam finding describes referred pain to the RLQ upon deep palpation of the left lower quadrant?",
      options: [
        "Rovsing Sign",
        "Psoas Sign",
        "Obturator Sign",
        "Murphy Sign"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Rovsing sign is elicited when deep palpation of the left lower quadrant produces pain in the right lower quadrant. It occurs because retroperitoneal pressure displacement of colonic gas or peritoneal shifting stretches the inflamed parietal peritoneum overlying the diseased appendix."
    },
    {
      id: "q-surg-2",
      unitName: "General Surgery",
      topicName: "Trauma & Critical Surgical Resuscitation",
      question: "According to the Advanced Trauma Life Support (ATLS) 10th edition, a trauma patient with approximately 35% acute circulating blood loss (Class III Hemorrhagic Shock) will characteristically exhibit:",
      options: [
        "Hypotension (decreased systolic BP), tachycardia (HR >120 bpm), and oliguria",
        "Normal blood pressure, normal pulse pressure, and minimal anxiety",
        "Severe bradycardia and warm, flushed peripheries",
        "Hypertension with widened pulse pressure and bounding pulses"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Class III hemorrhagic shock (30-40% blood loss, ~1500-2000 mL in a 70kg adult) marks the tipping point where compensatory vasoconstriction fails, causing overt hypotension, significant tachycardia (>120 bpm), tachypnea, reduced pulse pressure, and oliguria."
    },
    {
      id: "q-surg-3",
      unitName: "General Surgery",
      topicName: "Acute Abdomen & Surgical Emergencies",
      question: "A 56-year-old female with a history of exploratory laparotomy 4 years ago presents with colicky abdominal pain, bilious emesis, and abdominal distension. Supine abdominal radiographs show centrally located dilated small bowel loops with a 'stepladder' pattern of air-fluid levels and minimal colonic gas. What is the most likely etiology?",
      options: [
        "Postoperative peritoneal adhesions",
        "Incarcerated femoral hernia",
        "Colonic adenocarcinoma with competent ileocecal valve",
        "Acute mesenteric arterial thrombosis"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Postoperative peritoneal adhesions account for 60-70% of all mechanical small bowel obstructions (SBO) in adults with prior abdominal surgical interventions. Air-fluid levels in dilated central loops without distal colonic gas confirm mechanical transit arrest."
    }
  ],
  "Internal Medicine": [
    {
      id: "q-med-1",
      unitName: "Internal Medicine",
      topicName: "Acute Coronary Syndromes (ACS)",
      question: "A 64-year-old male presents with crushing substernal chest pressure radiating to the jaw. 12-lead ECG demonstrates ST-segment elevations in leads II, III, and aVF with reciprocal ST depression in leads I and aVL. Which coronary artery is most likely occluded?",
      options: [
        "Right Coronary Artery (RCA)",
        "Left Anterior Descending (LAD) artery",
        "Left Main Stem Artery",
        "Diagonal branch 1 of LAD"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Leads II, III, and aVF look at the inferior diaphragmatic surface of the left ventricle, supplied by the Posterior Descending Artery (PDA). In approximately 85-90% of the population (right-dominant circulation), the PDA arises from the Right Coronary Artery (RCA)."
    },
    {
      id: "q-med-2",
      unitName: "Internal Medicine",
      topicName: "Nephrology & Acid-Base Balance",
      question: "A 32-year-old type 1 diabetic presents with tachypnea and confusion. Laboratory results show: Na+ = 138 mEq/L, Cl- = 98 mEq/L, HCO3- = 10 mEq/L, Glucose = 480 mg/dL. What is the calculated Serum Anion Gap and its classification?",
      options: [
        "30 mEq/L — High Anion Gap Metabolic Acidosis (HAGMA)",
        "10 mEq/L — Normal Anion Gap Metabolic Acidosis",
        "18 mEq/L — Normal Anion Gap Metabolic Acidosis",
        "42 mEq/L — Primary Respiratory Alkalosis"
      ],
      correctIndex: 0,
      explanation: "CLINICAL RATIONALE: Anion Gap = [Na+] - ([Cl-] + [HCO3-]) = 138 - (98 + 10) = 138 - 108 = 30 mEq/L. Normal range is 8-12 mEq/L. A gap of 30 mEq/L definitively indicates a severe High Anion Gap Metabolic Acidosis (HAGMA), caused here by unmeasured beta-hydroxybutyrate and acetoacetate ketoacid anions."
    }
  ]
};

export const INITIAL_QUIZ_HISTORY: QuizHistoryItem[] = [
  {
    id: "hist-1",
    userId: "1",
    unitName: "Biochemistry II",
    topicName: "Glycolysis & Pyruvate Fate",
    score: 4,
    total: 4,
    pnlScore: 100,
    timestamp: Date.now() - 1000 * 60 * 60 * 24 * 2
  },
  {
    id: "hist-2",
    userId: "1",
    unitName: "General Surgery",
    topicName: "Appendicitis, Peritonitis & Perforation",
    score: 2,
    total: 3,
    pnlScore: 66.7,
    timestamp: Date.now() - 1000 * 60 * 60 * 24 * 1
  },
  {
    id: "hist-3",
    userId: "1",
    unitName: "Internal Medicine",
    topicName: "Acute Coronary Syndromes",
    score: 2,
    total: 2,
    pnlScore: 100,
    timestamp: Date.now() - 1000 * 60 * 60 * 6
  }
];

export const INITIAL_CHAT_SESSIONS: ChatSession[] = [
  {
    id: "session-1",
    userId: "1",
    title: "Lineweaver-Burk Kinetic Deviations",
    description: "Deep dive into uncompetitive vs non-competitive inhibitor plots",
    timestamp: Date.now() - 1000 * 60 * 60 * 48,
    messages: [
      {
        id: "m-1",
        sender: "user",
        text: "Can you explain why uncompetitive inhibitors result in parallel lines on double-reciprocal plots?",
        timestamp: Date.now() - 1000 * 60 * 60 * 48
      },
      {
        id: "m-2",
        sender: "assistant",
        text: "In uncompetitive inhibition, the inhibitor binds exclusively to the enzyme-substrate (ES) complex, not free enzyme. This creates two distinct kinetic effects:\n\n1. **Apparent Vmax decreases**: The ESI complex cannot turn over into product, reducing maximum catalytic capacity.\n2. **Apparent Km decreases proportionally**: Depleting the ES complex pulls the E + S ⇌ ES equilibrium to the right by Le Chatelier's principle, seemingly increasing affinity for substrate.\n\nBecause the slope of the Lineweaver-Burk plot is **Km / Vmax**, and both constants decrease by the exact same multiplier $\\alpha'$, the slope $(Km / Vmax)$ remains completely unchanged! Hence, the lines are strictly parallel with shifted intercepts.",
        timestamp: Date.now() - 1000 * 60 * 60 * 47
      }
    ]
  },
  {
    id: "session-2",
    userId: "1",
    title: "Inferior STEMI & Right Ventricle Infiltration",
    description: "Nitrate contraindications and V4R lead diagnosis",
    timestamp: Date.now() - 1000 * 60 * 60 * 12,
    messages: [
      {
        id: "m-3",
        sender: "user",
        text: "Why must we avoid nitroglycerin if an inferior MI involves the right ventricle?",
        timestamp: Date.now() - 1000 * 60 * 60 * 12
      },
      {
        id: "m-4",
        sender: "assistant",
        text: "A damaged, infarcted Right Ventricle acts as a stiff, passive conduit rather than a vigorous pump. It becomes profoundly **preload-dependent** to push blood across the pulmonary vascular bed into the left ventricle.\n\nNitroglycerin is a potent venous vasodilator that pools blood in systemic capacitance veins, precipitously dropping Central Venous Pressure and right ventricular end-diastolic volume. In RV infarction, giving nitrates can cause immediate catastrophic systemic hypotension and cardiovascular collapse!\n\n**Key Rule**: Before giving nitrates in inferior ST elevation (leads II, III, aVF), always obtain right-sided lead **V4R**.",
        timestamp: Date.now() - 1000 * 60 * 60 * 11
      }
    ]
  }
];
