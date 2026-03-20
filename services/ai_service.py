import os
import re
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

# Job levels configuration
JOB_LEVELS = {
    "junior": {
        "description": "entry-level positions with 0-2 years experience",
        "focus": "fundamental skills, learning ability, potential, enthusiasm"
    },
    "intermediate": {
        "description": "mid-level positions with 2-5 years experience",
        "focus": "applied skills, project delivery, growing expertise, teamwork"
    },
    "senior": {
        "description": "senior-level positions with 5+ years experience",
        "focus": "leadership, strategic thinking, mentorship, complex problem-solving"
    },
    "lead": {
        "description": "leadership positions with team management responsibilities",
        "focus": "team management, strategic planning, decision making, cross-functional collaboration"
    },
    "manager": {
        "description": "managerial positions with direct reports",
        "focus": "people management, budget oversight, strategic initiatives, stakeholder management"
    }
}


def validate_job_level(level: str) -> str:
    """Validate and normalize job level"""
    level = level.lower().strip() if level else "intermediate"
    if level not in JOB_LEVELS:
        level = "intermediate"
    return level


def generate_questions(cv_text: str, level: str = "intermediate", role: str = "HR") -> List[str]:
    """
    Generate interview questions based on CV and job level.
    
    Args:
        cv_text: The extracted text from the CV
        level: Job level (junior, intermediate, senior, lead, manager)
        role: The role/position being interviewed for
    
    Returns:
        List of 5+ relevant interview questions
    """
    # Validate and normalize level
    level = validate_job_level(level)
    level_info = JOB_LEVELS[level]
    
    # Truncate CV text to avoid token limits
    truncated_cv = cv_text[:3000] if cv_text else ""
    
    if not truncated_cv.strip():
        return get_default_questions(level)
    
    try:
        prompt = f"""Based on this CV, generate 7 relevant interview questions for a {role} position at {level} level ({level_info['description']}).

Focus on: {level_info['focus']}

CV Content:
{truncated_cv}

Generate exactly 7 questions, one per line, numbered 1-7. Each question should be specific to the CV content and appropriate for {level} level.

Questions:"""

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-base",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_length": 600, "temperature": 0.7}}
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                questions_text = result[0].get("generated_text", "")
                # Parse questions from response
                questions = parse_questions(questions_text)
                if len(questions) >= 5:
                    return questions[:7]
        
        # Fallback to contextual questions
        return generate_contextual_questions(cv_text, level, role)
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        return generate_contextual_questions(cv_text, level, role)


def parse_questions(text: str) -> List[str]:
    """Parse questions from generated text"""
    questions = []
    lines = text.split('\n')
    
    for line in lines:
        # Remove numbering and clean
        line = re.sub(r'^\d+[.)]\s*', '', line.strip())
        line = line.strip()
        
        # Check if it looks like a question
        if '?' in line and len(line) > 15:
            questions.append(line)
    
    return questions


def generate_contextual_questions(cv_text: str, level: str, role: str) -> List[str]:
    """Generate contextual questions based on CV content analysis"""
    
    # Analyze CV for key terms
    cv_lower = cv_text.lower()
    
    # Detect technical skills
    tech_skills = []
    skill_keywords = ["python", "java", "javascript", "react", "angular", "vue", "node", "sql", 
                      "docker", "kubernetes", "aws", "azure", "gcp", "git", "agile", "scrum"]
    for skill in skill_keywords:
        if skill in cv_lower:
            tech_skills.append(skill)
    
    # Detect soft skills
    soft_skills = []
    soft_keywords = ["lead", "team", "manage", "mentor", "communicate", "present", "collaborate"]
    for skill in soft_keywords:
        if skill in cv_lower:
            soft_skills.append(skill)
    
    # Detect experience keywords
    has_management = any(kw in cv_lower for kw in ["manage", "lead", "team lead", "head of"])
    has_projects = any(kw in cv_lower for kw in ["project", "deliver", "implement", "develop"])
    has_achievements = any(kw in cv_lower for kw in ["achieved", "increased", "improved", "reduced"])
    
    # Generate contextual questions based on level
    questions = []
    
    # Question 1: Introduction (always)
    if level in ["junior"]:
        questions.append("Can you tell me about yourself and what motivated you to pursue this career path?")
    else:
        questions.append("Can you briefly walk me through your professional background and key experiences?")
    
    # Question 2: Skills and experience (contextual)
    if tech_skills:
        questions.append(f"You mentioned experience with {', '.join(tech_skills[:3])}. Can you describe a project where you applied these skills?")
    else:
        questions.append("What are your strongest technical skills and how have you applied them in your work?")
    
    # Question 3: Problem-solving (based on level)
    if level in ["senior", "lead", "manager"]:
        questions.append("Describe a complex technical or business challenge you faced. How did you approach it and what was the outcome?")
    else:
        questions.append("Describe a challenging problem you encountered in your work or studies. How did you solve it?")
    
    # Question 4: Teamwork/Leadership (based on experience)
    if has_management or level in ["lead", "manager"]:
        questions.append("Can you describe your experience leading a team? What leadership style do you prefer and why?")
    elif has_projects:
        questions.append("Tell me about a successful project you worked on. What was your role and what did you learn?")
    else:
        questions.append("How do you typically work with others to achieve common goals?")
    
    # Question 5: Achievements
    if has_achievements:
        questions.append("What are you most proud of achieving in your career so far?")
    else:
        questions.append("What would you consider your greatest professional achievement?")
    
    # Question 6: Career goals (based on level)
    if level in ["junior"]:
        questions.append("Where do you see yourself in 3-5 years, and how does this position fit into your career goals?")
    else:
        questions.append("What are your career goals for the next few years, and how does this role align with them?")
    
    # Question 7: Role-specific
    questions.append(f"Why are you interested in this {role} position, and what unique value can you bring to our team?")
    
    return questions[:7]


def get_default_questions(level: str = "intermediate") -> List[str]:
    """Get default questions based on level"""
    return [
        "Can you tell me about yourself and your professional background?",
        "What are your main technical skills and how do you apply them in your work?",
        "Describe a challenging project you worked on and how you overcame obstacles.",
        "What are your greatest strengths and areas for improvement?",
        "Tell me about a time when you had to work with a difficult team member or client.",
        "What are your career goals for the next few years?",
        f"Why are you interested in this position and where do you see your career going?"
    ]


def evaluate_answer(answer: str, question: str = "") -> Dict[str, Any]:
    """
    Evaluate an interview answer using AI.
    
    Args:
        answer: The candidate's answer
        question: The question that was asked (optional, for context)
    
    Returns:
        Dictionary with score, sub-scores, and feedback
    """
    if not answer or not answer.strip():
        return {
            "score": 0,
            "fluency": 0,
            "confidence": 0,
            "correctness": 0,
            "feedback": "No answer provided. Please provide a response to the question."
        }
    
    try:
        prompt = f"""Evaluate this interview answer for clarity, confidence, and relevance to the question.

Question: {question if question else "General interview question"}
Answer: {answer[:500]}

Provide your evaluation in this format:
Score: [number 0-100]
Clarity: [1-10]
Confidence: [1-10]
Relevance: [1-10]
Feedback: [2-3 sentences of constructive feedback]
Suggestions: [1-2 specific suggestions for improvement]"""

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-base",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_length": 400}}
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                eval_text = result[0].get("generated_text", "")
                return parse_evaluation(eval_text, answer)
        
        # Fallback to basic evaluation
        return basic_evaluate(answer)
        
    except Exception as e:
        print(f"Error evaluating answer: {e}")
        return basic_evaluate(answer)


def parse_evaluation(eval_text: str, original_answer: str) -> Dict[str, Any]:
    """Parse AI evaluation text into structured scores"""
    
    # Extract scores
    score = 70  # default
    clarity = 7
    confidence = 7
    relevance = 7
    feedback = ""
    suggestions = ""
    
    lines = eval_text.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'score:' in line_lower:
            numbers = re.findall(r'\d+', line)
            if numbers:
                score = min(max(int(numbers[0]), 0), 100)
        elif 'clarity:' in line_lower:
            numbers = re.findall(r'\d+', line)
            if numbers:
                clarity = min(max(int(numbers[0]), 1), 10)
        elif 'confidence:' in line_lower:
            numbers = re.findall(r'\d+', line)
            if numbers:
                confidence = min(max(int(numbers[0]), 1), 10)
        elif 'relevance:' in line_lower:
            numbers = re.findall(r'\d+', line)
            if numbers:
                relevance = min(max(int(numbers[0]), 1), 10)
        elif 'feedback:' in line_lower:
            feedback = line.replace('Feedback:', '').strip()
        elif 'suggestions:' in line_lower:
            suggestions = line.replace('Suggestions:', '').strip()
    
    # If no feedback was extracted, use default
    if not feedback:
        feedback = "Good answer! Consider adding more specific examples."
    
    return {
        "score": score,
        "fluency": min(clarity * 10, 100),
        "confidence": min(confidence * 10, 100),
        "correctness": min(relevance * 10, 100),
        "feedback": feedback,
        "suggestions": suggestions if suggestions else "Try to provide more specific examples from your experience."
    }


def basic_evaluate(answer: str) -> Dict[str, Any]:
    """Basic keyword-based evaluation as fallback"""
    score = 0
    words = answer.split()
    word_count = len(words)

    # Length scoring (ideal answer is 30-150 words)
    if word_count > 150:
        score += 20
    elif word_count > 50:
        score += 30
    elif word_count > 20:
        score += 20
    elif word_count > 10:
        score += 10
    else:
        score += 5

    # Keywords scoring for quality indicators
    quality_keywords = {
        "achievement": ["achieved", "accomplished", "success", "improved", "increased", "reduced"],
        "action": ["led", "managed", "developed", "created", "implemented", "designed"],
        "collaboration": ["team", "collaborated", "shared", "mentored", "supported"],
        "learning": ["learned", "developed", "improved", "grew", "expanded"],
        "challenge": ["challenge", "problem", "issue", "difficult", "obstacle"]
    }
    
    answer_lower = answer.lower()
    
    for category, keywords in quality_keywords.items():
        for keyword in keywords:
            if keyword in answer_lower:
                score += 5
                break

    # Structure scoring
    has_structure = False
    if "." in answer:
        score += 10
        has_structure = True
    if "," in answer:
        score += 5
    if any(word in answer_lower for word in ["first", "second", "finally", "additionally"]):
        score += 10
        has_structure = True
    
    # STAR method indicators
    star_keywords = ["situation", "task", "action", "result", "outcome"]
    star_count = sum(1 for kw in star_keywords if kw in answer_lower)
    if star_count >= 2:
        score += 15

    score = min(score, 100)

    # Determine sub-scores
    confidence = min(score + (10 if word_count > 30 else -10), 100)
    fluency = min(score + (5 if has_structure else -5), 100)
    correctness = min(score + (5 if star_count >= 2 else 0), 100)

    # Generate feedback
    if score >= 80:
        feedback = "Excellent answer! You provided specific details and structured your response well."
    elif score >= 60:
        feedback = "Good answer! Consider adding more specific examples to strengthen your response."
    elif score >= 40:
        feedback = "Decent attempt. Try to provide more concrete examples and structure your answer better."
    else:
        feedback = "Consider expanding your answer with specific examples from your experience."

    return {
        "score": score,
        "fluency": fluency,
        "confidence": confidence,
        "correctness": correctness,
        "feedback": feedback,
        "suggestions": "Use the STAR method (Situation, Task, Action, Result) to structure your answers."
    }


def final_evaluation(answers: List[str], questions: List[str] = None) -> Dict[str, Any]:
    """
    Generate final evaluation report with detailed analysis.
    
    Args:
        answers: List of all candidate answers
        questions: Optional list of questions asked
    
    Returns:
        Dictionary with final report including scores, strengths, improvements, recommendations
    """
    if not answers:
        return {
            "overall_score": 0,
            "average_scores": {"fluency": 0, "confidence": 0, "correctness": 0},
            "strengths": [],
            "areas_for_improvement": [],
            "recommendations": [],
            "detailed_report": "No answers provided."
        }
    
    # Evaluate each answer
    individual_evaluations = []
    total_score = 0
    total_fluency = 0
    total_confidence = 0
    total_correctness = 0
    
    for answer in answers:
        eval_result = evaluate_answer(answer, questions[answers.index(answer)] if questions and len(questions) > answers.index(answer) else "")
        individual_evaluations.append(eval_result)
        total_score += eval_result["score"]
        total_fluency += eval_result["fluency"]
        total_confidence += eval_result["confidence"]
        total_correctness += eval_result["correctness"]
    
    # Calculate averages
    num_answers = len(answers)
    avg_score = round(total_score / num_answers)
    avg_fluency = round(total_fluency / num_answers)
    avg_confidence = round(total_confidence / num_answers)
    avg_correctness = round(total_correctness / num_answers)
    
    # Generate strengths and improvements
    strengths = []
    improvements = []
    recommendations = []
    
    if avg_fluency >= 70:
        strengths.append("Good communication clarity and structure")
    else:
        improvements.append("Work on organizing your thoughts before speaking")
        recommendations.append("Practice the STAR method for better structure")
    
    if avg_confidence >= 70:
        strengths.append("Confident delivery of answers")
    else:
        improvements.append("Show more confidence in your responses")
        recommendations.append("Practice mock interviews to build confidence")
    
    if avg_correctness >= 70:
        strengths.append("Relevant and accurate answers to questions")
    else:
        improvements.append("Focus more on answering what was asked")
        recommendations.append("Take a moment to understand each question fully")
    
    if avg_score >= 80:
        recommendations.append("You're ready for real interviews! Keep practicing to maintain your skills.")
    elif avg_score >= 60:
        recommendations.append("Good progress! Continue practicing with different question types.")
    else:
        recommendations.append("Focus on basics first: structure, examples, and confidence.")
    
    # Build detailed report
    report = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    FINAL INTERVIEW REPORT                        ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  📊 OVERALL SCORE: {avg_score}/100                                    ║
║                                                                  ║
║  📈 SUB-SCORES:                                                  ║
║     • Clarity/Fluency:    {avg_fluency}/100                          ║
║     • Confidence:         {avg_confidence}/100                          ║
║     • Relevance/Accuracy: {avg_correctness}/100                          ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✅ STRENGTHS:                                                  ║"""
    
    for strength in strengths:
        report += f"\n║     • {strength:<54} ║"
    
    report += """
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ⚠️  AREAS FOR IMPROVEMENT:                                      ║"""
    
    for improvement in improvements:
        report += f"\n║     • {improvement:<54} ║"
    
    report += """
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  💡 RECOMMENDATIONS:                                            ║"""
    
    for rec in recommendations:
        report += f"\n║     • {rec:<54} ║"
    
    report += """
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    
    return {
        "overall_score": avg_score,
        "average_scores": {
            "fluency": avg_fluency,
            "confidence": avg_confidence,
            "correctness": avg_correctness
        },
        "individual_scores": [e["score"] for e in individual_evaluations],
        "strengths": strengths,
        "areas_for_improvement": improvements,
        "recommendations": recommendations,
        "detailed_report": report,
        "total_questions": num_answers
    }
