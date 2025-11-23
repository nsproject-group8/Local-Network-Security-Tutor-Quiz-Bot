# 🔌 API Reference

Complete API documentation for the Network Security Tutor & Quiz Bot backend.

**Base URL**: `http://localhost:8000`

## Authentication

Currently, no authentication is required for local development. For production deployment, implement JWT or OAuth2.

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "detail": "Error message here"
}
```

---

## Health & System

### Check System Health
Get the current system status and service availability.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "ollama_available": true,
  "chroma_initialized": true,
  "documents_indexed": 42
}
```

**Status Values**:
- `healthy`: All services operational
- `degraded`: Some services unavailable

---

## Q&A Tutor Agent

### Ask Question
Submit a question to the Q&A tutor agent.

**Endpoint**: `POST /api/qa/ask`

**Request Body**:
```json
{
  "question": "What is a firewall?",
  "include_web_search": false
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | string | Yes | The question to ask |
| include_web_search | boolean | No | Include web search results (default: false) |

**Response**:
```json
{
  "question": "What is a firewall?",
  "answer": "A firewall is a network security device that monitors...",
  "citations": [
    {
      "source": "network_security.pdf",
      "content": "A firewall establishes a barrier...",
      "page": 42,
      "url": null,
      "confidence": 0.92
    }
  ],
  "confidence_score": 0.89,
  "timestamp": "2025-11-19T10:30:45.123Z"
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain DDoS attacks",
    "include_web_search": true
  }'
```

---

## Quiz Agent

### Generate Quiz
Create a new quiz with specified parameters.

**Endpoint**: `POST /api/quiz/generate`

**Request Body**:
```json
{
  "mode": "topic_specific",
  "topic": "Encryption",
  "num_questions": 5,
  "question_types": ["multiple_choice", "true_false", "open_ended"]
}
```

**Parameters**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| mode | string | Yes | "random" or "topic_specific" |
| topic | string | No | Topic name (required for topic_specific) |
| num_questions | integer | No | Number of questions (default: 5, max: 15) |
| question_types | array | No | Question types to include |

**Question Types**:
- `multiple_choice`: 4-option MCQ
- `true_false`: Binary T/F questions
- `open_ended`: Free-form answers

**Response**:
```json
{
  "quiz_id": "550e8400-e29b-41d4-a716-446655440000",
  "questions": [
    {
      "id": "q1-uuid",
      "type": "multiple_choice",
      "question": "What does VPN stand for?",
      "options": [
        "A) Virtual Private Network",
        "B) Very Protected Network",
        "C) Variable Protocol Network",
        "D) Verified Private Node"
      ],
      "correct_answer": "A) Virtual Private Network",
      "topic": "VPN",
      "difficulty": "medium",
      "citation": {
        "source": "networking_basics.pdf",
        "content": "VPN stands for Virtual Private Network...",
        "page": 15,
        "confidence": 0.95
      }
    }
  ],
  "generated_at": "2025-11-19T10:35:00.000Z"
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "random",
    "num_questions": 10,
    "question_types": ["multiple_choice", "true_false"]
  }'
```

### Grade Quiz
Submit quiz answers for grading.

**Endpoint**: `POST /api/quiz/grade?quiz_id={quiz_id}`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| quiz_id | string | Yes | The quiz UUID |

**Request Body**:
```json
[
  {
    "quiz_id": "550e8400-e29b-41d4-a716-446655440000",
    "question_id": "q1-uuid",
    "user_answer": "A) Virtual Private Network"
  },
  {
    "quiz_id": "550e8400-e29b-41d4-a716-446655440000",
    "question_id": "q2-uuid",
    "user_answer": "True"
  }
]
```

**Response**:
```json
{
  "quiz_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_questions": 5,
  "correct_answers": 4,
  "score_percentage": 80.0,
  "grade": "B",
  "feedback": [
    {
      "question_id": "q1-uuid",
      "is_correct": true,
      "user_answer": "A) Virtual Private Network",
      "correct_answer": "A) Virtual Private Network",
      "similarity_score": null,
      "feedback": "Correct! Well done.",
      "citations": [...],
      "grade": "A"
    },
    {
      "question_id": "q2-uuid",
      "is_correct": false,
      "user_answer": "False",
      "correct_answer": "True",
      "similarity_score": null,
      "feedback": "Incorrect. The correct answer is: True",
      "citations": [...],
      "grade": "F"
    }
  ],
  "submitted_at": "2025-11-19T10:40:00.000Z"
}
```

**Example cURL**:
```bash
curl -X POST "http://localhost:8000/api/quiz/grade?quiz_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "quiz_id": "550e8400-e29b-41d4-a716-446655440000",
      "question_id": "q1-uuid",
      "user_answer": "A) Virtual Private Network"
    }
  ]'
```

---

## Document Management

### Upload Document
Upload a single document for indexing.

**Endpoint**: `POST /api/documents/upload`

**Content-Type**: `multipart/form-data`

**Form Data**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | Document file (PDF, DOCX, PPTX, TXT, MD) |

**Supported Formats**:
- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- PowerPoint (`.pptx`)
- Plain Text (`.txt`)
- Markdown (`.md`)

**Max File Size**: 50MB

**Response**:
```json
{
  "message": "Document uploaded and indexed successfully",
  "filename": "network_security_textbook.pdf",
  "chunks_indexed": 156
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@/path/to/document.pdf"
```

**Example Python**:
```python
import requests

with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/documents/upload',
        files=files
    )
    print(response.json())
```

### Ingest Directory
Process all documents from a directory.

**Endpoint**: `POST /api/documents/ingest-directory`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| directory_path | string | No | Path to directory (default: ./data/documents) |

**Response**:
```json
{
  "message": "Directory ingested successfully",
  "directory": "./data/documents",
  "chunks_indexed": 543,
  "total_documents": 1250
}
```

**Example cURL**:
```bash
curl -X POST "http://localhost:8000/api/documents/ingest-directory?directory_path=/path/to/docs"
```

### Get Document Count
Retrieve the total number of indexed document chunks.

**Endpoint**: `GET /api/documents/count`

**Response**:
```json
{
  "total_documents": 1250
}
```

**Example cURL**:
```bash
curl http://localhost:8000/api/documents/count
```

### Clear Documents
Delete all indexed documents (use with caution).

**Endpoint**: `DELETE /api/documents/clear`

**Response**:
```json
{
  "message": "All documents cleared successfully"
}
```

**Example cURL**:
```bash
curl -X DELETE http://localhost:8000/api/documents/clear
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

### Common Error Messages

#### 400 Bad Request
```json
{
  "detail": "Unsupported file type. Allowed: .pdf, .docx, .pptx, .txt, .md"
}
```

#### 404 Not Found
```json
{
  "detail": "Quiz 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Error generating text with Ollama: Connection refused"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented for local development. For production, consider implementing:

- Request rate limits per IP
- Document upload size limits
- Quiz generation frequency limits

---

## WebSocket Support

Currently not implemented. Future versions may include:

- Real-time Q&A streaming
- Live quiz updates
- Progress notifications

---

## Example Integration

### Python Client Example

```python
import requests

class NetworkSecurityTutorClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def ask_question(self, question, include_web=False):
        response = requests.post(
            f"{self.base_url}/api/qa/ask",
            json={
                "question": question,
                "include_web_search": include_web
            }
        )
        return response.json()
    
    def generate_quiz(self, mode="random", topic=None, num=5):
        response = requests.post(
            f"{self.base_url}/api/quiz/generate",
            json={
                "mode": mode,
                "topic": topic,
                "num_questions": num
            }
        )
        return response.json()
    
    def upload_document(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/documents/upload",
                files=files
            )
        return response.json()

# Usage
client = NetworkSecurityTutorClient()
result = client.ask_question("What is encryption?")
print(result['answer'])
```

### JavaScript Client Example

```javascript
class NetworkSecurityTutorClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async askQuestion(question, includeWeb = false) {
    const response = await fetch(`${this.baseUrl}/api/qa/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        include_web_search: includeWeb
      })
    });
    return response.json();
  }

  async generateQuiz(mode = 'random', topic = null, numQuestions = 5) {
    const response = await fetch(`${this.baseUrl}/api/quiz/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode,
        topic,
        num_questions: numQuestions
      })
    });
    return response.json();
  }

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }
}

// Usage
const client = new NetworkSecurityTutorClient();
const result = await client.askQuestion('What is a firewall?');
console.log(result.answer);
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:

**URL**: `http://localhost:8000/docs`

Features:
- Try out endpoints directly
- View request/response schemas
- Download OpenAPI specification
- Test authentication

---

## Best Practices

1. **Document Upload**: Upload documents before using Q&A or Quiz features
2. **Web Search**: Use sparingly to reduce external dependencies
3. **Quiz Generation**: Start with smaller quiz sizes for faster generation
4. **Error Handling**: Always check response status codes
5. **File Validation**: Verify file types before uploading

---

## Support

For issues or questions:
- Check `/health` endpoint first
- Review logs in `logs/app.log`
- Ensure Ollama is running
- Verify ChromaDB is initialized

---

**API Version**: 1.0.0  
**Last Updated**: November 19, 2025
