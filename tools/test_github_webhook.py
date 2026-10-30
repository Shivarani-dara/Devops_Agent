import hashlib
import hmac
import json

from tools import github_webhook


def test_valid_push_webhook_triggers_jenkins(monkeypatch):
    secret = "test-webhook-secret"
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)

    called = {}

    def fake_trigger(job_name):
        called["job_name"] = job_name
        return {"success": True, "queue_id": 123, "build_number": 1}

    monkeypatch.setattr(
        github_webhook, "trigger_jenkins_build", fake_trigger
    )

    payload = json.dumps({
        "ref": "refs/heads/main",
        "repository": {
            "full_name": "Shivarani-dara/devops_agent_test"
        }
    }).encode()

    signature = "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    client = github_webhook.app.test_client()
    response = client.post(
        "/github-webhook",
        data=payload,
        content_type="application/json",
        headers={
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 202
    assert called["job_name"] == "devops-agent-test"
