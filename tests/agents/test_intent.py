"""Tests for intent classifier — casual, admin, agent, continuation routing."""

from __future__ import annotations

from backend.app.agents.intent import casual_response, classify_intent


class TestClassifyIntent:
    """Intent classification — routing messages to correct path."""

    def test_casual_greetings(self):
        assert classify_intent("hello") == "casual"
        assert classify_intent("Hi") == "casual"
        assert classify_intent("hey there") == "casual"
        assert classify_intent("good morning") == "casual"

    def test_casual_thanks(self):
        assert classify_intent("thanks") == "casual"
        assert classify_intent("thank you") == "casual"
        assert classify_intent("thx") == "casual"

    def test_casual_acknowledgments(self):
        assert classify_intent("ok") == "casual"
        assert classify_intent("okay") == "casual"
        assert classify_intent("got it") == "casual"
        assert classify_intent("sure") == "casual"

    def test_casual_farewells(self):
        assert classify_intent("bye") == "casual"
        assert classify_intent("goodbye") == "casual"
        assert classify_intent("see you") == "casual"

    def test_casual_how_are_you(self):
        assert classify_intent("how are you") == "casual"
        assert classify_intent("what's up") == "casual"

    def test_admin_commands(self):
        assert classify_intent("/status") == "admin"
        assert classify_intent("/help") == "admin"
        assert classify_intent("status") == "admin"
        assert classify_intent("health") == "admin"
        assert classify_intent("version") == "admin"

    def test_admin_system_commands(self):
        assert classify_intent("reload") == "admin"
        assert classify_intent("restart") == "admin"
        assert classify_intent("show logs") == "admin"
        assert classify_intent("get config") == "admin"

    def test_continuation_signals(self):
        assert classify_intent("continue") == "continuation"
        assert classify_intent("keep going") == "continuation"
        assert classify_intent("go on") == "continuation"
        assert classify_intent("next") == "continuation"

    def test_agent_tasks(self):
        assert classify_intent("find files modified today") == "agent"
        assert classify_intent("summarize the latest commit") == "agent"
        assert classify_intent("what is the capital of France") == "agent"
        assert classify_intent("search for TODO comments in code") == "agent"

    def test_empty_message_defaults_to_agent(self):
        assert classify_intent("") == "agent"

    def test_short_task_is_agent(self):
        assert classify_intent("summarize") == "agent"
        assert classify_intent("search xyz") == "agent"
        assert classify_intent("run") == "agent"


class TestCasualResponse:
    """Fast-path responses for casual messages."""

    def test_hello_response(self):
        resp = casual_response("hello")
        assert "Hello" in resp

    def test_thanks_response(self):
        resp = casual_response("thanks")
        assert "welcome" in resp.lower()

    def test_bye_response(self):
        resp = casual_response("bye")
        assert "Goodbye" in resp

    def test_how_are_you_response(self):
        resp = casual_response("how are you")
        assert "doing well" in resp.lower()

    def test_lol_response(self):
        resp = casual_response("lol")
        assert resp == "😊"

    def test_fallback_response(self):
        resp = casual_response("nice")
        assert "great" in resp.lower()
