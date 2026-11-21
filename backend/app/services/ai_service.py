
from google import genai
from google.genai import types
import time
import logging
import json
import os
import random
from datetime import datetime
from dotenv import load_dotenv

# Load deployment and local environment files explicitly. Hosted spaces keep
# their injected variables, since load_dotenv does not override existing values.
_env_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
for _env_path in (
    os.path.join(_env_dir, ".env"),
    os.path.join(_env_dir, "app", ".env"),
):
    if os.path.exists(_env_path):
        load_dotenv(_env_path)

logger = logging.getLogger("AI_SERVICE")


def _split_api_keys(value: str | None) -> list[str]:
    if not value:
        return []
    # Values may be supplied by secrets as one key, comma-separated, or
    # semicolon-separated. Ignore whitespace and duplicate entries.
    import re
    return [key for key in (part.strip() for part in re.split(r"[,;\n]", value)) if key]


GEMINI_API_KEYS: list[str] = []

# Support GEMINI_API_KEY, GEMINI_API_KEYS, and numbered GEMINI_API_KEY_1/N.
for env_name in ("GEMINI_API_KEYS", "GEMINI_API_KEY"):
    for key in _split_api_keys(os.getenv(env_name)):
        if key not in GEMINI_API_KEYS:
            GEMINI_API_KEYS.append(key)

i = 1
while True:
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key is None:
        break
    for parsed_key in _split_api_keys(key):
        if parsed_key not in GEMINI_API_KEYS:
            GEMINI_API_KEYS.append(parsed_key)
    i += 1

class AiService:
    def __init__(self):
        self.key_index = 0
        configured_model = os.getenv("GEMINI_MODEL", "").strip()
        self.model_variants = [
            configured_model,
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-flash-latest",
        ] if configured_model else [
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-flash-latest",
        ]
        self.model_variants = list(dict.fromkeys(self.model_variants))
        self.logs = []

        if GEMINI_API_KEYS:
            self._create_client()
        else:
            logger.error("❌ No Gemini API keys found.")

    def _create_client(self):
        key = GEMINI_API_KEYS[self.key_index % len(GEMINI_API_KEYS)]
        self.client = genai.Client(
            api_key=key,
            http_options={"timeout": 30_000},
        )

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
        if not GEMINI_API_KEYS:
            logger.error("GEMINI API key is not configured")
            return None

        task_name = "Chat/General"
        for variant in self.model_variants:
            for key_attempt in range(len(GEMINI_API_KEYS)):
                start_time = time.time()
                current_key_idx = self.key_index % len(GEMINI_API_KEYS)
                try:
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    ) if system_instruction else types.GenerateContentConfig(
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    )

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

                    if "404" in err_msg or "not found" in err_msg or "no longer available" in err_msg:
                        logger.warning(f"Model {variant} is unavailable. Trying next variant...")
                        break

                    if "503" in err_msg or "504" in err_msg or "high demand" in err_msg:
                        logger.warning(f"Model {variant} is temporarily unavailable. Retrying after delay...")
                        time.sleep(2)
                        # A provider 503 is not a key failure. Do not rotate keys for it.
                        continue

                    if "401" in err_msg or "403" in err_msg or "permission" in err_msg or "api key" in err_msg:
                        logger.warning("Gemini rejected the current key. Rotating credentials...")
                        self._rotate_key()
                        time.sleep(1)
                        continue

                    logger.warning(f"Gemini request failed: {str(e)[:240]}")
                    self._rotate_key()
                    time.sleep(1)
                    continue
        logger.error("All configured Gemini models and keys failed")
        return None

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


 