import os
import requests
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

def generate_questions(cv_text, level="easy", role="HR"):
    """Generate interview questions based on CV using HuggingFace"""
    try:
        # Use a smaller, faster model for question generation
        prompt = f"""Based on this CV, generate 5 relevant interview questions for a {role} position at {level} level.

CV Content:
{cv_text[:2000]}

Generate exactly 5 questions, one per line, focused on:
- Skills and experience
- Problem-solving abilities
- Teamwork and communication
- Specific achievements
- Career goals

Questions:"""

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-base",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_length": 500}}
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                questions_text = result[0].get("generated_text", "")
                # Parse questions from response
                questions = [q.strip() for q in questions_text.split("\n") if q.strip() and "?" in q]
                if len(questions) >= 5:
                    return questions[:5]
        
        # Fallback to default questions if API fails
        return [
            "Tell me about yourself and your professional background.",
            "What are your main technical skills and how do you apply them?",
            "Describe a challenging project you worked on and how you overcame obstacles.",
            "What are your greatest strengths and areas for improvement?",
            "Why are you interested in this position and where do you see your career going?"
        ]
    except Exception as e:
        print(f"Error generating questions: {e}")
        return [
            "Tell me about yourself and your professional background.",
            "What are your main technical skills and how do you apply them?",
            "Describe a challenging project you worked on and how you overcame obstacles.",
            "What are your greatest strengths and areas for improvement?",
            "Why are you interested in this position and where do you see your career going?"
        ]


def evaluate_answer(answer):
    """Evaluate an interview answer using AI"""
    try:
        prompt = f"""Evaluate this interview answer and provide:
1. A score from 0-100
2. Feedback on clarity, confidence, and relevance
3. Suggestions for improvement

Answer: {answer}

Provide your evaluation in this format:
Score: [number]
Feedback: [your feedback]
Suggestions: [suggestions]"""

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-base",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_length": 300}}
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                eval_text = result[0].get("generated_text", "")
                # Try to extract score from response
                try:
                    score_line = [line for line in eval_text.split("\n") if "Score:" in line]
                    if score_line:
                        score = int(''.join(filter(str.isdigit, score_line[0])))
                        score = min(max(score, 0), 100)
                    else:
                        score = 70  # default
                except:
                    score = 70
                
                return {
                    "score": score,
                    "fluency": min(score + 10, 100),
                    "confidence": min(score + 5, 100),
                    "correctness": min(score + 8, 100),
                    "feedback": eval_text[:200] if eval_text else "Good answer! Try to provide more specific examples."
                }
        
        # Fallback to basic evaluation
        return basic_evaluate(answer)
    except Exception as e:
        print(f"Error evaluating answer: {e}")
        return basic_evaluate(answer)


def basic_evaluate(answer):
    """Basic keyword-based evaluation as fallback"""
    score = 0
    words = answer.split()

    # Length scoring
    if len(words) > 20:
        score += 30
    elif len(words) > 10:
        score += 20
    else:
        score += 10

    # Keywords scoring
    keywords = ["experience", "project", "team", "skill", "problem", "achievement", "learned", "challenge"]
    for word in keywords:
        if word.lower() in answer.lower():
            score += 8

    # Structure scoring
    if "." in answer:
        score += 15
    if "," in answer:
        score += 5

    score = min(score, 100)

    return {
        "score": score,
        "fluency": min(score + 10, 100),
        "confidence": min(score + 5, 100),
        "correctness": min(score + 8, 100),
        "feedback": "Good answer! 👍 Try adding more specific examples from your experience."
    }


def final_evaluation(answers):
    """Generate final evaluation report"""
    try:
        answers_text = "\n".join([f"Q{i+1}: {a[:200]}" for i, a in enumerate(answers)])
        
        prompt = f"""Based on these interview answers, provide:
1. An overall score (0-100)
2. Strengths
3. Areas for improvement
4. Final recommendations

Answers:
{answers_text}

Evaluation:"""

        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-base",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json={"inputs": prompt, "parameters": {"max_length": 400}}
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
        
        # Fallback to basic evaluation
        return basic_final_evaluation(answers)
    except Exception as e:
        print(f"Error in final evaluation: {e}")
        return basic_final_evaluation(answers)


def basic_final_evaluation(answers):
    """Basic final evaluation as fallback"""
    avg = sum([basic_evaluate(a)["score"] for a in answers]) / len(answers) if answers else 0
    
    return f"""
📊 FINAL INTERVIEW REPORT

Overall Score: {int(avg)}/100

✅ Strengths:
- Demonstrated communication skills
- Provided relevant answers
- Showed engagement with questions

⚠️ Areas for Improvement:
- Add more specific examples
- Use the STAR method for behavioral questions
- Elaborate more on technical details

💡 Recommendations:
- Practice with mock interviews
- Prepare more specific stories from your experience
- Research common interview questions for your role
"""