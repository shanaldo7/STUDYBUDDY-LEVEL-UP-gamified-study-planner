"""Additive hunter-system UX and progression helpers for StudyBuddy.

This module is intentionally backend-agnostic: the existing SQLite schema, XP
logic, quests and dungeon systems remain authoritative. It only adds tables and
UI for skill progression, offline-safe browser journaling, and accessibility.
"""

import html
import json
import random
import time
import uuid

import streamlit as st
import streamlit.components.v1 as components


SKILLS = [
    {
        "id": "focus_boost",
        "name": "Focus Boost",
        "icon": "◈",
        "cost": 1,
        "tier": 1,
        "description": "+10% XP from completed focus sessions.",
        "requires": [],
    },
    {
        "id": "hint_unlock",
        "name": "Hint Unlock",
        "icon": "◇",
        "cost": 1,
        "tier": 1,
        "description": "Unlock one tactical hint per dungeon run.",
        "requires": [],
    },
    {
        "id": "revision_mastery",
        "name": "Revision Mastery",
        "icon": "✦",
        "cost": 1,
        "tier": 2,
        "description": "Good/Easy revision reviews receive a small interval bonus.",
        "requires": ["focus_boost"],
    },
    {
        "id": "quiz_combo",
        "name": "Quiz Combo",
        "icon": "⚡",
        "cost": 2,
        "tier": 2,
        "description": "Consecutive correct dungeon answers gain stronger damage scaling.",
        "requires": ["hint_unlock"],
    },
    {
        "id": "xp_multiplier",
        "name": "XP Multiplier",
        "icon": "✧",
        "cost": 3,
        "tier": 3,
        "description": "+10% XP on future progression rewards.",
        "requires": ["revision_mastery", "quiz_combo"],
    },
]




HUNTER_SYSTEM_CSS = """
<style>
.hunter-skill-hero{position:relative;overflow:hidden;padding:22px 24px;margin:0 0 18px;border:1px solid rgba(103,232,249,.22);border-radius:20px;background:radial-gradient(circle at 90% 20%,rgba(167,139,250,.16),transparent 35%),linear-gradient(145deg,rgba(7,15,29,.94),rgba(19,12,37,.94));box-shadow:0 18px 50px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.05)}
.hunter-skill-kicker{color:#67e8f9;font:800 .64rem Orbitron,sans-serif;letter-spacing:2px}
.hunter-skill-title{color:#f5fbff;font:800 clamp(1.35rem,3vw,2rem) Orbitron,sans-serif;margin-top:5px}
.hunter-skill-sub{color:#8fa3bf;font-size:.84rem;margin-top:6px}
.skill-node{min-height:180px;padding:17px;border-radius:16px;border:1px solid rgba(126,177,235,.16);background:linear-gradient(150deg,rgba(17,29,50,.78),rgba(8,13,25,.82));transition:transform .2s,border-color .2s,box-shadow .2s;margin-bottom:10px}
.skill-node:hover{transform:translateY(-4px);border-color:rgba(103,232,249,.35);box-shadow:0 14px 32px rgba(0,0,0,.3)}
.skill-node.unlocked{border-color:rgba(74,222,128,.32);box-shadow:inset 0 0 22px rgba(74,222,128,.035)}
.skill-node.ready{border-color:rgba(103,232,249,.30)}
.skill-node.locked{opacity:.58}
.skill-node-icon{font-size:1.6rem;color:#67e8f9;text-shadow:0 0 14px rgba(103,232,249,.35)}
.skill-node-name{font:800 1rem Orbitron,sans-serif;color:#f4f8ff;margin-top:8px}
.skill-node-copy{font-size:.74rem;color:#8298b3;line-height:1.5;margin-top:7px;min-height:48px}
.skill-node-meta{font-size:.65rem;color:#67e8f9;letter-spacing:1px;font-weight:800;margin-top:10px}
@media(prefers-reduced-motion:reduce){.skill-node{transition:none}.skill-node:hover{transform:none}}
</style>
"""

def ensure_tables(db_fn):
    with db_fn() as con:
        con.execute(
            """CREATE TABLE IF NOT EXISTS hunter_progress (
                id INTEGER PRIMARY KEY CHECK(id=1),
                max_level_seen INTEGER NOT NULL DEFAULT 1,
                skill_points_spent INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            )"""
        )
        con.execute(
            """CREATE TABLE IF NOT EXISTS hunter_skills (
                skill_id TEXT PRIMARY KEY,
                unlocked_at TEXT NOT NULL
            )"""
        )


def sync_level(db_fn, level, now_text):
    ensure_tables(db_fn)
    with db_fn() as con:
        row = con.execute("SELECT max_level_seen FROM hunter_progress WHERE id=1").fetchone()
        if not row:
            con.execute(
                "INSERT INTO hunter_progress(id,max_level_seen,skill_points_spent,updated_at) VALUES(1,?,?,?)",
                (max(1, int(level)), 0, now_text),
            )
        elif int(level) > int(row["max_level_seen"]):
            con.execute(
                "UPDATE hunter_progress SET max_level_seen=?,updated_at=? WHERE id=1",
                (int(level), now_text),
            )


def skill_state(db_fn, level, now_text):
    sync_level(db_fn, level, now_text)
    with db_fn() as con:
        progress = con.execute("SELECT * FROM hunter_progress WHERE id=1").fetchone()
        unlocked = {r["skill_id"] for r in con.execute("SELECT skill_id FROM hunter_skills").fetchall()}
    earned = max(0, int(progress["max_level_seen"]) - 1)
    spent = int(progress["skill_points_spent"])
    return {
        "earned": earned,
        "spent": spent,
        "available": max(0, earned - spent),
        "max_level": int(progress["max_level_seen"]),
        "unlocked": unlocked,
    }


def skill_unlocked(db_fn, skill_id):
    with db_fn() as con:
        return bool(con.execute("SELECT 1 FROM hunter_skills WHERE skill_id=?", (skill_id,)).fetchone())


def unlock_skill(db_fn, skill_id, level, now_text):
    state = skill_state(db_fn, level, now_text)
    skill = next((s for s in SKILLS if s["id"] == skill_id), None)
    if not skill:
        return False, "Skill not found."
    if skill_id in state["unlocked"]:
        return False, "Skill already unlocked."
    if state["available"] < skill["cost"]:
        return False, "Not enough skill points."
    missing = [x for x in skill["requires"] if x not in state["unlocked"]]
    if missing:
        names = ", ".join(next(s["name"] for s in SKILLS if s["id"] == x) for x in missing)
        return False, f"Requires: {names}."
    with db_fn() as con:
        con.execute("INSERT INTO hunter_skills(skill_id,unlocked_at) VALUES(?,?)", (skill_id, now_text))
        con.execute(
            "UPDATE hunter_progress SET skill_points_spent=skill_points_spent+?,updated_at=? WHERE id=1",
            (skill["cost"], now_text),
        )
    return True, f"{skill['name']} unlocked."


def xp_multiplier(db_fn):
    return 1.10 if skill_unlocked(db_fn, "xp_multiplier") else 1.0


def focus_multiplier(db_fn):
    return 1.10 if skill_unlocked(db_fn, "focus_boost") else 1.0


def combo_multiplier(db_fn, combo):
    if not skill_unlocked(db_fn, "quiz_combo"):
        return 1.0
    return min(2.0, 1.0 + max(0, int(combo) - 1) * 0.12)


def revision_interval_multiplier(db_fn):
    return 1.10 if skill_unlocked(db_fn, "revision_mastery") else 1.0


def render_skill_tree(db_fn, profile, now_text):
    st.markdown(HUNTER_SYSTEM_CSS, unsafe_allow_html=True)
    state = skill_state(db_fn, int(profile["xp"]) // 100 + 1, now_text)
    st.markdown(
        """<div class="hunter-skill-hero">
          <div class="hunter-skill-kicker">AWAKENING TREE · EARNED PROGRESSION</div>
          <div class="hunter-skill-title">Hunter Skill Tree</div>
          <div class="hunter-skill-sub">Spend earned skill points on study abilities. Nothing is pay-to-win.</div>
        </div>""",
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    a.metric("Available points", state["available"])
    b.metric("Points earned", state["earned"])
    c.metric("Highest level reached", state["max_level"])

    for tier in (1, 2, 3):
        tier_skills = [s for s in SKILLS if s["tier"] == tier]
        st.markdown(f"### Tier {tier}")
        cols = st.columns(len(tier_skills))
        for col, skill in zip(cols, tier_skills):
            with col:
                unlocked = skill["id"] in state["unlocked"]
                prereq_ok = all(x in state["unlocked"] for x in skill["requires"])
                status = "UNLOCKED" if unlocked else ("AVAILABLE" if prereq_ok else "LOCKED")
                cls = "skill-node unlocked" if unlocked else ("skill-node ready" if prereq_ok else "skill-node locked")
                st.markdown(
                    f"""<div class="{cls}">
                      <div class="skill-node-icon">{skill["icon"]}</div>
                      <div class="skill-node-name">{html.escape(skill["name"])}</div>
                      <div class="skill-node-copy">{html.escape(skill["description"])}</div>
                      <div class="skill-node-meta">{status} · {skill["cost"]} SP</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if not unlocked:
                    label = f"Unlock · {skill['cost']} SP"
                    if st.button(label, key=f"unlock_skill_{skill['id']}", disabled=not prereq_ok, use_container_width=True):
                        ok, msg = unlock_skill(db_fn, skill["id"], int(profile["xp"]) // 100 + 1, now_text)
                        if ok:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.warning(msg)

    st.caption("Skill points are earned from Hunter level progression and remain earned even if XP later drops.")


def render_offline_indicator():
    components.html(
        """
<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:transparent;font-family:Inter,system-ui">
<div id="status" role="status" aria-live="polite"
     style="display:inline-flex;align-items:center;gap:7px;padding:6px 10px;border-radius:999px;
            border:1px solid rgba(126,177,235,.18);background:rgba(7,13,25,.72);
            color:#9fb2cb;font-size:12px">
  <span id="dot" style="width:7px;height:7px;border-radius:50%;background:#4ade80;display:inline-block"></span>
  <span id="text">Online · local progress protected</span>
</div>
<script>
const status = document.getElementById("status");
const dot = document.getElementById("dot");
const text = document.getElementById("text");
function paint(){
  const online = navigator.onLine;
  dot.style.background = online ? "#4ade80" : "#fbbf24";
  text.textContent = online
    ? "Online · local progress protected"
    : "Offline — progress saved on this device";
  status.style.borderColor = online ? "rgba(74,222,128,.18)" : "rgba(251,191,36,.25)";
}
window.addEventListener("online", paint);
window.addEventListener("offline", paint);
paint();
</script>
</body></html>
""",
        height=38,
    )


def retry_call(fn, attempts=3, base_delay=0.45):
    """Retry transient failures with exponential backoff + jitter."""
    last = None
    for attempt in range(max(1, int(attempts))):
        try:
            return fn()
        except Exception as exc:
            last = exc
            if attempt >= attempts - 1:
                raise
            time.sleep(base_delay * (2 ** attempt) + random.uniform(0, base_delay))
    raise last


def make_completion_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex}"


def render_offline_journal():
    """Persist browser-side completion receipts so completed timers are not forgotten."""
    components.html(
        """
<script>
(() => {
  const KEY = "studybuddy_completion_journal_v1";
  const read = () => {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); }
    catch (_) { return []; }
  };
  const write = (items) => {
    try { localStorage.setItem(KEY, JSON.stringify(items.slice(-100))); } catch (_) {}
  };
  const api = {
    add(item) {
      const items = read();
      if (!items.some(x => x.id === item.id)) {
        items.push(item);
        write(items);
      }
    }
  };
  window.StudyBuddyOffline = api;
})();
</script>
""",
        height=0,
    )
