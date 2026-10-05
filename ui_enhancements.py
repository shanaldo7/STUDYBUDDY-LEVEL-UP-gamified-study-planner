"""StudyBuddy UI enhancement layer.

Adapted design patterns inspired by:
- Kstheme/Study-Planner (MIT)
- imDarshanGK/AI-Study-Planner (MIT)

This module intentionally keeps StudyBuddy's Solo-Leveling visual identity while
borrowing useful dashboard patterns: visual hierarchy, information cards,
workflow strips, and compact action panels.
"""

import html
import streamlit as st


def esc(value):
    return html.escape(str(value or ""))


def inject_enhanced_ui():
    st.markdown(
        """
<style>
:root{
  --ux-cyan:#67e8f9;
  --ux-cyan2:#5eead4;
  --ux-violet:#a78bfa;
  --ux-gold:#fbbf24;
  --ux-panel:rgba(10,18,34,.72);
  --ux-line:rgba(126,177,235,.16);
  --ux-muted:#8fa3bf;
}
.ux-shell{
  position:relative;
  border:1px solid var(--ux-line);
  border-radius:18px;
  padding:18px;
  background:linear-gradient(145deg,rgba(17,28,48,.78),rgba(7,12,24,.72));
  box-shadow:0 16px 45px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.05);
  overflow:hidden;
  margin:8px 0 16px;
}
.ux-shell:before{
  content:"";position:absolute;left:-10%;right:-10%;top:-90px;height:160px;
  background:radial-gradient(ellipse,rgba(103,232,249,.10),transparent 65%);
  pointer-events:none;
}
.ux-kicker{
  color:var(--ux-cyan);font-size:.68rem;font-weight:800;letter-spacing:2px;
  text-transform:uppercase;margin-bottom:5px;
}
.ux-title{font-size:1.35rem;font-weight:850;color:#edf8ff;letter-spacing:.2px}
.ux-sub{color:var(--ux-muted);font-size:.86rem;margin-top:4px}
.ux-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:12px 0}
.ux-card{
  min-height:96px;padding:13px 14px;border:1px solid var(--ux-line);border-radius:14px;
  background:linear-gradient(145deg,rgba(255,255,255,.035),rgba(255,255,255,.012));
  transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
}
.ux-card:hover{transform:translateY(-3px);border-color:rgba(103,232,249,.28);box-shadow:0 12px 28px rgba(0,0,0,.22)}
.ux-label{font-size:.68rem;text-transform:uppercase;letter-spacing:1.2px;color:var(--ux-muted);font-weight:800}
.ux-value{font-size:1.5rem;font-weight:850;color:#f5fbff;margin-top:5px}
.ux-note{font-size:.72rem;color:#7890ad;margin-top:4px}
.ux-workflow{
  display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px;margin:12px 0 18px;
}
.ux-step{
  padding:10px 11px;border-left:3px solid rgba(103,232,249,.35);
  border-radius:0 10px 10px 0;background:rgba(255,255,255,.025);
}
.ux-step.active{border-left-color:var(--ux-cyan);background:rgba(103,232,249,.07);box-shadow:inset 0 0 18px rgba(103,232,249,.035)}
.ux-step b{display:block;font-size:.76rem;color:#edf8ff}
.ux-step span{display:block;color:#7890ad;font-size:.66rem;line-height:1.4;margin-top:3px}
.ux-action{
  display:flex;gap:12px;align-items:center;padding:13px 15px;border-radius:14px;
  border:1px solid rgba(167,139,250,.18);
  background:linear-gradient(100deg,rgba(103,232,249,.055),rgba(167,139,250,.055));
  margin:10px 0 15px;
}
.ux-action-icon{font-size:1.35rem}
.ux-action-main{flex:1}
.ux-action-label{font-size:.65rem;color:var(--ux-cyan);font-weight:800;letter-spacing:1.3px}
.ux-action-title{font-size:.98rem;color:#f2f7ff;font-weight:800;margin-top:2px}
.ux-action-copy{font-size:.72rem;color:#8498b3;margin-top:2px}
.ux-chip{
  display:inline-block;padding:4px 8px;border-radius:999px;margin:3px 4px 0 0;
  border:1px solid rgba(103,232,249,.18);background:rgba(103,232,249,.045);
  color:#bcefff;font-size:.66rem;font-weight:700;
}
@media(max-width:900px){
  .ux-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .ux-workflow{grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:560px){
  .ux-grid,.ux-workflow{grid-template-columns:1fr}
}
@media(prefers-reduced-motion:reduce){
  .ux-card{transition:none}
  .ux-card:hover{transform:none}
}
</style>
""",
        unsafe_allow_html=True,
    )


def render_command_header(kicker, title, subtitle):
    st.markdown(
        f"""
<div class="ux-shell">
  <div class="ux-kicker">{esc(kicker)}</div>
  <div class="ux-title">{esc(title)}</div>
  <div class="ux-sub">{esc(subtitle)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_metrics(items):
    cards = []
    for label, value, note in items[:4]:
        cards.append(
            f"""
<div class="ux-card">
  <div class="ux-label">{esc(label)}</div>
  <div class="ux-value">{esc(value)}</div>
  <div class="ux-note">{esc(note)}</div>
</div>
"""
        )
    st.markdown('<div class="ux-grid">' + "".join(cards) + "</div>", unsafe_allow_html=True)


def render_workflow(active=0):
    steps = [
        ("1 · PLAN", "Deploy quests"),
        ("2 · TRAIN", "Focus + practice"),
        ("3 · TEST", "Dungeon + mock"),
        ("4 · REVIEW", "Fix weak areas"),
        ("5 · LEVEL", "Earn XP + unlock"),
    ]
    cards=[]
    for i,(title,copy) in enumerate(steps):
        cls="ux-step active" if i==active else "ux-step"
        cards.append(f'<div class="{cls}"><b>{title}</b><span>{copy}</span></div>')
    st.markdown('<div class="ux-workflow">'+"".join(cards)+"</div>",unsafe_allow_html=True)


def render_next_action(icon,title,copy,tag="AI RECOMMENDATION"):
    st.markdown(
        f"""
<div class="ux-action">
  <div class="ux-action-icon">{esc(icon)}</div>
  <div class="ux-action-main">
    <div class="ux-action-label">{esc(tag)}</div>
    <div class="ux-action-title">{esc(title)}</div>
    <div class="ux-action-copy">{esc(copy)}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_chips(values):
    if not values:
        return
    st.markdown("".join(f'<span class="ux-chip">{esc(v)}</span>' for v in values), unsafe_allow_html=True)
