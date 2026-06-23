# 🤖 Bedrock AgentCore: Production-Ready AI Agent

A robust, enterprise-grade AI Agent built on AWS Bedrock, designed to demonstrate production best practices for agentic workflows. This project moves beyond basic LLM wrappers to implement a complete software engineering lifecycle: Infrastructure as Code, multi-layer guardrails, automated LLM evaluations, and CI/CD pipelines.

> **Note:** This agent uses the AWS Bedrock Converse API, making it completely model-agnostic. While currently configured to run on Z.AI GLM 4.7 Flash, it can be swapped to Amazon Nova, Claude, or Llama with zero changes to the core orchestration logic.

## 🏗️ Architecture & Key Features

### The Agent Loop

Instead of a single prompt-response, this agent utilizes a Think -> Plan -> Act -> Observe loop to interact with external tools safely.

```text
User Input -> [Input Guardrails] -> LLM Think -> Tool Call -> Execute Tool -> LLM Observe -> [Output Guardrails] -> Response
                                            ^                                                             |
                                            |_____________________________________________________________|
                                                              (Repeats until task is complete)

```

### Defense in Depth (Guardrails)
Security isn't just a system prompt; it's enforced at multiple levels:

Input Guards: Regex-based Prompt Injection blocking, SQL injection detection, and PII redaction (Emails, SSNs).
Bedrock Native Guardrails: AWS managed content filters.
Output Guards: System prompt leak prevention and output length truncation.

### Production CI/CD Pipeline
Automated quality gates ensure the agent never regresses:

Lint & Format: black and flake8 enforce clean code.
Unit Tests: Fast, isolated tests for memory limits, math logic, and guardrails using pytest.
Agent Evals: The pipeline spins up AWS resources and runs the agent against a test suite (e.g., "Does it use the weather tool when asked?", "Does it refuse prompt injections?"), failing the build if accuracy drops below 80%.
GitFlow Deployment: Merging to develop triggers a staging deployment via AWS CDK. Merging to main triggers production.

## 🛠️ Tech Stack
| Component | Technology |
| :--- | :--- |
| **Runtime** | Python 3.11 |
| **LLM Orchestration** | AWS Bedrock Converse API (`zai.glm-4.7-flash`) |
| **Tools** | Custom Python classes mapped to Bedrock toolConfig standard |
| **Infrastructure** | AWS CDK (Lambda, API Gateway, DynamoDB, CloudWatch, SNS) |
| **CI/CD** | GitHub Actions |
| **Testing / Evals** | `pytest`, `pytest-cov` |

## 🚀 Local Setup
### Prerequisites
```
Python 3.11+
An AWS Account with Bedrock access
AWS CLI configured locally (aws configure)
```

### 1. Clone and Setup
```
git clone https://github.com/YOUR_USERNAME/bedrock-agentcore-production.git
cd bedrock-agentcore-production
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Enable Bedrock Model Access
```
Go to the AWS Bedrock Console -> Model Access and request access to GLM 4.7 Flash.
```

### 3. Run the Agent
```
python src/main.py
Try asking: "What's the weather in Tokyo?" or "Calculate 15% of 150".
```

### 4. Run Evaluations
Test the agent's decision-making skills locally:
```
python scripts/run_evals.py
```

## 📁 Project Structure
Understanding this structure is key to understanding production AI engineering:
```
├── .github/workflows/     # GitHub Actions CI/CD pipelines
├── infrastructure/cdk/     # AWS CDK code (Lambda, API GW, DynamoDB, Alarms)
├── scripts/                # Execution scripts (eval runner)
├── src/
│   ├── actions/            # Tools the agent can use (Calculator, Weather, DB)
│   │   └── base.py         # BaseTool class enforcing Bedrock toolConfig schema
│   ├── agent/              
│   │   ├── agentcore.py    # THE BRAIN: The Converse API Think/Act/Observe loop
│   │   └── streaming_agent.py # Streaming variant using ConverseStream API
│   ├── evals/              
│   │   ├── framework.py    # Custom evaluation engine (pass/fail/scoring)
│   │   └── test_suites.py  # Test cases for tool selection, safety, and accuracy
│   ├── guards/             # Input/Output security layers
│   ├── memory/             # Conversation history management (local & DynamoDB)
│   ├── utils/              # Bedrock client wrapper, Structured Logger, Metrics
│   ├── handler_production.py # AWS Lambda entry point integrating all guards
│   └── main.py             # Local interactive testing script
└── tests/
    └── unit/               # Fast tests for memory, math, and guardrails
```
## 🔄 CI/CD Branch Strategy
This repository uses a simplified GitFlow pattern managed by GitHub Actions:
| Branch | Triggered Actions | Deploy Target |
| :--- | :--- | :--- |
| `main` | Lint, Unit Tests, Agent Evals | Production (via CDK) |
| `develop` | Lint, Unit Tests, Agent Evals, Deploy | Dev/Staging (via CDK) |
| `feature/*` (PRs) | Lint, Unit Tests, Agent Evals | None (Skipped) |

## 📈 Future Roadmap
```
 Add RAG (Retrieval Augmented Generation) using Bedrock Knowledge Bases
 Implement streaming responses in the local main.py UI
 Add Langfuse or Arize Phoenix for deep LLM observability and tracing
 Increase unit test coverage to >80%
```
 
## 📝 License
This project is for educational and portfolio demonstration purposes.
