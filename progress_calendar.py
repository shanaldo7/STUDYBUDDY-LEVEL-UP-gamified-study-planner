"""Historical StudyBuddy activity calendar.

Additive UI only: reads existing telemetry tables and never changes progression,
rewards, quests, exams, or revision scheduling.
"""

from datetime import date, timedelta
import html
import streamlit as st


def _daily_activity(db, start, end):
    days = {}
    cursor = start
    while cursor <= end:
        key = cursor.isoformat()
        days[key] = {
            "xp": 0,
            "focus": 0,
            "quests": 0,
            "dungeons": 0,
            "reviews": 0,
        }
        cursor += timedelta(days=1)

    with db() as con:
        for row in con.execute(
            """SELECT substr(happened_at,1,10) d, COALESCE(SUM(amount),0) xp
               FROM xp_log
               WHERE substr(happened_at,1,10) BETWEEN ? AND ?
               GROUP BY d""",
            (start.isoformat(), end.isoformat()),
        ):
            if row["d"] in days:
                days[row["d"]]["xp"] = int(row["xp"] or 0)

        for row in con.execute(
            """SELECT substr(started_at,1,10) d, COALESCE(SUM(minutes),0) minutes
               FROM focus_sessions
               WHERE completed=1 AND substr(started_at,1,10) BETWEEN ? AND ?
               GROUP BY d""",
            (start.isoformat(), end.isoformat()),
        ):
            if row["d"] in days:
                days[row["d"]]["focus"] = int(row["minutes"] or 0)

        for row in con.execute(
            """SELECT substr(completed_at,1,10) d, COUNT(*) n
               FROM quests
               WHERE completed=1 AND completed_at IS NOT NULL
                 AND substr(completed_at,1,10) BETWEEN ? AND ?
               GROUP BY d""",
            (start.isoformat(), end.isoformat()),
        ):
            if row["d"] in days:
                days[row["d"]]["quests"] = int(row["n"] or 0)

        for row in con.execute(
            """SELECT substr(played_at,1,10) d, COUNT(*) n
               FROM dungeon_runs
               WHERE substr(played_at,1,10) BETWEEN ? AND ?
               GROUP BY d""",
            (start.isoformat(), end.isoformat()),
        ):
            if row["d"] in days:
                days[row["d"]]["dungeons"] = int(row["n"] or 0)

        for row in con.execute(
            """SELECT substr(reviewed_at,1,10) d, COUNT(*) n
               FROM review_log
               WHERE substr(reviewed_at,1,10) BETWEEN ? AND ?
               GROUP BY d""",
            (start.isoformat(), end.isoformat()),
        ):
            if row["d"] in days:
                days[row["d"]]["reviews"] = int(row["n"] or 0)

    return days


def _activity_level(item):
    """Return a stable 0-4 intensity from existing study activity."""
    xp = max(0, item["xp"])
    focus = max(0, item["focus"])
    quests = max(0, item["quests"])
    dungeons = max(0, item["dungeons"])
    reviews = max(0, item["reviews"])

    score = (
        min(xp, 100)
        + min(focus, 60)
        + min(quests * 20, 40)
        + min(dungeons * 25, 50)
        + min(reviews * 8, 40)
    )
    if score <= 0:
        return 0
    if score < 30:
        return 1
    if score < 70:
        return 2
    if score < 130:
        return 3
    return 4


def render_progress_calendar(db, profile):
    today = date.today()
    start = today - timedelta(days=83)
    activity = _daily_activity(db, start, today)

    active_days = sum(1 for x in activity.values() if _activity_level(x) > 0)
    total_xp = sum(x["xp"] for x in activity.values())
    focus_minutes = sum(x["focus"] for x in activity.values())
    completed_quests = sum(x["quests"] for x in activity.values())
    dungeon_runs = sum(x["dungeons"] for x in activity.values())
    reviews = sum(x["reviews"] for x in activity.values())

    st.markdown(
        """<div class="hero">
        <div class="hero-kicker">HUNTER HISTORY · CONSISTENCY MAP</div>
        <div class="hero-title">Progress Calendar</div>
        <p class="hero-sub">See when your study activity actually happened. Every cell is calculated from StudyBuddy's existing local telemetry.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    a, b, c, d, e = st.columns(5)
    a.metric("Active days", active_days)
    b.metric("XP earned", f"{total_xp:,}")
    c.metric("Focus", f"{focus_minutes}m")
    d.metric("Quests", completed_quests)
    e.metric("Reviews", reviews)

    # Render 12 weeks as a compact GitHub-style activity map.
    # The first column starts at the Sunday containing the 84-day window.
    grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
    cells = []
    cursor = grid_start
    while cursor <= today:
        cells.append(cursor)
        cursor += timedelta(days=1)

    levels = []
    for dte in cells:
        item = activity.get(dte.isoformat(), {})
        level = _activity_level(item) if item else 0
        label = "No recorded study activity"
        if item and level:
            label = (
                f"{item['xp']} XP · {item['focus']}m focus · "
                f"{item['quests']} quests · {item['dungeons']} dungeons · "
                f"{item['reviews']} reviews"
            )
        levels.append((dte, level, label))

    style = """
    <style>
      .progress-calendar-wrap{overflow-x:auto;padding:10px 4px 16px}
      .progress-calendar{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,14px);grid-auto-columns:14px;gap:4px;width:max-content}
      .progress-day{width:14px;height:14px;border-radius:4px;border:1px solid rgba(126,177,235,.12);box-sizing:border-box}
      .progress-day.l0{background:rgba(126,177,235,.055)}
      .progress-day.l1{background:rgba(103,232,249,.20);border-color:rgba(103,232,249,.20)}
      .progress-day.l2{background:rgba(34,211,238,.42);border-color:rgba(34,211,238,.38)}
      .progress-day.l3{background:rgba(139,92,246,.62);border-color:rgba(139,92,246,.55)}
      .progress-day.l4{background:rgba(251,191,36,.90);border-color:rgba(251,191,36,.75);box-shadow:0 0 8px rgba(251,191,36,.20)}
      .progress-legend{display:flex;justify-content:flex-end;align-items:center;gap:6px;color:#71839f;font-size:.65rem;margin-top:8px}
      .progress-legend .progress-day{display:inline-block}
      .progress-calendar-note{color:#71839f;font-size:.68rem;margin-top:8px}
      .progress-detail{padding:14px 16px;border:1px solid rgba(126,177,235,.15);border-radius:16px;background:linear-gradient(145deg,rgba(13,23,43,.72),rgba(10,14,27,.66));margin-top:12px}
      .progress-detail b{color:#edf5ff}.progress-detail span{color:#71839f;font-size:.72rem}
      @media(max-width:700px){.progress-calendar{grid-auto-columns:12px;grid-template-rows:repeat(7,12px);gap:3px}.progress-day{width:12px;height:12px}}
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

    calendar_html = '<div class="progress-calendar-wrap"><div class="progress-calendar">'
    for dte, level, label in levels:
        calendar_html += (
            f'<div class="progress-day l{level}" title="{html.escape(dte.isoformat() + " · " + label, quote=True)}"></div>'
        )
    calendar_html += "</div>"
    calendar_html += (
        '<div class="progress-legend"><span>Less</span>'
        '<span class="progress-day l0"></span><span class="progress-day l1"></span>'
        '<span class="progress-day l2"></span><span class="progress-day l3"></span>'
        '<span class="progress-day l4"></span><span>More</span></div>'
        '<div class="progress-calendar-note">Intensity combines XP, completed focus minutes, completed quests, dungeon runs and revision reviews. It is not a grade.</div>'
        "</div>"
    )
    st.markdown(calendar_html, unsafe_allow_html=True)

    st.subheader("Recent activity")
    recent = sorted(
        ((dte, item) for dte, item in activity.items() if _activity_level(item) > 0),
        key=lambda pair: pair[0],
        reverse=True,
    )[:14]
    if not recent:
        st.info("No activity is recorded in the last 84 days yet. Complete a quest, focus session, dungeon, or revision review to populate the map.")
        return

    for dte, item in recent:
        st.markdown(
            f"""<div class="progress-detail">
              <b>{html.escape(dte)}</b>
              <span> · {item["xp"]} XP · {item["focus"]} min focus · {item["quests"]} quests ·
              {item["dungeons"]} dungeons · {item["reviews"]} reviews</span>
            </div>""",
            unsafe_allow_html=True,
        )

    if dungeon_runs:
        st.caption(f"{dungeon_runs} dungeon run(s) recorded in this 84-day window.")
