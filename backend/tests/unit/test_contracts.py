"""TC061 contracts 1.2 subset: strict types, states, versions, null and HTTP."""
import importlib
import asyncio
import json
from pathlib import Path
from uuid import uuid4

import pytest
import httpx
from jsonschema import Draft202012Validator, FormatChecker
from pydantic import TypeAdapter, ValidationError

from app.core.contracts import ErrorBody, ErrorEnvelope, Health, Revision, Version

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "docs/architecture/contracts/contracts.schema.json").read_text(encoding="utf-8"))


def validate(name, payload):
    Draft202012Validator({"$ref": f"#/$defs/{name}", "$defs": SCHEMA["$defs"]}, format_checker=FormatChecker()).validate(payload)


def test_TC061_health_states_and_unknown_fields():
    for status in ["alive", "ready", "not_ready"]:
        validate("Health", Health(status=status).model_dump())
    for payload in [{"status": "ok"}, {"status": "alive", "extra": True}, {"status": "alive", "checks": {"db": 1}}]:
        with pytest.raises(ValidationError):
            Health.model_validate(payload)


@pytest.mark.parametrize("kind,valid,invalid", [(Version, 1, [0, -1, "1", True]), (Revision, 0, [-1, "0", False])])
def test_TC061_versions(kind, valid, invalid):
    adapter = TypeAdapter(kind, config={"strict": True})
    assert adapter.validate_python(valid) == valid
    for value in invalid:
        with pytest.raises(ValidationError):
            adapter.validate_python(value)


def test_TC061_nullable_and_uuid_format():
    body = dict(code="NOT_READY", message="尚未准备", details={}, retryable=True, turn_id=None)
    for turn_id in [None, uuid4()]:
        validate("ErrorEnvelope", ErrorEnvelope(error=ErrorBody(**{**body, "turn_id": turn_id}), request_id="req-test").model_dump(mode="json"))
    with pytest.raises(ValidationError):
        ErrorBody(**{**body, "turn_id": "not-a-uuid"})
    with pytest.raises(ValidationError):
        ErrorBody(**{k: v for k, v in body.items() if k != "turn_id"})


def test_TC061_http_contract(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("MODEL_MODE", "disabled")
    module = importlib.import_module("app.main")
    async def check():
      async with httpx.AsyncClient(transport=httpx.ASGITransport(app=module.create_app()), base_url="http://test") as client:
        for path, status, state in [("live", 200, "alive"), ("ready", 503, "not_ready")]:
            response = await client.get(f"/api/v1/health/{path}")
            assert response.status_code == status
            payload = response.json()
            assert payload["request_id"] == response.headers["x-request-id"]
            assert payload["data"]["status"] == state
            validate("Health", payload["data"])
        response = await client.get("/missing")
        assert response.status_code == 404
        validate("ErrorEnvelope", response.json())
        operations = json.loads((ROOT / "docs/architecture/contracts/http-operations.json").read_text(encoding="utf-8"))["operations"]
        expected = {op["path"] for op in operations if "/health/" in op["path"]}
        assert set((await client.get("/openapi.json")).json()["paths"]) == expected
    asyncio.run(check())
