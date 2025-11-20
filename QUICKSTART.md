# 🚀 Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 18+
- Ollama

## Installation

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Start Ollama
ollama serve

# In another terminal, pull the model
ollama pull llama3.2:3b
```

### 2. Run Setup Script

```bash
./setup.sh
```

This will:
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Create necessary directories
- ✅ Create sample document
- ✅ Set up configuration

## Running the Application

### Option 1: Use Start Script (Recommended)

```bash
./start.sh
```

This starts both backend and frontend automatically!

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## First Steps

1. **Upload Documents** (Documents tab)
   - Upload your network security PDFs, slides, or textbooks
   - Or use the sample document created during setup

2. **Ask Questions** (Q&A Tutor tab)
   - Try: "What is a firewall?"
   - Try: "Explain DDoS attacks"

3. **Take a Quiz** (Quiz tab)
   - Generate a random quiz
   - Or create a topic-specific quiz on "Encryption"

## Testing the System

### Check Health
```bash
curl http://localhost:8000/health
```

### Test Q&A
```bash
curl -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is encryption?", "include_web_search": false}'
```

### Upload Document via CLI
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@data/documents/your-file.pdf"
```

## Troubleshooting

### Ollama not available
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Backend errors
```bash
# Check logs
tail -f logs/app.log

# Check if port 8000 is available
lsof -i :8000
```

### Frontend not connecting
- Verify backend is running: http://localhost:8000/health
- Check browser console for errors
- Try clearing browser cache

## Sample Questions to Try

- What is a VPN and how does it work?
- Explain the difference between symmetric and asymmetric encryption
- What are the main types of DDoS attacks?
- How does an Intrusion Detection System work?
- What is the OSI model?

## Next Steps

- 📚 Upload more documents for better responses
- 🎯 Try different quiz configurations
- 🔍 Enable web search for additional context
- 📊 Check the dashboard for system status

## Need Help?

- Check the full README.md for detailed documentation
- View API documentation at http://localhost:8000/docs
- Check logs in the `logs/` directory

---

**Happy Learning! 🎓**
