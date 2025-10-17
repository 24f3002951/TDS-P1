from flask import Flask, request, jsonify
from models import init_db, SessionLocal, Task, Repo
from generator import generate_static_site
from sqlalchemy.exc import NoResultFound
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
init_db()


def verify_secret(provided, expected):
    return provided == expected


@app.route('/api-endpoint', methods=['POST'])
def api_endpoint():
    payload = request.get_json(force=True)
    # Minimal validation
    email = payload.get('email')
    secret = payload.get('secret')
    task = payload.get('task')
    round_idx = payload.get('round')
    nonce = payload.get('nonce')
    brief = payload.get('brief')
    attachments = payload.get('attachments', [])

    # Instructors will set expected secrets in a simple env map for local testing
    expected_secret = os.environ.get('EXPECTED_SECRET')
    if expected_secret and not verify_secret(secret, expected_secret):
        return jsonify({'error': 'invalid secret'}), 400

    # Generate a static site and push to GitHub if token available
    gh_token = os.getenv('GH_TOKEN')
    repo_dir, repo_url, commit_sha, pages_url = generate_static_site(
        task or 'task',
        brief or 'Hello world',
        attachments,
        gh_token=gh_token
    )

    # Log to DB
    db = SessionLocal()
    t = Task(email=email, task=task, round=round_idx, nonce=nonce, brief=brief, attachments=str(attachments), evaluation_url=payload.get('evaluation_url'))
    db.add(t)
    db.commit()

    # Post back to evaluation_url within 10 minutes (simulate immediate)
    eval_url = payload.get('evaluation_url')
    if eval_url and repo_url:  # Only notify if we have a real repo
        body = {
            'email': email,
            'task': task,
            'round': round_idx,
            'nonce': nonce,
            'repo_url': repo_url,
            'commit_sha': commit_sha,
            'pages_url': pages_url,
        }
        
        # Exponential backoff for retries
        delays = [1, 2, 4, 8]  # seconds
        last_error = None
        
        for delay in delays:
            try:
                resp = requests.post(
                    eval_url,
                    json=body,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                resp.raise_for_status()
                break  # Success
            except Exception as e:
                last_error = e
                time.sleep(delay)
        else:  # All retries failed
            # Log failure but still return 200 so students know their endpoint worked
            return jsonify({
                'warning': f'created repo but failed to notify evaluation_url after retries: {last_error}',
                'repo_url': repo_url,
                'pages_url': pages_url
            }), 200

    return jsonify({'status': 'ok', 'repo_dir': repo_dir}), 200


@app.route('/evaluation', methods=['POST'])
def evaluation():
    payload = request.get_json(force=True)
    email = payload.get('email')
    task = payload.get('task')
    round_idx = payload.get('round')
    nonce = payload.get('nonce')
    repo_url = payload.get('repo_url')
    commit_sha = payload.get('commit_sha')
    pages_url = payload.get('pages_url')

    db = SessionLocal()
    try:
        # find matching task
        t = db.query(Task).filter_by(email=email, task=task, round=round_idx, nonce=nonce).one()
    except NoResultFound:
        return jsonify({'error': 'no matching task'}), 400

    r = Repo(email=email, task=task, round=round_idx, nonce=nonce, repo_url=repo_url, commit_sha=commit_sha, pages_url=pages_url)
    db.add(r)
    db.commit()

    return jsonify({'status': 'received'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
