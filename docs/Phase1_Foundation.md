## PHASE 1: THE ABSOLUTE FOUNDATION
### 1.1 What is Amazon Bedrock? (The 30-Second Version)
text

┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS AI SERVICES LANDSCAPE                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Amazon SageMaker          ← Build/train YOUR OWN models (hard)            │
│        │                                                                    │
│   Amazon Bedrock            ← USE existing models via API (what we want)    │
│        │                                                                    │
│        ├── Bedrock Models       ← Just call Claude, Llama, etc.             │
│        ├── Bedrock Knowledge    ← RAG (Retrieval Augmented Generation)      │
│        ├── Bedrock Agents       ← Original agent builder                    │
│        ├── Bedrock AgentCore    ← NEW: Production-grade agent framework     │
│        └── Bedrock Guardrails   ← Safety & compliance                       │
│                                                                             │
│   Amazon Q                   ← Pre-built AI assistant for specific tasks    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
Why Bedrock over just using OpenAI/Anthropic directly?

Single API for multiple model providers
Built-in enterprise security (VPC, encryption, data residency)
Native AWS integrations (S3, DynamoDB, Lambda, etc.)
No data leaves your AWS account for training
Pay-per-use, no upfront commitment

### 1.2 What is AgentCore Specifically?
text

┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEDROCK AGENTS vs AGENTCORE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   BEDROCK AGENTS (Original)              AGENTCORE (New)                    │
│   ─────────────────────────              ──────────────────                 │
│   • Managed service                      • Framework you deploy             │
│   • AWS console & API only               • Code-first approach              │
│   • Limited customization                • Full control over orchestration  │
│   • Basic observability                  • Deep observability built-in      │
│   • Hard to test locally                 • Local development support        │
│   • Difficult CI/CD                      • Designed for CI/CD               │
│   • "Black box" orchestration            • Transparent execution            │
│                                                                             │
│   USE WHEN:                             USE WHEN:                           │
│   • Quick prototype                      • Production workloads             │
│   • Simple use cases                     • Complex business logic           │
│   • Low traffic                         • High traffic                      │
│   • Don't want to manage infra           • Need full control                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

### 1.3 Prerequisites - What You Need Before Starting
bash

1. AWS Account with proper access
Go to: https://console.aws.amazon.com/
Create account if you don't have one

2. Enable Bedrock Model Access (CRITICAL - models are disabled by default)
Console: Bedrock → Model access → Request access
Enable at minimum:
   - Claude 3.5 Sonnet (primary model)
   - Claude 3 Haiku (fast/cheap model)
   - Claude 3.5 Haiku (newer fast model)

3. Install AWS CLI
Mac: brew install awscli
Windows: Download from https://aws.amazon.com/cli/
Linux: sudo apt install awscli

4. Configure AWS CLI
aws configure
AWS Access Key ID: [your key]
AWS Secret Access Key: [your secret]
Default region: us-east-1 (recommended for Bedrock)
Default output format: json

5. Verify access
aws bedrock list-foundation-models --region us-east-1 --query "modelSummaries[?contains(modelId, 'claude')].modelId"

Should show claude-3-5-sonnet, claude-3-haiku, etc.

6. Install Python 3.10+ and set up environment
python --version  # Should be 3.10+

7. Install Node.js 18+ (needed for CDK later)
node --version   # Should be 18+
npm --version

### 1.4 Create Your Project Structure
bash

### Create the project
mkdir bedrock-agentcore-production
cd bedrock-agentcore-production

### Create the full structure
mkdir -p \
    src/agent \
    src/actions \
    src/evals \
    src/guards \
    src/memory \
    src/utils \
    infrastructure/cdk \
    infrastructure/terraform \
    tests/unit \
    tests/integration \
    tests/evals \
    .github/workflows \
    scripts \
    docs \
    config

### Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
 .venv\Scripts\activate   # Windows

### Create requirements files
touch requirements.txt requirements-dev.txt requirements-prod.txt
Project Structure Explained:

text

bedrock-agentcore-production/
├── src/
│   ├── agent/           # Core agent logic, orchestration
│   ├── actions/         # Tools the aclsgent can call
│   ├── evals/           # Evaluation frameworks
│   ├── guards/          # Guardrails and safety checks
│   ├── memory/          # Conversation memory, context
│   └── utils/           # Shared utilities
├── infrastructure/
│   ├── cdk/             # AWS CDK for infrastructure
│   └── terraform/       # Alternative: Terraform configs
├── tests/
│   ├── unit/            # Fast, isolated tests
│   ├── integration/     # Tests with real AWS services
│   └── evals/           # Agent quality evaluations
├── .github/workflows/   # CI/CD pipelines
├── scripts/             # Deployment, setup scripts
├── docs/                # Documentation
└── config/              # Configuration files