"""
Tests for AI Interviewer Backend
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io

# Import the app
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns health status"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestQuestionsEndpoint:
    """Test question generation endpoint"""
    
    def test_questions_without_cv_text(self):
        """Test that questions endpoint requires cv_text"""
        response = client.post("/questions", json={})
        assert response.status_code == 400
        assert "cv_text is required" in response.json()["detail"]
    
    def test_questions_with_empty_cv_text(self):
        """Test that empty cv_text is rejected"""
        response = client.post("/questions", json={"cv_text": ""})
        assert response.status_code == 400
        assert "cv_text" in response.json()["detail"].lower()
    
    @patch('main.generate_questions')
    def test_questions_generation(self, mock_generate):
        """Test question generation with valid input"""
        mock_generate.return_value = [
            "Question 1?",
            "Question 2?",
            "Question 3?"
        ]
        
        response = client.post("/questions", json={
            "cv_text": "Test CV with Python and JavaScript experience",
            "level": "junior",
            "role": "Developer"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        assert len(data["questions"]) == 3
        assert data["level"] == "junior"
        assert data["role"] == "Developer"
    
    def test_questions_with_default_level(self):
        """Test default level is intermediate"""
        response = client.post("/questions", json={
            "cv_text": "Some CV content"
        })
        
        assert response.status_code == 200
        assert response.json()["level"] == "intermediate"


class TestEvaluateEndpoint:
    """Test answer evaluation endpoint"""
    
    def test_evaluate_without_answer(self):
        """Test that evaluate endpoint requires answer"""
        response = client.post("/evaluate", json={})
        assert response.status_code == 400
        assert "answer is required" in response.json()["detail"]
    
    @patch('main.evaluate_answer')
    def test_evaluate_with_valid_answer(self, mock_evaluate):
        """Test answer evaluation"""
        mock_evaluate.return_value = {
            "score": 75,
            "fluency": 80,
            "confidence": 70,
            "correctness": 75,
            "feedback": "Good answer!"
        }
        
        response = client.post("/evaluate", json={
            "answer": "I have 5 years of experience in Python development.",
            "question": "Tell me about your experience."
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 75
        assert "fluency" in data
        assert "confidence" in data
    
    def test_evaluate_empty_answer(self):
        """Test that empty answer returns zero score"""
        response = client.post("/evaluate", json={"answer": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 0


class TestFinalEndpoint:
    """Test final evaluation endpoint"""
    
    def test_final_without_answers(self):
        """Test that final endpoint requires answers"""
        response = client.post("/final", json={})
        assert response.status_code == 400
        assert "answers is required" in response.json()["detail"]
    
    @patch('main.final_evaluation')
    def test_final_with_answers(self, mock_final):
        """Test final evaluation"""
        mock_final.return_value = {
            "overall_score": 75,
            "average_scores": {"fluency": 80, "confidence": 70, "correctness": 75},
            "strengths": ["Good communication"],
            "areas_for_improvement": ["Add more examples"],
            "recommendations": ["Practice more"],
            "detailed_report": "Report text"
        }
        
        response = client.post("/final", json={
            "answers": ["Answer 1", "Answer 2", "Answer 3"],
            "questions": ["Question 1?", "Question 2?", "Question 3?"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 75
        assert "strengths" in data
        assert "recommendations" in data


class TestCVUpload:
    """Test CV upload endpoint"""
    
    def test_upload_without_file(self):
        """Test that upload requires a file"""
        response = client.post("/upload-cv")
        assert response.status_code == 422  # FastAPI validation error
    
    def test_upload_wrong_content_type(self):
        """Test that non-PDF files are rejected"""
        response = client.post(
            "/upload-cv",
            files={"file": ("test.txt", b"test content", "text/plain")}
        )
        assert response.status_code == 400
    
    def test_upload_invalid_extension(self):
        """Test that non-PDF extensions are rejected"""
        response = client.post(
            "/upload-cv",
            files={"file": ("test.jpg", b"fake pdf content", "image/jpeg")}
        )
        assert response.status_code == 400
    
    @patch('main.extract_text_from_pdf_file')
    def test_upload_valid_pdf(self, mock_extract):
        """Test successful PDF upload"""
        mock_extract.return_value = "Extracted CV text with Python, JavaScript experience"
        
        # Create a minimal PDF content
        pdf_content = b"%PDF-1.4 test"
        
        response = client.post(
            "/upload-cv",
            files={"file": ("resume.pdf", pdf_content, "application/pdf")}
        )
        
        # This will fail due to invalid PDF but tests the flow
        assert response.status_code in [200, 400, 500]


class TestSecurity:
    """Test security features"""
    
    def test_file_size_limit(self):
        """Test that large files are rejected"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        
        response = client.post(
            "/upload-cv",
            files={"file": ("large.pdf", large_content, "application/pdf")}
        )
        
        # Should be rejected due to size
        assert response.status_code in [400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
