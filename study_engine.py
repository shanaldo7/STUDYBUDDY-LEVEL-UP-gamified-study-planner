"""StudyBuddy adaptive learning engine.

Local-first: exam planning, mastery scoring, weak-topic detection and
wrong-answer -> revision-card conversion. No extra runtime dependency.
"""

from datetime import date, datetime, timedelta
import hashlib
import html


def _now():
    return datetime.now().isoformat(timespec="seconds")


def ensure_tables(db):
    """Additive schema migration. Never deletes existing StudyBuddy data."""
    with db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT,
                exam_date TEXT NOT NULL,
                target_score INTEGER NOT NULL DEFAULT 80,
                created_at TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS exam_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                weight INTEGER NOT NULL DEFAULT 1,
                status TEXT NOT NULL DEFAULT 'Planned',
                FOREIGN KEY(exam_id) REFERENCES exams(id)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS mastery_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL DEFAULT '',
                kind TEXT NOT NULL,
                score REAL NOT NULL,
                source TEXT NOT NULL,
                happened_at TEXT NOT NULL
            )
        """)


def _safe_subject(value):
    return str(value or "General").strip() or "General"


def record_mastery_event(db, subject, topic, kind, score, source):
    with db() as con:
        con.execute(
            """INSERT INTO mastery_events(subject,topic,kind,score,source,happened_at)
               VALUES(?,?,?,?,?,?)""",
            (_safe_subject(subject), str(topic or "").strip(), kind, float(score), source, _now()),
        )


def create_revision_from_miss(db, subject, question, correct_answer, explanation):
    """Create one revision card for a wrong dungeon answer, avoiding duplicates."""
    subject = _safe_subject(subject)
    front = str(question).strip()
    back = f"Correct answer: {str(correct_answer).strip()}\n\n{str(explanation or 'Review this concept and retry it later.').strip()}"
    if not front:
        return False
    key = hashlib.sha1((subject + "|" + front).encode("utf-8")).hexdigest()[:16]
    with db() as con:
        existing = con.execute(
            "SELECT id FROM revision_cards WHERE subject=? AND front=?",
            (subject, front),
        ).fetchone()
        if existing:
            con.execute(
                "INSERT INTO app_settings(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (f"miss_seen_{key}", _now()),
            )
            return False
        con.execute(
            """INSERT INTO revision_cards(subject,front,back,due,created_at)
               VALUES(?,?,?,?,?)""",
            (subject, front, back, date.today().isoformat(), _now()),
        )
        con.execute(
            "INSERT INTO app_settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (f"miss_seen_{key}", _now()),
        )
    return True


def mastery_snapshot(db, limit=12):
    """Return subject-level mastery using only observed local activity."""
    with db() as con:
        subjects = set()
        for r in con.execute("SELECT DISTINCT COALESCE(subject,'General') FROM quests").fetchall():
            subjects.add(_safe_subject(r[0]))
        for r in con.execute("SELECT DISTINCT COALESCE(subject,'General') FROM dungeon_runs").fetchall():
            subjects.add(_safe_subject(r[0]))
        for r in con.execute("SELECT DISTINCT COALESCE(subject,'General') FROM revision_cards").fetchall():
            subjects.add(_safe_subject(r[0]))

        result = []
        for subject in sorted(subjects):
            q = con.execute(
                """SELECT COUNT(*) AS total, COALESCE(SUM(completed),0) AS done
                   FROM quests WHERE COALESCE(subject,'General')=?""",
                (subject,),
            ).fetchone()
            d = con.execute(
                """SELECT COALESCE(SUM(questions),0) AS questions,
                          COALESCE(SUM(correct),0) AS correct
                   FROM dungeon_runs WHERE subject=?""",
                (subject,),
            ).fetchone()
            rev = con.execute(
                """SELECT COUNT(*) AS n,
                          COALESCE(SUM(CASE WHEN rating IN ('Good','Easy') THEN 1 ELSE 0 END),0) AS positive
                   FROM review_log rl
                   JOIN revision_cards rc ON rc.id=rl.card_id
                   WHERE COALESCE(rc.subject,'General')=?""",
                (subject,),
            ).fetchone()

            components = []
            if int(q["total"] or 0):
                components.append((100.0 * int(q["done"] or 0) / int(q["total"]), 0.30))
            if int(d["questions"] or 0):
                components.append((100.0 * int(d["correct"] or 0) / int(d["questions"]), 0.45))
            if int(rev["n"] or 0):
                components.append((100.0 * int(rev["positive"] or 0) / int(rev["n"]), 0.25))

            if components:
                weight = sum(w for _, w in components)
                score = sum(s * w for s, w in components) / weight
            else:
                score = 0.0

            evidence = int(q["total"] or 0) + int(d["questions"] or 0) + int(rev["n"] or 0)
            result.append({
                "subject": subject,
                "score": round(max(0.0, min(100.0, score))),
                "evidence": evidence,
                "quest_total": int(q["total"] or 0),
                "quest_done": int(q["done"] or 0),
                "quiz_questions": int(d["questions"] or 0),
                "quiz_correct": int(d["correct"] or 0),
                "reviews": int(rev["n"] or 0),
            })

    result.sort(key=lambda x: (x["score"], -x["evidence"], x["subject"]))
    return result[:limit]


def active_exams(db):
    with db() as con:
        return con.execute(
            "SELECT * FROM exams WHERE active=1 ORDER BY exam_date,id"
        ).fetchall()


def create_exam(db, name, subject, exam_date, target_score, topics):
    with db() as con:
        cur = con.execute(
            """INSERT INTO exams(name,subject,exam_date,target_score,created_at,active)
               VALUES(?,?,?,?,?,1)""",
            (name.strip(), subject.strip(), exam_date.isoformat(), int(target_score), _now()),
        )
        exam_id = cur.lastrowid
        for topic in topics:
            topic = str(topic).strip()
            if topic:
                con.execute(
                    "INSERT INTO exam_topics(exam_id,topic) VALUES(?,?)",
                    (exam_id, topic),
                )
    return exam_id


def exam_plan(db, exam_id):
    with db() as con:
        exam = con.execute("SELECT * FROM exams WHERE id=?", (exam_id,)).fetchone()
        topics = con.execute(
            "SELECT * FROM exam_topics WHERE exam_id=? ORDER BY id", (exam_id,)
        ).fetchall()
    if not exam:
        return None

    mastery = {r["subject"].lower(): r for r in mastery_snapshot(db, 50)}
    today = date.today()
    try:
        exam_day = date.fromisoformat(exam["exam_date"])
    except ValueError:
        exam_day = today
    days = max(0, (exam_day - today).days)

    rows = []
    for topic in topics:
        subject = _safe_subject(exam["subject"] or topic["topic"])
        m = mastery.get(subject.lower())
        score = int(m["score"]) if m else 0
        risk = max(0, 100 - score)
        rows.append({
            "topic": topic["topic"],
            "score": score,
            "risk": risk,
            "priority": max(1, int(topic["weight"])) * (risk + 10),
        })
    rows.sort(key=lambda x: x["priority"], reverse=True)

    return {
        "exam": exam,
        "topics": rows,
        "days": days,
        "total_topics": len(rows),
        "at_risk": sum(1 for x in rows if x["score"] < 60),
    }


def render_exam_center(st, db, profile, ask_ai, has_ai_key):
    """Streamlit page for exam planning + mastery radar."""
    st.markdown(
        """<div class="exam-hero">
          <div class="exam-kicker">TACTICAL ACADEMIC COMMAND · EXAM PROTOCOL</div>
          <div class="exam-title">Exam Command Center</div>
          <div class="exam-sub">Build an exam map, measure real mastery from your activity, identify risk, and let the study engine turn the gap into a daily attack plan.</div>
        </div>""",
        unsafe_allow_html=True,
    )

    exams = active_exams(db)
    today = date.today()
    mastery = mastery_snapshot(db)

    if exams:
        options = {f"{e['name']} · {e['exam_date']}": e["id"] for e in exams}
        selected_label = st.selectbox("Active exam", list(options.keys()))
        selected_id = options[selected_label]
        plan = exam_plan(db, selected_id)
        exam = plan["exam"]

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Days left", max(0, plan["days"]))
        c2.metric("Target score", f"{exam['target_score']}%")
        c3.metric("At-risk topics", plan["at_risk"])
        c4.metric("Syllabus", plan["total_topics"])

        if plan["days"] == 0:
            st.warning("EXAM DAY · Switch to short recall, formula review and confidence checks. Avoid starting large new topics.")
        elif plan["days"] <= 3:
            st.error("FINAL RAID · Prioritize high-risk topics and active recall. Avoid passive rereading.")
        elif plan["days"] <= 7:
            st.warning("HIGH ALERT · Spend most study time on the lowest-mastery topics.")
        else:
            st.success("TRAINING WINDOW · You have time to build mastery systematically.")

        if plan["topics"]:
            st.markdown("### ◈ Syllabus Risk Map")
            for item in plan["topics"]:
                score = item["score"]
                label = "CRITICAL" if score < 45 else ("AT RISK" if score < 60 else ("STABLE" if score < 80 else "MASTERED"))
                width = max(4, score)
                st.markdown(
                    f"""<div class="exam-topic-row">
                      <div class="exam-topic-name"><b>{html.escape(item['topic'])}</b><span>{label}</span></div>
                      <div class="exam-topic-track"><div style="width:{width}%"></div></div>
                      <div class="exam-topic-score">{score}%</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("Add syllabus topics below to activate the exam risk map.")

        st.markdown("### ◈ Daily Battle Plan")
        days_left = max(1, plan["days"])
        top = plan["topics"][:3]
        if top:
            blocks = []
            for i,item in enumerate(top):
                mins = 25 if item["score"] < 60 else 15
                blocks.append((f"{mins} MIN", "RECOVER" if item["score"] < 60 else "REINFORCE", item["topic"], f"Mastery {item['score']}%"))
            for t,kind,topic,sub in blocks:
                st.markdown(
                    f"""<div class="exam-plan-row"><b>{t}</b><div><strong>{kind} · {html.escape(topic)}</strong><span>{sub}</span></div><em>DAY 1 / {days_left}</em></div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Your first move is to add topics below.")

        if st.button("✨ Generate adaptive exam plan with Gemma", type="primary", use_container_width=True):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            else:
                summary = "; ".join(f"{x['topic']}={x['score']}%" for x in plan["topics"])
                prompt = (
                    f"Create a practical exam plan for {exam['name']} ({exam['subject']}). "
                    f"Days remaining: {plan['days']}. Target: {exam['target_score']}%. "
                    f"Topic mastery: {summary or 'no topic evidence'}. "
                    "Return exactly 5 numbered actions. Prioritize weak topics, active recall and practice. "
                    "Do not invent syllabus content."
                )
                with st.spinner("Gemma is building your adaptive plan..."):
                    try:
                        advice = ask_ai(prompt)
                        st.markdown(
                            f"<div class='exam-ai-output'>{html.escape(str(advice)).replace(chr(10),'<br>')}</div>",
                            unsafe_allow_html=True,
                        )
                    except Exception as exc:
                        st.error(str(exc))
    else:
        st.markdown(
            """<div class="exam-empty">
              <div>◈ NO EXAM PROTOCOL ACTIVE</div>
              <span>Create your first exam below. Your mastery radar will populate as you study.</span>
            </div>""",
            unsafe_allow_html=True,
        )

    with st.expander("＋ Create / update an exam", expanded=not bool(exams)):
        with st.form("create_exam_form"):
            a,b = st.columns(2)
            name = a.text_input("Exam name", placeholder="Semester 3 Python")
            subject = b.text_input("Subject", placeholder="Python")
            exam_date = st.date_input("Exam date", value=today + timedelta(days=14), min_value=today)
            target = st.slider("Target score", 40, 100, 80, 5)
            topics_text = st.text_area(
                "Syllabus topics",
                placeholder="Lists\nFunctions\nFile handling\nOOP\nException handling",
                help="One topic per line.",
            )
            save = st.form_submit_button("🚀 Deploy Exam Protocol", type="primary")
        if save:
            topics = [x.strip() for x in topics_text.splitlines() if x.strip()]
            if not name.strip():
                st.error("Enter an exam name.")
            elif not topics:
                st.error("Add at least one syllabus topic.")
            else:
                create_exam(db, name, subject, exam_date, target, topics)
                st.success("Exam protocol deployed.")
                st.rerun()

    st.markdown("### ◈ Global Mastery Radar")
    if mastery:
        for row in mastery:
            score = int(row["score"])
            status = "CRITICAL" if score < 45 else ("AT RISK" if score < 60 else ("STABLE" if score < 80 else "MASTERED"))
            st.markdown(
                f"""<div class="mastery-row"><b>{html.escape(row['subject'])}</b><div class="mastery-track"><div style="width:{max(3,score)}%"></div></div><strong>{score}%</strong><span>{status} · {row['evidence']} evidence events</span></div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("Complete a quest, dungeon, or revision review to begin measuring mastery.")

    st.caption("Mastery is an evidence score from local quests, dungeon accuracy and revision reviews. It is not an official academic grade.")
