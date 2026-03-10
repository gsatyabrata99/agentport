# AgentPort

**Build AI agents visually. Deploy them anywhere — your infrastructure, your compliance.**

AgentPort is a no-code agent builder that compiles to portable, self-contained AI agents you deploy to your own infrastructure. No vendor lock-in. No data leaving your environment.

---

## The Problem

Every no-code agent builder today is a walled garden.

Agents built in Copilot Studio only run in Microsoft's cloud. Agents built in Relevance AI only run on Relevance AI's servers. If you work in healthcare, finance, or insurance — industries where sensitive data legally cannot leave your environment — none of these tools work for you.

Building a custom agent from scratch costs $300K–$500K and takes months.

AgentPort closes the gap: **genuinely no-code builder + deploy to your own infrastructure + compliance baked in.**

---

## How It Works

```
patient_intake.yaml  →  AgentPort Engine  →  patient_intake.zip
                                                      │
                                              ┌───────┴────────┐
                                              │  FastAPI app   │
                                              │  LangGraph     │
                                              │  Dockerfile    │
                                              │  Audit logs    │
                                              └───────┬────────┘
                                                      │
                                             docker compose up
                                                      │
                                              POST /invoke ✓
```

1. Define your agent in YAML — nodes, tools, LLM config, compliance settings
2. Run the engine — it compiles your definition into a full Python project
3. Deploy the ZIP to any server, VM, or Kubernetes cluster you control

---

## Quickstart

```bash
git clone https://github.com/gsatyabrata99/agentport.git
cd agentport/engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate an agent from the example YAML
python -m agentport_engine._cli ../examples/patient_intake.yaml ../examples/output.zip

# Extract and run
unzip ../examples/output.zip -d ../examples/my_agent
cd ../examples/my_agent
cp .env.example .env  # add your API key
uvicorn patient_intake.main:app --port 8001
```

```bash
curl -X POST http://localhost:8001/invoke \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi I need to register as a new patient", "session_id": "s1"}'

# {"response": "I can help with that. Could you provide your full name, date of birth, reason for visit, and insurance ID?", "session_id": "s1"}
```

## Canvas

AgentPort includes a visual drag-and-drop canvas for building agents without writing YAML manually.

![AgentPort Canvas](docs/canvas.png)

Open the canvas:
cd web && npm install && npm run dev

---

## Agent Definition Schema

Agents are defined in YAML. Here's a minimal example:

```yaml
name: patient_intake
version: "1.0.0"
description: HIPAA-compliant patient intake agent

llm:
  provider: openai
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  temperature: 0.2
  max_tokens: 1024

nodes:
  - id: intake_agent
    type: llm_call
    system_prompt: |
      You are a HIPAA-compliant patient intake assistant.
      Collect name, DOB, reason for visit, and insurance ID.
      Use your tools to verify insurance and schedule appointments.
    tools: [verify_insurance, check_availability, schedule_appointment]

edges:
  - from: __start__
    to: intake_agent

tools:
  - name: verify_insurance
    description: Verify patient insurance coverage
    parameters:
      - name: insurance_id
        type: string
        required: true

compliance:
  frameworks: [HIPAA, SOC2]
  audit_logging: true
  data_residency: customer_infrastructure
```

---

## What Gets Generated

Running the engine on a YAML file produces a ZIP containing:

```
my_agent/
├── main.py           # FastAPI app with /health and /invoke endpoints
├── graph.py          # LangGraph agent graph
├── state.py          # TypedDict state schema
├── tools.py          # Tool stubs (wire to your real APIs)
├── audit.py          # Immutable audit logging
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

Every generated agent includes:
- `/health` endpoint for load balancer checks
- `/invoke` endpoint for agent interaction
- Structured JSON audit logs on every node enter/exit
- Environment-variable-based LLM and API key configuration

---

## Compliance Features

| Feature | How It Works |
|---|---|
| Data residency | Agent runs entirely on your infrastructure — no data sent to AgentPort |
| Audit logging | Immutable JSON logs written to stdout or file on every event |
| Model flexibility | Bring your own LLM API key — OpenAI, Anthropic, or any LangChain-compatible model |
| HITL gates | Human-in-the-loop approval nodes (coming soon) |
| RBAC | Role-based access control config (coming soon) |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              AgentPort Engine               │
│                                             │
│  schema.py    →  Pydantic models            │
│  validator.py →  Schema validation          │
│  compiler.py  →  Topological graph sort     │
│  generator.py →  Jinja2 template rendering  │
│  packager.py  →  ZIP assembly               │
└─────────────────────────────────────────────┘

Runtime stack: LangGraph + FastAPI + Docker
LLM support:   OpenAI, Anthropic (provider-agnostic)
Compliance:    HIPAA, SOC2, GDPR-ready
```

---

## Roadmap

- [x] YAML schema and Pydantic validation
- [x] LangGraph compiler and code generator
- [x] FastAPI wrapper with audit logging
- [x] Docker packaging
- [x] Multi-provider LLM support (OpenAI, Anthropic)
- [x] React Flow visual canvas (frontend builder)
- [ ] FastAPI management layer (agent registry, versioning)
- [ ] Human-in-the-loop approval gates
- [ ] RBAC configuration
- [ ] One-click deploy to AWS / Azure / GCP

---

## Built With

- [LangGraph](https://github.com/langchain-ai/langgraph) — agent graph runtime
- [FastAPI](https://fastapi.tiangolo.com) — generated API wrapper
- [Pydantic](https://docs.pydantic.dev) — schema validation
- [Jinja2](https://jinja.palletsprojects.com) — code generation templates
- [Docker](https://docker.com) — portable deployment

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built by [Ganesh Satyabrata](https://linkedin.com/in/gsatyabrata)*
