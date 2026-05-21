"""
Spark Core 2.0 - Ronde 2 deel 1 + Avatar polish backend tests.

Covers:
- Avatar gallery with locked bot-owned avatars (locket-stempel)
- Roadkill logo fallback (is_fallback boolean + fallback_url)
- Locked avatar guard in PUT /api/avatar/select (403 for non-admin, allow for admin/owner)
- Community messages enriched with avatar + is_fallback
- Community archive tree (year/month/day) + day messages
- Community recap (offset_days + specific date)
- Chat intent: community_recap ('wat is gisteren besproken', 'community recap', 'eergisteren')
- Base Line KB concept recognition
"""
import os
import pytest
import requests

BASE_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].splitlines()[0]
).rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_ID = "user-001"
NON_ADMIN_ID = "user-c609d7d1"
HARRY_AVATAR_REF = "gallery:81f84abcc3b5"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ----- 1. Gallery: 28 avatars, 3 locked bots -----
def test_avatar_gallery_locked_bots(session):
    r = session.get(f"{API}/avatar/gallery")
    assert r.status_code == 200, r.text
    data = r.json()
    avatars = data.get("avatars") or data.get("items") or data
    if isinstance(data, dict) and "avatars" in data:
        avatars = data["avatars"]
    assert isinstance(avatars, list)
    assert len(avatars) == 28, f"Expected 28 avatars, got {len(avatars)}"

    locked = [a for a in avatars if a.get("locked") is True]
    assert len(locked) == 3, f"Expected exactly 3 locked avatars, got {len(locked)}: {[a.get('id') for a in locked]}"

    bot_owners = {a.get("bot_owner") for a in locked}
    assert bot_owners == {"bot-harry", "bot-smith", "bot-madelief"}, f"Unexpected bot_owners: {bot_owners}"


# ----- 2. Current avatar with fallback -----
def test_avatar_current_fallback_fields(session):
    r = session.get(f"{API}/avatar/current/{ADMIN_ID}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "is_fallback" in data, f"Missing is_fallback in: {data}"
    assert isinstance(data["is_fallback"], bool)
    assert "fallback_url" in data, f"Missing fallback_url in: {data}"
    assert "/api/avatar/gallery/roadkill-logo/image" in data["fallback_url"], data["fallback_url"]


# ----- 3. Non-admin selecting locked bot avatar → 403 -----
def test_select_locked_avatar_non_admin_forbidden(session):
    # Save Marieke's current avatar first
    cur = session.get(f"{API}/avatar/current/{NON_ADMIN_ID}").json()
    original_ref = cur.get("avatar_ref") or cur.get("ref")

    r = session.put(
        f"{API}/avatar/select/{NON_ADMIN_ID}",
        json={"avatar_ref": HARRY_AVATAR_REF},
    )
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"
    detail = (r.json().get("detail") or r.text).lower()
    assert "bot-harry" in detail, f"Expected 'bot-harry' in error detail: {detail}"

    # Restore if changed (defensive — should not have changed since 403)
    if original_ref:
        session.put(f"{API}/avatar/select/{NON_ADMIN_ID}", json={"avatar_ref": original_ref})


# ----- 4. Admin can bypass locked guard -----
def test_select_locked_avatar_admin_bypass(session):
    # Save admin current avatar to restore
    cur = session.get(f"{API}/avatar/current/{ADMIN_ID}").json()
    original_ref = cur.get("avatar_ref") or cur.get("ref")

    r = session.put(
        f"{API}/avatar/select/{ADMIN_ID}",
        json={"avatar_ref": HARRY_AVATAR_REF},
    )
    assert r.status_code == 200, f"Admin bypass failed: {r.status_code} {r.text}"

    # Restore
    if original_ref:
        session.put(f"{API}/avatar/select/{ADMIN_ID}", json={"avatar_ref": original_ref})


# ----- 5. Bot can select its own locked avatar -----
def test_select_own_locked_avatar_bot_harry(session):
    r = session.put(
        f"{API}/avatar/select/bot-harry",
        json={"avatar_ref": HARRY_AVATAR_REF},
    )
    assert r.status_code == 200, f"Bot-harry selecting own avatar failed: {r.status_code} {r.text}"


# ----- 6. Community messages enriched with avatar + fallback -----
def test_community_messages_avatar_enrichment(session):
    r = session.get(f"{API}/bots/community/messages")
    assert r.status_code == 200, r.text
    data = r.json()
    messages = data.get("messages") if isinstance(data, dict) else data
    assert isinstance(messages, list), f"messages not a list: {type(messages)}"
    assert len(messages) > 0, "Empty messages list"

    for m in messages[:20]:
        assert "avatar" in m, f"missing avatar in: {m}"
        av = m["avatar"]
        assert isinstance(av, dict), f"avatar not dict: {av}"
        # is_fallback is only present (true) when the message author has no avatar
        if av.get("is_fallback") is True:
            url = av.get("url") or av.get("fallback_url") or ""
            assert "roadkill-logo" in url, f"fallback should point to roadkill-logo, got: {url}"


# ----- 7. Community archive tree -----
def test_community_archive_tree(session):
    r = session.get(f"{API}/bots/community/archive")
    assert r.status_code == 200, r.text
    data = r.json()
    tree = data.get("tree") or data.get("archive") or data
    assert isinstance(tree, dict), f"tree not dict: {type(tree)}"
    assert len(tree) > 0, "Empty archive tree"

    # Validate structure year -> month -> day -> {count, first, last}
    for year, months in tree.items():
        assert year.isdigit() and len(year) == 4, f"bad year: {year}"
        assert isinstance(months, dict)
        for month, days in months.items():
            assert isinstance(days, dict), f"days for {year}/{month} not dict"
            for day, info in days.items():
                assert isinstance(info, dict)
                assert "count" in info
                assert "first" in info
                assert "last" in info
                break
            break
        break


# ----- 8. Archive for specific day -----
def test_community_archive_day_messages(session):
    r = session.get(f"{API}/bots/community/archive", params={"year": "2026", "month": "03", "day": "18"})
    assert r.status_code == 200, r.text
    data = r.json()
    messages = data.get("messages") if isinstance(data, dict) else data
    assert isinstance(messages, list), f"messages not list: {type(messages)}"
    if len(messages) >= 2:
        # Verify chronological order
        ts = [m.get("timestamp") or m.get("ts") or m.get("time") for m in messages]
        assert ts == sorted(ts), "messages not chronologically sorted"


# ----- 9. Recap by offset_days=1 (yesterday) -----
def test_community_recap_yesterday(session):
    r = session.get(f"{API}/bots/community/recap", params={"offset_days": 1})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "date" in data
    assert "recap" in data
    assert "total" in data or "count" in data or "total_count" in data
    assert "top_topics" in data
    assert "users" in data or "user_counts" in data
    assert "messages_preview" in data or "preview" in data


# ----- 10. Recap by specific date 2026-03-18 -----
def test_community_recap_specific_date(session):
    r = session.get(f"{API}/bots/community/recap", params={"date": "2026-03-18"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("date") == "2026-03-18", f"unexpected date: {data.get('date')}"
    users = data.get("users") or data.get("user_counts") or {}
    # Willem Spakman should have 6 messages
    found = False
    for name, cnt in users.items():
        if "willem" in name.lower() and "spakman" in name.lower():
            assert cnt == 6, f"Willem Spakman count {cnt} != 6"
            found = True
            break
    assert found, f"Willem Spakman not in users dict: {users}"


# ----- 11. Chat intent: 'Wat is gisteren in de community besproken?' -----
def test_chat_intent_community_recap_gisteren(session):
    r = session.post(
        f"{API}/chat/message",
        json={"message": "Wat is gisteren in de community besproken?", "user_id": ADMIN_ID},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("type") == "community_recap", f"type={data.get('type')} expected community_recap. Full: {data}"
    msg = data.get("message") or data.get("response") or ""
    assert "Community-recap gisteren" in msg, f"missing header in message: {msg[:300]}"
    assert msg.lstrip().startswith("📋"), f"message should start with 📋: {msg[:120]}"


# ----- 12. Chat intent: 'community recap' → today (offset 0) -----
def test_chat_intent_community_recap_today(session):
    r = session.post(
        f"{API}/chat/message",
        json={"message": "community recap", "user_id": ADMIN_ID},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("type") == "community_recap", f"type={data.get('type')} expected community_recap. Full: {data}"


# ----- 13. Chat intent: 'eergisteren' → offset_days=2 -----
def test_chat_intent_community_recap_eergisteren(session):
    r = session.post(
        f"{API}/chat/message",
        json={"message": "wat is eergisteren besproken", "user_id": ADMIN_ID},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("type") == "community_recap", f"type={data.get('type')} expected community_recap. Full: {data}"
    msg = data.get("message") or data.get("response") or ""
    # Should reference eergisteren (offset 2)
    assert "eergisteren" in msg.lower() or "📋" in msg, f"unexpected recap msg: {msg[:200]}"


# ----- 14. KB: Base Line concept (after cache clear) -----
def test_kb_base_line_concept(session):
    # Clear KB cache first
    clr = session.post(f"{API}/admin/storage-cache/clear")
    # Tolerate 200/204; do not fail if endpoint missing
    assert clr.status_code in (200, 204, 404), clr.text

    r = session.post(
        f"{API}/chat/message",
        json={"message": "vertel over Base Line", "user_id": ADMIN_ID},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    msg = (data.get("message") or data.get("response") or "").lower()
    assert "base line" in msg or "baseline" in msg, f"Spark did not mention Base Line: {msg[:400]}"
