"""The local profile: stored choices, learned values, sources, reset, delete, and chat use."""

import model_client
import profile
import sessions


def _done(cid, skill, reason="completed"):
    sessions.create_session(cid, skill)
    sessions.end_session(cid, reason)


def test_empty_profile():
    p = profile.get_profile()
    assert p["display_name"] is None and p["usual_skill"] is None and p["usual_source"] is None
    assert p["animate_source"] == "system" and p["last_checkin"] is None
    assert p["counts"]["breathing"] == {"completed": 0, "stopped": 0, "left": 0}


def test_counts_and_learned_usual_update_when_a_session_ends():
    _done("a", "stop")
    assert profile.get_profile()["usual_skill"] == "stop"
    _done("b", "breathing")
    _done("c", "breathing")
    _done("d", "breathing", "stopped")
    p = profile.get_profile()
    assert (p["usual_skill"], p["usual_source"]) == ("breathing", "learned")
    assert p["counts"]["breathing"] == {"completed": 2, "stopped": 1, "left": 0}


def test_chosen_usual_overrides_learned_until_reset(client):
    _done("a", "breathing")
    p = client.post("/api/profile", json={"usual_skill": "reframe", "animate_circle": False, "display_name": "  Sam  "}).json()
    assert (p["usual_skill"], p["usual_source"], p["display_name"]) == ("reframe", "chosen", "Sam")
    assert (p["animate_circle"], p["animate_source"]) == (False, "chosen")
    assert client.get("/api/usual").json() == {"skill": "reframe", "source": "chosen"}
    p = client.post("/api/profile/reset").json()
    assert (p["usual_skill"], p["usual_source"], p["animate_source"], p["display_name"]) == ("breathing", "learned", "system", "Sam")


def test_checkin_is_stored_with_a_time(client):
    p = client.post("/api/profile", json={"last_checkin": "overwhelmed"}).json()
    assert p["last_checkin"] == "overwhelmed" and p["last_checkin_at"]
    assert client.post("/api/profile", json={"last_checkin": "panicked"}).status_code == 422
    assert client.post("/api/profile", json={"usual_skill": "grounding"}).status_code == 422


def test_summary_has_labels_and_counts_only():
    s = sessions.create_session("x", "reframe")
    sessions.end_session("x", "completed")
    sessions.add_message(s["id"], "model", "FICTIONAL-PRIVATE-TEXT", "mock", 1)
    profile.update_profile({"display_name": "Sam", "last_checkin": "tense"})
    summary = profile.summary()
    assert summary == ("Name: Sam. Usual skill: Cognitive reframe [reframe], learned. "
                       "Last check-in: Tense or wound up. Sessions: Cognitive reframe 1 completed.")
    assert "FICTIONAL" not in summary


def test_delete_all_clears_the_profile(client):
    client.post("/api/profile", json={"display_name": "Sam", "usual_skill": "stop"})
    _done("a", "breathing")
    client.delete("/api/history")
    p = client.get("/api/profile").json()
    assert p["display_name"] is None and p["usual_skill"] is None


def test_mock_chat_reply_is_tailored_to_the_profile(client):
    profile.update_profile({"display_name": "Sam", "usual_skill": "stop"})
    cid = client.post("/api/conversations").json()["id"]
    reply = client.post(f"/api/conversations/{cid}/messages", json={"text": "Fictional: nervous before an exam, any help"}).json()["reply"]
    assert reply["text"].startswith("Hi Sam.") and "STOP" in reply["text"]
    assert reply["offer_skill"] == "stop" and reply["model_status"] == "mock"


def test_diagnosis_request_gets_the_limit_reply(client):
    cid = client.post("/api/conversations").json()["id"]
    reply = client.post(f"/api/conversations/{cid}/messages", json={"text": "Can you tell me if I have anxiety?"}).json()["reply"]
    assert reply["text"] == model_client.CHAT_FALLBACK
    assert "can't assess anything" in reply["text"]
    assert reply["role"] == "fallback" and reply["offer_skill"] is None
