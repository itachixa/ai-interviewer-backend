# AI Interviewer - Backend

Backend API for the AI Interviewer application. Provides CV parsing, question generation, and answer evaluation.

## Features

- **CV Upload & Parsing**: Upload PDF CVs and extract text content securely
- **Dynamic Question Generation**: Generate personalized interview questions based on CV content and job level
- **Answer Evaluation**: Real-time feedback with scores and suggestions
- **Final Report**: Comprehensive evaluation with strengths, improvements, and recommendations

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Navigate to the backend directory:
   ```bash
   cd ai-interviewer-backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` and add your HuggingFace API token:
   ```
   HF_TOKEN=your_huggingface_token_here
   ```
   
   Get your token from: https://huggingface.co/settings/tokens

### Running the Server

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Detailed health status |
| POST | `/upload-cv` | Upload and parse CV PDF |
| POST | `/questions` | Generate interview questions |
| POST | `/evaluate` | Evaluate a single answer |
| POST | `/final` | Generate final evaluation report |

## Job Levels

The system supports these job levels for question generation:

- `junior`: Entry-level (0-2 years experience)
- `intermediate`: Mid-level (2-5 years experience)
- `senior`: Senior-level (5+ years experience)
- `lead`: Leadership position
- `manager`: Managerial position

## Security

- **File Upload Limits**: Maximum 10MB, 100 pages
- **Temporary File Cleanup**: Files are automatically deleted after processing
- **Environment Variables**: API tokens are stored in `.env` file (never committed)

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Project Structure

```
ai-interviewer-backend/
├── main.py                 # FastAPI application
├── services/
│   ├── ai_service.py       # AI-powered question generation & evaluation
│   └── pdf_parser.py       # PDF text extraction
├── routes/                 # API route modules (deprecated - integrated in main.py)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── .gitignore            # Git ignore rules
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid input)
- `500`: Server error

Error responses include a `detail` field with the error message.

## License

MIT
