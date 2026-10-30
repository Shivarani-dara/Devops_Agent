import hmac
import hashlib
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

from flask import Flask, request, jsonify, abort
from .jenkins_tools import trigger_jenkins_build

app = Flask(__name__)

AGENT_ROOT = Path(__file__).resolve().parent.parent

for env_name, filename in [
    ("GITHUB_WEBHOOK_SECRET", ".github_webhook_secret"),
    ("JENKINS_FAILURE_TOKEN", ".jenkins_failure_token"),
]:
    secret_file = AGENT_ROOT / filename
    if secret_file.is_file():
        os.environ.setdefault(env_name, secret_file.read_text().strip())
TEST_PROJECT_PATH = Path.home() / "test_project"
ALLOWED_REPOSITORY = "Shivarani-dara/devops_agent_test"
ALLOWED_JOB = "devops-agent-test"

repair_queue = queue.Queue()
seen_builds = set()
seen_lock = threading.Lock()


@app.post("/github-webhook")
def github_webhook():
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
    if not secret:
        abort(503, "Webhook secret is not configured")

    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(
        secret.encode(), request.get_data(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        abort(401, "Invalid signature")

    event = request.headers.get("X-GitHub-Event", "")
    if event == "ping":
        return jsonify({"status": "ok"})
    if event != "push":
        return jsonify({"status": "ignored"})

    payload = request.get_json(silent=True) or {}
    if payload.get("ref") != "refs/heads/main":
        return jsonify({"status": "ignored", "reason": "not main"})

    repository = payload.get("repository", {}).get("full_name")
    if repository != ALLOWED_REPOSITORY:
        abort(403, "Repository not allowed")

    commit = payload.get("head_commit") or {}
    message = commit.get("message", "").strip()
    if message.startswith("AI debugging fix"):
        return jsonify({
            "status": "ignored",
            "reason": "repair-agent push; repair loop handles the build",
        })

    result = trigger_jenkins_build(ALLOWED_JOB)
    if not result.get("success"):
        app.logger.error("Jenkins trigger failed: %s", result.get("error"))
        return jsonify({
            "status": "error",
            "message": "Could not trigger Jenkins build",
        }), 502

    return jsonify({
        "status": "queued",
        "repository": repository,
        "job": ALLOWED_JOB,
        "queue_id": result.get("queue_id"),
        "build_number": result.get("build_number"),
    }), 202


@app.post("/jenkins-failure")
def jenkins_failure():
    secret = os.environ.get("JENKINS_FAILURE_TOKEN")
    if not secret:
        abort(503, "Jenkins failure token is not configured")

    supplied = request.headers.get("X-Jenkins-Token", "")
    if not hmac.compare_digest(supplied, secret):
        abort(401, "Invalid Jenkins token")

    payload = request.get_json(silent=True) or {}
    job_name = payload.get("job_name")
    build_number = payload.get("build_number")

    if job_name != ALLOWED_JOB:
        app.logger.warning("Rejected job_name=%r build_number=%r", job_name, build_number)
        abort(403, "Jenkins job not allowed")
    if type(build_number) is not int or build_number < 1:
        return jsonify({
            "status": "error",
            "message": "build_number must be a positive integer",
        }), 400

    key = (job_name, build_number)
    with seen_lock:
        if key in seen_builds:
            return jsonify({
                "status": "ignored",
                "reason": "build already queued or processed",
            }), 200
        seen_builds.add(key)
        repair_queue.put(key)

    app.logger.warning("Queued repair for %s build #%s", job_name, build_number)
    return jsonify({
        "status": "queued",
        "job": job_name,
        "build_number": build_number,
    }), 202


def repair_worker():
    while True:
        job_name, build_number = repair_queue.get()
        try:
            if not TEST_PROJECT_PATH.is_dir():
                app.logger.error("Project directory missing: %s", TEST_PROJECT_PATH)
                continue

            command = [
                sys.executable,
                str(AGENT_ROOT / "agent.py"),
                str(TEST_PROJECT_PATH),
                "--jenkins-job", job_name,
                "--jenkins-build", str(build_number),
            ]
            print(
                f"\nQueued Jenkins failure: {job_name} build #{build_number}\n"
                "Starting interactive repair agent...\n",
                flush=True,
            )
            result = subprocess.run(command, cwd=str(AGENT_ROOT), check=False)
            if result.returncode:
                app.logger.error(
                    "Repair agent exited with code %s for build #%s",
                    result.returncode, build_number,
                )
        except Exception:
            app.logger.exception("Repair worker failed for build #%s", build_number)
        finally:
            repair_queue.task_done()


if __name__ == "__main__":
    threading.Thread(
        target=repair_worker, name="jenkins-repair-worker", daemon=True
    ).start()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
