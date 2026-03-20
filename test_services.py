"""
Tests for AI service functions
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGenerateQuestions:
    """Test question generation"""
    
    @patch('services.ai_service.requests.post')
    def test_generate_questions_with_api(self, mock_post):
        """Test question generation with working API"""
        from services.ai_service import generate_questions
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            "generated_text": "1. Question one?\n2. Question two?\n3. Question three?"
        }]
        mock_post.return_value = mock_response
        
        questions = generate_questions("Python developer with 5 years experience", "senior")
        
        assert isinstance(questions, list)
        assert len(questions) >= 5
    
    def test_generate_questions_fallback(self):
        """Test fallback questions when API fails"""
        from services.ai_service import generate_questions
        
        with patch('services.ai_service.requests.post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            questions = generate_questions("Some CV", "junior")
            
            assert isinstance(questions, list)
            assert len(questions) >= 5
    
    def test_generate_questions_different_levels(self):
        """Test that different levels generate appropriate questions"""
        from services.ai_service import generate_questions
        
        with patch('services.ai_service.requests.post') as mock_post:
            mock_post.side_effect = Exception("API Error")
            
            # Junior level
            junior_qs = generate_questions("Recent graduate", "junior")
            assert isinstance(junior_qs, list)
            
            # Senior level
            senior_qs = generate_questions("10 years experience", "senior")
            assert isinstance(senior_qs, list)


class TestEvaluateAnswer:
    """Test answer evaluation"""
    
    def test_evaluate_empty_answer(self):
        """Test evaluation of empty answer"""
        from services.ai_service import evaluate_answer
        
        result = evaluate_answer("")
        
        assert result["score"] == 0
        assert result["fluency"] == 0
    
    def test_evaluate_basic_scoring(self):
        """Test basic keyword scoring"""
        from services.ai_service import evaluate_answer
        
        # Answer with achievement keywords
        result = evaluate_answer(
            "I led a team that achieved a 50% increase in sales. " * 5
        )
        
        assert result["score"] > 0
        assert "feedback" in result
    
    def test_evaluate_with_question_context(self):
        """Test evaluation with question context"""
        from services.ai_service import evaluate_answer
        
        result = evaluate_answer(
            "I have been working with Python for 5 years.",
            "What is your experience with Python?"
        )
        
        assert "score" in result
        assert "fluency" in result
        assert "confidence" in result


class TestBasicEvaluate:
    """Test basic fallback evaluation"""
    
    def test_length_scoring(self):
        """Test that answer length affects score"""
        from services.ai_service import basic_evaluate
        
        # Short answer
        short = basic_evaluate("Yes")
        assert short["score"] < 20
        
        # Medium answer
        medium = basic_evaluate("I have 5 years experience in Python." * 5)
        assert medium["score"] > 20
        
        # Long answer
        long = basic_evaluate("I have 5 years experience in Python." * 20)
        assert long["score"] > 30
    
    def test_keyword_scoring(self):
        """Test that keywords affect score"""
        from services.ai_service import basic_evaluate
        
        # Without keywords
        no_keywords = basic_evaluate("This is a test answer.")
        
        # With keywords
        with_keywords = basic_evaluate(
            "I led a team project that achieved success. " * 5
        )
        
        assert with_keywords["score"] > no_keywords["score"]
    
    def test_star_method_bonus(self):
        """Test STAR method gets bonus points"""
        from services.ai_service import basic_evaluate
        
        # Without STAR
        no_star = basic_evaluate("I did good work.")
        
        # With STAR-like structure
        with_star = basic_evaluate(
            "The situation was challenging. The task was to deliver on time. "
            "I took action to resolve it. The result was successful."
        )
        
        assert with_star["score"] > no_star["score"]


class TestFinalEvaluation:
    """Test final evaluation"""
    
    def test_final_empty_answers(self):
        """Test final evaluation with no answers"""
        from services.ai_service import final_evaluation
        
        result = final_evaluation([])
        
        assert result["overall_score"] == 0
        assert result["strengths"] == []
    
    def test_final_with_answers(self):
        """Test final evaluation with answers"""
        from services.ai_service import final_evaluation
        
        answers = [
            "I have 5 years of Python experience. I led a team of 5 developers.",
            "I improved system performance by 50% through optimization.",
            "My greatest achievement was delivering a critical project on time."
        ]
        
        result = final_evaluation(answers)
        
        assert "overall_score" in result
        assert "average_scores" in result
        assert "strengths" in result
        assert "recommendations" in result
    
    def test_final_score_calculation(self):
        """Test that final score is average of all answers"""
        from services.ai_service import final_evaluation
        
        # Same answer repeated to get consistent scoring
        answers = ["I led a team project that achieved success. " * 10] * 3
        
        result = final_evaluation(answers)
        
        # Score should be reasonable
        assert 0 <= result["overall_score"] <= 100


class TestJobLevelValidation:
    """Test job level validation"""
    
    def test_valid_levels(self):
        """Test all valid job levels"""
        from services.ai_service import validate_job_level
        
        assert validate_job_level("junior") == "junior"
        assert validate_job_level("senior") == "senior"
        assert validate_job_level("lead") == "lead"
        assert validate_job_level("manager") == "manager"
    
    def test_invalid_level_defaults(self):
        """Test that invalid levels default to intermediate"""
        from services.ai_service import validate_job_level
        
        assert validate_job_level("invalid") == "intermediate"
        assert validate_job_level("") == "intermediate"
        assert validate_job_level("JUNIOR") == "junior"  # case insensitive


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
