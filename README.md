# PR Review Automation System

An automated PR review system that uses LLM agents to analyze and review GitHub pull requests.

## Architecture with Feedback Loop

```
GitHub PR → Webhook → FastAPI Server → Main Agent (LLM Orchestrator)
                                            ↓
                      ┌─────────────────────────────────────┐
                      │                                     │
            ┌─────────▼───┐  ┌──────────▼──────┐  ┌────────▼────────┐
            │ Summarize   │  │ Analyze Diff +  │  │ Classify Code   │
            │ Code        │  │ Context         │  │ Type            │
            └─────────────┘  └─────────────────┘  └─────────────────┘
                                            │
                      ┌─────────────────────▼─────────────────────┐
                      │            Type Classification            │
                      └─────────┬─────────┬─────────┬─────────────┘
                               │         │         │
                    ┌──────────▼──┐ ┌────▼────┐ ┌──▼────────┐
                    │ Dynamic     │ │ Dynamic │ │ Dynamic   │
                    │ Frontend    │ │ Backend │ │ Generic   │
                    │ Prompt      │ │ Prompt  │ │ Prompt    │
                    └─────────────┘ └─────────┘ └───────────┘
                               │         │         │
                               └─────────▼─────────┘
                                       │
                               ┌───────▼────────┐
                               │ Review         │
                               │ Generator      │
                               └────────────────┘
                                       │
                               ┌───────▼────────┐
                               │ Post Comment   │
                               │ to PR          │
                               └────────────────┘
                                       │
                               ┌───────▼────────┐
                               │ Database       │
                               │ Storage        │
                               └────────────────┘
                                       │
                      ┌────────────────▼────────────────┐
                      │         Feedback Loop           │
                      └────────┬────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ PR Comments         │
                    │ (Feedback)          │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Feedback Analyzer   │
                    │ (LLM)               │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Prompt Updater      │
                    │ (Improve Prompts)   │
                    └──────────┬──────────┘
                               │
                               │ Updates prompts for better reviews
                               └─────────────────────────────────────┐
                                                                     │
                              ┌──────────────────────────────────────▼┐
                              │           Main Agent                  │
                              │      (Improved Reviews)               │
                              └───────────────────────────────────────┘
```

## Features

- **Automated PR Analysis**: Processes GitHub PRs via webhooks
- **Multi-Agent Architecture**: Specialized agents for summarization, analysis, and classification
- **Type-Specific Reviews**: Different prompts for frontend, backend, and generic code
- **Database Storage**: SQLite database for reviews and feedback
- **GitHub Integration**: Posts reviews back to PRs automatically
- **RESTful API**: Endpoints for managing reviews and feedback
- **🔄 Feedback Loop**: System learns and improves from user feedback
- **Dynamic Prompts**: Prompts evolve based on feedback to provide better reviews
- **Automatic Learning**: Processes PR comments to identify feedback and improve
- **Feedback Analytics**: Track improvement areas and system evolution

## Quick Setup

### 1. Clone and Install Dependencies

```bash
cd /path/to/your/project
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_token_here
WEBHOOK_SECRET=your_webhook_secret_here
DATABASE_URL=sqlite:///./pr_reviews.db
```

**Get API Keys:**
- **Groq API Key**: Sign up at [https://console.groq.com/](https://console.groq.com/)
- **GitHub Token**: Go to GitHub Settings → Developer settings → Personal access tokens
  - Select scopes: `repo`, `write:repo_hook`

### 3. Test the System

```bash
python test_system.py
```

### 4. Run the Server

```bash
python -m app.main
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Set Up ngrok (for webhooks)

```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000
```

Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

### 6. Configure GitHub Webhook

1. Go to your GitHub repository
2. Settings → Webhooks → Add webhook
3. **Payload URL**: `https://your-ngrok-url.ngrok.io/api/v1/github/webhook`
4. **Content type**: `application/json`
5. **Secret**: Use the same value as `WEBHOOK_SECRET` in your `.env`
6. **Events**: Select "Pull requests" AND "Issue comments" (for feedback loop)
7. **Active**: ✅ Check

## API Endpoints

### Core Endpoints
- `GET /` - System status
- `GET /health` - Health check
- `POST /api/v1/github/webhook` - GitHub webhook endpoint

### Review Management
- `GET /api/v1/reviews` - List all reviews
- `GET /api/v1/reviews/{id}` - Get specific review
- `POST /api/v1/reviews/{id}/feedback` - Add feedback to review
- `POST /api/v1/reviews/{id}/process-feedback` - Process feedback and update system
- `GET /api/v1/stats` - Review statistics

### Feedback Loop & Learning
- `GET /api/v1/prompts` - Get all current prompts with version info
- `GET /api/v1/prompts/{code_type}` - Get prompt for specific code type
- `POST /api/v1/prompts/reset` - Reset all prompts to defaults
- `GET /api/v1/feedback-stats` - Feedback statistics and learning progress

## Usage

### Basic Flow
1. **Create a PR** in your connected repository
2. **System automatically**:
   - Receives webhook
   - Fetches PR data from GitHub
   - Analyzes code changes
   - Classifies code type (frontend/backend/other)
   - Generates appropriate review
   - Posts review as PR comment
   - Stores data in database

### Feedback Loop
3. **Provide feedback** by commenting on the PR:
   ```
   @pr-bot feedback: The review should include more security analysis
   ```
   or
   ```
   Review missed the performance implications of this change
   ```

4. **System learns**:
   - Detects feedback comments automatically
   - Analyzes feedback using LLM
   - Updates prompts to improve future reviews
   - Acknowledges feedback with a response

5. **View results & learning**:
   - Check PR comments for automated review and feedback responses
   - Visit `http://localhost:8000/api/v1/reviews` for stored reviews
   - Visit `http://localhost:8000/api/v1/prompts` to see prompt evolution
   - Visit `http://localhost:8000/api/v1/feedback-stats` for learning statistics

### Demo the Feedback Loop
Run the feedback loop demo to see how the system learns:
```bash
python demo_feedback_loop.py
```

## Project Structure

```
├── app/
│   ├── agents/           # LLM agents and orchestrator
│   │   ├── groq_client.py      # Groq API client
│   │   ├── main_agent.py       # Main orchestrator
│   │   ├── sub_agents.py       # Specialized sub-agents
│   │   ├── prompts.py          # Type-specific prompts
│   │   └── review_generator.py # Review generation
│   ├── api/              # FastAPI routes
│   │   ├── webhooks.py         # GitHub webhook handling
│   │   └── reviews.py          # Review management API
│   ├── database/         # Database models and connection
│   │   ├── models.py           # SQLAlchemy models
│   │   └── database.py         # DB connection and setup
│   ├── github/           # GitHub API integration
│   │   └── client.py           # GitHub client
│   ├── config.py         # Configuration management
│   └── main.py           # FastAPI app
├── test_system.py        # Test script
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Customization

### Adding New Code Types

1. Edit `app/agents/sub_agents.py` → `CodeTypeClassifier`
2. Add new prompt in `app/agents/prompts.py`
3. Update `get_prompt_for_type()` function

### Modifying Review Prompts

Edit the prompts in `app/agents/prompts.py`:
- `FRONTEND_PROMPT` - For UI/frontend code
- `BACKEND_PROMPT` - For API/backend code  
- `GENERIC_PROMPT` - For other code types

### Database Schema Changes

1. Modify `app/database/models.py`
2. Delete existing `pr_reviews.db` file
3. Restart the system (tables will be recreated)

## Troubleshooting

### Common Issues

1. **Groq API Key Invalid**
   - Verify key at [https://console.groq.com/](https://console.groq.com/)
   - Check `.env` file configuration

2. **GitHub Integration Not Working**
   - Verify GitHub token permissions
   - Check webhook URL is accessible
   - Verify webhook secret matches

3. **Database Issues**
   - Delete `pr_reviews.db` and restart
   - Check file permissions

### Logs

The system logs important events to console. Look for:
- ✅ Successful operations
- ❌ Errors and failures
- 🔄 Processing status

## Next Steps

- Add more sophisticated diff analysis
- Implement feedback learning loop
- Add support for multiple LLM providers
- Create web dashboard for review management
- Add unit tests and CI/CD pipeline

## License

MIT License - see LICENSE file for details.