"""StudyBuddy AI Hunter Intelligence: one evidence/context layer for adaptive study tools."""

from datetime import date
import html
import re
from pypdf import PdfReader
from study_engine import mastery_snapshot, active_exams, exam_plan


def _esc(v):
    return html.escape(str(v or ""))


def learning_context(db, profile):
    mastery = mastery_snapshot(db, 20)
    with db() as con:
        pending = con.execute(
            "SELECT title,subject,due,minutes,difficulty FROM quests WHERE completed=0 ORDER BY due,id LIMIT 12"
        ).fetchall()
        dungeons = con.execute(
            "SELECT subject,difficulty,questions,correct,played_at FROM dungeon_runs ORDER BY id DESC LIMIT 12"
        ).fetchall()
        focus = con.execute(
            "SELECT COALESCE(SUM(minutes),0) AS n FROM focus_sessions WHERE completed=1 AND substr(started_at,1,10)>=date('now','-7 day')"
        ).fetchone()["n"]
        due = con.execute("SELECT COUNT(*) AS n FROM revision_cards WHERE due<=?", (date.today().isoformat(),)).fetchone()["n"]
        total_cards = con.execute("SELECT COUNT(*) AS n FROM revision_cards").fetchone()["n"]
        reviews = con.execute(
            "SELECT rating,COUNT(*) AS n FROM review_log WHERE reviewed_at>=datetime('now','-30 day') GROUP BY rating"
        ).fetchall()

    mastery_text = "; ".join(f"{x['subject']}={x['score']}% evidence={x['evidence']}" for x in mastery) or "none"
    quest_text = "; ".join(
        f"{x['title']} [{x['subject'] or 'General'}] due={x['due']} {x['minutes']}min {x['difficulty']}" for x in pending
    ) or "none"
    dungeon_text = "; ".join(
        f"{x['subject']} {x['correct']}/{x['questions']} ({round(100*x['correct']/max(1,x['questions']))}%)" for x in dungeons
    ) or "none"
    review_text = "; ".join(f"{x['rating']}={x['n']}" for x in reviews) or "none"

    return f"""
<student>
level={profile.get('level','?')}
rank={profile.get('rank','?')}
xp={profile.get('xp',0)}
streak={profile.get('streak',0)} days
</student>
<mastery>{mastery_text}</mastery>
<pending_quests>{quest_text}</pending_quests>
<recent_dungeons>{dungeon_text}</recent_dungeons>
<revision>due={due}; total={total_cards}; reviews={review_text}</revision>
<focus_last_7_days>{int(focus or 0)} minutes</focus_last_7_days>
""".strip()


def grounded_prompt(context, task, output_rules=""):
    return f"""
<role>
You are StudyBuddy's AI Learning Intelligence engine.
</role>
<rules>
- Treat supplied telemetry as the source of truth for student progress.
- Never invent scores, completed work, deadlines, syllabus topics, or history.
- Separate OBSERVED evidence from INFERENCE and RECOMMENDATION.
- If evidence is insufficient, say exactly what is missing.
- Prefer active recall, deliberate practice, worked examples and spaced repetition.
- Never present an AI estimate as an official academic grade.
- Be specific: give an action, duration and verification step.
- Avoid generic motivational filler.
</rules>
<evidence>
{context}
</evidence>
<task>
{task}
</task>
<output_rules>
{output_rules}
</output_rules>
""".strip()


def _pdf_text(path, limit=14000):
    try:
        reader = PdfReader(str(path))
        parts, size = [], 0
        for page in reader.pages:
            text = page.extract_text() or ""
            if text:
                parts.append(text)
                size += len(text)
            if size >= limit:
                break
        return "\n\n".join(parts)[:limit].strip()
    except Exception:
        return ""


def _parse_exam(raw):
    pattern = re.compile(
        r"(?:^|\n)\s*(\d+)\.\s*(.*?)\n\s*A\)\s*(.*?)\n\s*B\)\s*(.*?)\n\s*C\)\s*(.*?)\n\s*D\)\s*(.*?)\n\s*ANSWER:\s*([ABCD])",
        re.I | re.S,
    )
    return [
        {"number": int(m.group(1)), "question": m.group(2).strip(),
         "options": {"A":m.group(3).strip(),"B":m.group(4).strip(),"C":m.group(5).strip(),"D":m.group(6).strip()},
         "answer":m.group(7).upper()}
        for m in pattern.finditer(raw)
    ]


def render_ai_intelligence(st, db, profile, ask_ai, has_ai_key, selected_model):
    profile_data = {"level":profile.get("level","?"),"rank":profile.get("rank","?"),"xp":profile.get("xp",0),"streak":profile.get("streak",0)}
    context = learning_context(db, profile_data)
    mastery = mastery_snapshot(db, 20)
    weakest = mastery[0] if mastery else None
    exams = active_exams(db)

    st.markdown(
        f"""<div class="intel-hero">
        <div class="intel-kicker">AI HUNTER INTELLIGENCE · EVIDENCE-GROUNDED</div>
        <div class="intel-title">Study Intelligence Command Center</div>
        <div class="intel-sub">Your quests, dungeons, revision, focus and exams now feed one adaptive decision layer.</div>
        <div class="hero-meta"><span class="system-chip">Model · {_esc(selected_model)}</span>
        <span class="system-chip purple">{"✓ AI Connected" if has_ai_key() else "Connect AI in sidebar"}</span></div>
        </div>""", unsafe_allow_html=True
    )

    a,b,c,d = st.columns(4)
    a.metric("Weakest area", weakest["subject"] if weakest else "No data")
    b.metric("Observed mastery", f"{weakest['score']}%" if weakest else "—")
    c.metric("Active exams", len(exams))
    d.metric("Evidence layer", "5 sources")

    tabs = st.tabs(["⚡ Study Now","🧠 Weakness","🎓 Readiness","🧪 Mock Exam","🗂️ Study Pack","🃏 Flashcards","🗺️ Mind Map","📉 Marks","🎤 Mentor"])

    with tabs[0]:
        st.markdown("### ⚡ What should I study right now?")
        if weakest:
            st.info(f"Target: {weakest['subject']} · observed mastery {weakest['score']}% · {weakest['evidence']} evidence events")
        minutes = st.slider("Available time", 10, 120, 30, 5, key="ai_next_minutes")
        if st.button("⚔️ Generate next adaptive quest", type="primary", use_container_width=True):
            if not has_ai_key():
                st.warning("Connect Gemma AI in the sidebar first.")
            else:
                task = f"Choose exactly one highest-value study action for the next {minutes} minutes. Use weakness, pending work, revision due and exam risk. Return TARGET, WHY, 3 STEPS, DURATION, PRACTICE CHECK and XP SUGGESTION."
                try:
                    st.session_state["ai_next"] = ask_ai(
                        grounded_prompt(context, task, "Under 250 words."),
                        "You are StudyBuddy's evidence-based adaptive learning engine. Be decisive and precise."
                    )
                except Exception as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_next"):
            st.markdown(f"<div class='intel-callout' style='white-space:pre-wrap'>{_esc(st.session_state['ai_next'])}</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown("### 🧠 AI Weakness Detector")
        for row in mastery:
            score=int(row["score"])
            label="CRITICAL" if score<45 else ("AT RISK" if score<60 else ("STABLE" if score<80 else "MASTERED"))
            st.markdown(
                f"<div class='mastery-row'><b>{_esc(row['subject'])}</b><div class='mastery-track'><div style='width:{max(3,score)}%'></div></div><strong>{score}%</strong><span>{label} · {row['evidence']} evidence</span></div>",
                unsafe_allow_html=True
            )
        if not mastery:
            st.info("Complete quests, dungeon questions or revision reviews to generate the radar.")
        if st.button("🔍 Explain biggest weakness", key="ai_weakness"):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            else:
                try:
                    st.session_state["ai_weakness"] = ask_ai(
                        grounded_prompt(context,"Identify the most actionable weakness. Explain evidence, uncertainty and a 3-step correction drill.","Use OBSERVED, RISK, DRILL. Under 220 words."),
                        "You are a diagnostic learning scientist. Never overclaim from sparse evidence."
                    )
                except Exception as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_weakness"):
            st.markdown(f"<div class='intel-callout' style='white-space:pre-wrap'>{_esc(st.session_state['ai_weakness'])}</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown("### 🎓 Exam Readiness")
        if not exams:
            st.info("Create an exam in Exam Command Center first.")
        for exam in exams[:5]:
            plan = exam_plan(db, exam["id"])
            avg = round(sum(x["score"] for x in plan["topics"]) / max(1,len(plan["topics"])))
            readiness = round(max(0,min(100,avg)))
            st.metric(exam["name"], f"{readiness}%", f"{max(0,plan['days'])} days left")
        if exams and st.button("🧠 Build route to target score", key="ai_readiness"):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            else:
                try:
                    st.session_state["ai_readiness"] = ask_ai(
                        grounded_prompt(context,"Build the safest route to the active exam target. Give top 3 actions, time allocation and final self-test.","Use a compact table and action list. Never invent syllabus topics."),
                        "You are an exam-preparation strategist."
                    )
                except Exception as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_readiness"):
            st.markdown(f"<div class='intel-callout' style='white-space:pre-wrap'>{_esc(st.session_state['ai_readiness'])}</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown("### 🧪 AI Mock Exam Generator")
        subject=st.text_input("Subject",key="ai_mock_subject",placeholder="DBMS")
        count=st.slider("Questions",5,20,10,key="ai_mock_count")
        difficulty=st.selectbox("Difficulty",["Exam level","Hard","Mixed"],key="ai_mock_diff")
        if st.button("⚔️ Generate mock exam",type="primary",key="ai_mock_generate"):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            elif not subject.strip():
                st.warning("Enter a subject.")
            else:
                task=f"Create exactly {count} multiple-choice questions for {subject.strip()} at {difficulty}. Four options A-D. Exact format per question: 1. QUESTION, A) ..., B) ..., C) ..., D) ..., ANSWER: A. End with EXAM_END. Test understanding, not trivia."
                try:
                    raw=ask_ai(grounded_prompt(context,task,"Do not add explanations before EXAM_END."),"You are a rigorous exam setter. Each question must have one defensible answer.")
                    st.session_state["ai_mock_questions"]=_parse_exam(raw)
                    st.session_state["ai_mock_raw"]=raw
                except Exception as exc:
                    st.error(str(exc))
        qs=st.session_state.get("ai_mock_questions",[])
        if qs:
            answers={}
            for q in qs:
                answers[q["number"]]=st.radio(
                    f"{q['number']}. {q['question']}",list(q["options"]),
                    format_func=lambda x,o=q["options"]:f"{x}) {o[x]}",
                    key=f"ai_mock_answer_{q['number']}",horizontal=True
                )
            if st.button("📊 Submit mock exam",type="primary",key="ai_mock_submit"):
                correct=sum(answers[q["number"]]==q["answer"] for q in qs)
                score=round(100*correct/max(1,len(qs)))
                st.success(f"Score: {correct}/{len(qs)} · {score}%")
                st.session_state["ai_mock_score"]=score
        elif st.session_state.get("ai_mock_raw"):
            st.markdown(st.session_state["ai_mock_raw"])

    with tabs[4]:
        st.markdown("### 🗂️ Notes → AI Study Pack")
        with db() as con:
            pdfs=con.execute("SELECT title,subject,stored_path FROM pdfs ORDER BY added_at DESC").fetchall()
        if not pdfs:
            st.info("Upload a PDF in Important PDFs first.")
        else:
            choices={f"{p['title']} · {p['subject'] or 'General'}":p for p in pdfs}
            chosen=st.selectbox("Source PDF",list(choices),key="ai_source_pdf")
            kind=st.selectbox("Generate",["Study guide","Important questions","Flashcards","Mock exam blueprint","Simple explanation"],key="ai_pack_kind")
            if st.button("✨ Build study pack",type="primary",key="ai_build_pack"):
                if not has_ai_key():
                    st.warning("Connect Gemma AI first.")
                else:
                    source=choices[chosen]
                    text=_pdf_text(source["stored_path"])
                    if not text:
                        st.error("This PDF has no extractable text. Scanned-image OCR is not enabled yet.")
                    else:
                        try:
                            task=f"Using only the supplied document, create a {kind.lower()} for {source['title']}. Preserve terminology. Mark unsupported claims UNKNOWN."
                            prompt=f"<source_document>\n{text}\n</source_document>\n"+grounded_prompt(context,task,"Exam-useful and structured.")
                            st.session_state["ai_pack"]=ask_ai(prompt,"You are a source-grounded study assistant. The document is authoritative for document-specific facts.")
                        except Exception as exc:
                            st.error(str(exc))
            if st.session_state.get("ai_pack"):
                st.markdown(st.session_state["ai_pack"])

    with tabs[5]:
        st.markdown("### 🃏 Adaptive Flashcard Forge")
        topic=st.text_input("Topic",key="ai_flash_topic",placeholder="Normalization")
        count=st.slider("Cards",5,20,10,key="ai_flash_count")
        if st.button("🧠 Generate flashcards",key="ai_flash_generate"):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            elif not topic.strip():
                st.warning("Enter a topic.")
            else:
                try:
                    st.session_state["ai_flashcards"]=ask_ai(
                        grounded_prompt(context,f"Create {count} active-recall flashcards about {topic.strip()}. Format FRONT, BACK, WHY. Target common misconceptions.","Be concise."),
                        "You are an expert active-recall tutor."
                    )
                except Exception as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_flashcards"):
            st.markdown(st.session_state["ai_flashcards"])

    with tabs[6]:
        st.markdown("### 🗺️ AI Mind Map")
        topic=st.text_input("Topic",key="ai_mind_topic",placeholder="Software Engineering")
        if st.button("🗺️ Build mind map",key="ai_mind_generate"):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            elif not topic.strip():
                st.warning("Enter a topic.")
            else:
                try:
                    st.session_state["ai_mindmap"]=ask_ai(
                        grounded_prompt(context,f"Create a compact hierarchical mind map for {topic.strip()} using Mermaid mindmap syntax.","Return only Mermaid mindmap code."),
                        "You are a knowledge-structure designer."
                    )
                except Exception as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_mindmap"):
            st.code(st.session_state["ai_mindmap"],language="text")

    with tabs[7]:
        st.markdown("### 📉 Why am I losing marks?")
        if st.button("🔎 Analyze performance",key="ai_marks"):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            else:
                try:
                    st.session_state["ai_marks"]=ask_ai(
                        grounded_prompt(context,"Analyze likely causes of lost marks. Distinguish observed patterns from hypotheses. Give percentages only when calculable. End with a targeted 20-minute drill.","Use OBSERVED PATTERNS, POSSIBLE CAUSES, NEXT DRILL."),
                        "You are a careful academic performance analyst. Never fabricate statistics."
                    )
                except Exception as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_marks"):
            st.markdown(f"<div class='intel-callout' style='white-space:pre-wrap'>{_esc(st.session_state['ai_marks'])}</div>",unsafe_allow_html=True)

    with tabs[8]:
        st.markdown("### 🎤 Context-Aware Shadow Mentor")
        q=st.text_area("Ask your mentor",placeholder="What should I revise tonight?",key="ai_mentor_q")
        if st.button("⚔️ Ask mentor",type="primary",key="ai_mentor"):
            if not has_ai_key():
                st.warning("Connect Gemma AI first.")
            elif not q.strip():
                st.warning("Ask a question first.")
            else:
                try:
                    st.session_state["ai_mentor_answer"]=ask_ai(
                        grounded_prompt(context,f"Answer: {q.strip()}. Use telemetry to personalize. If a fact is outside telemetry, label it general knowledge.","Be direct and include one concrete next action."),
                        "You are StudyBuddy's Shadow Mentor: precise, supportive, concise and evidence-aware."
                    )
                except Exception as exc:
                    st.error(str(exc))
        if st.session_state.get("ai_mentor_answer"):
            st.markdown(f"<div class='intel-callout' style='white-space:pre-wrap'>{_esc(st.session_state['ai_mentor_answer'])}</div>",unsafe_allow_html=True)
