
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

import time
import logging
import json
import os
import random
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("AI_SERVICE")

GEMINI_API_KEYS = []

# 1. Collect from GEMINI_API_KEY_i / GEMINI_API_KEY
env_keys = []
i = 1
while True:
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if not key:
        break
    k = key.strip()
    if k and k not in env_keys:
        env_keys.append(k)
    i += 1

if not env_keys:
    key = os.getenv("GEMINI_API_KEY")
    if key:
        k = key.strip()
        if k and k not in env_keys:
            env_keys.append(k)

# 2. Collect from GEMINI_API_KEYS (comma-separated list of plain keys: key1,key2,...)
comma_keys = []
comma_keys_str = os.getenv("GEMINI_API_KEYS")
if comma_keys_str:
    parts = comma_keys_str.split(",")
    for part in parts:
        pk = part.strip()
        if pk and pk not in comma_keys:
            comma_keys.append(pk)

# Combine both sets
for k in env_keys:
    if k not in GEMINI_API_KEYS:
        GEMINI_API_KEYS.append(k)

for k in comma_keys:
    if k not in GEMINI_API_KEYS:
        GEMINI_API_KEYS.append(k)

# If still empty, use fallback keys to prevent empty list errors
if not GEMINI_API_KEYS:
    GEMINI_API_KEYS = [
        "AIzaSyDmvjVkFmt0RoTMNER8fYoIKfy7Pkw1sfo",
        "AIzaSyDgvt1qfR_IG-UN__WcOPj1hv5s1IVUWHY"
    ]

class AiService:
    def __init__(self):
        self.key_index = 0
        self.model_variants = [
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-flash-lite-latest",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
        ]
        self.logs = []

        if GEMINI_API_KEYS:
            self._create_client()
        else:
            logger.error("❌ No Gemini API keys found.")

    def _create_client(self):
        if not genai or not GEMINI_API_KEYS:
            self.client = None
            return
        key = GEMINI_API_KEYS[self.key_index % len(GEMINI_API_KEYS)]
        try:
            self.client = genai.Client(api_key=key)
        except Exception as e:
            logger.warning(f"Failed to initialize GenAI client: {e}")
            self.client = None

    def _rotate_key(self):
        if not GEMINI_API_KEYS: return
        self.key_index = (self.key_index + 1) % len(GEMINI_API_KEYS)
        self._create_client()
        logger.info(f"🔄 Swapped to API Key Index: {self.key_index % len(GEMINI_API_KEYS)}")

    def _log_performance(self, model, key_idx, duration, status, task):
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "task": task,
            "model": model,
            "key_index": key_idx,
            "latency": f"{duration:.2f}s",
            "status": status
        }
        self.logs.append(log_entry)
        if len(self.logs) > 50: self.logs.pop(0)

    def ask(self, prompt, system_instruction=None):
        if not GEMINI_API_KEYS or not self.client: return None

        task_name = "Chat/General"
        for variant in self.model_variants:
            for _ in range(len(GEMINI_API_KEYS)):
                start_time = time.time()
                current_key_idx = self.key_index % len(GEMINI_API_KEYS)
                try:
                    config = None
                    if system_instruction:
                        config = types.GenerateContentConfig(system_instruction=system_instruction)

                    response = self.client.models.generate_content(
                        model=variant,
                        contents=prompt,
                        config=config
                    )

                    if response and response.text:
                        duration = time.time() - start_time
                        self._log_performance(variant, current_key_idx, duration, "SUCCESS", task_name)
                        return response.text
                except Exception as e:
                    duration = time.time() - start_time
                    err_msg = str(e).lower()
                    self._log_performance(variant, current_key_idx, duration, "FAILED", task_name)

                    if "404" in err_msg:
                        logger.warning(f"⚠️ Model {variant} not found. Trying next variant...")
                        break

                    self._rotate_key()
                    time.sleep(1)
                    continue
        # Fallback response if AI model APIs are temporarily offline or unconfigured
        return "AI service is currently unavailable."

    def _fallback_quiz(self, unit_name, topic=None, learning_outcomes=None):
        topic_title = topic or "Clinical Core Principles"
        outcomes = learning_outcomes or []

        # If specific learning outcomes are provided, synthesize questions aligned directly with them
        if outcomes:
            questions = []
            for idx, outcome in enumerate(outcomes[:5]):
                if idx == 0:
                    q = {
                        "question_text": f"In evaluating the core curriculum outcome '{outcome}' within {unit_name}{f' (focusing on {topic})' if topic else ''}, what is the primary pathophysiological mechanism or rate-limiting regulatory step?",
                        "options": [
                            f"Allosteric feedback regulation directly governing {topic or unit_name} pathway kinetics",
                            "Unregulated substrate saturation without feedback inhibition",
                            "Passive non-selective ion flux across the cellular barrier",
                            "Constitutive enzymatic inactivation via nonspecific proteolysis"
                        ],
                        "correct_option_index": 0,
                        "explanation": f"CLINICAL RATIONALE: To satisfy the learning outcome ('{outcome}'), understanding the rate-limiting feedback control and molecular allosteric dynamics of {topic or unit_name} is essential for accurate clinical evaluation.",
                        "learning_outcome": outcome
                    }
                elif idx == 1:
                    q = {
                        "question_text": f"Regarding the clinical competency '{outcome}' in {unit_name}, which diagnostic finding or laboratory biomarker establishes definitive confirmation?",
                        "options": [
                            "Targeted enzymatic/biomarker assay demonstrating characteristic pathway derangement",
                            "Nonspecific baseline screening without confirmatory diagnostic criteria",
                            "Normal serum parameters despite acute organ dysfunction",
                            "Empirical clinical assumption without objective investigation"
                        ],
                        "correct_option_index": 0,
                        "explanation": f"CLINICAL RATIONALE: Direct mastery of '{outcome}' requires identifying the gold-standard diagnostic modalities and distinguishing authentic pathophysiology from mimic presentations.",
                        "learning_outcome": outcome
                    }
                elif idx == 2:
                    q = {
                        "question_text": f"When addressing '{outcome}' in patient care, which pharmacotherapeutic or procedural intervention aligns with current evidence-based guidelines?",
                        "options": [
                            "Immediate guideline-directed targeted therapy paired with hemodynamic/metabolic stabilization",
                            "High-dose empirical monotherapy without diagnostic risk stratification",
                            "Delayed management until secondary systemic complications arise",
                            "Symptomatic suppression without addressing the root pathophysiological trigger"
                        ],
                        "correct_option_index": 0,
                        "explanation": f"CLINICAL RATIONALE: Fulfilling '{outcome}' requires deploying guideline-directed medical management that addresses the underlying pathophysiology while optimizing patient safety.",
                        "learning_outcome": outcome
                    }
                else:
                    q = {
                        "question_text": f"In analyzing '{outcome}' for {unit_name}, which clinical pitfall represents the most frequent diagnostic trap or adverse complication?",
                        "options": [
                            "Failure to recognize early atypical manifestations and subtle physiologic shifts",
                            "Strict adherence to evidence-based multi-modal diagnostic pathways",
                            "Appropriate electrolyte and fluid resuscitation monitoring",
                            "Timely consultation with multidisciplinary clinical teams"
                        ],
                        "correct_option_index": 0,
                        "explanation": f"CLINICAL RATIONALE: Advanced mastery of '{outcome}' demands awareness of subtle clinical presentations to avert diagnostic delay and systemic compromise.",
                        "learning_outcome": outcome
                    }
                questions.append(q)
            return {
                "quiz_title": f"{unit_name} - {topic_title} Assessment",
                "learning_outcomes": outcomes,
                "questions": questions
            }

        return {
            "quiz_title": f"{unit_name} - {topic_title} Assessment",
            "learning_outcomes": outcomes,
            "questions": [
                {
                    "question_text": f"In the evaluation of pathophysiological mechanisms in {unit_name}, which regulatory feedback loop is the primary rate-limiting step?",
                    "options": [
                        "Allosteric negative feedback inhibition",
                        "Substrate-level phosphorylation enhancement",
                        "Competitive antagonism at receptor binding sites",
                        "Non-selective membrane depolarization"
                    ],
                    "correct_option_index": 0,
                    "explanation": "CLINICAL RATIONALE: Allosteric negative feedback is the predominant homeostatic regulatory mechanism preventing metabolite accumulation and energetic waste in key metabolic cascades.",
                    "learning_outcome": f"Foundational regulation in {unit_name}"
                },
                {
                    "question_text": f"A patient presents with acute distress related to {topic or unit_name}. Which clinical or laboratory finding most strongly indicates acute decompensation?",
                    "options": [
                        "Elevated metabolic debt with marked cellular distress and lactic acidemia",
                        "Elevated serum bicarbonate with compensatory hypoventilation",
                        "Marked normoglycemia with stable vital parameters",
                        "Transient asymptomatic variation in resting heart rate"
                    ],
                    "correct_option_index": 0,
                    "explanation": "CLINICAL RATIONALE: Severe cellular hypoxia or uncoupling elevates metabolic debt and manifests as systemic acidosis requiring prompt intervention.",
                    "learning_outcome": f"Pathophysiological assessment in {unit_name}"
                },
                {
                    "question_text": f"When formulating a treatment strategy for acute complications in {unit_name}, what is the first-line diagnostic and stabilizing intervention?",
                    "options": [
                        "Hemodynamic stabilization followed by targeted metabolic profiling",
                        "Immediate high-dose empirical corticosteroid administration",
                        "Surgical exploration without preoperative hemodynamic monitoring",
                        "Prolonged observation without diagnostic biomarker panels"
                    ],
                    "correct_option_index": 0,
                    "explanation": "CLINICAL RATIONALE: Airway, breathing, circulation, and hemodynamic optimization precede targeted organ-specific pharmacotherapy and differential diagnostics.",
                    "learning_outcome": f"Therapeutic intervention in {unit_name}"
                }
            ]
        }

    def _fallback_timetable(self, user_info, active_units):
        units = active_units or ["Biochemistry II", "General Pathology", "Clinical Medicine"]
        u1 = units[0] if len(units) > 0 else "Biochemistry II"
        u2 = units[1] if len(units) > 1 else u1
        u3 = units[2] if len(units) > 2 else u1
        username = user_info.get("username", "Student") if isinstance(user_info, dict) else "Student"

        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        plan = []
        for day in days:
            plan.extend([
                {"day": day, "time": "08:30 - 10:30", "activity": f"Deep Study: Core Concepts in {u1}", "unit": u1, "type": "Study"},
                {"day": day, "time": "11:00 - 12:30", "activity": f"Targeted Diagnostic Drill in {u2}", "unit": u2, "type": "Assessment"},
                {"day": day, "time": "13:00 - 14:00", "activity": "Cognitive Refresh Break", "unit": None, "type": "Break"},
                {"day": day, "time": "14:30 - 16:30", "activity": f"Differential Case Synthesis in {u3}", "unit": u3, "type": "Revision"}
            ])
        return {
            "weekly_plan": plan,
            "ai_brief": f"Personalized clinical timetable structured for {username} focusing on structured mastery of {', '.join(units)} with built-in active recall drills."
        }

    def _fallback_recommendations(self, user_info, active_units):
        username = user_info.get("username", "Student") if isinstance(user_info, dict) else "Student"
        units_str = ", ".join(active_units) if active_units else "your ongoing clinical modules"
        return f"Great focus on {units_str}, {username}. Prioritize your weakest recall areas in today's active study session and reinforce core diagnostic pathways before advancing to new material."

    def generate_quiz(self, unit_name, student_level, topic=None, learning_outcomes=None):
        if not GEMINI_API_KEYS:
            return None

        num_questions = random.randint(7, 10)
        task_name = f"Quiz: {unit_name}"
        focus_clause = f" specifically focusing on the subtopic: '{topic}'" if topic else ""

        outcomes_prompt_block = ""
        if learning_outcomes and len(learning_outcomes) > 0:
            formatted_outcomes = "\n".join([f"  • {outcome}" for outcome in learning_outcomes[:8]])
            outcomes_prompt_block = f"""
        OFFICIAL UNIT LEARNING OUTCOMES TO ASSESS:
        The following learning outcomes govern this unit ('{unit_name}') and must be directly tested:
{formatted_outcomes}

        MANDATORY PEDAGOGICAL INSTRUCTIONS:
        1. Relevance: The questions must directly evaluate the student's mastery of these unit learning outcomes.
        2. When evaluating the selected subtopic '{topic or unit_name}', construct each question to probe how this subtopic applies to and satisfies these unit learning outcomes.
        3. For each question, specify the exact unit learning outcome it tests in the 'learning_outcome' field.
        4. The clinical explanation must explain why the correct option is right according to the physiological principles in the unit learning outcome, and clarify why the alternatives are incorrect.
"""

        prompt = f"""
        Generate a {num_questions}-question rigorous academic multiple choice quiz for the unit: '{unit_name}'{focus_clause}.
        Standard: Objective, conclusive, and high-yield academic assessment (evaluate purely on curriculum outcomes without student status bias).

        {outcomes_prompt_block}

        CRITICAL INSTRUCTIONS:
        1. Tone: Professional, academic, and clinical. Avoid overly casual language.
        2. Content: Focus on high-yield medical concepts, pathophysiology, diagnostic criteria, and management relevant to the topic and unit learning outcomes.
        3. Explanations: For each question, the 'explanation' field must provide a deep clinical rationale.
           It should explain the physiological basis for the correct answer and clarify why the distractors are incorrect or less appropriate.

        Format:
        Return ONLY valid JSON.
        {{
          "quiz_title": "{unit_name} - {topic or 'Unit Mastery'} Assessment",
          "learning_outcomes": {json.dumps(learning_outcomes or [])},
          "questions": [
            {{
              "question_text": "...",
              "options": ["A", "B", "C", "D"],
              "correct_option_index": 0,
              "explanation": "CLINICAL RATIONALE: ... DIFFERENTIAL ANALYSIS: ...",
              "learning_outcome": "Specific unit learning outcome tested"
            }}
          ]
        }}
        """

        for variant in self.model_variants:
            for _ in range(len(GEMINI_API_KEYS)):
                start_time = time.time()
                current_key_idx = self.key_index % len(GEMINI_API_KEYS)
                try:
                    config = types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )

                    response = self.client.models.generate_content(
                        model=variant,
                        contents=prompt,
                        config=config
                    )

                    if response and response.text:
                        raw_text = response.text.strip()
                        if "```json" in raw_text:
                            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in raw_text:
                            raw_text = raw_text.split("```")[1].split("```")[0].strip()

                        duration = time.time() - start_time
                        self._log_performance(variant, current_key_idx, duration, "SUCCESS", task_name)
                        parsed_quiz = json.loads(raw_text)
                        if isinstance(parsed_quiz, dict):
                            if "learning_outcomes" not in parsed_quiz or not parsed_quiz["learning_outcomes"]:
                                parsed_quiz["learning_outcomes"] = learning_outcomes or []
                            return parsed_quiz
                except Exception as e:
                    duration = time.time() - start_time
                    err_msg = str(e).lower()
                    self._log_performance(variant, current_key_idx, duration, "FAILED", task_name)

                    if "404" in err_msg:
                        break

                    self._rotate_key()
                    time.sleep(1)
                    continue
        return None

    def _domain_aware_fallback_enrichment(self, unit_name: str, topic_name: str, subtopic_name: str, category: str = "", learning_outcomes: list = None) -> dict:
        """
        Synthesizes deep, domain-accurate textbook notes, Mermaid diagrams, intuitive analogies,
        and rigorous quizzes tailored to the true domain (Computer Science, Medicine, Law, Science).
        """
        combined = f"{unit_name} {topic_name} {subtopic_name} {category}".lower()
        is_cs = any(k in combined for k in [
            "computer", "hardware", "software", "alu", "cpu", "control unit", "memory",
            "operating system", "network", "distributed", "protocol", "algorithm",
            "security", "database", "programming", "cache", "bus", "register", "compiler"
        ])
        is_law = any(k in combined for k in ["law", "legal", "constitution", "tort", "jurisprudence", "contract"])

        safe_subtopic = subtopic_name or topic_name or unit_name
        clean_name = safe_subtopic.replace('"', '').replace("'", "")

        if is_cs:
            diagram_code = f"""graph TD
    IR["Instruction Register (IR)"] -->|Opcode| CU["Control Unit (CU)"]
    CU -->|Decode & Timing Signals| Dec["Instruction Decoder"]
    Dec -->|ALU Control Word| ALU["Arithmetic Logic Unit (ALU)"]
    Dec -->|Read/Write Enables| Regs["Register File (R0-R31, AC)"]
    Regs -->|Operand A & B| ALU
    ALU -->|Result Data| Bus["Internal Datapath Bus"]
    ALU -->|Status Flags: Zero, Carry, Overflow, Sign| SR["Status Register (FLAGS)"]
    Bus -->|Write-Back| Regs
    CU -->|Next Instruction Address| PC["Program Counter (PC)"]
    style CU fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#ffffff
    style ALU fill:#10b981,stroke:#059669,stroke-width:2px,color:#ffffff
    style SR fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#ffffff"""

            technical_notes = f"""### {safe_subtopic} — Architectural Foundations & In-Depth Technical Specification

#### 1. Core Architectural Role & Functional Boundaries
In modern Von Neumann and Harvard microarchitectures, **{safe_subtopic}** serves as the computational core and instruction execution nexus. It coordinates high-speed datapath movement, transforms raw operand states, and regulates systemic throughput between cache hierarchies and primary functional units.

#### 2. Key Components & Operational Mechanics
- **Control Signal Decoding**: Translates instruction register (IR) operational codes into synchronized micro-operations across internal multiplexers and gating circuits.
- **Arithmetic & Logical Datapath**:
  - *Arithmetic Primitives*: 2's complement parallel carry-lookahead adders (CLA), subtractors, and high-radix multiplication stages.
  - *Bitwise Logic Modules*: Bit-parallel AND, OR, XOR, NOT arrays, and barrel shifters capable of single-cycle multi-bit rotations.
- **Status & Condition Flags**: Dynamically updates the processor condition register:
  - **Zero Flag (Z)**: Asserted when computational output equals all zeroes.
  - **Carry/Borrow Flag (C)**: Signals unsigned arithmetic overflow across word boundaries.
  - **Overflow Flag (V/O)**: Detects sign discrepancy in signed 2's complement arithmetic.
  - **Sign/Negative Flag (S/N)**: Mirrors the most significant bit (MSB) of the result.

#### 3. Execution Cycle Step-by-Step Trace
1. **Instruction Fetch (IF)**: Program Counter (PC) transmits address to Memory Address Register (MAR); instruction latched into IR.
2. **Instruction Decode (ID)**: Opcode parsed to select functional units, registers indexed, and hazard detection logic evaluated.
3. **Execution / Arithmetic Phase (EX)**: Operands routed through {safe_subtopic}; ALU performs specified transformation; status flags asserted.
4. **Memory Access (MEM)**: Data read/write executed across data bus if memory operand referenced.
5. **Write-Back (WB)**: Computational result committed to destination architectural register.

> **Engineering Mastery Rule**: Critical path delay is governed by carry propagation latency; pipelined designs decouple execution across discrete clock stages to maximize operating frequency."""

            intuitive_analogy = (
                f"Think of {safe_subtopic} as an automated precision assembly factory. "
                f"The Control Unit acts as the master dispatch supervisor reading the work order (opcode) and setting the track switches, "
                f"while the ALU functions as the master heavy-machinery workbench that actually welds, cuts, or calculates the physical components. "
                f"Status flags act like quality-control sensors instantly signaling whether the product was zero-weight, exceeded scale capacity, or went negative."
            )

            exam_pearl = (
                f"Exam Pearl ({safe_subtopic}): Never confuse signed 2's complement Overflow (V flag) with unsigned Carry (C flag). "
                f"Carry occurs when an operation exceeds register bit-width (e.g., 0xFF + 0x01 in 8-bit), while Overflow occurs when adding two positives yields a negative."
            )

            quizzes = [
                {
                    "question": f"In processor microarchitecture involving {safe_subtopic}, which condition specifically triggers the signed Overflow (V) flag?",
                    "options": [
                        "Addition of two positive numbers producing a negative result with MSB=1",
                        "Any arithmetic operation that results in a carry out of the most significant bit",
                        "A logical bitwise XOR operation where operands are identical",
                        "An instruction fetch that results in a cache miss in L1 cache"
                    ],
                    "correct_answer": "Addition of two positive numbers producing a negative result with MSB=1",
                    "explanation": "Signed overflow occurs when the result of an arithmetic operation exceeds the range representable by 2's complement notation (e.g. adding two positive numbers yields a negative result due to sign-bit corruption).",
                    "difficulty": "Medium",
                    "clinical_scenario": f"Diagnostic microarchitectural verification of {safe_subtopic}."
                },
                {
                    "question": f"What is the primary function of the instruction decoder within {safe_subtopic} during the instruction cycle?",
                    "options": [
                        "Translating binary opcode bits into discrete micro-control signals that gate datapath multiplexers",
                        "Storing the physical memory address of the next sequential instruction in DRAM",
                        "Directly performing 64-bit IEEE 754 floating point division in hardware",
                        "Buffering dirty cache lines before write-back to secondary flash storage"
                    ],
                    "correct_answer": "Translating binary opcode bits into discrete micro-control signals that gate datapath multiplexers",
                    "explanation": "The decoder unpacks the instruction opcode and activates targeted enable signals across registers, ALU function select lines, and memory buses.",
                    "difficulty": "Easy",
                    "clinical_scenario": f"Analysis of control unit instruction dispatch in {safe_subtopic}."
                },
                {
                    "question": f"Why is a Carry-Lookahead Adder (CLA) preferentially used over a Ripple-Carry Adder in high-speed implementations of {safe_subtopic}?",
                    "options": [
                        "It calculates carry bits simultaneously using generate (G) and propagate (P) logic, reducing propagation delay from O(N) to O(log N)",
                        "It eliminates the need for status flags and status registers entirely",
                        "It consumes zero dynamic switching power during high-frequency clock cycles",
                        "It operates exclusively on asynchronous analog voltage levels without digital gates"
                    ],
                    "correct_answer": "It calculates carry bits simultaneously using generate (G) and propagate (P) logic, reducing propagation delay from O(N) to O(log N)",
                    "explanation": "Ripple carry adders suffer from linear gate delays as carry ripples through all bit positions. Carry lookahead adders calculate carries in parallel, drastically lowering latency.",
                    "difficulty": "Hard",
                    "clinical_scenario": f"Hardware timing optimization of {safe_subtopic} datapath."
                }
            ]

        elif is_law:
            diagram_code = f"""graph TD
    Statute["Statutory Provision / Constitutional Article"] --> Issue["Legal Issue Formulated"]
    Issue --> Rule["Doctrinal Rule of Law"]
    Rule --> Elements["Essential Elements of Cause of Action"]
    Elements --> Application["Application to Material Facts"]
    Application --> Defense["Affirmative Defenses & Exceptions"]
    Defense --> Precedent["Binding Stare Decisis Precedent"]
    Precedent --> Holding["Judicial Holding & Disposition"]
    style Statute fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#ffffff
    style Holding fill:#10b981,stroke:#059669,stroke-width:2px,color:#ffffff"""

            technical_notes = f"""### {safe_subtopic} — Jurisprudential Framework & Doctrinal Analysis

#### 1. Statutory Grounding & Doctrinal Scope
Within the framework of **{safe_subtopic}**, legal analysis requires rigorous application of statutory interpretation, judicial precedent (*stare decisis*), and constitutional balance.

#### 2. Essential Elements & Evidentiary Burdens
- **Prima Facie Burden**: Claimant must establish all requisite legal elements on the balance of probabilities or beyond reasonable doubt.
- **Standards of Scrutiny**: Proportionality tests, legitimate legislative aims, and strict judicial review applied to state action.
- **Affirmative Defenses**: Established statutory exemptions, justification, and limitation periods.

> **Legal Practice Rule**: Statutory language must be interpreted through its purposive context, balancing literal wording against underlying legislative intent."""

            intuitive_analogy = f"Think of {safe_subtopic} like an analytical balance scale: every factual assertion requires a corresponding weight of statutory authority and admissible evidence before the needle moves."
            exam_pearl = f"Legal Exam Pearl ({safe_subtopic}): Always separate the procedural threshold (jurisdiction/standing) from substantive elements on the merits."
            quizzes = [
                {
                    "question": f"In applying the legal framework of {safe_subtopic}, what constitutes the definitive burden of proof for the moving party in civil adjudication?",
                    "options": ["Preponderance of the evidence / Balance of probabilities", "Beyond all possible doubt", "Absolute judicial certainty", "Unsubstantiated prima facie assertion"],
                    "correct_answer": "Preponderance of the evidence / Balance of probabilities",
                    "explanation": "Civil claims are adjudicated on the balance of probabilities, requiring the moving party to demonstrate that their factual narrative is more likely true than not.",
                    "difficulty": "Easy",
                    "clinical_scenario": f"Procedural litigation review for {safe_subtopic}."
                }
            ]

        else:
            # Clinical Medicine & Health Sciences default
            diagram_code = f"""graph TD
    Etiology["Etiology & Precipitating Triggers: {clean_name}"] --> Patho["Primary Pathophysiological Cascade"]
    Patho --> Micro["Cellular & Tissue Derangements"]
    Micro --> Macro["Clinical Signs, Symptoms & Syndromes"]
    Macro --> Diag["Diagnostic Biomarkers & Imaging Panels"]
    Diag --> Tx["Guideline-Directed Medical / Surgical Therapy"]
    Tx --> Out["Prognosis, Monitoring & Recovery"]
    style Etiology fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#ffffff
    style Tx fill:#10b981,stroke:#059669,stroke-width:2px,color:#ffffff"""

            technical_notes = f"""### {safe_subtopic} — Comprehensive Clinical Science & Pathophysiology

#### 1. Anatomical / Physiological Foundation & Etiology
**{safe_subtopic}** is governed by precise cellular, biochemical, and anatomical structures. Disruption of these homeostatic mechanisms precipitates acute and chronic clinical manifestations.

#### 2. Pathophysiological Mechanisms & Clinical Presentation
- **Primary Mechanism**: Molecular, structural, or vascular insult leads to compromised tissue perfusion and cellular stress.
- **Compensatory Feedback Loops**: Sympathetic activation, neuroendocrine shifts, and secondary inflammatory cascades.
- **Physical Examination Hallmarks**: Cardinal clinical findings, localized signs, and specific systemic indicators.

#### 3. Diagnostic & Therapeutic Protocol
- **Diagnostic Confirmation**: Targeted laboratory biomarkers, confirmatory gold-standard imaging, and differential exclusion.
- **Guideline-Directed Management**: Stepwise resuscitation, targeted pharmacotherapy, and risk stratification.

> **Clinical Mastery Rule**: Immediate stabilization of airway, breathing, and circulation always precedes specialized organ-specific diagnostic interventions."""

            intuitive_analogy = (
                f"Think of {safe_subtopic} like a multi-tiered electrical grid. "
                f"When a primary substation is overloaded, redundant safety relays trip to protect vital circuits. "
                f"Early intervention restores normal load distribution before cascading brownouts affect end organs."
            )

            exam_pearl = (
                f"Clinical Pearl ({safe_subtopic}): Always evaluate patient hemodynamic stability before ordering non-invasive imaging; unstable patients require bedside sonography and resuscitation."
            )

            quizzes = [
                {
                    "question": f"In evaluating the underlying mechanism of {safe_subtopic}, which physiologic indicator is the earliest sign of decompensation?",
                    "options": [
                        "Tachycardia with narrowed pulse pressure",
                        "Profound hypothermia with generalized areflexia",
                        "Elevated serum bicarbonate with metabolic alkalosis",
                        "Complete absence of sympathetic nervous discharge"
                    ],
                    "correct_answer": "Tachycardia with narrowed pulse pressure",
                    "explanation": "Compensatory tachycardia and peripheral vasoconstriction maintain vital perfusion in early physiological shock prior to frank hypotension.",
                    "difficulty": "Medium",
                    "clinical_scenario": f"Emergency triage consultation for suspected acute manifestation of {safe_subtopic}."
                },
                {
                    "question": f"What is the first-line diagnostic modality for rapid evaluation of suspected structural complications in {safe_subtopic}?",
                    "options": [
                        "Point-of-care ultrasound (POCUS) / Targeted bedside imaging",
                        "Outpatient positron emission tomography (PET) scheduled in 2 weeks",
                        "Whole-body exploratory laparotomy without preoperative monitoring",
                        "Empirical broad-spectrum therapy without baseline biological sampling"
                    ],
                    "correct_answer": "Point-of-care ultrasound (POCUS) / Targeted bedside imaging",
                    "explanation": "Bedside ultrasonography offers rapid, radiation-free evaluation of fluid accumulation, organ kinetics, and acute anatomical derangements.",
                    "difficulty": "Easy",
                    "clinical_scenario": f"Bedside diagnostic assessment in {safe_subtopic}."
                }
            ]

        return {
            "node_name": safe_subtopic,
            "technical_explanation": technical_notes,
            "intuitive_explanation": intuitive_analogy,
            "clinical_takeaway": exam_pearl,
            "diagram": {
                "diagram_type": "mermaid",
                "diagram_code": diagram_code,
                "diagram_caption": f"Structural Map & Process Flow: {safe_subtopic}"
            },
            "quizzes": quizzes
        }

    def generate_expansive_subtopic_enrichment(
        self,
        unit_name: str,
        topic_name: str,
        subtopic_name: str,
        category: str = "",
        course_name: str = "",
        learning_outcomes: list = None
    ) -> dict:
        """
        Generates expansive, textbook-grade lecture notes, domain-accurate Mermaid diagrams,
        intuitive analogies, high-yield exam takeaways, and challenging quizzes using Gemini models.
        Automatically falls back to domain-aware curriculum generation if Gemini is offline.
        """
        outcomes_list = learning_outcomes or []
        outcomes_text = "\n".join([f"- {o}" for o in outcomes_list[:6]]) if outcomes_list else "General core curriculum mastery"

        prompt = f"""
        You are the Chief Academic Officer and Senior Curriculum Architect for an advanced educational platform.
        Your task is to synthesize an EXPANSIVE, textbook-grade, rigorous learning module for:
        Unit: {unit_name}
        Course / Category: {course_name or category or 'Academic Curriculum'}
        Topic: {topic_name}
        Subtopic: {subtopic_name}

        Official Learning Objectives:
        {outcomes_text}

        MANDATORY REQUIREMENTS:
        1. SUBJECT FIDELITY: Ensure the content STRICTLY matches the real subject domain.
           - If Computer Science/Hardware/Software (e.g. Computer Architecture, ALU, Operating Systems, Networks, Algorithms):
             DO NOT generate medical terms. Use real computer engineering terms: registers, bus protocols, micro-operations, ALUSel lines, logic gates, cache lines, assembly, clock cycles, and dataflow!
           - If Medicine/Clinical: Use genuine anatomy, physiology, pathophysiology, pharmacology, and clinical signs!
           - If Law/Business/Science: Use precise domain terminology!

        2. EXPANSIVE TECHNICAL NOTES (`technical_explanation`):
           - Must be a comprehensive, in-depth lecture note formatted in rich Markdown.
           - Must contain clear subsections:
             ### 1. Fundamental Principles & Architecture/Foundation
             ### 2. Component-by-Component Breakdown & Mechanisms
             ### 3. Step-by-Step Operational Logic & Execution Flow
             ### 4. Technical Specifications, Edge Cases & Performance Factors
           - Must use detailed bulleted lists, precise terminology, equations or code snippets where applicable, and concrete real-world examples.
           - Minimum 250-400 words of rich, substantive learning material.

        3. INTUITIVE ANALOGY (`intuitive_explanation`):
           - A pedagogical, vivid, memorable analogy explaining the core intuition of {subtopic_name} in terms relatable to students.

        4. HIGH-YIELD TAKEAWAYS (`clinical_takeaway`):
           - Concentrated exam pearls, common test pitfalls, traps, and mnemonics for board/university examinations.

        5. ACCURATE MERMAID DIAGRAM (`diagram`):
           - Return valid Mermaid.js graph code (e.g., `graph TD; ...`) that directly models {subtopic_name}'s components, signals, or steps.
           - For Computer Architecture: Diagram the actual hardware/datapath flow (e.g. PC -> IR -> Decoder -> ALU -> Flags -> Bus).
           - Must NOT use generic placeholders like 'Clinical Presentation' on computer science units.

        6. ASSESSMENTS (`quizzes`):
           - 3 to 4 challenging multiple-choice questions testing core concepts.
           - 4 distinct options per question.
           - Explicit `correct_answer` matching one option.
           - Detailed `explanation` breaking down why the answer is correct and why distractors are wrong.

        FORMAT: Return ONLY a valid JSON object matching this schema:
        {{
          "technical_explanation": "Markdown string containing extensive lecture notes...",
          "intuitive_explanation": "Analogous explanation...",
          "clinical_takeaway": "Exam pearl / key takeaway...",
          "diagram": {{
            "diagram_type": "mermaid",
            "diagram_code": "graph TD\\n  A[Step 1] --> B[Step 2]...",
            "diagram_caption": "Descriptive diagram caption"
          }},
          "quizzes": [
            {{
              "question": "Question text...",
              "options": ["Option A", "Option B", "Option C", "Option D"],
              "correct_answer": "Option A",
              "explanation": "Detailed rationale...",
              "difficulty": "Medium",
              "clinical_scenario": "Realistic application scenario..."
            }}
          ]
        }}
        """

        if GEMINI_API_KEYS and self.client and types:
            for variant in self.model_variants:
                for _ in range(len(GEMINI_API_KEYS)):
                    start_time = time.time()
                    current_key_idx = self.key_index % len(GEMINI_API_KEYS)
                    try:
                        config = types.GenerateContentConfig(response_mime_type="application/json")
                        response = self.client.models.generate_content(
                            model=variant,
                            contents=prompt,
                            config=config
                        )
                        if response and response.text:
                            raw_text = response.text.strip()
                            if "```json" in raw_text:
                                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                            elif "```" in raw_text:
                                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                            parsed = json.loads(raw_text)
                            if isinstance(parsed, dict) and "technical_explanation" in parsed:
                                duration = time.time() - start_time
                                self._log_performance(variant, current_key_idx, duration, "SUCCESS", f"Enrichment: {subtopic_name}")
                                parsed["node_name"] = subtopic_name
                                return parsed
                    except Exception as e:
                        duration = time.time() - start_time
                        err_msg = str(e).lower()
                        self._log_performance(variant, current_key_idx, duration, "FAILED", f"Enrichment: {subtopic_name}")
                        if "404" in err_msg:
                            break
                        self._rotate_key()
                        time.sleep(0.5)
                        continue

        # Deterministic domain-aware fallback
        logger.info(f"Using domain-aware fallback enrichment generator for: {subtopic_name}")
        return self._domain_aware_fallback_enrichment(
            unit_name=unit_name,
            topic_name=topic_name,
            subtopic_name=subtopic_name,
            category=category or course_name,
            learning_outcomes=outcomes_list
        )

    def generate_timetable(self, user_info, quiz_history, active_units, recent_chat_titles, previous_timetable=None, study_context=None):
        performance_summary = ""
        for q in quiz_history:
            score_val = getattr(q, 'pnl', None) or getattr(q, 'score', 0)
            unit_name = getattr(q, 'unit_name', 'General')
            performance_summary += f"- {unit_name}: {score_val}% score\n"

        chat_context = ", ".join(recent_chat_titles)

        timetable_continuity = ""
        if previous_timetable:
            timetable_continuity = f"Previous Timetable Context:\n{json.dumps(previous_timetable)}\n"

        detailed_context = ""
        if study_context:
            sc_dict = study_context if isinstance(study_context, dict) else study_context.dict()
            weak = sc_dict.get("weak_topics", [])
            mastered = sc_dict.get("mastered_topics", [])
            pending = sc_dict.get("pending_subtopic_names", [])
            completed = sc_dict.get("completed_subtopic_names", [])
            avg_score = sc_dict.get("average_quiz_score")
            overall_progress = sc_dict.get("overall_progress_percentage")

            detailed_context = f"""
            REAL-TIME STUDENT LEARNING & PERFORMANCE METRICS:
            - Overall Syllabus Completion: {overall_progress if overall_progress is not None else 'N/A'}%
            - Average Assessment Score: {avg_score if avg_score is not None else 'N/A'}%
            - Critical Weak Areas (Assessment accuracy < 70%): {', '.join(weak) if weak else 'None detected yet'}
            - Mastered High-Yield Concepts (Assessment accuracy >= 80%): {', '.join(mastered) if mastered else 'Building mastery'}
            - High-Priority Pending Subtopics: {', '.join(pending[:6]) if pending else 'Follow core syllabus'}
            - Recently Completed Subtopics: {', '.join(completed[:4]) if completed else 'None'}
            """

        prompt = f"""
        Generate a dynamic, hyper-personalized weekly study timetable for {user_info['username']}.
        Current Level: {user_info['semester_status']}
        Active Units: {', '.join(active_units)}

        {detailed_context}

        Performance History:
        {performance_summary if performance_summary else "No assessments taken yet."}

        Recent Consultation Topics:
        {chat_context if chat_context else "No recent consultations."}

        {timetable_continuity}

        CRITICAL REQUIREMENT:
        You MUST generate exactly 3 to 4 sequential study slots/activities per day for EACH day of the week (Monday through Sunday).
        Directly align the slots with the student's real-time metrics:
        1. Schedule morning 'Deep Study' sessions targeting their pending subtopics or foundational concepts.
        2. Schedule afternoon 'Diagnostic Assessment' and 'Targeted Revision' sessions specifically addressing their WEAK topics to convert weaknesses into exam-ready strengths.
        3. Include scheduled mental calibration and synthesis breaks.
        Do NOT just output one task per day. Fill the schedule of each day with 3-4 items.

        Format:
        {{
          "weekly_plan": [
            {{ "day": "Monday", "time": "08:30 - 10:30", "activity": "Deep Study: Core Pathophysiology", "unit": "Biochemistry II", "type": "Study" }},
            {{ "day": "Monday", "time": "11:00 - 12:00", "activity": "Targeted Assessment: Diagnostic Traps", "unit": "General Surgery", "type": "Assessment" }},
            {{ "day": "Monday", "time": "12:00 - 13:00", "activity": "Cognitive Refresh Break", "unit": null, "type": "Break" }},
            {{ "day": "Monday", "time": "14:30 - 16:30", "activity": "Differential Case Study & Revision", "unit": "Internal Medicine", "type": "Revision" }},
            ...
          ],
          "ai_brief": "A customized clinical rationale explaining how this week's plan tackles their specific weak topics and advances their pending subtopics..."
        }}
        """

        response = self.ask(prompt)
        if response:
            try:
                raw_text = response.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()
                return json.loads(raw_text)
            except Exception as e:
                logger.error(f"Failed to parse timetable JSON: {e}")
        return None

    def get_recommendations(self, user_info, quiz_history, active_units, study_context=None):
        history_summary = ""
        for q in quiz_history:
            score_val = getattr(q, 'pnl', None) or getattr(q, 'score', 0)
            unit_name = getattr(q, 'unit_name', 'General')
            history_summary += f"- {unit_name}: {score_val}% score\n"

        detailed_context = ""
        if study_context:
            sc_dict = study_context if isinstance(study_context, dict) else study_context.dict()
            weak = sc_dict.get("weak_topics", [])
            mastered = sc_dict.get("mastered_topics", [])
            pending = sc_dict.get("pending_subtopic_names", [])
            completed = sc_dict.get("completed_subtopic_names", [])
            avg_score = sc_dict.get("average_quiz_score")
            overall_progress = sc_dict.get("overall_progress_percentage")

            detailed_context = f"""
            REAL-TIME LEARNING & QUIZ PERFORMANCE METRICS:
            - Syllabus Progress: {overall_progress if overall_progress is not None else 'N/A'}%
            - Mean Assessment Score: {avg_score if avg_score is not None else 'N/A'}%
            - Verified Mastered Topics: {', '.join(mastered) if mastered else 'Consolidating knowledge'}
            - Critical Weak Areas (Quiz Score < 70%): {', '.join(weak) if weak else 'No acute deficiencies'}
            - Next Pending Subtopics to Unlock: {', '.join(pending[:4]) if pending else 'Syllabus on track'}
            """

        prompt = f"""
        You are Zenith AI, the elite academic mentor and guide for {user_info['username']}.
        Persona: {user_info.get('ai_persona', 'Academic Mentor')}
        Level: {user_info['semester_status']}
        Active Units: {', '.join(active_units)}

        {detailed_context}

        Assessment History:
        {history_summary if history_summary else "No assessments taken yet."}

        INSTRUCTIONS:
        Formulate a punchy, highly motivating, and academically precise 3-sentence Zenith Insight for the student's dashboard.
        1. Sentence 1: Acknowledge their actual learning progress or a topic they demonstrated mastery in.
        2. Sentence 2: Directly call out their weakest area or a critical diagnostic pitfall/mechanism they must review immediately based on their quiz data.
        3. Sentence 3: Prescribe the exact next actionable subtopic they should conquer today.
        Avoid vague platitudes. Speak directly to their real academic data!
        """

        rec = self.ask(prompt)
        if not rec or "AI service is currently unavailable" in rec:
            return "AI service is currently unavailable."
        return rec

ai_service = AiService()


 