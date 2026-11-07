import importlib
import sys
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient

from test_rate_limit import make_limiter


@pytest.fixture
def environment(monkeypatch):
    # 路由集成测试隔离真实数据库、向量库和付费模型。
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("SECRET_KEY", "test-key-only")
    llm = MagicMock()
    rag = MagicMock()
    monkeypatch.setitem(sys.modules, "utils.llm", llm)
    monkeypatch.setitem(sys.modules, "utils.rag", rag)
    chat = importlib.import_module("routers.chat")
    interviews = importlib.import_module("routers.interviews")
    from database import get_db
    from dependencies.rate_limit import get_rate_limiter
    from utils.auth import get_current_user

    app = FastAPI()
    app.include_router(chat.router)
    app.include_router(interviews.router)
    db = MagicMock()
    limiter = make_limiter(chat_requests=1, interview_requests=1)

    def authenticate(authorization: str | None = Header(default=None)):
        if authorization != "Bearer test":
            raise HTTPException(401)
        return {"id": 1}

    app.dependency_overrides[get_current_user] = authenticate
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    with TestClient(app) as client:
        yield client, db, limiter, chat, interviews
    limiter.close()
    # import 缓存也需清理，避免下一用例仍引用前一用例的模型替身。
    sys.modules.pop("routers.chat", None)
    sys.modules.pop("routers.interviews", None)


@pytest.mark.parametrize("url,payload,scope", [
    ("/chat", {"question": "hi", "conversation_id": 1}, "chat"),
    ("/chat/stream", {"question": "hi", "conversation_id": 1}, "chat"),
    ("/interviews", {"resume_id": 1}, "interview"),
    ("/interviews/1/answer", {"answer": "my answer"}, "interview"),
])
def test_denied_before_database_or_model(environment, url, payload, scope):
    client, db, limiter, chat, interviews = environment
    limiter.check(1, scope)
    response = client.post(url, json=payload, headers={"Authorization": "Bearer test"})
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    assert response.json()["detail"]["code"] == "rate_limit_exceeded"
    assert not db.mock_calls
    chat.rag_answer.assert_not_called()
    chat.chat_with_llm_stream.assert_not_called()
    interviews.generate_interview_question.assert_not_called()
    interviews.evaluate_interview_answer_with_knowledge.assert_not_called()


def test_authentication_does_not_consume_budget(environment):
    client, db, limiter, chat, _ = environment
    payload = {"question": "hi", "conversation_id": 1}
    assert client.post("/chat", json=payload).status_code == 401
    chat.rag_answer.return_value = {"answer": "ok"}
    assert client.post("/chat", json=payload, headers={"Authorization": "Bearer test"}).status_code == 200
    chat.rag_answer.assert_called_once_with("hi", 1, db)
    # 普通问答已占用同一用户的配额，不能换用流式入口绕过。
    assert client.post("/chat/stream", json=payload, headers={"Authorization": "Bearer test"}).status_code == 429


def test_outage_returns_retryable_503_before_writes(environment, monkeypatch):
    from services.rate_limit import RateLimitUnavailable
    client, db, limiter, _, _ = environment

    def unavailable(*args):
        raise RateLimitUnavailable()

    monkeypatch.setattr(limiter, "check", unavailable)
    response = client.post("/interviews/1/answer", json={"answer": "keep this"}, headers={"Authorization": "Bearer test"})
    assert response.status_code == 503
    assert response.headers["Retry-After"] == "5"
    assert response.json()["detail"]["code"] == "rate_limit_unavailable"
    assert not db.mock_calls
