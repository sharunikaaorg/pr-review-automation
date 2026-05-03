# PR Review Automation System — Complete Documentation

## 1. Overview

The PR Review Automation System is an AI-powered code review platform that automatically analyzes GitHub pull requests using a multi-agent LLM architecture. When a developer opens a PR, the system receives a webhook from GitHub, orchestrates multiple specialized AI agents to analyze the code, generates a detailed review, and posts it back as a PR comment — all within seconds.

The system also features a feedback loop: developers can comment on the review, and the system learns from that feedback by evolving its review prompts over time.

### Tech Stack

| Component | Technology | Version |
|---|---|---|
| Web Framework | FastAPI | 0.104.1 |
| ASGI Server | Uvicorn | 0.24.0 |
| LLM Provider | Groq (Llama 3.3 70B) | 0.4.1 |
| GitHub Integration | PyGithub + Requests | 2.1.1 / 2.31.0 |
| Database | SQLite via SQLAlchemy | 2.0.23 |
| Validation | Pydantic | 2.5.0 |
| Tunnel (dev) | ngrok | — |

---

## 2. Architecture

### High-Level System Diagram

```
┌──────────┐     Webhook (POST)      ┌──────────────────┐
│  GitHub  │ ──────────────────────► │  ngrok Tunnel    │
│  (PR/    │                         │  (public URL)    │
│  Comment)│ ◄────────────────────── │                  │
└──────────┘   PR Comment (Review)   └────────┬─────────┘
                                              │
                                              ▼
                                     ┌──────────────────┐
                                     │  FastAPI Server   │
                                     │  (Port 8000)      │
                                     │                   │
                                     │  POST /api/v1/    │
                                     │  github/webhook   │
                                     └────────┬──────────┘
                                              │
                              ┌───────────────▼───────────────┐
                              │       Main Agent              │
                              │       (LLM Orchestrator)      │
                              └───┬─────────┬─────────┬───────┘
                                  │         │         │
                    ┌─────────────▼┐  ┌─────▼──────┐  ┌▼─────────────┐
                    │ Code         │  │ Diff       │  │ Code Type    │
                    │ Summarizer   │  │ Analyzer   │  │ Classifier   │
                    │ (300 tokens) │  │ (500 tok)  │  │ (heuristic   │
                    └──────┬───────┘  └─────┬──────┘  │  + 50 tok)   │
                           │                │         └──┬────────────┘
                           │                │            │
                           └────────┬───────┘            │
                                    │    ┌───────────────┘
                                    ▼    ▼
                           ┌─────────────────────┐
                           │  Dynamic Prompt      │
                           │  Manager             │
                           │  (frontend/backend/  │
                           │   generic prompts)   │
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │  Review Generator    │
                           │  (1500 tokens)       │
                           └──────────┬──────────┘
                                      │
                          ┌───────────┴───────────┐
                          ▼                       ▼
                 ┌─────────────────┐    ┌─────────────────┐
                 │  Post Comment   │    │  SQLite DB      │
                 │  to GitHub PR   │    │  (pr_reviews,   │
                 └─────────────────┘    │   feedback)     │
                                        └────────┬────────┘
                                                 │
                              ┌──────────────────▼──────────────────┐
                              │           Feedback Loop             │
                              └──────────┬─────────────────────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  Feedback Analyzer   │
                              │  (800 tokens)        │
                              └──────────┬──────────┘
                                         │
                              ┌──────────▼──────────┐
                              │  Prompt Updater      │
                              │  (1200 tokens)       │
                              └──────────┬──────────┘
                                         │
                                         ▼
                              Updates Dynamic Prompts
                              (version incremented,
                               saved to JSON file)
```


---

## 3. Ideation & Design Decisions

### Problem Statement

Manual code reviews are time-consuming and inconsistent. Reviewers may miss security issues, forget best practices, or provide varying levels of detail depending on workload. An automated first-pass review can catch common issues instantly, freeing human reviewers to focus on architecture and business logic.

### Why a Multi-Agent Architecture?

A single monolithic prompt would hit token limits on large diffs and produce unfocused reviews. By splitting the work across specialized agents, each one operates within tight token budgets and has a clear responsibility:

| Agent | Responsibility | Why Separate? |
|---|---|---|
| Code Summarizer | Distill what changed | Gives the reviewer context without reading raw diffs |
| Diff Analyzer | Identify risks and quality issues | Focused analysis without review-writing overhead |
| Code Type Classifier | Route to the right prompt | Frontend, backend, and infra code need different review criteria |
| Review Generator | Produce the final review | Combines all inputs with a type-specific expert prompt |

### Why Groq + Llama 3.3 70B?

- Groq provides extremely fast inference (sub-second for most calls)
- Llama 3.3 70B Versatile offers strong code understanding at no cost
- The entire 4-agent pipeline completes in ~5-8 seconds

### Why a Feedback Loop?

Static prompts degrade over time as codebases evolve. The feedback loop allows the system to learn from developer corrections — if reviews consistently miss security issues, the prompt evolves to emphasize security. This is implemented as prompt versioning rather than fine-tuning, keeping the system simple and transparent.

---

## 4. Agentic Workflow — Step by Step

### Phase 1: PR Review Pipeline

```
Developer opens/updates PR
         │
         ▼
Step 1 ─ GitHub fires webhook (X-GitHub-Event: pull_request)
         │
Step 2 ─ FastAPI receives POST /api/v1/github/webhook
         ├── Verifies HMAC-SHA256 signature
         ├── Checks action is: opened | reopened | synchronize
         └── Spawns background task (non-blocking response to GitHub)
         │
Step 3 ─ Background task: Fetch PR data from GitHub API
         ├── PR title, description, author, branches
         ├── Full diff (via GitHub diff API)
         └── List of changed files
         │
Step 4 ─ Main Agent orchestrates sub-agents sequentially:
         │
         ├── 4a. Code Summarizer
         │        Input:  diff (first 3000 chars), title, description
         │        Output: ~200 word summary of changes
         │        Tokens: max 300
         │
         ├── 4b. Diff Analyzer
         │        Input:  diff (first 4000 chars), file list (first 10)
         │        Output: Structured analysis (complexity, risks, quality)
         │        Tokens: max 500
         │
         ├── 4c. Code Type Classifier
         │        Input:  file list, diff
         │        Logic:  Heuristic first (file extensions), LLM fallback
         │        Output: "frontend" | "backend" | "other"
         │
         │        Heuristic rules:
         │        Frontend: .js .jsx .ts .tsx .vue .html .css .scss .sass
         │        Backend:  .py .java .go .rb .php .rs .cpp .c .cs
         │        If frontend_count > backend_count × 2 → frontend
         │        If backend_count > frontend_count × 2 → backend
         │        Otherwise → LLM decides (max 50 tokens)
         │
         └── 4d. Review Generator
                  Input:  code_type, summary, analysis, diff (first 5000 chars)
                  Prompt: Loaded from Dynamic Prompt Manager (type-specific)
                  Output: Full structured code review
                  Tokens: max 1500
         │
Step 5 ─ Save review to SQLite database (pr_reviews table)
         │
Step 6 ─ Post review as comment on the GitHub PR
         (Prefixed with "## 🤖 Automated Code Review")
```


### Phase 2: Feedback Loop

```
Developer comments on PR with feedback
         │
         ▼
Step 1 ─ GitHub fires webhook (X-GitHub-Event: issue_comment)
         │
Step 2 ─ Server checks if comment contains feedback indicators:
         │   "@pr-bot"  "feedback:"  "review feedback:"  "bot feedback:"
         │   "improve:"  "suggestion:"  "the review should"
         │   "missing from review"  "review missed"  "add to review"
         │
Step 3 ─ If feedback detected → spawns background task
         │
Step 4 ─ Feedback Analyzer (LLM, 800 tokens)
         │   Input:  feedback text, original review, code type
         │   Output: JSON with:
         │     - feedback_type: positive | negative | suggestion | clarification
         │     - confidence: 0.0–1.0
         │     - improvement_areas: ["security", "testing", ...]
         │     - specific_issues: ["Missing input validation", ...]
         │     - prompt_updates: ["Add section about X", ...]
         │     - priority: high | medium | low
         │
Step 5 ─ Save feedback to database (feedback table)
         │
Step 6 ─ If priority is high or medium AND prompt_updates exist:
         │
         ├── Prompt Updater (LLM, 1200 tokens)
         │     Input:  current prompt, feedback analysis
         │     Output: improved prompt text
         │
         └── Dynamic Prompt Manager saves updated prompt
               - Version incremented by 0.1 (e.g., 1.0 → 1.1)
               - Feedback summary appended to history (last 10 kept)
               - Saved to dynamic_prompts.json
         │
Step 7 ─ Bot replies on PR acknowledging the feedback
         "I've updated my review approach based on your suggestions. 🤖✨"
```

### How Prompts Evolve

```
Version 1.0 (Default)                    Version 1.1 (After feedback)
┌─────────────────────────┐              ┌─────────────────────────────────┐
│ "Review focusing on:    │   feedback:  │ "Review focusing on:            │
│  - Architecture         │ ──────────►  │  - Architecture                 │
│  - Best practices       │  "add more   │  - Best practices               │
│  - Security             │   security   │  - Security (EXPANDED:          │
│  - Performance"         │   analysis"  │    input validation, injection, │
│                         │              │    auth token handling)          │
└─────────────────────────┘              │  - Performance"                 │
                                         └─────────────────────────────────┘
```

---

## 5. Type-Specific Review Prompts

The system uses three specialized prompts, each tailored to the code type:

### Frontend Prompt
Focuses on: component design & reusability, accessibility compliance, responsive design, state management patterns, performance (lazy loading, memoization, bundle size), TypeScript/JavaScript best practices, CSS organization, XSS prevention, input sanitization.

### Backend Prompt
Focuses on: API design & RESTful principles, database schema changes, error handling & logging, input validation, SQL injection prevention, authentication & authorization, query optimization, caching strategies, database indexing, scalability, unit & integration testing.

### Generic Prompt
Focuses on: code clarity & readability, maintainability, coding standards, design patterns, error handling, security vulnerabilities, breaking changes, backward compatibility, configuration management, dependency review.

All prompts accept three variables: `{summary}`, `{analysis}`, and `{diff_content}`.


---

## 6. Database Schema

SQLite database (`pr_reviews.db`) with two tables:

### Table: `pr_reviews`

| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-increment primary key |
| `pr_number` | Integer, NOT NULL | GitHub PR number |
| `repo_full_name` | String(255), NOT NULL | e.g., `org/repo-name` |
| `review_content` | Text, NOT NULL | The generated review |
| `code_type` | String(50), NOT NULL | `frontend`, `backend`, or `other` |
| `summary` | Text, nullable | Code change summary |
| `diff_analysis` | Text, nullable | Diff analysis output |
| `created_at` | DateTime | Auto-set on creation |
| `updated_at` | DateTime | Auto-set on update |
| `pr_metadata` | JSON, nullable | PR title, description, files changed |

### Table: `feedback`

| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-increment primary key |
| `review_id` | Integer, NOT NULL | References `pr_reviews.id` |
| `feedback_type` | String(50), NOT NULL | `positive`, `negative`, `suggestion`, `clarification` |
| `feedback_content` | Text, NOT NULL | Raw feedback text |
| `created_at` | DateTime | Auto-set on creation |

---

## 7. API Reference

### Core

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | System status and version |
| `GET` | `/health` | Health check (Groq + GitHub config status) |

### Webhook

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/github/webhook` | Receives GitHub webhooks. Verifies HMAC-SHA256 signature. Handles `pull_request` and `issue_comment` events. |

### Reviews

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/reviews` | List reviews (query: `skip`, `limit`) |
| `GET` | `/api/v1/reviews/{id}` | Get a specific review |
| `POST` | `/api/v1/reviews/{id}/feedback` | Submit feedback for a review |
| `POST` | `/api/v1/reviews/{id}/process-feedback` | Process feedback and trigger prompt update |
| `GET` | `/api/v1/stats` | Review counts by code type |

### Prompts & Learning

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/prompts` | All prompts with version info |
| `GET` | `/api/v1/prompts/{code_type}` | Prompt for `frontend`, `backend`, or `other` |
| `POST` | `/api/v1/prompts/reset` | Reset all prompts to defaults |
| `GET` | `/api/v1/feedback-stats` | Feedback counts by type |


---

## 8. Project Structure

```
pr-review-automation/
├── app/
│   ├── main.py                    # FastAPI app, CORS, startup, routers
│   ├── config.py                  # Environment config (Groq, GitHub, DB)
│   ├── __init__.py
│   │
│   ├── agents/                    # LLM agent layer
│   │   ├── groq_client.py         # Groq API client singleton
│   │   ├── main_agent.py          # Orchestrator (process_pr, process_feedback)
│   │   ├── sub_agents.py          # CodeSummarizer, DiffAnalyzer, CodeTypeClassifier
│   │   ├── review_generator.py    # Generates final review using dynamic prompts
│   │   ├── prompts.py             # Static prompt templates (frontend/backend/generic)
│   │   ├── dynamic_prompts.py     # Prompt versioning and evolution manager
│   │   └── feedback_analyzer.py   # FeedbackAnalyzer + PromptUpdater
│   │
│   ├── api/                       # FastAPI route handlers
│   │   ├── webhooks.py            # GitHub webhook endpoint + event handlers
│   │   └── reviews.py             # Review CRUD, feedback, prompts, stats
│   │
│   ├── github/                    # GitHub API integration
│   │   └── client.py              # PR data fetching, review posting, signature verification
│   │
│   └── database/                  # Data persistence
│       ├── database.py            # SQLAlchemy engine, session, create_tables
│       ├── models.py              # PRReview and Feedback ORM models
│       └── __init__.py            # Exports: get_db, create_tables, PRReview, Feedback
│
├── dynamic_prompts.json           # Evolved prompts (auto-generated, gitignored)
├── pr_reviews.db                  # SQLite database (auto-generated)
├── requirements.txt               # Python dependencies
├── .env                           # API keys and secrets
├── test_system.py                 # Unit test with mock PR data
├── test_integration.py            # Full integration test (server + API + LLM + DB)
├── demo_feedback_loop.py          # Feedback loop demonstration script
└── README.md
```

---

## 9. Setup & Deployment

### Prerequisites

- Python 3.12+
- A Groq API key ([console.groq.com](https://console.groq.com/))
- A GitHub personal access token with `repo` and `write:repo_hook` scopes
- ngrok (for local development webhook tunneling)

### Installation

```bash
git clone https://github.com/sharunikaaorg/pr-review-automation.git
cd pr-review-automation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Create `.env` in the project root:

```env
GROQ_API_KEY=gsk_your_groq_api_key
GITHUB_TOKEN=ghp_your_github_token
WEBHOOK_SECRET=your_random_secret_string
DATABASE_URL=sqlite:///./pr_reviews.db
```

### Running

```bash
# Terminal 1: Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start ngrok tunnel
ngrok http 8000
```

### GitHub Webhook Configuration

1. Go to your repository → Settings → Webhooks → Add webhook
2. **Payload URL**: `https://<your-ngrok-id>.ngrok-free.app/api/v1/github/webhook`
3. **Content type**: `application/json`
4. **Secret**: Same value as `WEBHOOK_SECRET` in `.env`
5. **Events**: Select `Pull requests` and `Issue comments`
6. **Active**: ✅

### Verify It Works

```bash
# Quick health check
curl http://localhost:8000/health

# Run the full integration test
python test_integration.py
```

---

## 10. Token Budget & Performance

Each PR review makes 3–4 LLM calls to Groq. Here's the token budget:

| Agent | Max Output Tokens | Input Truncation | Typical Latency |
|---|---|---|---|
| Code Summarizer | 300 | Diff: 3,000 chars | ~1s |
| Diff Analyzer | 500 | Diff: 4,000 chars | ~2s |
| Code Type Classifier | 50 (LLM fallback only) | Diff: 2,000 chars | ~0.5s |
| Review Generator | 1,500 | Diff: 5,000 chars | ~3s |
| **Total per PR** | **~2,350** | | **~5–8s** |

Feedback processing adds:

| Agent | Max Output Tokens | Typical Latency |
|---|---|---|
| Feedback Analyzer | 800 | ~2s |
| Prompt Updater | 1,200 | ~3s |
| **Total per feedback** | **~2,000** | **~5s** |

---

## 11. Features Summary

| Feature | Description |
|---|---|
| **Automated PR Review** | Reviews posted automatically when PRs are opened, reopened, or updated |
| **Multi-Agent Pipeline** | 4 specialized agents: summarizer, analyzer, classifier, reviewer |
| **Type-Specific Reviews** | Different review criteria for frontend, backend, and generic code |
| **Hybrid Classification** | File-extension heuristic with LLM fallback for ambiguous PRs |
| **Webhook Integration** | HMAC-SHA256 verified GitHub webhooks with background processing |
| **Feedback Loop** | Developers comment on reviews → system learns and improves prompts |
| **Dynamic Prompt Evolution** | Prompts versioned and updated based on feedback (stored in JSON) |
| **Feedback Detection** | Auto-detects feedback keywords in PR comments |
| **Database Storage** | All reviews and feedback persisted in SQLite |
| **REST API** | Full API for reviews, stats, prompts, and feedback management |
| **Prompt Reset** | One-click reset to default prompts |
| **Health Monitoring** | Health endpoint showing Groq and GitHub configuration status |

---

## 12. End-to-End Example

Here's what happens when a developer opens PR #3 ("Add health check utilities"):

```
17:52:19.880  Webhook received: pull_request (action: opened)
17:52:19.880  Processing PR #3 in sharunikaaorg/pr-review-automation
17:52:22.192  Fetched PR data (2 files, 1848 char diff)
17:52:22.192  Running code summarizer...
17:52:23.004  ✓ Summary generated (Groq API 200 OK)
17:52:23.011  Running diff analyzer...
17:52:24.739  ✓ Analysis generated (Groq API 200 OK)
17:52:24.740  Classified as: backend (heuristic — .py files)
17:52:24.740  Generating review with backend prompt...
17:52:27.834  ✓ Review generated (Groq API 200 OK, 6913 chars)
17:52:27.843  Saved to database (review ID: 2)
17:52:29.937  ✓ Review posted to GitHub PR #3
17:52:29.937  Processing complete (total: ~10s)
```

The developer sees a comment on their PR:

> ## 🤖 Automated Code Review
>
> *Structured review covering architecture, error handling, security,
> performance, and testing recommendations specific to the backend code...*

If the developer replies with feedback like:

> @pr-bot feedback: The review should check for timeout handling in health checks

The system automatically:
1. Detects the feedback keyword (`@pr-bot`)
2. Analyzes the feedback via LLM
3. Updates the backend prompt to emphasize timeout handling
4. Replies: "I've updated my review approach based on your suggestions. 🤖✨"
5. Future backend reviews now include timeout analysis
