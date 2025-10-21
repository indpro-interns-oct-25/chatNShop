# 🤖 Intent Classification Backend - Setup Guide

A hybrid rule-based + LLM intent classification system for chatNShop.

## 🚀 Quick Start

### Service Architecture
The system uses multiple services for optimal performance:
- **Qdrant**: Vector database for semantic similarity search
- **Redis**: Caching and message queues  
- **PostgreSQL**: Primary data storage
- **FastAPI**: Main application server

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git
- Docker & Docker Compose (for services)
- Redis (for caching and queues)
- PostgreSQL (for data storage)
- Qdrant (for vector database/embeddings)

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd chatNShop-1

# Create virtual environment if python is not working
# Use the specified version eg: python3 -m venv venv 
python -m venv venv

# Activate virtual environment
# Windows (Git Bash):
source venv/Scripts/activate
# Windows (CMD):
venv\Scripts\activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
# Upgrade pip and install build tools first
python -m pip install --upgrade pip setuptools wheel

# Install core packages (recommended for Windows)
pip install fastapi uvicorn[standard] pydantic python-dotenv

# For mac 
# Install core packages (recommended for Windows)
pip install fastapi "uvicorn[standard]" pydantic python-dotenv

# Install all packages (if no issues)
pip install -r requirements.txt
```

> **Windows Note**: If you encounter build errors, install packages individually starting with the core ones above.

### 3. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
# At minimum, set:
# - OPENAI_API_KEY=your-openai-key
# - DATABASE_URL=your-postgres-url
# - REDIS_URL=your-redis-url
# - QDRANT_API_KEY=your-qdrant-key
```

### 4. Start Services
```bash
# Start Qdrant vector database
docker-compose up -d qdrant

# Or start all services
docker-compose up -d

# Verify Qdrant is running
curl http://localhost:6333/collections
```

### 5. Run the Application
```bash
# Make sure virtual environment is activated first!
source venv/Scripts/activate  # Windows Git Bash
# or: venv\Scripts\activate   # Windows CMD

# Development mode (with auto-reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Alternative if uvicorn command not found
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## 📁 Project Structure

```
app/
├── ai/                          # AI modules
│   ├── intent_classification/   # Rule-based classification
│   └── llm_intent/             # LLM-based classification
├── api/v1/                     # API endpoints
├── services/                   # Business logic
├── models/                     # Data models
├── schemas/                    # Pydantic schemas
├── core/                       # Core utilities
└── main.py                     # FastAPI application
```

## 🛠️ Common Commands

Here are the essential commands for development:

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest -v

# Format code
black app/ tests/ && isort app/ tests/

# Lint code
flake8 app/ && mypy app/

# Start services
docker-compose up -d

# Stop services
docker-compose down
```

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest -v --cov=app --cov-report=html --cov-report=term

# Run specific test modules
pytest tests/test_ai/ -v                           # AI-specific tests
pytest tests/test_ai/test_intent_classification/ -v # Intent classification tests
```

## 📊 Key Features

### 🎯 Intent Classification
- **Rule-based**: Fast keyword and pattern matching
- **LLM-powered**: OpenAI GPT for complex queries
- **Hybrid mode**: Best of both worlds

### 🔄 Processing Pipeline
- Ambiguity resolution
- Confidence scoring
- Fallback mechanisms
- Entity extraction
- Vector similarity search (Qdrant)

### 🗂️ Vector Database
- **Qdrant**: High-performance vector search
- **Embeddings**: Semantic similarity matching
- **Collections**: Organized intent embeddings
- **Real-time**: Fast similarity queries

### 📈 Monitoring & Analytics
- Cost tracking for OpenAI usage
- Performance metrics
- A/B testing capabilities
- Feedback collection

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# API Settings
APP_NAME=Intent Classification API
DEBUG=true
LOG_LEVEL=info

# AI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Database & Cache
DATABASE_URL=postgresql://user:pass@localhost:5432/intentdb
REDIS_URL=redis://localhost:6379/0

# Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=qdrant-secret-key
QDRANT_COLLECTION_NAME=intent_embeddings

# Classification Settings
MIN_CONFIDENCE_THRESHOLD=0.7
ENABLE_HYBRID_MODE=true
```

### Classification Modes

1. **Rule-based only**: Fast, deterministic
2. **LLM only**: Flexible, context-aware
3. **Hybrid**: Rule-based first, LLM fallback

## 🏗️ Development Workflow

### 1. Feature Development
```bash
git checkout -b feature/your-feature
# Make changes
pytest -v                    # Run tests
flake8 app/ && mypy app/    # Lint code
git commit -m "Add your feature"
```

### 2. Adding New Intents
1. Update `app/ai/intent_classification/intents.py`
2. Add keywords to `app/ai/intent_classification/keywords/`
3. Update LLM prompts if needed
4. Add tests

### 3. Code Quality
```bash
black app/ tests/ && isort app/ tests/    # Auto-format code
flake8 app/ && mypy app/                   # Check code quality
pytest -v --cov=app --cov-report=html     # Ensure test coverage
```

## 🚀 Deployment

### Production Setup
```bash
# Start all services
docker-compose up -d

# Set production environment
export DEBUG=false
export LOG_LEVEL=warning

# Run with multiple workers
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Docker Services
```bash
# Start all services (Qdrant, Redis, PostgreSQL)
docker-compose up -d

# Start only Qdrant
docker-compose up -d qdrant

# View service logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Docker Application (Optional)
```bash
# Build Docker image
docker build -t intent-classification-api .

# Run Docker container
docker run -p 8000:8000 --env-file .env intent-classification-api
```

## 📚 API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints
- `POST /api/v1/intent/classify` - Classify user intent
- `POST /api/v1/feedback` - Submit classification feedback
- `GET /api/v1/analytics` - View classification metrics
- `GET /health` - Health check

## 🔍 Troubleshooting

### Common Issues

**1. Virtual Environment Issues**
```bash
# Ensure virtual environment is activated
source venv/Scripts/activate  # Windows Git Bash
venv\Scripts\activate         # Windows CMD
source venv/bin/activate      # Linux/Mac

# If activation fails, recreate the environment
rm -rf venv                   # Delete old environment
python -m venv venv           # Create new one
```

**2. Package Installation Errors**
```bash
# Install build tools first
python -m pip install --upgrade pip setuptools wheel

# Install packages individually if requirements.txt fails
pip install fastapi uvicorn[standard] pydantic python-dotenv

# For Windows-specific build issues
pip install --only-binary=all <package-name>
```

**3. uvicorn Command Not Found**
```bash
# Use python module syntax instead
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or check if virtual environment is activated
which python  # Should point to venv/Scripts/python
```

**2. Services Not Running**
```bash
# Start all services
docker-compose up -d

# Check individual services
docker-compose ps
```

**3. Database Connection**
```bash
# Check PostgreSQL is running
# Verify DATABASE_URL in .env
```

**4. Redis Connection**
```bash
# Check Redis is running
redis-cli ping  # Should return PONG
```

**5. Qdrant Connection**
```bash
# Check Qdrant is running
curl http://localhost:6333/collections
# Or check service status
docker-compose ps qdrant
```

**6. OpenAI API Issues**
```bash
# Verify OPENAI_API_KEY in .env
# Check API quota and billing
```

**7. Vector Database Issues**
```bash
# Restart Qdrant
docker-compose stop qdrant
docker-compose up -d qdrant

# Check Qdrant logs
docker-compose logs qdrant
```

### Debug Mode
```bash
# Run with debug logging
LOG_LEVEL=debug uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Make changes and add tests
4. Ensure all tests pass: `pytest -v`
5. Format code: `black app/ tests/ && isort app/ tests/`
6. Submit a pull request

## 📞 Support

For questions or issues:
1. Check this README
2. Look at API docs: `/docs`
3. Review logs for errors
4. Contact the development team

## 🏁 Complete Development Workflow

### New Developer Setup
```bash
# 1. Clone and setup Python environment
git clone <repo-url>
cd chatNShop-1
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env  # Creates .env from .env.example
# Edit .env with your actual API keys

# 4. Start all services
docker-compose up -d

# 5. Run the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Daily Development
```bash
# Start your day
source venv/Scripts/activate                     # Activate virtual environment
docker-compose up -d                             # Start Qdrant, Redis, etc.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Start API server

# During development
pytest -v                                        # Run tests
black app/ tests/ && isort app/ tests/          # Format code
flake8 app/ && mypy app/                        # Check code quality

# End of day
docker-compose down                              # Stop all services
```

### Service Management
```bash
# All services
docker-compose up -d     # Start all
docker-compose down      # Stop all  
docker-compose logs -f   # View logs

# Individual services
docker-compose up -d qdrant  # Just vector database
docker-compose ps            # Check status
```

---

**Happy coding! 🎉**