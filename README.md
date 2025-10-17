# LLM Code Deployment - Instructor Framework

Framework for managing student LLM-assisted code generation tasks. This system:

1. Accepts task submissions via a Google Form
2. Sends coding tasks to students' API endpoints
3. Evaluates their GitHub repos and Pages deployments
4. Manages multiple rounds of tasks/feedback

## Setup

1. Install dependencies:
   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # Windows
   pip install -r requirements.txt
   ```

2. Set up environment variables in `.env`:
   ```
   GH_TOKEN=your_github_token
   EXPECTED_SECRET=test-secret  # For local testing
   ```

3. Initialize database:
   ```bash
   python -c "from models import init_db; init_db()"
   ```

## Usage

1. Create `submissions.csv` with student info:
   ```csv
   timestamp,email,endpoint,secret
   2025-10-17,student@example.com,http://localhost:5000,test-secret
   ```

2. Start the evaluation server:
   ```bash
   python app.py
   ```

3. Send round 1 tasks:
   ```bash
   python round1.py
   ```

4. Run evaluations:
   ```bash
   python evaluate.py
   ```

5. Send round 2 tasks:
   ```bash
   python round2.py
   ```

## API Endpoints

### /api-endpoint (Student Implementation)
- Accepts POST with task details
- Creates/updates GitHub repo
- Returns 200 OK with confirmation

### /evaluation
- Accepts POST with repo details
- Validates task completion
- Returns 200 OK on success

## Files

- `app.py` - Flask server with API endpoints
- `models.py` - SQLite database models
- `generator.py` - Static site generator with GitHub integration
- `round1.py`/`round2.py` - Task generators
- `evaluate.py` - Repo evaluation script

## License

MIT License
