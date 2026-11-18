import os
import json
import random
import re
import logging
import requests
from django.conf import settings
from .questions_bank import QUESTIONS_BANK, CODING_CHALLENGES, SKILL_KEYWORDS

logger = logging.getLogger(__name__)


def call_gemini_json(prompt: str) -> dict | list | None:
    """
    Call Google Gemini REST API and parse JSON output.
    Uses official generative language endpoint without extra library dependencies.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')
    if not api_key:
        return None

    model = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash') or 'gemini-1.5-flash'
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get('candidates', [])
            if candidates:
                text = candidates[0]['content']['parts'][0]['text']
                # Clean up json markdown ticks if present
                clean = re.sub(r'^```json\s*', '', text.strip(), flags=re.MULTILINE)
                clean = re.sub(r'```$', '', clean.strip(), flags=re.MULTILINE)
                return json.loads(clean.strip())
        else:
            logger.error(f"Gemini API returned status {response.status_code}: {response.text}")
    except Exception as e:
        logger.warning(f"Gemini API call failed: {e}")

    return None


def generate_personalized_questions(resume_data: dict, interview_type: str, difficulty: str, count: int, target_role: str) -> list[dict]:
    """
    Generate questions grounded in the candidate's actual resume.
    Ensures categories match the student's selected interview type and includes automatic coding questions.
    """
    skills = resume_data.get('technical_skills', []) or ['Python', 'Problem Solving']
    projects = resume_data.get('projects', []) or ['Web Application Project']
    langs = resume_data.get('programming_languages', []) or ['Python']

    # Try Gemini AI first if configured
    prompt = f"""You are a senior technical interviewer at a top tech company.
Generate an interview question set tailored strictly to this student candidate's resume:
Target Role: {target_role}
Interview Type: {interview_type} (Allowed categories: technical, coding, hr, project, skill, experience, cross)
Difficulty: {difficulty}
Total Questions Required: {count}

Candidate Resume Profile:
- Technical Skills: {', '.join(skills)}
- Programming Languages: {', '.join(langs)}
- Projects: {', '.join(projects)}
- Education: {', '.join(resume_data.get('education', []))}

Generate exactly {count} questions as a JSON array of objects.
For any programming/coding questions (at least 1 if interview_type is 'coding', 'technical', or 'mixed'), set "is_coding": true, specify "coding_language": "{langs[0].lower() if langs else 'python'}", provide "starter_code", and "test_cases": [{{"input": "...", "expected_output": "..."}}].

JSON Schema:
[
  {{
    "question_number": int,
    "text": "Question statement",
    "category": "technical|coding|hr|project|skill|experience|cross",
    "difficulty": "{difficulty}",
    "is_coding": bool,
    "coding_language": "python|java|cpp|javascript",
    "starter_code": "boilerplate or empty",
    "test_cases": [
      {{"input": "sample_input", "expected_output": "sample_output"}}
    ],
    "model_answer": "Expected ideal solution/explanation"
  }}
]
"""
    ai_questions = call_gemini_json(prompt)
    if isinstance(ai_questions, list) and len(ai_questions) >= count:
        # Validate and return
        results = []
        for i, q in enumerate(ai_questions[:count], start=1):
            q['question_number'] = i
            results.append(q)
        return results

    # ================= Offline / Heuristic Generator Fallback =================
    logger.info("Using grounded offline question bank to synthesize interview questions.")
    generated = []
    used_texts = set()

    # 1. Determine coding questions requirement
    needs_coding = interview_type in ['coding', 'technical', 'mixed']
    coding_count = 1 if count <= 5 else (2 if count <= 10 else 3)
    if interview_type == 'coding':
        coding_count = min(count, len(CODING_CHALLENGES))

    if needs_coding:
        # Select matching coding challenges
        for challenge in CODING_CHALLENGES:
            if len(generated) >= coding_count:
                break
            pref_lang = langs[0].lower() if langs and langs[0].lower() in challenge['starter_codes'] else 'python'
            generated.append({
                'question_number': len(generated) + 1,
                'text': f"Coding Assessment: {challenge['title']}\n{challenge['problem']}",
                'category': 'coding',
                'difficulty': challenge['difficulty'],
                'is_coding': True,
                'coding_language': pref_lang,
                'starter_code': challenge['starter_codes'].get(pref_lang, challenge['starter_codes']['python']),
                'test_cases': challenge['test_cases'],
                'model_answer': challenge['model_answer']
            })
            used_texts.add(challenge['title'])

    # 2. Project questions grounded in candidate's actual projects
    if interview_type in ['project', 'mixed', 'technical']:
        for proj in projects[:2]:
            if len(generated) >= count:
                break
            q_text = f"Can you explain the architecture and key challenges you faced while building your '{proj}' project?"
            if q_text not in used_texts:
                generated.append({
                    'question_number': len(generated) + 1,
                    'text': q_text,
                    'category': 'project',
                    'difficulty': difficulty,
                    'is_coding': False,
                    'coding_language': '',
                    'starter_code': '',
                    'test_cases': [],
                    'model_answer': f"Candidate should explain high-level architecture, database choices, endpoints, error handling, and security of {proj}."
                })
                used_texts.add(q_text)

    # 3. Technical & Skill-based questions grounded in resume skills
    lower_skills = [s.lower() for s in skills]
    for skill_key, bank_qs in QUESTIONS_BANK.items():
        if len(generated) >= count:
            break
        if skill_key in ['hr', 'project_based', 'cross_questions', 'experience_based']:
            continue
        # Check if candidate resume mentioned this skill or keyword
        keywords = SKILL_KEYWORDS.get(skill_key, [skill_key])
        has_skill = any(kw in lower_skills or any(kw in s for s in lower_skills) for kw in keywords)
        if has_skill or interview_type == 'technical':
            for q_text in bank_qs:
                if len(generated) >= count:
                    break
                if q_text not in used_texts:
                    generated.append({
                        'question_number': len(generated) + 1,
                        'text': q_text,
                        'category': 'technical',
                        'difficulty': difficulty,
                        'is_coding': False,
                        'coding_language': '',
                        'starter_code': '',
                        'test_cases': [],
                        'model_answer': f"Technical explanation demonstrating conceptual depth regarding {skill_key}."
                    })
                    used_texts.add(q_text)

    # 4. HR Questions if selected
    if interview_type in ['hr', 'mixed']:
        for q_text in QUESTIONS_BANK.get('hr', []):
            if len(generated) >= count:
                break
            if q_text not in used_texts:
                generated.append({
                    'question_number': len(generated) + 1,
                    'text': q_text,
                    'category': 'hr',
                    'difficulty': 'intermediate',
                    'is_coding': False,
                    'coding_language': '',
                    'starter_code': '',
                    'test_cases': [],
                    'model_answer': "Structured STAR response (Situation, Task, Action, Result) demonstrating professionalism."
                })
                used_texts.add(q_text)

    # 5. Fill remaining quota
    if len(generated) < count:
        all_other = [
            q for cat, q_list in QUESTIONS_BANK.items()
            if cat not in ['coding', 'cross_questions']
            for q in q_list if q not in used_texts
        ]
        random.shuffle(all_other)
        for q_text in all_other:
            if len(generated) >= count:
                break
            generated.append({
                'question_number': len(generated) + 1,
                'text': q_text,
                'category': 'technical',
                'difficulty': difficulty,
                'is_coding': False,
                'coding_language': '',
                'starter_code': '',
                'test_cases': [],
                'model_answer': "Comprehensive technical explanation with clear rationale."
            })
            used_texts.add(q_text)

    # Re-index question numbers
    for i, q in enumerate(generated, start=1):
        q['question_number'] = i

    return generated[:count]


def evaluate_answer_with_ai(question_text: str, category: str, answer_text: str, is_coding: bool = False, code_meta: dict = None) -> dict:
    """
    Evaluate student's oral answer or coding submission on a scale of 0 to 10.
    Returns: score, technical_correctness, relevance, clarity, strengths, weaknesses, improvements, recommended_topics, model_answer, follow_up_question.
    """
    clean_ans = answer_text.strip()
    if not clean_ans or len(clean_ans) < 3:
        return {
            'score': 1.0,
            'technical_correctness': 1.0,
            'relevance': 1.0,
            'clarity': 1.0,
            'strengths': "Attempted the question.",
            'weaknesses': "Answer was too brief or empty.",
            'improvements': "Provide a detailed answer explaining your thought process step by step.",
            'recommended_topics': ["Core Fundamentals", "Communication in Technical Interviews"],
            'model_answer': "A comprehensive answer covering definitions, architecture, and real-world trade-offs.",
            'follow_up_question': "Would you like to elaborate on this concept in more detail?"
        }

    # Try Gemini AI evaluation
    prompt = f"""You are a fair and rigorous technical interview evaluator at a top engineering company.
Evaluate the candidate's answer for the following question:

Question: {question_text}
Category: {category}
Is Coding Question: {is_coding}
Candidate Answer / Code:
{clean_ans}

{f"Execution Results: {json.dumps(code_meta)}" if code_meta else ""}

Evaluate the response strictly and output valid JSON following this schema:
{{
  "score": float between 0.0 and 10.0,
  "technical_correctness": float between 0.0 and 10.0,
  "relevance": float between 0.0 and 10.0,
  "clarity": float between 0.0 and 10.0,
  "strengths": "1-2 sentences highlighting what was answered well",
  "weaknesses": "1-2 sentences identifying omissions, edge cases, or misconceptions",
  "improvements": "1-2 actionable tips to elevate the answer to senior engineering standard",
  "recommended_topics": ["topic1", "topic2"],
  "model_answer": "Ideal concise explanation or implementation",
  "follow_up_question": "A logical follow-up question digging deeper into their response"
}}
"""
    ai_result = call_gemini_json(prompt)
    if isinstance(ai_result, dict) and 'score' in ai_result:
        # Sanitize floats
        ai_result['score'] = max(0.0, min(10.0, float(ai_result.get('score', 5.0))))
        ai_result['technical_correctness'] = max(0.0, min(10.0, float(ai_result.get('technical_correctness', ai_result['score']))))
        ai_result['relevance'] = max(0.0, min(10.0, float(ai_result.get('relevance', ai_result['score']))))
        ai_result['clarity'] = max(0.0, min(10.0, float(ai_result.get('clarity', ai_result['score']))))
        return ai_result

    # ================= Offline Intelligent Heuristic Evaluator =================
    words = clean_ans.split()
    word_count = len(words)

    # Base score estimation based on depth, terminology and structure
    base_score = 5.0
    if word_count > 60:
        base_score += 2.0
    elif word_count > 30:
        base_score += 1.0
    elif word_count < 10:
        base_score -= 2.0

    # Coding check
    if is_coding and code_meta:
        passed = code_meta.get('passed_test_cases', 0)
        total = code_meta.get('total_test_cases', 1)
        if total > 0:
            pass_ratio = passed / total
            base_score = round(pass_ratio * 7.0 + (2.0 if 'def ' in clean_ans or 'public' in clean_ans or 'function' in clean_ans else 0.5), 1)

    # Cap score
    score = max(2.0, min(9.5, base_score))

    strengths = "Good initiative in addressing the key requirements and communicating clearly."
    if word_count > 40:
        strengths = "Structured response with relevant technical vocabulary and clear logic."

    weaknesses = "Could provide deeper mathematical bounds, edge-case analysis, or architectural trade-offs."
    if word_count < 20:
        weaknesses = "Explanation was succinct. Real interviews expect elaboration and examples."

    improvements = "Structure your answer using the STAR method for behavioral questions, or State-Complexity-Tradeoffs for technical questions."
    recommended = ["Algorithm Optimization", "System Architecture", "Best Practices"]

    # Generate context-aware follow-up
    follow_up = "Can you describe a production edge case where this approach might fail or experience performance degradation?"
    if is_coding:
        follow_up = "What is the Big-O Time Complexity and Space Complexity of the solution you wrote, and can it be optimized?"

    return {
        'score': round(score, 1),
        'technical_correctness': round(min(10.0, score + 0.2), 1),
        'relevance': round(min(10.0, score + 0.5), 1),
        'clarity': round(min(10.0, score), 1),
        'strengths': strengths,
        'weaknesses': weaknesses,
        'improvements': improvements,
        'recommended_topics': recommended,
        'model_answer': "An optimal response addresses core principles, provides examples, and outlines time/space trade-offs.",
        'follow_up_question': follow_up
    }


def generate_session_report_summary(session) -> dict:
    """
    Summarize performance across all answers in the session.
    """
    questions = session.questions.all()
    evaluations = [q.answer.evaluation for q in questions if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')]

    if evaluations:
        avg_score = sum(e.score for e in evaluations) / len(evaluations)
    else:
        avg_score = 5.0

    if avg_score >= 8.0:
        readiness = "Placement Ready (Excellent)"
        notes = "Outstanding command of core principles, articulate communication, and solid problem solving ability."
    elif avg_score >= 6.5:
        readiness = "Placement Ready (Good)"
        notes = "Strong foundational knowledge with room for polish in deeper architectural trade-offs and edge case handling."
    elif avg_score >= 5.0:
        readiness = "Needs Polish"
        notes = "Demonstrates good effort and basic familiarity. Needs more practice explaining complex systems and optimizing coding solutions."
    else:
        readiness = "Foundational Training Needed"
        notes = "Focus on data structures, algorithmic complexity, and structured communication frameworks."

    strengths = [e.strengths for e in evaluations if e.strengths][:3]
    weaknesses = [e.weaknesses for e in evaluations if e.weaknesses][:3]
    recommendations = []
    for e in evaluations:
        if isinstance(e.recommended_topics, list):
            recommendations.extend(e.recommended_topics)
    recommendations = list(dict.fromkeys(recommendations))[:5] or ["DSA Review", "System Design", "Mock Interviews"]

    return {
        'readiness': readiness,
        'summary_notes': notes,
        'strengths_summary': " | ".join(strengths) if strengths else "Consistent participation and clear intent.",
        'weaknesses_summary': " | ".join(weaknesses) if weaknesses else "Deepen coverage of production constraints.",
        'key_recommendations': recommendations
    }
