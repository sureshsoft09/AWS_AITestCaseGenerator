# MedAssureAI - Healthcare Test Automation Platform

A sophisticated multi-agent AI system for healthcare test automation, powered by AWS Bedrock Claude 3.7 Sonnet and the Strands framework. The platform features intelligent agents with persistent memory, orchestrated workflows, and compliance-focused test generation.

## 🌟 Features

### Multi-Agent Architecture
- **Orchestrator Agent**: Coordinates specialized agents and manages workflow
- **Reviewer Agent**: Analyzes requirements for ambiguities, duplicates, gaps, and compliance issues
- **Test Generator Agent**: Creates comprehensive test artifacts (epics, features, use cases, test cases)
- **Enhancement Agent**: Refactors and improves existing test cases
- **Migration Agent**: Migrates test cases from Excel files into standardized formats

### AI & Memory
- **AWS Bedrock Claude 3.7 Sonnet**: Advanced language model for intelligent test generation
- **Persistent Memory**: OpenSearch-backed vector memory system using mem0
- **Session Management**: Context-aware conversations across sessions
- **Vector Search**: VECTORSEARCH collection with KNN support

### Compliance & Healthcare Focus
- FDA 21 CFR Part 11
- IEC 62304 (Medical Device Software)
- ISO 13485, ISO 14971
- HIPAA compliance
- GDPR data protection

## 🏗️ Architecture

```
MedAssureAI/
├── agents/                    # Strands-based AI agents
│   ├── orchestrator_agent.py # Main orchestration agent
│   ├── reviewer_agent.py     # Requirements analysis
│   ├── test_generator_agent.py
│   ├── enhance_agent.py
│   └── migrate_agent.py
├── backend/                   # FastAPI backend service
│   ├── api/                  # REST API endpoints
│   ├── services/             # Business logic
│   └── middleware/           # Auth & validation
├── frontend/                  # React + TypeScript UI
│   └── src/
│       ├── components/
│       └── utils/
├── infrastructure/           # IaC & deployment
│   ├── cloudformation/
│   ├── terraform/
│   └── lambda/
└── mcp-servers/             # Model Context Protocol servers
    ├── dynamodb/
    └── jira/
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS Account with Bedrock access
- AWS CLI configured
- OpenSearch Serverless (VECTORSEARCH collection)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sureshsoft09/AWS_AITestCaseGenerator.git
cd AWS_AITestCaseGenerator
```

2. **Set up Python virtual environment**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Install agent dependencies**
```bash
cd agents
pip install -r requirements.txt
```

4. **Configure environment variables**

Create `agents/.env` file:
```env
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-7-sonnet-20250219-v1:0

# OpenSearch Configuration
OPENSEARCH_ENDPOINT=https://your-collection-id.us-east-1.aoss.amazonaws.com
OPENSEARCH_INDEX=medassure_sessions

# mem0 Configuration
MEM0_LLM_PROVIDER=aws_bedrock
MEM0_LLM_MODEL=us.anthropic.claude-3-5-sonnet-20241022-v2:0
MEM0_EMBEDDER_PROVIDER=aws_bedrock
MEM0_EMBEDDER_MODEL=amazon.titan-embed-text-v2:0

# Service Configuration
SERVICE_PORT=8001
LOG_LEVEL=INFO
ENVIRONMENT=development
```

5. **Set up OpenSearch VECTORSEARCH collection**

Run the PowerShell script:
```powershell
.\infrastructure\create_vectorsearch_collection.ps1
```

Or use AWS CLI:
```bash
aws opensearchserverless create-collection \
    --name medassure-agents-memory \
    --type VECTORSEARCH \
    --region us-east-1
```

6. **Create OpenSearch indices**
```bash
cd agents
python create_opensearch_indices.py
```

### Running the Agents Service

```bash
cd agents
python -m agents.orchestrator_agent
```

The service will be available at `http://localhost:8001`

### API Documentation

Access Swagger UI at: `http://localhost:8001/docs`

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Process Query
```bash
POST /processquery
{
  "session_id": "user-session-123",
  "user_query": "Analyze requirements for Patient Information Collection",
  "context": {}
}
```

### Agent Status
```bash
GET /api/agents/status
```

## 🔧 Configuration

### AWS Bedrock Models

Available Claude models with inference profiles:
- `us.anthropic.claude-3-7-sonnet-20250219-v1:0` - Main agent model
- `us.anthropic.claude-3-5-sonnet-20241022-v2:0` - Memory LLM
- `amazon.titan-embed-text-v2:0` - Embeddings for vector search

### OpenSearch Configuration

The platform uses OpenSearch Serverless VECTORSEARCH collection:
- **Type**: VECTORSEARCH (supports KNN)
- **Indices**: `mem0`, `mem0migrations`
- **Vector Dimension**: 1024
- **Method**: HNSW with nmslib engine

## 🧪 Testing

```bash
cd backend
pytest tests/
```

## 📦 Dependencies

### Core Frameworks
- **strands-agents**: 1.19.0 - AI agent framework
- **strands-agents-tools**: 0.2.17 - Agent tools including mem0
- **mem0ai**: 1.0.1 - Memory management
- **FastAPI**: 0.109.0+ - Web framework
- **boto3**: 1.34.0+ - AWS SDK

### Full dependency list
See `agents/requirements.txt` and `backend/requirements.txt`

## 🔐 Security

- AWS IAM authentication for Bedrock and OpenSearch
- Data access policies for OpenSearch collections
- Environment-based configuration
- HIPAA and GDPR compliant data handling

## 📊 Features in Detail

### Memory System
- **Persistent Storage**: Vector embeddings in OpenSearch
- **Contextual Retrieval**: Semantic search across conversation history
- **Session Management**: User-specific memory isolation
- **Auto-summarization**: Key information extraction

### Test Artifact Generation
- **Hierarchical Structure**: Epics → Features → Use Cases → Test Cases
- **Traceability**: Complete requirement-to-test mapping
- **Compliance Tags**: Automatic regulatory standard tagging
- **Template-based**: Consistent formatting across artifacts

### Requirements Analysis
- **Ambiguity Detection**: Vague terms and unclear requirements
- **Gap Analysis**: Missing criteria and edge cases
- **Duplicate Detection**: Redundant requirements identification
- **Compliance Check**: Regulatory standard validation

## 🛠️ Infrastructure

### CloudFormation Templates
- DynamoDB tables for session storage
- OpenSearch Serverless cluster
- AWS Textract pipeline for document processing

### Terraform Modules
- Complete infrastructure as code
- Multi-environment support
- Resource tagging and compliance

## 🔄 CI/CD

### GitHub Actions (Coming Soon)
- Automated testing
- Deployment pipelines
- Security scanning

## 📈 Monitoring & Logging

- Structured JSON logging
- CloudWatch integration
- OpenTelemetry instrumentation
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Strands AI Framework](https://github.com/strands-agents/sdk-python)
- Powered by AWS Bedrock Claude models
- Memory system using [mem0](https://github.com/mem0ai/mem0)

## 📧 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/sureshsoft09/AWS_AITestCaseGenerator/issues)
- Email: sureshsoft09@gmail.com

## 🗺️ Roadmap

- [ ] Frontend deployment
- [ ] JIRA integration for test case management
- [ ] Excel import/export functionality
- [ ] Real-time collaboration features
- [ ] Enhanced compliance reporting
- [ ] Multi-language support
- [ ] Mobile application

---

**Built with ❤️ for Healthcare Test Automation**
