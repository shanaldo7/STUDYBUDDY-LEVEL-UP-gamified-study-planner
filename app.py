import os
import sqlite3
import hashlib
import calendar
import json
import urllib.request
import urllib.error
import random
import re
import time
import streamlit.components.v1 as components
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

from anime_rpg import render as render_anime_rpg
from ai_intelligence import render_ai_intelligence
from progress_calendar import render_progress_calendar
from ui_enhancements import inject_enhanced_ui, render_command_header, render_metrics, render_workflow, render_next_action
from hunter_system import ensure_tables as ensure_hunter_tables, sync_level as sync_hunter_level, render_skill_tree, render_offline_indicator, render_offline_journal, focus_multiplier, combo_multiplier, revision_interval_multiplier, xp_multiplier, retry_call, wallet, grant_currency
from premium_hunter import inject_premium_css, render_dungeon_map, render_system_guide, render_voice_study_mode, render_offline_console, render_sound_settings
from study_engine import (
    ensure_tables as ensure_adaptive_tables,
    render_exam_center,
    create_revision_from_miss,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except Exception:
    genai = None
    types = None
    _GENAI_AVAILABLE = False

# ============================================================
# STUDYBUDDY: LEVEL UP — gamified study planner
# Data is stored locally beside this app in ./study_data
# ============================================================
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "study_data"
PDF_DIR = DATA_DIR / "important_pdfs"
DB_PATH = DATA_DIR / "studybuddy.db"
PDF_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

MOTION_CSS = (APP_DIR / "assets" / "motion.css").read_text(encoding="utf-8") if (APP_DIR / "assets" / "motion.css").exists() else ""
MOTION_JS = (APP_DIR / "assets" / "motion.js").read_text(encoding="utf-8") if (APP_DIR / "assets" / "motion.js").exists() else ""

inject_enhanced_ui()
inject_premium_css()

st.set_page_config(page_title="StudyBuddy | Level Up", page_icon="⚔️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;600;700;800&family=Rajdhani:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

/* ── Design tokens ────────────────────────────────────────────── */
:root {
  --bg-0: #070a14;
  --bg-1: #0b1122;
  --bg-2: #111a30;
  --line: rgba(126, 177, 235, 0.18);
  --line-strong: rgba(126, 177, 235, 0.32);
  --cyan: #5eead4;
  --cyan-soft: #67e8f9;
  --purple: #a78bfa;
  --gold: #fbbf24;
  --text: #e6eefb;
  --text-dim: #b9c9e3;
  --text-muted: #8899b3;
  --radius-sm: 10px;
  --radius-md: 14px;
  --radius-lg: 18px;
  --radius-xl: 22px;
  --shadow-sm: 0 4px 14px rgba(0,0,0,.25), inset 0 1px 0 rgba(255,255,255,.05);
  --shadow-md: 0 10px 30px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.06);
  --shadow-lg: 0 18px 50px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.07);
}

/* ── Base app ─────────────────────────────────────────────────── */
.stApp {
  background:
    radial-gradient(1000px 550px at 8% -5%, #12294e 0%, transparent 55%),
    radial-gradient(900px 500px at 92% 0%, #231246 0%, transparent 52%),
    linear-gradient(180deg, var(--bg-0) 0%, var(--bg-1) 50%, #080c18 100%);
  background-attachment: fixed;
  color: var(--text);
}
.block-container {
  max-width: 1400px;
  padding-top: 4.1rem;
  padding-bottom: 2.5rem;
  padding-left: 1.6rem;
  padding-right: 1.6rem;
}
html, body, [class*="css"], p, div, span, li {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  line-height: 1.55;
  letter-spacing: 0;
}
h1, h2, h3, h4 {
  font-family: 'Orbitron', 'Rajdhani', sans-serif !important;
  letter-spacing: 0.3px;
  line-height: 1.3;
}
h1 { font-size: clamp(1.5rem, 2.6vw, 2.2rem); font-weight: 800; }
h2 { font-size: clamp(1.2rem, 2vw, 1.55rem); font-weight: 700; margin-top: 1.4rem; }
h3 { font-size: 1.08rem; font-weight: 700; }
p { font-size: 0.95rem; color: var(--text-dim); }
hr { border-color: var(--line); margin: 1.2rem 0; }
.muted { color: var(--text-muted); font-size: 0.82rem; line-height: 1.55; }

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(6,10,20,.92) 0%, rgba(5,9,19,.88) 100%);
  border-right: 1px solid var(--line);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 8px 0 24px rgba(0,0,0,.22);
}
[data-testid="stSidebar"] .block-container {
  padding-top: 1.2rem;
  padding-left: 0.9rem;
  padding-right: 0.9rem;
}
.sidebar-brand {
  padding: 4px 6px 12px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 14px;
}
.sidebar-brand-name {
  font-family: 'Orbitron', 'Rajdhani', sans-serif;
  font-size: 1.15rem;
  font-weight: 800;
  color: #f3f8ff;
  letter-spacing: 0.5px;
}
.sidebar-brand-name span { color: var(--cyan); }
.sidebar-brand-sub {
  color: var(--text-muted);
  font-size: 0.72rem;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  font-weight: 600;
  margin-top: 2px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: 2px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  padding: 7px 10px;
  margin: 1px 0;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  transition: all .18s ease-out;
  font-size: 0.92rem;
  font-weight: 500;
  min-height: 35px;
  align-items: center;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
  background: rgba(94, 234, 212, 0.06);
  border-color: rgba(94, 234, 212, 0.18);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(110deg, rgba(22,72,106,.55), rgba(60,38,112,.5));
  border-color: rgba(94, 234, 212, 0.38);
  box-shadow: inset 3px 0 0 var(--cyan), 0 0 14px rgba(94,234,212,.08);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
  color: #eaf6ff !important;
  font-weight: 600;
}
.sidebar-section-label {
  color: var(--text-muted);
  font-size: 0.7rem;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  font-weight: 700;
  padding: 14px 8px 6px;
}
.sidebar-hunter {
  padding: 10px 12px;
  border: 1px solid rgba(74,222,128,.18);
  border-radius: var(--radius-sm);
  background: rgba(9, 25, 18, .55);
  margin-top: 8px;
}
.status-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 8px rgba(74,222,128,.6);
  margin-right: 7px;
  vertical-align: middle;
}
.ai-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.3px;
  border: 1px solid var(--line);
  margin-top: 6px;
}
.ai-status.connected {
  background: rgba(15, 40, 32, 0.55);
  border-color: rgba(74, 222, 128, 0.28);
  color: #86efac;
}
.ai-status.connected .status-dot {
  background: #4ade80;
  box-shadow: 0 0 8px rgba(74,222,128,.6);
}
.ai-status.disconnected {
  background: rgba(55, 26, 26, 0.4);
  border-color: rgba(248, 113, 113, 0.28);
  color: #fca5a5;
}
.ai-status.disconnected .status-dot {
  background: #f87171;
  box-shadow: 0 0 8px rgba(248,113,113,.55);
}

/* ── Hero / page header ───────────────────────────────────────── */
.hero {
  position: relative;
  overflow: hidden;
  padding: 22px 26px;
  border: 1px solid rgba(94, 234, 212, 0.28);
  border-radius: var(--radius-xl);
  background:
    radial-gradient(circle at 92% 50%, rgba(167,139,250,.18), transparent 40%),
    linear-gradient(115deg, rgba(14, 38, 66, .82), rgba(30, 22, 58, .78));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: var(--shadow-md);
  transition: border-color .25s ease;
}
.hero:hover { border-color: rgba(94, 234, 212, 0.48); }
.hero-kicker {
  color: var(--cyan);
  text-transform: uppercase;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 0.7rem;
  letter-spacing: 2px;
  opacity: 0.95;
}
.hero-title {
  font-family: 'Orbitron', 'Rajdhani', sans-serif;
  font-size: clamp(1.35rem, 2.6vw, 2rem);
  font-weight: 800;
  margin: 6px 0 8px;
  color: #f8fbff;
  letter-spacing: 0.2px;
}
.hero-sub {
  color: var(--text-dim);
  margin: 0;
  font-size: 0.94rem;
  max-width: 65ch;
}
.hero-meta {
  margin-top: 14px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.rank {
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(251,191,36,.4);
  color: #fde68a;
  background: rgba(62, 44, 12, .55);
  padding: 4px 11px;
  border-radius: 999px;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 0.72rem;
  letter-spacing: 0.8px;
}
.system-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 11px;
  border: 1px solid rgba(94,234,212,.22);
  border-radius: 999px;
  background: rgba(8, 24, 32, .55);
  color: #bff1e6;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 0.72rem;
  letter-spacing: 0.5px;
}
.system-chip.purple {
  border-color: rgba(167,139,250,.25);
  background: rgba(24, 14, 48, .55);
  color: #ddd6fe;
}

/* ── Panels, cards, stats ────────────────────────────────────── */
.panel,
.stat,
.quest,
.achievement-card,
[data-testid="stMetric"],
.system-panel,
.shadow-reaction,
.system-next,
.dungeon-result,
.review-card,
.level-up-banner,
.reward-banner,
.timer-shell,
.guild-banner {
  background: linear-gradient(160deg, rgba(22,35,61,.62), rgba(12,18,34,.62));
  border: 1px solid var(--line);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: var(--shadow-sm);
  transition: border-color .2s ease, transform .2s ease, background .2s ease;
}
.panel {
  padding: 18px 20px;
  margin-bottom: 14px;
  border-radius: var(--radius-lg);
}
.panel:hover,
.stat:hover,
.quest:hover,
.achievement-card:hover,
[data-testid="stMetric"]:hover {
  border-color: var(--line-strong);
  background: linear-gradient(160deg, rgba(28,45,78,.7), rgba(16,24,44,.7));
}
.panel-title {
  font-family: 'Orbitron', 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 0.95rem;
  color: #f0f6ff;
  margin-bottom: 10px;
  letter-spacing: 0.3px;
}
.stat {
  padding: 14px 16px;
  border-radius: var(--radius-md);
  min-height: 84px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.stat-label {
  color: var(--text-muted);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  margin-bottom: 6px;
}
.stat-value {
  font-family: 'Orbitron', 'Rajdhani', sans-serif;
  font-size: 1.7rem;
  font-weight: 700;
  color: #f5f9ff;
  line-height: 1.15;
}
[data-testid="stMetric"] {
  padding: 14px 16px;
  border-radius: var(--radius-md);
}
[data-testid="stMetric"] label {
  color: var(--text-muted) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
  color: #f4f8ff !important;
  font-family: 'Orbitron', 'Rajdhani', sans-serif;
  font-weight: 700 !important;
  font-size: 1.65rem !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem; }

/* ── Progress bars ────────────────────────────────────────────── */
.xp-track, .hp-track, .day-bar {
  border-radius: 99px;
  background: #162440;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,.05);
}
.xp-track { height: 8px; margin: 8px 0 4px; }
.hp-track { height: 12px; margin: 12px 0; }
.day-bar  { height: 7px; flex: 1; }
.xp-fill, .day-fill {
  height: 100%;
  background: linear-gradient(90deg, #22d3ee, #8b5cf6);
  border-radius: 99px;
  box-shadow: 0 0 10px rgba(34,211,238,.35);
}
.hp-fill {
  height: 100%;
  background: linear-gradient(90deg, #ef4444, #f97316);
  box-shadow: 0 0 10px rgba(239,68,68,.4);
  transition: width .45s ease;
}
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, #22d3ee, #a78bfa) !important;
  box-shadow: 0 0 8px rgba(34,211,238,.3);
  border-radius: 99px;
}

/* ── Buttons ──────────────────────────────────────────────────── */
div.stButton > button,
[data-testid="stFormSubmitButton"] button {
  border-radius: var(--radius-sm);
  border: 1px solid rgba(94,234,212,.28);
  background: linear-gradient(135deg, rgba(24,54,82,.8), rgba(44,30,82,.78));
  color: #eaf3ff;
  font-weight: 600;
  font-size: 0.88rem;
  padding: 0.45rem 1rem;
  min-height: 38px;
  transition: all .18s ease-out;
  box-shadow: 0 3px 12px rgba(0,0,0,.22);
  letter-spacing: 0.1px;
}
div.stButton > button:hover,
[data-testid="stFormSubmitButton"] button:hover {
  border-color: var(--cyan);
  color: #fff;
  transform: translateY(-1.5px);
  background: linear-gradient(135deg, #17486e, #4a3283);
  box-shadow: 0 7px 20px rgba(34,211,238,.18);
}
div.stButton > button:active,
[data-testid="stFormSubmitButton"] button:active {
  transform: translateY(0);
}
div.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] {
  border-color: rgba(94,234,212,.45);
  background: linear-gradient(135deg, rgba(20,88,116,.9), rgba(76,45,140,.88));
  box-shadow: 0 4px 18px rgba(34,211,238,.15);
}
div.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
  border-color: var(--cyan);
  background: linear-gradient(135deg, #0e6b7c, #5c3aa5);
}




/* ── Global 3D System UI ─────────────────────────────────────── */
.stApp::before{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.16;background-image:linear-gradient(rgba(103,232,249,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(167,139,250,.035) 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(to bottom,black,transparent 88%);}
.block-container{position:relative;z-index:1;}
.hero,.guild-banner{transform-style:preserve-3d;position:relative;box-shadow:0 22px 65px rgba(0,0,0,.42),inset 0 1px 0 rgba(255,255,255,.06);}
.hero::after,.guild-banner::after{content:"";position:absolute;inset:1px;border-radius:inherit;pointer-events:none;background:linear-gradient(115deg,rgba(255,255,255,.06),transparent 22%,transparent 72%,rgba(167,139,250,.06));}
.hero:hover,.guild-banner:hover{transform:perspective(1200px) rotateX(.7deg) translateY(-2px);border-color:rgba(103,232,249,.45);}
.panel,.stat,.quest,.achievement-card,.system-panel,.review-card,.timer-shell,[data-testid="stMetric"]{transform-style:preserve-3d;}
.panel:hover,.stat:hover,.quest:hover,.achievement-card:hover,.system-panel:hover,.review-card:hover,.timer-shell:hover,[data-testid="stMetric"]:hover{transform:perspective(900px) rotateX(.8deg) translateY(-3px);box-shadow:0 16px 38px rgba(0,0,0,.34),inset 0 1px 0 rgba(255,255,255,.07);}
.hud-card{position:relative;overflow:hidden;min-height:145px;padding:18px;border:1px solid rgba(126,177,235,.18);border-radius:18px;background:linear-gradient(145deg,rgba(18,31,57,.84),rgba(12,16,31,.82));box-shadow:0 14px 36px rgba(0,0,0,.32),inset 0 1px 0 rgba(255,255,255,.05);transition:transform .22s,border-color .22s,box-shadow .22s;}
.hud-card::before{content:"";position:absolute;width:130px;height:130px;right:-45px;top:-50px;border-radius:50%;background:radial-gradient(circle,rgba(103,232,249,.16),transparent 68%);}
.hud-card:hover{transform:perspective(800px) rotateY(-2deg) translateY(-5px);border-color:rgba(103,232,249,.42);box-shadow:0 22px 48px rgba(0,0,0,.42),0 0 24px rgba(103,232,249,.07);}
.hud-icon{font-size:1.65rem;filter:drop-shadow(0 0 10px rgba(167,139,250,.35));}.hud-label{margin-top:9px;color:#fff;font:800 .85rem Orbitron,sans-serif}.hud-desc{color:#7f91ac;font-size:.69rem;margin-top:5px;line-height:1.35;}
.dashboard-core{position:relative;overflow:hidden;min-height:255px;padding:25px;border-radius:26px;border:1px solid rgba(103,232,249,.25);background:radial-gradient(circle at 78% 30%,rgba(139,92,246,.25),transparent 28%),radial-gradient(circle at 12% 75%,rgba(34,211,238,.13),transparent 30%),linear-gradient(135deg,rgba(9,19,37,.97),rgba(27,14,49,.95));box-shadow:0 30px 85px rgba(0,0,0,.48),inset 0 1px 0 rgba(255,255,255,.07);}
.dashboard-core::before{content:"";position:absolute;width:270px;height:270px;right:-85px;top:-90px;border:1px solid rgba(167,139,250,.18);border-radius:50%;box-shadow:0 0 0 30px rgba(167,139,250,.025),0 0 0 60px rgba(167,139,250,.018);}
.core-kicker{color:#67e8f9;font:800 .62rem Orbitron,sans-serif;letter-spacing:2px}.core-title{color:#fff;font:800 clamp(1.6rem,3.4vw,2.7rem) Orbitron,sans-serif;margin:5px 0}.core-sub{color:#91a5c0;max-width:650px;font-size:.82rem}.core-stat-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:15px}.core-stat{padding:8px 12px;border-radius:11px;border:1px solid rgba(255,255,255,.09);background:rgba(4,9,20,.45)}.core-stat b{color:#fff;font:700 .95rem Orbitron,sans-serif}.core-stat span{color:#71839f;font-size:.61rem;text-transform:uppercase;margin-left:5px}
.page-orbit{position:relative;overflow:hidden;margin:0 0 16px;padding:10px 14px;border:1px solid rgba(126,177,235,.14);border-radius:14px;background:linear-gradient(90deg,rgba(8,15,30,.72),rgba(23,15,42,.62));display:flex;justify-content:space-between;align-items:center;gap:10px;box-shadow:0 8px 28px rgba(0,0,0,.22)}.page-orbit-main{color:#dceaff;font:700 .68rem Orbitron,sans-serif;letter-spacing:1.2px;text-transform:uppercase}.page-orbit-sub{color:#71839f;font-size:.68rem}
@media (prefers-reduced-motion:reduce){.hero:hover,.guild-banner:hover,.panel:hover,.stat:hover,.quest:hover,.achievement-card:hover,.system-panel:hover,.review-card:hover,.timer-shell:hover,[data-testid="stMetric"]:hover,.hud-card:hover{transform:none}}

/* ── Interactive 3D card carousel / cinematic gate ───────────── */
.shadow-carousel-wrap {
  position:relative; overflow:hidden; padding:26px 18px 20px;
  border-radius:26px; border:1px solid rgba(168,139,250,.20);
  background:
    radial-gradient(circle at 50% 30%,rgba(124,58,237,.16),transparent 34%),
    linear-gradient(145deg,rgba(12,9,25,.98),rgba(22,14,43,.96));
  box-shadow:0 28px 80px rgba(0,0,0,.48);
}
.shadow-carousel-bg {
  position:absolute; inset:0; overflow:hidden; pointer-events:none;
  background:radial-gradient(circle at 50% 90%,rgba(34,211,238,.08),transparent 35%);
}
.shadow-carousel-title { position:relative; text-align:center; margin-bottom:18px; }
.shadow-carousel-title .eyebrow {
  color:#c4b5fd; font:800 .62rem Orbitron,sans-serif; letter-spacing:2.2px;
}
.shadow-carousel-title h2 {
  color:#fff; font:800 clamp(1.45rem,3vw,2.2rem) Orbitron,sans-serif;
  margin:5px 0 2px;
}
.shadow-carousel-title p { color:#8795ad; margin:0; font-size:.78rem; }
.shadow-stage {
  position:relative; min-height:390px; display:flex; align-items:center;
  justify-content:center; perspective:1100px; margin:0 -4px;
}
.shadow-card {
  position:relative; overflow:hidden; width:245px; height:350px;
  border-radius:22px; border:1px solid rgba(255,255,255,.11);
  background:#080713; box-shadow:0 20px 45px rgba(0,0,0,.48);
  transform-style:preserve-3d; transition:transform .38s ease,opacity .3s ease,filter .3s ease,box-shadow .3s ease;
}
.shadow-card img { width:100%; height:100%; object-fit:cover; object-position:center top; display:block; }
.shadow-card::after {
  content:""; position:absolute; inset:0;
  background:linear-gradient(180deg,rgba(4,3,12,.04) 38%,rgba(5,4,15,.97) 100%);
}
.shadow-card.center {
  width:285px; height:385px; z-index:3;
  border-color:rgba(196,181,253,.62);
  box-shadow:0 0 0 1px rgba(167,139,250,.18),0 30px 65px rgba(0,0,0,.60),0 0 38px rgba(139,92,246,.16);
  transform:translateZ(50px) scale(1.02);
}
.shadow-card.left {
  margin-right:-48px; z-index:1; transform:rotateY(17deg) translateX(8px) scale(.90);
  filter:saturate(.72) brightness(.72);
}
.shadow-card.right {
  margin-left:-48px; z-index:1; transform:rotateY(-17deg) translateX(-8px) scale(.90);
  filter:saturate(.72) brightness(.72);
}
.shadow-card-copy {
  position:absolute; left:18px; right:18px; bottom:17px; z-index:2;
}
.shadow-card-rank {
  color:#c4b5fd; font:800 .58rem Orbitron,sans-serif; letter-spacing:1.5px;
}
.shadow-card-name {
  color:#fff; font:800 1.45rem Orbitron,sans-serif;
  text-shadow:0 3px 16px rgba(0,0,0,.7); margin-top:4px;
}
.shadow-card-meta {
  color:#a9b7cc; font-size:.67rem; text-transform:uppercase;
  letter-spacing:1.2px; margin-top:4px;
}
.shadow-card-glow {
  position:absolute; inset:auto 12% 8% 12%; height:30px; z-index:1;
  background:rgba(139,92,246,.34); filter:blur(22px);
}
.carousel-nav {
  display:flex; justify-content:center; align-items:center; gap:12px; margin-top:12px;
}
.carousel-dot {
  width:7px; height:7px; border-radius:50%; background:#48536a;
  display:inline-block; transition:all .2s;
}
.carousel-dot.active { width:24px; border-radius:99px; background:#c4b5fd; box-shadow:0 0 12px rgba(196,181,253,.45); }
.carousel-hint { text-align:center; color:#65738b; font-size:.67rem; letter-spacing:1px; text-transform:uppercase; margin-top:8px; }
.cinematic-video {
  position:absolute; inset:0; width:100%; height:100%; object-fit:cover;
  opacity:.16; filter:saturate(.75) contrast(1.1); pointer-events:none;
}
.cinematic-video-overlay {
  position:absolute; inset:0; background:linear-gradient(180deg,rgba(5,4,13,.35),rgba(8,5,18,.94));
  pointer-events:none;
}
@media (max-width:900px) {
  .shadow-card.left,.shadow-card.right { display:none; }
  .shadow-card.center { width:min(300px,78vw); height:370px; }
  .shadow-stage { min-height:380px; }
}
@media (prefers-reduced-motion:reduce) {
  .shadow-card { transition:none; }
}

/* ── Cinematic / Pinterest-inspired Dungeon UI ───────────────── */
.dungeon-gate {
  position:relative; overflow:hidden; border-radius:24px;
  border:1px solid rgba(126,177,235,.22);
  background:linear-gradient(135deg,rgba(9,14,28,.96),rgba(25,13,42,.94));
  box-shadow:0 25px 70px rgba(0,0,0,.45);
  margin:8px 0 18px;
}
.dungeon-gate::before {
  content:""; position:absolute; inset:0; pointer-events:none;
  background:radial-gradient(circle at 78% 18%,rgba(139,92,246,.18),transparent 36%),
             radial-gradient(circle at 15% 70%,rgba(34,211,238,.10),transparent 35%);
}
.dungeon-gate-content { position:relative; padding:26px; }
.dungeon-kicker { color:#67e8f9; font:800 .64rem Orbitron,sans-serif; letter-spacing:2px; text-transform:uppercase; }
.dungeon-gate-title { color:#fff; font:800 clamp(1.7rem,4vw,3rem) Orbitron,sans-serif; margin:7px 0; }
.dungeon-gate-sub { color:#9fb2cb; max-width:700px; font-size:.9rem; }
.boss-card {
  position:relative; overflow:hidden; border-radius:18px; min-height:330px;
  border:1px solid rgba(255,255,255,.10);
  background:#080c17; transition:transform .22s,border-color .22s,box-shadow .22s;
}
.boss-card:hover { transform:translateY(-5px); border-color:rgba(103,232,249,.45); box-shadow:0 16px 35px rgba(0,0,0,.42); }
.boss-card img { width:100%; height:250px; object-fit:cover; object-position:center top; display:block; }
.boss-card::after { content:""; position:absolute; inset:0; background:linear-gradient(180deg,transparent 48%,rgba(5,8,18,.97) 100%); pointer-events:none; }
.boss-card-copy { position:absolute; left:16px; right:16px; bottom:15px; z-index:2; }
.boss-card-name { color:#fff; font:800 1.2rem Orbitron,sans-serif; }
.boss-card-meta { color:#9fb2cb; font-size:.7rem; margin-top:4px; letter-spacing:1px; text-transform:uppercase; }
.boss-card-selected { border-color:#67e8f9; box-shadow:0 0 0 1px rgba(103,232,249,.35),0 18px 40px rgba(0,0,0,.45); }
.dungeon-battle-shell {
  border:1px solid rgba(126,177,235,.22); border-radius:24px; padding:10px;
  background:linear-gradient(145deg,rgba(7,11,22,.97),rgba(20,12,36,.94));
  box-shadow:0 28px 75px rgba(0,0,0,.48);
}
.dungeon-art-frame { position:relative; overflow:hidden; min-height:520px; border-radius:18px; background:#050811; }
.dungeon-art-frame img { width:100%; height:520px; object-fit:cover; object-position:center top; display:block; filter:saturate(1.08) contrast(1.05); }
.dungeon-art-frame::after { content:""; position:absolute; inset:0; pointer-events:none; background:linear-gradient(180deg,rgba(0,0,0,.02) 35%,rgba(4,6,14,.96) 100%); }
.dungeon-boss-overlay { position:absolute; inset:0; z-index:2; pointer-events:none; }
.boss-scanline { position:absolute; left:0; right:0; top:30%; height:1px; background:linear-gradient(90deg,transparent,var(--boss-glow),transparent); box-shadow:0 0 14px var(--boss-glow); opacity:.5; animation:bossScan 3.2s ease-in-out infinite; }
.boss-overlay-top,.boss-overlay-bottom { position:absolute; left:18px; right:18px; display:flex; justify-content:space-between; gap:10px; font:700 .62rem Orbitron,sans-serif; letter-spacing:1.4px; }
.boss-overlay-top { top:16px; color:#dbeafe; } .boss-overlay-top span:last-child{color:#86efac;}
.boss-overlay-bottom { bottom:18px; align-items:end; } .boss-overlay-bottom b{font-size:1.6rem;color:#fff;text-shadow:0 0 16px var(--boss-glow);} .boss-overlay-bottom span{color:var(--boss-glow);}
.dungeon-hud { height:100%; padding:22px; border-radius:18px; border:1px solid rgba(126,177,235,.18); background:linear-gradient(160deg,rgba(18,28,50,.84),rgba(8,13,26,.88)); }
.dungeon-hud-title { font:800 1.7rem Orbitron,sans-serif; color:#fff; margin:6px 0; }
.dungeon-hud-sub { color:#91a5c0; font-size:.82rem; }
.dungeon-hp-label { display:flex; justify-content:space-between; margin-top:20px; color:#9fb2cb; font-size:.72rem; }
.dungeon-hp { height:12px; margin-top:7px; border-radius:99px; overflow:hidden; background:#171d2b; }
.dungeon-hp > div { height:100%; background:linear-gradient(90deg,#ef4444,#f97316,#fbbf24); transition:width .55s ease; }
.dungeon-stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:16px 0; }
.dungeon-stat { padding:11px 8px; text-align:center; border:1px solid rgba(126,177,235,.14); border-radius:12px; background:rgba(7,13,26,.62); }
.dungeon-stat b { display:block; color:#fff; font:700 1rem Orbitron,sans-serif; } .dungeon-stat span{color:#7f93ad;font-size:.62rem;text-transform:uppercase;letter-spacing:1px;}
.dungeon-question { margin-top:17px; padding:18px; border-radius:15px; border:1px solid rgba(94,234,212,.20); background:linear-gradient(145deg,rgba(15,39,58,.55),rgba(28,17,51,.55)); }
.dungeon-question-label { color:#5eead4; font:700 .64rem Orbitron,sans-serif; letter-spacing:1.5px; }
.dungeon-question-text { color:#fff; font:700 1.16rem Rajdhani,sans-serif; line-height:1.45; margin-top:7px; }
.dungeon-result { padding:34px; text-align:center; border:1px solid rgba(251,191,36,.35); border-radius:20px; background:linear-gradient(150deg,rgba(58,43,16,.65),rgba(23,27,45,.65)); }
@keyframes bossScan { 0%,100%{transform:translateY(-70px);opacity:0;} 35%,65%{opacity:.7;} 50%{transform:translateY(210px);} }
@media (max-width: 850px) {
  .dungeon-art-frame,.dungeon-art-frame img{min-height:390px;height:390px;}
  .boss-card img{height:210px;}
  .dungeon-gate-content{padding:20px;}
}
@media (prefers-reduced-motion: reduce) {
  .boss-scanline{animation:none;} .boss-card{transition:none;} .boss-card:hover{transform:none;}
}
/* ── Forms & inputs ───────────────────────────────────────────── */
[data-testid="stForm"] {
  padding: 16px 18px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: linear-gradient(160deg, rgba(18,30,54,.5), rgba(12,17,32,.5));
  backdrop-filter: blur(10px);
}
label, [data-testid="stWidgetLabel"] p {
  color: var(--text-dim) !important;
  font-weight: 600 !important;
  font-size: 0.84rem !important;
  letter-spacing: 0.1px !important;
}
input, textarea, [data-baseweb="select"] > div,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  background: rgba(9, 16, 30, .78) !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text) !important;
  font-size: 0.9rem !important;
  transition: border-color .15s, box-shadow .15s;
}
input::placeholder, textarea::placeholder {
  color: #6a7b95 !important;
  font-size: 0.88rem;
}
input:focus, textarea:focus,
[data-baseweb="select"] > div:focus-within,
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--cyan) !important;
  box-shadow: 0 0 0 1px rgba(94,234,212,.35), 0 0 14px rgba(94,234,212,.08) !important;
  outline: none !important;
}
[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius: var(--radius-lg) !important;
  background: rgba(12,20,38,.45) !important;
  backdrop-filter: blur(10px);
  overflow: hidden;
}
[data-testid="stExpander"] details summary p {
  font-weight: 600;
  color: #e0ebff;
}
[data-baseweb="select"] ul {
  background: rgba(14,22,40,.96) !important;
  border: 1px solid var(--line-strong) !important;
  border-radius: var(--radius-sm) !important;
  backdrop-filter: blur(12px);
}
[data-baseweb="select"] ul li {
  color: var(--text-dim) !important;
}
[data-baseweb="select"] ul li:hover {
  background: rgba(94,234,212,.1) !important;
  color: #fff !important;
}

/* ── Tabs ─────────────────────────────────────────────────────── */
[data-testid="stTabs"] {
  border-bottom: 1px solid var(--line);
  margin-bottom: 16px;
}
[data-testid="stTabs"] [role="tablist"] { gap: 2px; }
[data-testid="stTabs"] [role="tab"] {
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  padding: 10px 16px !important;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.15px;
  min-height: 40px;
}
[data-testid="stTabs"] [role="tab"]:hover {
  color: var(--cyan-soft) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--cyan) !important;
  background: rgba(94,234,212,.06);
  border-bottom: 2px solid var(--cyan);
}

/* ── Chat UI ──────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
  background: linear-gradient(160deg, rgba(20,33,57,.6), rgba(14,20,36,.6));
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  padding: 12px 14px;
  box-shadow: var(--shadow-sm);
}
[data-testid="stChatMessage"][data-testid="chat-message-user"] {
  background: linear-gradient(160deg, rgba(14,55,68,.65), rgba(48,30,90,.6));
  border-color: rgba(94,234,212,.22);
}
[data-testid="stChatInput"] textarea {
  background: rgba(9,16,30,.82) !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--radius-sm) !important;
}
[data-testid="stChatInput"] textarea:focus {
  border-color: var(--cyan) !important;
}
.chat-empty {
  padding: 32px 24px;
  text-align: center;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-lg);
  background: rgba(12,20,38,.35);
}
.chat-empty-icon { font-size: 2.2rem; opacity: .8; }
.chat-empty-title {
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 1rem;
  color: #e8f3ff;
  margin: 8px 0 4px;
}
.chat-suggestion {
  display: inline-block;
  padding: 7px 13px;
  margin: 4px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: rgba(20,32,56,.55);
  color: var(--text-dim);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all .18s;
}
.chat-suggestion:hover {
  border-color: var(--cyan);
  color: var(--cyan-soft);
  background: rgba(94,234,212,.08);
}

/* ── Quest rows ───────────────────────────────────────────────── */
.quest {
  padding: 12px 16px;
  margin: 7px 0;
  border-radius: var(--radius-md);
}
.quest-done { opacity: .6; border-color: rgba(52,120,106,.4); }
.quest-title { font-weight: 600; color: #f0f6ff; }

/* ── Calendar ─────────────────────────────────────────────────── */
[class*="st-key-cal_"] { min-width: 0; }
[class*="st-key-cal_"] button {
  height: 76px;
  min-height: 76px;
  padding: 7px 4px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--line);
  background: linear-gradient(155deg, rgba(22,39,68,.72), rgba(11,18,34,.72));
  color: #dce9fb;
  white-space: pre-line;
  font-size: 11px;
  line-height: 1.4;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
  transition: all .18s ease;
}
[class*="st-key-cal_"] button:hover {
  transform: translateY(-2px);
  border-color: rgba(94,234,212,.45);
  background: linear-gradient(155deg, #1a4469, #34265a);
}
[class*="st-key-cal_"] button[kind="primary"] {
  border-color: var(--cyan);
  background: linear-gradient(145deg, #135268, #48317d);
  color: white;
  box-shadow: 0 0 0 1px rgba(94,234,212,.3), 0 5px 18px rgba(34,211,238,.2);
}

/* ── Achievements ─────────────────────────────────────────────── */
.achievement-card {
  min-height: 148px;
  padding: 16px;
  border-radius: var(--radius-md);
}
.achievement-card:hover {
  transform: translateY(-3px);
  border-color: rgba(94,234,212,.45);
  box-shadow: 0 12px 28px rgba(0,0,0,.4), 0 0 16px rgba(94,234,212,.1);
}
.achievement-locked { filter: grayscale(.85); opacity: .45; }
.achievement-icon { font-size: 1.9rem; }
.achievement-name {
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 0.86rem;
  color: #eef6ff;
  margin-top: 7px;
}

/* ── System / RPG extras ──────────────────────────────────────── */
.level-up-banner, .reward-banner {
  margin: 14px 0;
  padding: 16px 20px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(167,139,250,.38);
  background: linear-gradient(100deg, rgba(48,29,95,.65), rgba(16,45,84,.65));
  box-shadow: 0 0 22px rgba(139,92,246,.12), inset 0 1px 0 rgba(255,255,255,.06);
}
.level-up-kicker {
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 0.7rem;
  color: var(--cyan);
  letter-spacing: 2.2px;
}
.level-up-title {
  font-family: 'Orbitron', sans-serif;
  font-weight: 800;
  font-size: 1.5rem;
  color: white;
  margin: 5px 0;
  letter-spacing: 0.2px;
}
.reward-banner {
  color: #fde68a;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 0.82rem;
  letter-spacing: 1px;
}
.system-panel {
  padding: 18px 20px;
  border-radius: var(--radius-lg);
  border-color: rgba(94,234,212,.22);
}
.system-next {
  margin-top: 12px;
  padding: 13px 15px;
  border-radius: var(--radius-md);
  border: 1px solid rgba(167,139,250,.22);
  background: linear-gradient(135deg, rgba(26,22,56,.55), rgba(14,34,56,.55));
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.shadow-reaction {
  padding: 13px 16px;
  border-radius: var(--radius-md);
  border-color: rgba(94,234,212,.2);
  background: linear-gradient(135deg, rgba(7,24,40,.6), rgba(32,18,58,.6));
  margin-bottom: 14px;
}
.shadow-reaction span {
  font-family: 'Orbitron', sans-serif;
  font-weight: 800;
  font-size: 0.7rem;
  color: var(--purple);
  letter-spacing: 1.5px;
  display: block;
  margin-bottom: 5px;
}
.shadow-reaction b { color: #eaf3ff; font-weight: 600; }

.timer-shell, .dungeon-result, .guild-banner {
  padding: 22px;
  border-radius: var(--radius-xl);
}
.timer-shell {
  border-color: rgba(94,234,212,.25);
  background:
    radial-gradient(circle at 50% 0%, rgba(34,211,238,.12), transparent 45%),
    linear-gradient(150deg, rgba(11,26,48,.8), rgba(20,17,43,.8));
  box-shadow: var(--shadow-md);
}
.dungeon-result {
  text-align: center;
  border-color: rgba(251,191,36,.35);
  background: linear-gradient(150deg, rgba(58,43,16,.65), rgba(23,27,45,.65));
  box-shadow: 0 0 28px rgba(251,191,36,.08);
}
.guild-banner {
  border-color: rgba(94,234,212,.28);
  background: linear-gradient(115deg, rgba(16,47,79,.7), rgba(41,22,77,.7));
  box-shadow: var(--shadow-md);
}
.guild-code {
  font-family: 'Orbitron', sans-serif;
  font-weight: 800;
  font-size: 1.3rem;
  color: var(--cyan);
  letter-spacing: 2px;
}
.focus-badge {
  font-family: 'Orbitron', sans-serif;
  font-weight: 800;
  font-size: 0.72rem;
  letter-spacing: 2px;
  color: var(--cyan);
  text-transform: uppercase;
}
.review-card {
  padding: 24px 26px;
  border-radius: var(--radius-xl);
  border-color: rgba(167,139,250,.25);
  box-shadow: var(--shadow-md);
  min-height: 220px;
}
.review-front {
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 1.45rem;
  color: white;
  line-height: 1.35;
}
.review-back {
  font-size: 0.95rem;
  color: var(--text-dim);
  line-height: 1.65;
  padding-top: 14px;
  border-top: 1px solid rgba(255,255,255,.08);
  margin-top: 14px;
}

/* ── Dungeon boss art ─────────────────────────────────────────── */
.dungeon-boss-art {
  position: relative;
  overflow: hidden;
  height: 160px;
  margin: 8px 0 14px;
  border-radius: var(--radius-lg);
  border: 1px solid color-mix(in srgb, var(--boss-glow), transparent 55%);
  background:
    radial-gradient(ellipse at 50% 82%, color-mix(in srgb, var(--boss-glow), transparent 70%), transparent 58%),
    linear-gradient(150deg, #080d1b, #18102a);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 40px color-mix(in srgb, var(--boss-glow), transparent 85%);
}
.boss-aura {
  position: absolute;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  background: var(--boss-glow);
  opacity: .14;
  filter: blur(24px);
  animation: bossPulse 2.8s ease-in-out infinite;
}
.boss-art-emoji {
  position: relative;
  font-size: 84px;
  line-height: 1;
  filter: drop-shadow(0 0 16px var(--boss-glow));
  animation: bossFloat 3.5s ease-in-out infinite;
}
.boss-art-label {
  position: absolute;
  bottom: 10px;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 0.65rem;
  letter-spacing: 2px;
  color: var(--boss-glow);
}
.dungeon-boss {
  padding: 20px 22px;
  border-radius: var(--radius-xl);
  border: 1px solid rgba(248,113,113,.35);
  background:
    radial-gradient(circle at 50% 0%, rgba(127,29,29,.28), transparent 50%),
    linear-gradient(150deg, rgba(25,12,25,.9), rgba(10,17,31,.9));
  box-shadow: var(--shadow-lg), 0 0 24px rgba(239,68,68,.1);
  text-align: center;
}
.boss-icon {
  font-size: 60px;
  filter: drop-shadow(0 0 16px rgba(239,68,68,.55));
  animation: bossFloat 3.5s ease-in-out infinite;
}
.boss-name {
  font-family: 'Orbitron', sans-serif;
  font-weight: 800;
  font-size: 1.5rem;
  color: #fff;
  text-shadow: 0 0 14px rgba(239,68,68,.3);
}
.combo {
  font-family: 'Orbitron', sans-serif;
  font-weight: 800;
  font-size: 1.35rem;
  color: var(--gold);
  text-shadow: 0 0 12px rgba(251,191,36,.35);
}

/* ── Hunter report ────────────────────────────────────────────── */
.report-day {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 7px 0;
}

/* ── Animations (respect reduced motion) ──────────────────────── */
@keyframes bossPulse { 0%,100% { transform: scale(.85); opacity: .12; } 50% { transform: scale(1.15); opacity: .22; } }
@keyframes bossFloat { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; animation: none !important; }
  .hero-kicker { animation: none; }
}

/* ── Responsive tweaks ────────────────────────────────────────── */
@media (max-width: 900px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1rem; }
  [class*="st-key-cal_"] button { height: 62px; min-height: 62px; font-size: 10px; padding: 5px 3px; }
  .hero { padding: 18px 18px; }
  .stat-value, [data-testid="stMetricValue"] { font-size: 1.4rem; }
  .panel { padding: 15px 16px; }
  .stat { padding: 12px 13px; min-height: 74px; }
}
@media (max-width: 560px) {
  .hero-title { font-size: 1.25rem; }
  .boss-art-emoji { font-size: 62px; }
  .dungeon-boss-art { height: 130px; }
  .achievement-card { min-height: 132px; padding: 13px; }
  .system-chip, .rank { font-size: 0.66rem; padding: 3px 9px; }
}

/* ── Scrollbar polish ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(94,234,212,.15);
  border-radius: 99px;
  border: 2px solid transparent;
  background-clip: padding-box;
}
::-webkit-scrollbar-thumb:hover { background: rgba(94,234,212,.28); background-clip: padding-box; border: 2px solid transparent; }

/* ── Cinematic video glass system ───────────────────────────── */
.video-command-hero{position:relative;overflow:hidden;min-height:410px;margin:0 0 20px;border-radius:30px;border:1px solid rgba(103,232,249,.28);background:#050711;box-shadow:0 30px 90px rgba(0,0,0,.55),inset 0 1px 0 rgba(255,255,255,.08);isolation:isolate}
.video-command-hero video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.72;filter:saturate(1.08) contrast(1.06);z-index:-3}
.video-command-hero::before{content:"";position:absolute;inset:0;z-index:-2;background:linear-gradient(90deg,rgba(3,5,15,.94) 0%,rgba(4,6,17,.72) 38%,rgba(7,5,19,.30) 72%,rgba(4,5,14,.72) 100%),linear-gradient(180deg,rgba(5,5,16,.08),rgba(4,5,14,.78))}
.video-command-hero::after{content:"";position:absolute;inset:0;pointer-events:none;z-index:-1;background:linear-gradient(90deg,transparent,rgba(103,232,249,.08),transparent),repeating-linear-gradient(115deg,transparent 0 18px,rgba(255,255,255,.025) 19px 20px);mix-blend-mode:screen}
.video-glass{position:relative;width:min(720px,86%);margin:30px;padding:28px;border:1px solid rgba(255,255,255,.15);border-radius:24px;background:linear-gradient(145deg,rgba(5,10,24,.73),rgba(27,14,51,.52));backdrop-filter:blur(16px) saturate(135%);-webkit-backdrop-filter:blur(16px) saturate(135%);box-shadow:0 22px 60px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.10);transition:transform .35s cubic-bezier(.16,1,.3,1),border-color .25s ease}
.video-glass:hover{transform:perspective(1100px) rotateY(-1.2deg) rotateX(.8deg) translateY(-4px);border-color:rgba(103,232,249,.48)}
.video-kicker{color:#67e8f9;font:800 .62rem Orbitron,sans-serif;letter-spacing:2.2px;text-transform:uppercase}
.video-title{font:800 clamp(1.7rem,4vw,3.1rem) Orbitron,sans-serif;color:#fff;line-height:1.08;margin:8px 0}
.video-copy{color:#a8b8cf;font-size:.84rem;max-width:650px}
.video-hud-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.video-hud-chip{padding:8px 11px;border-radius:11px;background:rgba(3,7,17,.52);border:1px solid rgba(255,255,255,.09);font:700 .64rem Orbitron,sans-serif;color:#dceaff;letter-spacing:.7px}
.video-scanline{position:absolute;left:0;right:0;top:-5%;height:2px;background:linear-gradient(90deg,transparent,#67e8f9,#a78bfa,transparent);box-shadow:0 0 16px #67e8f9;opacity:.55;animation:videoScan 5s linear infinite;pointer-events:none}
@keyframes videoScan{0%{top:-5%}100%{top:105%}}
.module-hud{position:relative;overflow:hidden;margin:0 0 17px;padding:15px 18px;border:1px solid rgba(126,177,235,.18);border-radius:17px;background:linear-gradient(110deg,rgba(7,14,29,.82),rgba(27,14,49,.72));backdrop-filter:blur(14px);box-shadow:0 14px 38px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.06)}
.module-hud::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(#67e8f9,#a78bfa);box-shadow:0 0 15px rgba(103,232,249,.45)}
.module-hud::after{content:"";position:absolute;right:-40px;top:-65px;width:150px;height:150px;border-radius:50%;border:1px solid rgba(167,139,250,.14);box-shadow:0 0 0 20px rgba(167,139,250,.025),0 0 0 40px rgba(103,232,249,.015);pointer-events:none}
.module-hud-main{color:#eaf4ff;font:800 .73rem Orbitron,sans-serif;letter-spacing:1.35px;text-transform:uppercase}
.module-hud-sub{color:#71839f;font-size:.68rem;margin-top:3px}
.module-hud-live{float:right;color:#67e8f9;font:700 .58rem Orbitron,sans-serif;letter-spacing:1px}
.motion-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:10px 0 18px}
.motion-tile{position:relative;overflow:hidden;padding:15px;border-radius:17px;border:1px solid rgba(126,177,235,.16);background:linear-gradient(145deg,rgba(18,31,57,.78),rgba(11,14,29,.76));transition:transform .3s cubic-bezier(.16,1,.3,1),border-color .25s,box-shadow .3s}
.motion-tile:hover{transform:perspective(800px) rotateY(-2deg) translateY(-5px);border-color:rgba(103,232,249,.4);box-shadow:0 20px 45px rgba(0,0,0,.36),0 0 24px rgba(103,232,249,.06)}
.motion-tile-icon{font-size:1.35rem}.motion-tile-title{font:800 .72rem Orbitron,sans-serif;color:#fff;margin-top:6px}.motion-tile-copy{font-size:.67rem;color:#7386a1;margin-top:3px}
@media(max-width:800px){.video-glass{width:auto;margin:14px;padding:20px}.video-command-hero{min-height:430px}.motion-grid{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){.video-scanline{animation:none}.video-glass:hover,.motion-tile:hover{transform:none}}


.module-motion-row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-top:11px}
.module-motion{padding:8px 10px;border:1px solid rgba(126,177,235,.11);border-radius:11px;background:rgba(3,8,19,.36);transition:transform .22s,border-color .22s,background .22s}
.module-motion:hover{transform:translateY(-2px);border-color:rgba(103,232,249,.34);background:rgba(20,35,58,.52)}
.module-motion b{display:block;color:#dbeafe;font:700 .59rem Orbitron,sans-serif;letter-spacing:.6px}
.module-motion span{display:block;color:#667992;font-size:.61rem;margin-top:2px}
@media(max-width:650px){.module-motion-row{grid-template-columns:1fr}}


/* ── Pro Study Intelligence ───────────────────────────────── */
.intel-hero{position:relative;overflow:hidden;border-radius:26px;padding:28px;margin-bottom:18px;border:1px solid rgba(103,232,249,.25);background:radial-gradient(circle at 85% 20%,rgba(139,92,246,.20),transparent 30%),radial-gradient(circle at 15% 80%,rgba(34,211,238,.11),transparent 32%),linear-gradient(135deg,rgba(8,17,34,.94),rgba(28,14,48,.94));box-shadow:0 26px 75px rgba(0,0,0,.44)}
.intel-hero::before{content:"";position:absolute;right:-80px;top:-100px;width:300px;height:300px;border:1px solid rgba(103,232,249,.13);border-radius:50%;box-shadow:0 0 0 35px rgba(103,232,249,.025),0 0 0 70px rgba(167,139,250,.018);pointer-events:none}
.intel-kicker{color:#67e8f9;font:800 .62rem Orbitron,sans-serif;letter-spacing:2px;text-transform:uppercase}.intel-title{color:#fff;font:800 clamp(1.6rem,3vw,2.5rem) Orbitron,sans-serif;margin:6px 0}.intel-sub{color:#93a6c0;max-width:760px;font-size:.83rem}
.intel-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:12px 0 18px}
.intel-card{position:relative;overflow:hidden;padding:16px;border-radius:17px;border:1px solid rgba(126,177,235,.17);background:linear-gradient(145deg,rgba(18,31,57,.78),rgba(10,15,29,.78));box-shadow:0 14px 35px rgba(0,0,0,.26);transition:transform .25s,border-color .25s}
.intel-card:hover{transform:translateY(-4px);border-color:rgba(103,232,249,.4)}.intel-card-label{color:#7386a1;font:700 .59rem Orbitron,sans-serif;letter-spacing:1.2px}.intel-card-value{color:#fff;font:800 1.45rem Orbitron,sans-serif;margin-top:5px}.intel-card-note{color:#8091a8;font-size:.65rem;margin-top:3px}
.intel-radar{display:grid;grid-template-columns:1.25fr .75fr;gap:14px}.intel-panel{padding:18px;border-radius:20px;border:1px solid rgba(126,177,235,.16);background:linear-gradient(150deg,rgba(13,23,43,.78),rgba(10,14,27,.72));box-shadow:0 16px 42px rgba(0,0,0,.28)}
.intel-panel-title{color:#edf5ff;font:800 .78rem Orbitron,sans-serif;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px}.intel-topic{display:flex;align-items:center;gap:10px;margin:10px 0}.intel-topic-name{width:120px;color:#c7d5e8;font-size:.72rem}.intel-topic-track{height:8px;flex:1;border-radius:99px;background:#17243a;overflow:hidden}.intel-topic-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#22d3ee,#8b5cf6)}.intel-topic-score{width:38px;text-align:right;color:#fff;font:700 .67rem Orbitron,sans-serif}
.intel-plan{display:grid;gap:8px}.intel-plan-item{display:grid;grid-template-columns:70px 1fr auto;gap:10px;align-items:center;padding:11px;border-radius:13px;background:rgba(5,10,21,.5);border:1px solid rgba(255,255,255,.06)}.intel-plan-time{color:#67e8f9;font:800 .63rem Orbitron,sans-serif}.intel-plan-main{color:#eaf2ff;font-size:.73rem;font-weight:700}.intel-plan-sub{color:#71839f;font-size:.62rem}.intel-plan-xp{color:#fbbf24;font:700 .62rem Orbitron,sans-serif}
.intel-callout{padding:13px 15px;border-radius:14px;border:1px solid rgba(167,139,250,.20);background:linear-gradient(110deg,rgba(65,45,105,.22),rgba(10,22,42,.35));color:#b8c8de;font-size:.73rem;line-height:1.55}
.intel-streak{font:800 2rem Orbitron,sans-serif;color:#fff}.intel-streak span{font-size:.7rem;color:#67e8f9;letter-spacing:1px}
@media(max-width:950px){.intel-grid{grid-template-columns:repeat(2,1fr)}.intel-radar{grid-template-columns:1fr}}@media(max-width:600px){.intel-grid{grid-template-columns:1fr}}


/* ── Exam Command Center ───────────────────────────────────── */
.exam-hero{position:relative;overflow:hidden;border-radius:28px;padding:30px;margin-bottom:18px;border:1px solid rgba(251,191,36,.24);background:radial-gradient(circle at 85% 15%,rgba(251,191,36,.16),transparent 28%),radial-gradient(circle at 10% 90%,rgba(34,211,238,.11),transparent 30%),linear-gradient(135deg,rgba(12,18,34,.96),rgba(36,20,47,.94));box-shadow:0 28px 80px rgba(0,0,0,.44),inset 0 1px 0 rgba(255,255,255,.07)}
.exam-hero::after{content:"";position:absolute;right:-90px;top:-130px;width:330px;height:330px;border:1px solid rgba(251,191,36,.16);border-radius:50%;box-shadow:0 0 0 35px rgba(251,191,36,.025),0 0 0 70px rgba(167,139,250,.018);pointer-events:none}
.exam-kicker{color:#fbbf24;font:800 .62rem Orbitron,sans-serif;letter-spacing:2px}.exam-title{color:#fff;font:800 clamp(1.7rem,3vw,2.7rem) Orbitron,sans-serif;margin:7px 0}.exam-sub{color:#a7b6cc;max-width:800px;font-size:.84rem}
.exam-empty{padding:35px;text-align:center;border:1px dashed rgba(103,232,249,.25);border-radius:20px;background:rgba(6,14,28,.55);color:#67e8f9;font:800 .72rem Orbitron,sans-serif;letter-spacing:1.2px}.exam-empty span{display:block;color:#71839f;font:500 .75rem Inter,sans-serif;letter-spacing:0;margin-top:8px}
.exam-topic-row{display:grid;grid-template-columns:210px 1fr 55px;gap:12px;align-items:center;margin:9px 0;padding:10px 12px;border:1px solid rgba(126,177,235,.10);border-radius:13px;background:rgba(7,13,26,.45);transition:transform .2s,border-color .2s}.exam-topic-row:hover{transform:translateX(3px);border-color:rgba(103,232,249,.30)}.exam-topic-name{color:#e7f0ff;font-size:.73rem}.exam-topic-name span{display:block;color:#fbbf24;font:700 .54rem Orbitron,sans-serif;letter-spacing:.7px;margin-top:2px}.exam-topic-track,.mastery-track{height:9px;border-radius:99px;background:#16243b;overflow:hidden}.exam-topic-track>div,.mastery-track>div{height:100%;border-radius:99px;background:linear-gradient(90deg,#f59e0b,#22d3ee,#8b5cf6);box-shadow:0 0 12px rgba(34,211,238,.22)}.exam-topic-score{font:800 .68rem Orbitron,sans-serif;color:#fff;text-align:right}
.exam-plan-row{display:grid;grid-template-columns:78px 1fr 75px;gap:12px;align-items:center;padding:13px;margin:7px 0;border:1px solid rgba(126,177,235,.12);border-radius:14px;background:linear-gradient(100deg,rgba(18,29,51,.72),rgba(22,14,38,.58))}.exam-plan-row>b{color:#67e8f9;font:800 .61rem Orbitron,sans-serif}.exam-plan-row strong{color:#edf5ff;font-size:.73rem}.exam-plan-row span{display:block;color:#71839f;font-size:.62rem;margin-top:2px}.exam-plan-row em{font-style:normal;color:#fbbf24;font:700 .55rem Orbitron,sans-serif;text-align:right}
.exam-ai-output{padding:18px;border-radius:17px;border:1px solid rgba(167,139,250,.25);background:linear-gradient(120deg,rgba(50,34,84,.35),rgba(7,17,32,.60));color:#dce8f7;line-height:1.65;box-shadow:0 15px 40px rgba(0,0,0,.25)}
.mastery-row{display:grid;grid-template-columns:150px 1fr 55px 175px;gap:10px;align-items:center;margin:8px 0;padding:10px 12px;border-radius:13px;background:rgba(7,13,26,.43);border:1px solid rgba(126,177,235,.10)}.mastery-row>b{color:#e8f1ff;font-size:.72rem}.mastery-row>strong{font:800 .67rem Orbitron;color:#fff;text-align:right}.mastery-row>span{color:#71839f;font-size:.59rem}
@media(max-width:800px){.exam-topic-row{grid-template-columns:1fr}.mastery-row{grid-template-columns:1fr 1fr}.mastery-row .mastery-track{grid-column:1/-1}.exam-plan-row{grid-template-columns:65px 1fr}}

</style>
""", unsafe_allow_html=True)
if MOTION_CSS:
    st.markdown("<style id='studybuddy-motion-layer'>"+MOTION_CSS+"</style>", unsafe_allow_html=True)
st.markdown("<div class='sb-grid-floor' aria-hidden='true'></div>", unsafe_allow_html=True)



# ============================================================
# Cinematic motion UI helpers
# ============================================================
HERO_VIDEO_URL = "https://raw.githubusercontent.com/shanaldo7/STUDYBUDDY-LEVEL-UP-gamified-study-planner/main/assets/studybuddy_hero.mp4"

def render_module_hud(current_page):
    meta = {
        "📅 Quest Schedule": ("MISSION CONTROL · QUEST DEPLOYMENT","Deploy, prioritize and clear today's missions."),
        "⚔️ Dungeon Battles": ("COMBAT INSTANCE · KNOWLEDGE RAID","Turn correct answers into damage and clear the shadow."),
        "⏱️ Focus Room": ("TRAINING CHAMBER · DEEP WORK","Build focus streaks and convert time into progression."),
        "🧠 Revision Lab": ("MEMORY CORE · ACTIVE RECALL","Review due cards, streaks and mastery."),
        "✨ Gemma Study Lab": ("AI LAB · GEMMA INTELLIGENCE","Generate study material, quizzes and plans."),
        "🏆 Achievements": ("HUNTER ARCHIVE · MILESTONES","Track unlocks, rewards and progression."),
        "📊 Hunter Report": ("SYSTEM ANALYTICS · PERFORMANCE","Read your study telemetry and progression."),
        "🎯 Study Intelligence": ("ADAPTIVE CORE · PERSONALIZED LEARNING","Turn your activity into a daily plan, weak-topic radar and AI coaching."),
        "📈 Progress Calendar": ("HUNTER HISTORY · CONSISTENCY MAP","See when your study activity actually happened across the last 84 days."),
        "🌳 Skill Tree": ("AWAKENING TREE · STUDY ABILITIES","Spend earned skill points on permanent study abilities."),
        "🎓 Exam Command Center": ("EXAM PROTOCOL · TACTICAL PREPARATION","Map your syllabus, measure mastery, identify risk and deploy an adaptive study plan."),
        "🤖 AI System Assistant": ("SYSTEM CORE · AI ASSISTANT","Use the assistant as your tactical study operator."),
        "👥 Shadow Army": ("SHADOW COMMAND · COMPANIONS","Manage your companions and squad progression."),
        "🔒 Shadow Army": ("LOCKED SYSTEM · DUNGEON GATE","Clear your first Dungeon and reach Level 2 to awaken the Shadow Army."),
        "👑 Anime RPG": ("RPG SYSTEM · PROGRESSION","Characters, bosses, rewards and power progression."),
        "🤝 Guild Hall": ("GUILD NETWORK · STUDY PARTY","Coordinate your study party and shared goals."),
        "📚 Important PDFs": ("KNOWLEDGE ARCHIVE · DOCUMENTS","Organize the documents behind your study system."),
        "🧬 Character & Power": ("AWAKENING CORE · CHARACTER","Upgrade attributes, class identity and hunter power."),
        "⚙️ Settings": ("SYSTEM CONFIG · CONTROL PANEL","Tune your StudyBuddy system."),
    }
    title, subtitle = meta.get(current_page, ("SYSTEM MODULE · STUDYBUDDY","Interactive study system"))
    interaction_map = {
        "📅 Quest Schedule": (("DEPLOY","Create a mission"),("PRIORITIZE","Sort the board"),("CLEAR","Claim XP")),
        "⚔️ Dungeon Battles": (("LOCK TARGET","Choose shadow"),("STRIKE","Answer to damage"),("CLAIM","Collect rewards")),
        "⏱️ Focus Room": (("CHARGE","Start focus"),("COMBO","Protect streak"),("SYNC","Convert time to XP")),
        "🧠 Revision Lab": (("FLIP","Reveal recall"),("RATE","Grade memory"),("CHAIN","Continue queue")),
        "✨ Gemma Study Lab": (("GENERATE","Create content"),("REFINE","Tune output"),("DEPLOY","Send to study")),
        "🏆 Achievements": (("SCAN","Check milestones"),("UNLOCK","Reveal reward"),("EQUIP","Show badge")),
        "📊 Hunter Report": (("SCAN","Read telemetry"),("COMPARE","Find trends"),("EVOLVE","Choose next move")),
        "🎯 Study Intelligence": (("SCAN","Read telemetry"),("PRIORITIZE","Find weakness"),("DEPLOY","Start next action")),
        "📈 Progress Calendar": (("SCAN","Read activity"),("COMPARE","Spot gaps"),("EVOLVE","Protect consistency")),
        "🌳 Skill Tree": (("EARN","Gain points"),("UNLOCK","Awaken skill"),("EVOLVE","Improve study")),
        "🎓 Exam Command Center": (("MAP","Build syllabus"),("SCAN","Measure mastery"),("RAID","Attack weak topics")),
        "🤖 AI System Assistant": (("ASK","Send command"),("THINK","Process context"),("ACT","Execute advice")),
        "👥 Shadow Army": (("SUMMON","Select companion"),("TRAIN","Build power"),("FORMATION","Set squad")),
        "🔒 Shadow Army": (("LOCKED","Enter Dungeon"),("CLEAR","Complete battle"),("AWAKEN","Reach Level 2")),
        "👑 Anime RPG": (("EXPLORE","Open roster"),("RAID","Fight boss"),("REWARD","Upgrade")),
        "🤝 Guild Hall": (("CHECK IN","Update activity"),("PARTY","Manage hunters"),("GOAL","Track weekly XP")),
        "📚 Important PDFs": (("ARCHIVE","Add document"),("SCAN","Extract knowledge"),("REVIEW","Study source")),
        "🧬 Character & Power": (("AWAKEN","Choose attribute"),("UPGRADE","Spend progression"),("EQUIP","Set identity")),
        "⚙️ Settings": (("CONFIGURE","Tune system"),("SECURE","Manage AI"),("SAVE","Apply changes")),
    }
    interactions = interaction_map.get(current_page, (("OPEN","Explore module"),("ACT","Use controls"),("SYNC","Save progress")))
    cards = "".join(f"<div class='module-motion'><b>{a}</b><span>{b}</span></div>" for a,b in interactions)
    st.markdown(
        f"<div class='module-hud'><span class='module-hud-live'>● LIVE</span><div class='module-hud-main'>◈ {title}</div><div class='module-hud-sub'>{subtitle}</div><div class='module-motion-row'>{cards}</div></div>",
        unsafe_allow_html=True,
    )



# ---------- Database ----------
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

with db() as con:
    con.execute("""CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL DEFAULT 'Hunter',
        xp INTEGER NOT NULL DEFAULT 0, focus INTEGER NOT NULL DEFAULT 1,
        discipline INTEGER NOT NULL DEFAULT 1, knowledge INTEGER NOT NULL DEFAULT 1,
        energy INTEGER NOT NULL DEFAULT 1, streak INTEGER NOT NULL DEFAULT 0,
        last_study TEXT, title TEXT NOT NULL DEFAULT 'New Awakening'
    )""")
    con.execute("INSERT OR IGNORE INTO profile(id) VALUES(1)")
    # Add the character field for databases created by an earlier version.
    profile_columns = {row[1] for row in con.execute("PRAGMA table_info(profile)").fetchall()}
    if "character" not in profile_columns:
        con.execute("ALTER TABLE profile ADD COLUMN character TEXT NOT NULL DEFAULT 'Shadow Hunter'")
    if "penalty_enabled" not in profile_columns:
        con.execute("ALTER TABLE profile ADD COLUMN penalty_enabled INTEGER NOT NULL DEFAULT 1")
    if "penalty_amount" not in profile_columns:
        con.execute("ALTER TABLE profile ADD COLUMN penalty_amount INTEGER NOT NULL DEFAULT 10")
    con.execute("""CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, subject TEXT,
        due TEXT NOT NULL, minutes INTEGER NOT NULL, difficulty TEXT NOT NULL,
        reward INTEGER NOT NULL, completed INTEGER NOT NULL DEFAULT 0,
        completed_at TEXT, penalty_applied INTEGER NOT NULL DEFAULT 0
    )""")
    quest_columns = {row[1] for row in con.execute("PRAGMA table_info(quests)").fetchall()}
    if "completion_id" not in quest_columns:
        con.execute("ALTER TABLE quests ADD COLUMN completion_id TEXT")
    if "penalty_applied" not in quest_columns:
        con.execute("ALTER TABLE quests ADD COLUMN penalty_applied INTEGER NOT NULL DEFAULT 0")
        # Existing overdue quests are grandfathered in when this feature is first added.
        con.execute("UPDATE quests SET penalty_applied=1 WHERE due < ? AND completed=0", (date.today().isoformat(),))
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_quest_completion_id ON quests(completion_id)")
    con.execute("""CREATE TABLE IF NOT EXISTS penalty_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, quest_id INTEGER, amount INTEGER NOT NULL,
        applied_on TEXT NOT NULL, note TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, subject TEXT,
        filename TEXT NOT NULL, stored_path TEXT NOT NULL, file_hash TEXT UNIQUE,
        added_at TEXT NOT NULL
    )""")
    con.execute("CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    # New local-first RPG tables. Existing data is never removed.
    con.execute("""CREATE TABLE IF NOT EXISTS xp_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, amount INTEGER NOT NULL, source TEXT NOT NULL,
        note TEXT NOT NULL, happened_at TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS focus_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, minutes INTEGER NOT NULL,
        mode TEXT NOT NULL, completed INTEGER NOT NULL DEFAULT 1, completion_id TEXT
    )""")
    focus_columns = {row[1] for row in con.execute("PRAGMA table_info(focus_sessions)").fetchall()}
    if "completion_id" not in focus_columns:
        con.execute("ALTER TABLE focus_sessions ADD COLUMN completion_id TEXT")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_focus_completion_id ON focus_sessions(completion_id)")
    con.execute("""CREATE TABLE IF NOT EXISTS revision_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT, front TEXT NOT NULL, back TEXT NOT NULL,
        interval_days INTEGER NOT NULL DEFAULT 1, ease REAL NOT NULL DEFAULT 2.5, repetitions INTEGER NOT NULL DEFAULT 0,
        due TEXT NOT NULL, last_reviewed TEXT, created_at TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS review_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, card_id INTEGER NOT NULL, rating TEXT NOT NULL,
        reviewed_at TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS dungeon_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT NOT NULL, difficulty TEXT NOT NULL,
        questions INTEGER NOT NULL, correct INTEGER NOT NULL, xp_earned INTEGER NOT NULL,
        perfect INTEGER NOT NULL DEFAULT 0, played_at TEXT NOT NULL, boss_rank TEXT
    )""")
    _dungeon_columns = {row[1] for row in con.execute("PRAGMA table_info(dungeon_runs)").fetchall()}
    if "boss_rank" not in _dungeon_columns:
        con.execute("ALTER TABLE dungeon_runs ADD COLUMN boss_rank TEXT")
    if "completion_id" not in _dungeon_columns:
        con.execute("ALTER TABLE dungeon_runs ADD COLUMN completion_id TEXT")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_dungeon_completion_id ON dungeon_runs(completion_id)")
    con.execute("""CREATE TABLE IF NOT EXISTS achievements (
        id TEXT PRIMARY KEY, unlocked_at TEXT NOT NULL
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS guild (
        id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL DEFAULT 'Awakened Scholars',
        motto TEXT NOT NULL DEFAULT 'Study together. Rise together.', code TEXT NOT NULL DEFAULT '',
        weekly_goal INTEGER NOT NULL DEFAULT 500, created_at TEXT NOT NULL
    )""")
    con.execute("INSERT OR IGNORE INTO guild(id, created_at) VALUES(1, ?)", (datetime.now().isoformat(timespec="seconds"),))
    con.execute("""CREATE TABLE IF NOT EXISTS guild_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'Hunter',
        weekly_xp INTEGER NOT NULL DEFAULT 0, focus_minutes INTEGER NOT NULL DEFAULT 0,
        last_checkin TEXT, added_at TEXT NOT NULL
    )""")

# Additive adaptive-learning tables: exams, syllabus topics and mastery events.
ensure_adaptive_tables(db)
ensure_hunter_tables(db)

RANKS = [(0,"E-RANK"),(150,"D-RANK"),(400,"C-RANK"),(800,"B-RANK"),(1400,"A-RANK"),(2200,"S-RANK"),(3500,"NATIONAL LEVEL")]

INDIAN_CALENDAR_2026 = [
    ("2026-01-14", "🪔 Makar Sankranti / Pongal", "festival", "India"),
    ("2026-01-23", "🪷 Basant Panchami / Saraswati Puja", "festival", "India · West Bengal"),
    ("2026-01-26", "🇮🇳 Republic Day", "holiday", "India"),
    ("2026-03-04", "🎨 Holi", "holiday", "India"),
    ("2026-03-21", "🌙 Eid-ul-Fitr", "holiday", "India"),
    ("2026-03-31", "☸️ Mahavir Jayanti", "holiday", "India"),
    ("2026-04-03", "✝️ Good Friday", "holiday", "India"),
    ("2026-05-01", "☸️ Buddha Purnima", "holiday", "India"),
    ("2026-05-27", "🌙 Eid-ul-Zuha / Bakrid", "holiday", "India"),
    ("2026-06-26", "🌙 Muharram", "holiday", "India"),
    ("2026-08-15", "🇮🇳 Independence Day", "holiday", "India"),
    ("2026-08-26", "🌙 Milad-un-Nabi / Eid-e-Milad", "holiday", "India"),
    ("2026-09-04", "🪷 Janmashtami", "festival", "India"),
    ("2026-09-14", "🐘 Ganesh Chaturthi", "festival", "India"),
    ("2026-10-02", "🕊️ Gandhi Jayanti", "holiday", "India"),
    ("2026-10-10", "🌺 Mahalaya", "festival", "West Bengal · Kolkata"),
    ("2026-10-11", "🌸 Sharad Navratri begins", "festival", "India"),
    ("2026-10-16", "🔱 Durga Puja · Maha Shashthi", "festival", "West Bengal · Kolkata"),
    ("2026-10-17", "🔱 Durga Puja · Maha Saptami", "festival", "West Bengal · Kolkata"),
    ("2026-10-18", "🔱 Durga Puja · Maha Saptami", "festival", "West Bengal · Kolkata"),
    ("2026-10-19", "🔱 Durga Puja · Maha Ashtami", "holiday", "West Bengal · Kolkata"),
    ("2026-10-20", "🔱 Durga Puja · Maha Navami / Vijayadashami", "holiday", "West Bengal · Kolkata"),
    ("2026-10-21", "🌊 Durga Visarjan / Bijoya period", "festival", "West Bengal · Kolkata"),
    ("2026-10-25", "🪷 Kojagari Lakshmi Puja", "festival", "West Bengal · Kolkata"),
    ("2026-11-08", "🪔 Diwali / Deepavali", "holiday", "India"),
    ("2026-11-24", "🪯 Guru Nanak Jayanti", "holiday", "India"),
    ("2026-12-25", "🎄 Christmas Day", "holiday", "India"),
]

INDIAN_CALENDAR_SOURCES = {
    "India Post · Holidays 2026": "https://www.indiapost.gov.in/holidays-list",
    "Kolkata government holiday list": "https://cgca.gov.in/ccako/list-of-holiday",
    "ISRO/IIRS holiday calendar": "https://www.iirs.gov.in/holidaycalender",
    "Indian festival calendar": "https://www.drikpanchang.com/calendars/indian/indiancalendar.html",
}

def indian_calendar_events(year):
    if year != 2026:
        return []
    return [{"date": date.fromisoformat(d), "title": title, "kind": kind, "region": region}
            for d, title, kind, region in INDIAN_CALENDAR_2026]

def rank_for(xp):
    rank = RANKS[0][1]
    for threshold, name in RANKS:
        if xp >= threshold: rank = name
    return rank

def level_for(xp):
    return xp // 100 + 1

def xp_progress(xp):
    return xp % 100

# Shadow soldiers unlock as the player levels up. The AI gives each one a
# distinct study-support personality; it does not control game rewards.
SHADOW_ARMY = [
    {"id":"igris", "name":"Igris", "title":"Blood-Red Commander", "emoji":"⚔️", "level":2, "dungeons":1,
     "ability":"Discipline Protocol", "description":"Turns a big goal into a strict, manageable study mission.",
     "persona":"You are Igris, a formal, disciplined shadow knight and study companion. Speak with calm, loyal, concise commander-like language. Help the player break work into clear steps and stay disciplined. Never claim to change app data or award XP."},
    {"id":"tank", "name":"Tank", "title":"Frost Bear", "emoji":"🐻", "level":3, "dungeons":2,
     "ability":"Memory Guard", "description":"Helps the player remember concepts using recall prompts and simple examples.",
     "persona":"You are Tank, a powerful but friendly shadow bear who supports the hunter's learning. Use simple explanations, memory tricks, and short recall questions. Be warm and encouraging. Never claim to change app data or award XP."},
    {"id":"iron", "name":"Iron", "title":"Armored Guardian", "emoji":"🛡️", "level":5, "dungeons":3,
     "ability":"Focus Shield", "description":"Helps remove distractions and build a short, focused work session.",
     "persona":"You are Iron, an energetic armored shadow soldier. Help the player focus, overcome procrastination, and choose one practical next action. Use a playful, confident tone without being rude. Never claim to change app data or award XP."},
    {"id":"tusk", "name":"Tusk", "title":"High Orc Shaman", "emoji":"🔮", "level":7, "dungeons":5,
     "ability":"Knowledge Spell", "description":"Creates practice questions and explains difficult topics in beginner-friendly language.",
     "persona":"You are Tusk, a wise shadow shaman and study companion. Help with concepts, create short practice questions, and explain things in beginner-friendly steps. If the player asks for factual help, be accurate and admit uncertainty. Never claim to change app data or award XP."},
    {"id":"beru", "name":"Beru", "title":"Ant King", "emoji":"👑", "level":10, "dungeons":8,
     "ability":"Royal Tutor", "description":"Acts as an enthusiastic personal tutor: quizzes, gives feedback, and celebrates progress.",
     "persona":"You are Beru, an intensely loyal, enthusiastic shadow soldier and personal study tutor. Address the player as your honored master occasionally, but keep it friendly and not excessive. Offer quizzes, check understanding, and celebrate effort. Be concise and accurate; do not invent facts. Never claim to change app data or award XP."},
]

# Official Solo Leveling Season 2 shadow promotional art. Images load from the
# anime website when the app has internet access. Keep local fallback avatars.
SHADOW_IMAGES = {
    "igris": "https://sololeveling-anime.net/assets/img/special/shadows-visual/igrit.jpg",
    "tank": "https://sololeveling-anime.net/assets/img/special/shadows-visual/tank.jpg",
    "iron": "https://sololeveling-anime.net/assets/img/special/shadows-visual/iron.jpg",
    "tusk": "https://sololeveling-anime.net/assets/img/special/shadows-visual/kiba.jpg",
    "beru": "https://sololeveling-anime.net/assets/img/special/shadows-visual/beru.jpg",
}

@st.cache_data(ttl=86400, show_spinner=False)
def load_shadow_image(url):
    """Fetch official character art safely; return None if offline/unavailable."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "StudyBuddy/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                return None
            return response.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return None

def dungeon_battle_count():
    with db() as con:
        return int(con.execute("SELECT COUNT(*) FROM dungeon_runs").fetchone()[0] or 0)

def shadow_unlock_state(xp, battles=None):
    """Unlocks require BOTH Hunter level and completed Dungeon battles."""
    if battles is None:
        battles = dungeon_battle_count()
    current_level = level_for(xp)
    rows = []
    for soldier in SHADOW_ARMY:
        needed_level = int(soldier["level"])
        needed_battles = int(soldier.get("dungeons", 1))
        rows.append((soldier, current_level >= needed_level and battles >= needed_battles, needed_level, needed_battles))
    return rows

def unlocked_shadows(xp, battles=None):
    return [soldier for soldier, unlocked, _, _ in shadow_unlock_state(xp, battles) if unlocked]

def get_profile():
    with db() as con: return dict(con.execute("SELECT * FROM profile WHERE id=1").fetchone())

def award_xp(reward, minutes, source="quest", note="Study reward", completion_id=None):
    """Award XP once, with skill multipliers and optional idempotency receipt."""
    reward = int(round(max(0, int(reward)) * xp_multiplier(db)))
    if reward <= 0:
        return 0
    today = date.today().isoformat()
    with db() as con:
        if completion_id:
            if con.execute("SELECT 1 FROM xp_log WHERE note LIKE ? LIMIT 1", (f"%[{completion_id}]%",)).fetchone():
                return 0
        p = con.execute("SELECT * FROM profile WHERE id=1").fetchone()
        streak = p["streak"]
        last = p["last_study"]
        if last != today:
            if last == (date.today() - timedelta(days=1)).isoformat():
                streak += 1
            else:
                streak = 1
        old_level = level_for(p["xp"])
        con.execute("""UPDATE profile SET xp=xp+?, focus=MIN(focus+1,99),
            discipline=MIN(discipline+1,99), knowledge=MIN(knowledge+?,99),
            energy=MIN(energy+1,99), streak=?, last_study=? WHERE id=1""",
            (reward, max(1, int(minutes) // 30), streak, today))
        tagged_note = f"{note} [{completion_id}]" if completion_id else note
        con.execute("INSERT INTO xp_log(amount,source,note,happened_at) VALUES(?,?,?,?)",
                    (reward, source, tagged_note, datetime.now().isoformat(timespec="seconds")))
        new_level = level_for(p["xp"] + reward)
    if new_level > old_level:
        st.session_state["level_up_event"] = {"old": old_level, "new": new_level}
    return reward

def complete_quest(qid):
    q = None
    completion_id = None
    with db() as con:
        q = con.execute("SELECT * FROM quests WHERE id=? AND completed=0", (qid,)).fetchone()
        if q:
            completion_id = q["completion_id"] or make_completion_id("quest_" + str(qid))
            con.execute("UPDATE quests SET completed=1, completed_at=?, completion_id=? WHERE id=? AND completed=0", (datetime.now().isoformat(timespec="seconds"), completion_id, qid))
    # Award XP only after the quest update transaction has committed.
    if q:
        award_xp(q["reward"], q["minutes"], completion_id=completion_id)
        grant_currency(db, coins=max(5, q["reward"] // 5))
        return q["reward"]
    return 0


def apply_overdue_penalties():
    """Apply one-time, configurable XP penalties to missed quests, with a daily cap."""
    today = date.today().isoformat()
    with db() as con:
        profile_row = con.execute("SELECT penalty_enabled, penalty_amount, xp FROM profile WHERE id=1").fetchone()
        if not profile_row or not profile_row["penalty_enabled"]:
            return 0, 0
        amount = max(0, min(50, int(profile_row["penalty_amount"])))
        if amount == 0:
            return 0, 0
        already_today = con.execute("SELECT COALESCE(SUM(amount),0) FROM penalty_log WHERE applied_on=?", (today,)).fetchone()[0]
        daily_remaining = max(0, 30 - int(already_today))
        if daily_remaining <= 0:
            return 0, 0
        missed = con.execute("SELECT id,title FROM quests WHERE completed=0 AND due < ? AND penalty_applied=0 ORDER BY due,id", (today,)).fetchall()
        total_lost = 0
        count = 0
        for quest in missed:
            requested_loss = min(amount, daily_remaining - total_lost)
            # Mark each missed quest exactly once. If today's cap is reached, no XP is lost for remaining items.
            con.execute("UPDATE quests SET penalty_applied=1 WHERE id=?", (quest["id"],))
            current_xp = con.execute("SELECT xp FROM profile WHERE id=1").fetchone()[0]
            actual_loss = min(requested_loss, current_xp)
            if actual_loss > 0:
                con.execute("UPDATE profile SET xp=xp-? WHERE id=1", (actual_loss,))
                note = "Missed quest: " + quest["title"]
                con.execute("INSERT INTO penalty_log(quest_id,amount,applied_on,note) VALUES(?,?,?,?)",
                            (quest["id"], actual_loss, today, note))
                con.execute("INSERT INTO xp_log(amount,source,note,happened_at) VALUES(?,?,?,?)",
                            (-actual_loss, "penalty", note, datetime.now().isoformat(timespec="seconds")))
                total_lost += actual_loss
                count += 1
        return count, total_lost

# Run missed-quest checks on app load. The feature can be disabled in Settings.
_penalty_count, _penalty_total = apply_overdue_penalties()
if _penalty_total:
    st.toast(f"System penalty: -{_penalty_total} XP for {_penalty_count} missed quest(s).", icon="⚠️")

# ---------- Hosted AI (Google Gemma via Gemini API) ----------
DEFAULT_GEMMA_MODEL = "gemma-4-26b-a4b-it"
FALLBACK_GEMMA_MODEL = "gemma-4-31b-it"
SUPPORTED_GEMMA_MODELS = [
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
]


def resolve_api_key():
    """Resolve the API key from secure sources only. Never commit or log the return value.

    Priority order:
    1. Streamlit Cloud st.secrets['GEMINI_API_KEY']
    2. Environment variable GEMINI_API_KEY
    3. User-provided session state (sidebar input, ephemeral for this run)
    """
    try:
        secrets_key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None
        if secrets_key and isinstance(secrets_key, str) and secrets_key.strip():
            return secrets_key.strip()
    except Exception:
        pass
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    if env_key:
        return env_key
    session_key = st.session_state.get("gemini_api_key", "").strip() if hasattr(st, "session_state") else ""
    if session_key:
        return session_key
    return ""


def has_api_key():
    return bool(resolve_api_key())


def get_configured_genai():
    """Return a current Google Gen AI client configured with the secure API key."""
    if not _GENAI_AVAILABLE:
        return None
    key = resolve_api_key()
    if not key:
        return None
    try:
        return genai.Client(api_key=key, http_options={"api_version": "v1"})
    except Exception:
        return None


def _extract_text_from_response(response):
    """Extract generated text from response.text or candidate content parts."""
    direct = (getattr(response, "text", "") or "").strip()
    if direct:
        return direct
    chunks = []
    try:
        for candidate in getattr(response, "candidates", []) or []:
            content = getattr(candidate, "content", None)
            for part in getattr(content, "parts", []) or []:
                value = getattr(part, "text", None)
                if value:
                    chunks.append(str(value))
    except Exception:
        pass
    return "\n".join(chunks).strip()


def _response_diagnostic(response):
    """Return a useful reason when the API returns no text."""
    try:
        feedback = getattr(response, "prompt_feedback", None)
        block_reason = getattr(feedback, "block_reason", None) if feedback else None
        if block_reason and str(block_reason).lower() not in ("none", "unspecified", "block_reason_unspecified"):
            return f"The request was blocked by Google AI ({block_reason})."
    except Exception:
        pass
    try:
        for candidate in getattr(response, "candidates", []) or []:
            reason = getattr(candidate, "finish_reason", None)
            message = getattr(candidate, "finish_message", None)
            if reason and str(reason).lower() not in ("stop", "none", "finishreason.unspecified"):
                return f"Google AI returned no text because the model stopped with {reason}" + (f": {message}" if message else ".")
    except Exception:
        pass
    return "Google AI returned no text content."


def validate_api_key(candidate_key):
    """Validate the API key and Gemma model access without requiring generated text."""
    if not candidate_key or not isinstance(candidate_key, str) or not candidate_key.strip():
        return False, "Please enter an API key first."
    if not _GENAI_AVAILABLE:
        return False, "The Google Gen AI SDK is not installed. Run `pip install -r requirements.txt` inside your venv."
    candidate = candidate_key.strip()
    try:
        client = genai.Client(api_key=candidate, http_options={"api_version": "v1"})
        # Verify the exact model exists for this key. This avoids falsely
        # reporting a valid key as invalid just because a tiny test response
        # has no text payload.
        info = client.models.get(model=DEFAULT_GEMMA_MODEL)
        actions = [str(x).lower() for x in (getattr(info, "supported_actions", None) or [])]
        if actions and not any("generatecontent" in x for x in actions):
            return False, f"{DEFAULT_GEMMA_MODEL} is reachable, but generateContent is not available for it."
        return True, "Gemma AI connected successfully."
    except Exception as exc:
        msg = str(exc).lower()
        if ("api key" in msg and ("invalid" in msg or "not valid" in msg)) or "permission" in msg or "401" in msg or "403" in msg:
            return False, "That API key does not look valid. Copy it again from Google AI Studio."
        if "quota" in msg or "rate limit" in msg or "429" in msg or "resource exhausted" in msg:
            return False, "You hit a rate or quota limit. Wait a moment, or check your quota in Google AI Studio."
        if "not found" in msg or "404" in msg or ("model" in msg and ("not available" in msg or "unknown" in msg)):
            return False, f"The configured Gemma model is not available to this API key ({DEFAULT_GEMMA_MODEL})."
        if "network" in msg or "connect" in msg or "timeout" in msg or "unreachable" in msg or "dns" in msg:
            return False, "Could not reach Google AI. Check your internet connection and try again."
        return False, f"Connection failed: {str(exc)[:200]}"

def get_available_models():
    """Return only currently supported hosted Gemma model IDs."""
    return list(SUPPORTED_GEMMA_MODELS)


def get_selected_model():
    """Read the user's hosted-Gemma model choice, safely migrating obsolete values."""
    env_override = os.getenv("STUDYBUDDY_MODEL", "").strip()
    if env_override in SUPPORTED_GEMMA_MODELS:
        return env_override

    with db() as con:
        row = con.execute("SELECT value FROM app_settings WHERE key='gemma_model'").fetchone()
        if row and row["value"] in SUPPORTED_GEMMA_MODELS:
            return row["value"]
        legacy = con.execute("SELECT value FROM app_settings WHERE key='ollama_model'").fetchone()
        if legacy and legacy["value"] in SUPPORTED_GEMMA_MODELS:
            return legacy["value"]
    return DEFAULT_GEMMA_MODEL


def save_selected_model(model_name):
    if model_name not in SUPPORTED_GEMMA_MODELS:
        model_name = DEFAULT_GEMMA_MODEL
    with db() as con:
        con.execute("INSERT INTO app_settings(key,value) VALUES('gemma_model',?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (model_name,))


def _friendly_ai_error(exc, model_name):
    msg = str(exc) if exc is not None else ""
    low = msg.lower()
    if not _GENAI_AVAILABLE:
        return RuntimeError("Google GenAI SDK not installed. Run `pip install -r requirements.txt` and restart the app.")
    if not has_api_key():
        return RuntimeError("StudyBuddy AI is not connected. Open the sidebar and paste your Google AI API key under Connect StudyBuddy AI.")
    if ("api key" in low and ("invalid" in low or "not valid" in low)) or "permissiondenied" in low or "401" in low or "403" in low:
        return RuntimeError("Your Google AI API key was rejected. Open the sidebar and reconnect with a valid key.")
    if "quota" in low or "rate limit" in low or "resourceexhausted" in low or "429" in low:
        return RuntimeError("Quota or rate limit reached. Wait a minute, reduce request frequency, or upgrade your quota in Google AI Studio.")
    if "not found" in low or "404" in low or ("model" in low and ("not available" in low or "unknown" in low)):
        return RuntimeError(f"Model '{model_name}' is not reachable right now. Pick a different model in the sidebar or try again later.")
    if "network" in low or "connect" in low or "timeout" in low or "unreachable" in low or "dns" in low:
        return RuntimeError("Could not reach Google AI right now. Check your internet connection and try again.")
    if "content" in low and ("filter" in low or "blocked" in low or "safety" in low or "finish_reason" in low):
        return RuntimeError("The request was declined by the AI safety filter. Rephrase your study prompt and try again.")
    if msg:
        return RuntimeError(f"AI request failed: {msg[:220]}")
    return RuntimeError(f"AI request failed while using '{model_name}'. Try again in a moment.")


def ask_ollama(prompt, system_prompt="You are the StudyBuddy System Assistant. Be concise, practical, encouraging, and focused on studying.", model_override=None):
    """Call hosted Google Gemma with a centralized quality generation profile."""
    model_name = model_override if model_override in SUPPORTED_GEMMA_MODELS else get_selected_model()
    if not _GENAI_AVAILABLE:
        raise RuntimeError("The Google Gen AI SDK is not installed. Run pip install -r requirements.txt inside your venv.")
    client = get_configured_genai()
    if client is None:
        if not has_api_key():
            raise RuntimeError("StudyBuddy AI is not connected. Open the sidebar and paste your Google AI API key under Connect StudyBuddy AI.")
        raise RuntimeError("Could not configure the Google Gen AI client. Check your API key and internet connection.")

    quality_prompt = """
You are operating inside StudyBuddy, an educational application.
Follow the supplied task exactly. Optimize for correctness, clarity, useful structure and exam relevance.
Use only facts supported by supplied source material when the task says it is source-grounded.
Never invent student telemetry, document facts, citations, scores or deadlines.
If information is missing or uncertain, state that clearly instead of guessing.
For calculations, show the essential reasoning and verify the result.
For generated questions, ensure there is exactly one defensible answer.
For study advice, prefer active recall, deliberate practice and spaced repetition over passive rereading.
Do not claim to have performed an app action unless the application explicitly performs it.
""" + "\n\n" + system_prompt.strip()

    try:
        response = retry_call(
            lambda: client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                system_instruction=quality_prompt,
                temperature=0.2,
                top_p=0.9,
                    max_output_tokens=2048,
                ),
            ),
            attempts=3,
            base_delay=0.5,
        )
        result = _extract_text_from_response(response)
        if not result:
            raise RuntimeError(_response_diagnostic(response))
        return result
    except RuntimeError:
        raise
    except Exception as exc:
        raise _friendly_ai_error(exc, model_name)


# Cinematic Solo Leveling shadow roster for Dungeon Battles.
# Artwork is loaded from the official Solo Leveling Season 2 shadow-visual page.
DUNGEON_BOSSES = {
    "igrit": {
        "name":"Igris", "element":"SHADOW", "color":"#ef4444",
        "description":"The Blood-Red Commander. Precision and consistency are your weapons.",
        "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/igrit.jpg",
        "attack":"Blood-Red Cleave", "bonus":20, "rank":"S-RANK"
    },
    "beru": {
        "name":"Beru", "element":"SHADOW", "color":"#a855f7",
        "description":"The Ant King. A relentless knowledge trial that rewards momentum.",
        "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/beru.jpg",
        "attack":"Royal Devour", "bonus":25, "rank":"S-RANK"
    },
    "tank": {
        "name":"Tank", "element":"FROST", "color":"#22d3ee",
        "description":"The Frost Bear. Defensive mastery meets careful recall.",
        "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/tank.jpg",
        "attack":"Glacial Guard", "bonus":18, "rank":"A-RANK"
    },
    "kiba": {
        "name":"Kiba", "element":"SHADOW", "color":"#f43f5e",
        "description":"The High Orc Shaman. A tactical trial for deeper subject mastery.",
        "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/kiba.jpg",
        "attack":"Mana Break", "bonus":22, "rank":"A-RANK"
    },
    "kaisel": {
        "name":"Kaisel", "element":"SHADOW", "color":"#06b6d4",
        "description":"The Winged Mount. A high-mobility challenge for fast recall.",
        "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/kaisel.jpg",
        "attack":"Sky Rend", "bonus":24, "rank":"S-RANK"
    },
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_shadow_image(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"StudyBuddy/1.0"})
        with urllib.request.urlopen(req, timeout=12) as response:
            raw = response.read()
        return raw if raw else None
    except Exception:
        return None

def local_video_data_uri():
    """Return the bundled Shadow Army video as a data URI when available locally."""
    candidates = [
        APP_DIR / "assets" / "shadow_army.mp4",
        APP_DIR / "assets" / "dungeon_hero.mp4",
    ]
    for path in candidates:
        try:
            if path.exists() and path.stat().st_size > 0:
                import base64
                raw = base64.b64encode(path.read_bytes()).decode("ascii")
                return "data:video/mp4;base64," + raw
        except Exception:
            pass
    return None

def boss_visual(boss_id):
    boss = DUNGEON_BOSSES.get(boss_id, DUNGEON_BOSSES["igrit"])
    return f"""
    <div class="dungeon-boss-overlay" style="--boss-glow:{boss['color']}">
      <div class="boss-scanline"></div>
      <div class="boss-overlay-top">
        <span>{boss['rank']} · {boss['element']} CLASS</span>
        <span>● LIVE INSTANCE</span>
      </div>
      <div class="boss-overlay-bottom">
        <b>{boss['name'].upper()}</b><span>DUNGEON BOSS</span>
      </div>
    </div>"""

# ---------- RPG systems ----------
ACHIEVEMENTS = [
    {"id":"first_quest","icon":"⚔️","name":"First Awakening","desc":"Clear your first study quest.","kind":"completed_quests","value":1},
    {"id":"ten_quests","icon":"📜","name":"Quest Breaker","desc":"Complete 10 study quests.","kind":"completed_quests","value":10},
    {"id":"fifty_quests","icon":"🔥","name":"Relentless Hunter","desc":"Complete 50 study quests.","kind":"completed_quests","value":50},
    {"id":"xp_100","icon":"✨","name":"Awakened","desc":"Reach 100 total XP.","kind":"xp","value":100},
    {"id":"xp_500","icon":"💠","name":"Power Surge","desc":"Reach 500 total XP.","kind":"xp","value":500},
    {"id":"streak_7","icon":"🌙","name":"Seven-Day Shadow","desc":"Maintain a 7-day study streak.","kind":"streak","value":7},
    {"id":"focus_60","icon":"⏱️","name":"Focus Initiate","desc":"Complete 60 focused study minutes.","kind":"focus_minutes","value":60},
    {"id":"focus_300","icon":"🧿","name":"Deep Focus","desc":"Complete 300 focused study minutes.","kind":"focus_minutes","value":300},
    {"id":"first_dungeon","icon":"🏰","name":"First Descent","desc":"Clear your first dungeon battle.","kind":"dungeon_runs","value":1},
    {"id":"dungeon_3","icon":"🏰","name":"Dungeon Runner","desc":"Complete 3 dungeon runs.","kind":"dungeon_runs","value":3},
    {"id":"perfect_dungeon","icon":"💀","name":"Perfect Clear","desc":"Finish a dungeon with every answer correct.","kind":"perfect_dungeon","value":1},
    {"id":"review_10","icon":"🧠","name":"Memory Awakening","desc":"Review 10 flashcards.","kind":"reviews","value":10},
    {"id":"s_rank","icon":"👑","name":"S-Rank Scholar","desc":"Reach S-Rank.","kind":"rank","value":"S-RANK"},
    {"id":"answers_100","icon":"🎯","name":"Hundred Strikes","desc":"Answer 100 dungeon questions correctly.","kind":"correct_answers","value":100},
    {"id":"perfect_quiz","icon":"💎","name":"Flawless Hunter","desc":"Complete a perfect quiz.","kind":"perfect_dungeon","value":1},
    {"id":"focus_10","icon":"🔥","name":"Training Streak","desc":"Complete 10 focus sessions.","kind":"focus_sessions","value":10},
    {"id":"s_rank_boss","icon":"💀","name":"S-Rank Breaker","desc":"Clear an S-Rank boss.","kind":"s_rank_boss","value":1},
]

DUNGEON_BANK = {
    "python":[
        {"q":"Which keyword is used to define a function in Python?","options":["func","def","function","lambda"],"answer":1,"explain":"Python uses the def keyword to define named functions."},
        {"q":"What is the result of len([10,20,30])?","options":["2","3","4","30"],"answer":1,"explain":"The list contains three elements, so len returns 3."},
        {"q":"Which data type stores an ordered, mutable collection?","options":["tuple","set","list","string"],"answer":2,"explain":"Lists are ordered and mutable collections in Python."},
        {"q":"Which operator is used for exponentiation in Python?","options":["^","**","//","%%"],"answer":1,"explain":"Python uses ** for exponentiation."},
        {"q":"What does a for loop commonly iterate over?","options":["An iterable","Only integers","Only strings","Only dictionaries"],"answer":0,"explain":"A for loop iterates over an iterable such as a list, string, tuple, or range."},
    ],
    "dbms":[
        {"q":"Which key uniquely identifies a row in a relation?","options":["Foreign key","Primary key","Candidate value","Index key"],"answer":1,"explain":"A primary key uniquely identifies each row."},
        {"q":"What does SQL stand for?","options":["Structured Query Language","Simple Query Logic","System Queue Language","Sequential Query Link"],"answer":0,"explain":"SQL stands for Structured Query Language."},
        {"q":"Which command retrieves rows from a table?","options":["GET","SELECT","FETCHTABLE","READ"],"answer":1,"explain":"SELECT is used to retrieve data."},
        {"q":"A foreign key mainly creates what kind of relationship?","options":["Referential link","UI link","Memory link","Thread link"],"answer":0,"explain":"A foreign key references a key in another table, enforcing referential integrity."},
        {"q":"Which normal form removes repeating groups?","options":["1NF","2NF","3NF","BCNF"],"answer":0,"explain":"First Normal Form removes repeating groups and requires atomic values."},
    ],
    "software engineering":[
        {"q":"What does SRS stand for?","options":["Software Requirements Specification","System Runtime Service","Software Resource System","Structured Requirement Syntax"],"answer":0,"explain":"SRS means Software Requirements Specification."},
        {"q":"PERT is mainly used for what?","options":["Risk-free coding","Project time estimation","Database indexing","UI design"],"answer":1,"explain":"PERT estimates activity/project duration using optimistic, most likely, and pessimistic times."},
        {"q":"Which model emphasizes repeated risk analysis?","options":["Waterfall","Spiral","V-Model","Big Bang"],"answer":1,"explain":"The Spiral model explicitly incorporates risk analysis in iterative cycles."},
        {"q":"What does UML stand for?","options":["Unified Modeling Language","Universal Machine Logic","User Modeling Layer","Unified Module Library"],"answer":0,"explain":"UML is Unified Modeling Language."},
        {"q":"COCOMO is associated with estimating what?","options":["Software effort/cost","Network bandwidth","Database size","Test coverage"],"answer":0,"explain":"COCOMO estimates software development effort, cost, and schedule."},
    ],
    "maths":[
        {"q":"What is the arithmetic mean of 2, 4 and 6?","options":["3","4","5","6"],"answer":1,"explain":"(2+4+6)/3 = 4."},
        {"q":"A probability must lie between which values?","options":["-1 and 1","0 and 1","1 and 100","-100 and 100"],"answer":1,"explain":"Probability ranges from 0 (impossible) to 1 (certain)."},
        {"q":"What is the square of 5?","options":["10","15","20","25"],"answer":3,"explain":"5 × 5 = 25."},
        {"q":"If a fair coin is tossed once, the probability of heads is?","options":["0","1/4","1/2","1"],"answer":2,"explain":"There are two equally likely outcomes, so P(heads)=1/2."},
        {"q":"The median is the value that lies where in ordered data?","options":["At the beginning","At the center","At the maximum","At the minimum"],"answer":1,"explain":"The median is the middle value after ordering the observations."},
    ],
}


def _now():
    return datetime.now().isoformat(timespec="seconds")


def current_week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())


def get_activity_metrics():
    week_start = current_week_start().isoformat()
    with db() as con:
        completed = con.execute("SELECT COUNT(*) FROM quests WHERE completed=1").fetchone()[0]
        focus_minutes = con.execute("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions WHERE completed=1").fetchone()[0]
        week_focus = con.execute("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions WHERE completed=1 AND substr(started_at,1,10)>=?", (week_start,)).fetchone()[0]
        dungeon_runs = con.execute("SELECT COUNT(*) FROM dungeon_runs").fetchone()[0]
        dungeon_wins = con.execute("SELECT COUNT(*) FROM dungeon_runs WHERE correct>0").fetchone()[0]
        perfects = con.execute("SELECT COUNT(*) FROM dungeon_runs WHERE perfect=1").fetchone()[0]
        correct_answers = con.execute("SELECT COALESCE(SUM(correct),0) FROM dungeon_runs").fetchone()[0]
        focus_sessions = con.execute("SELECT COUNT(*) FROM focus_sessions WHERE completed=1").fetchone()[0]
        s_rank_boss = con.execute("SELECT COUNT(*) FROM dungeon_runs WHERE boss_rank='S-RANK'").fetchone()[0]
        reviews = con.execute("SELECT COUNT(*) FROM review_log").fetchone()[0]
        due_cards = con.execute("SELECT COUNT(*) FROM revision_cards WHERE due<=?", (date.today().isoformat(),)).fetchone()[0]
    return {"completed_quests":completed,"focus_minutes":int(focus_minutes or 0),"week_focus":int(week_focus or 0),
            "dungeon_runs":dungeon_runs,"dungeon_wins":dungeon_wins,"perfect_dungeon":perfects,
            "correct_answers":int(correct_answers or 0),"focus_sessions":int(focus_sessions or 0),
            "s_rank_boss":int(s_rank_boss or 0),"reviews":reviews,"due_cards":due_cards}


def evaluate_achievements():
    profile_now = get_profile()
    metrics = get_activity_metrics()
    rank = rank_for(profile_now["xp"])
    values = {**metrics, "xp":profile_now["xp"], "streak":profile_now["streak"], "rank":rank}
    unlocked_now = []
    with db() as con:
        existing = {row[0] for row in con.execute("SELECT id FROM achievements").fetchall()}
        for ach in ACHIEVEMENTS:
            current = values.get(ach["kind"], 0)
            ok = (current == ach["value"] if ach["kind"] == "rank" else current >= ach["value"])
            if ok and ach["id"] not in existing:
                con.execute("INSERT INTO achievements(id,unlocked_at) VALUES(?,?)", (ach["id"], _now()))
                unlocked_now.append(ach)
    return unlocked_now


def maybe_award_daily_bonus():
    today = date.today().isoformat()
    with db() as con:
        key = "daily_bonus_" + today
        if con.execute("SELECT 1 FROM app_settings WHERE key=?", (key,)).fetchone():
            return False
        row = con.execute("SELECT COUNT(*) AS total, COALESCE(SUM(completed),0) AS done FROM quests WHERE due=?", (today,)).fetchone()
        if row["total"] == 0 or row["done"] != row["total"]:
            return False
        con.execute("INSERT INTO app_settings(key,value) VALUES(?,?)", (key, "1"))
    award_xp(25, 15, source="daily_bonus", note="Daily quest board cleared")
    st.session_state["daily_bonus_event"] = True
    return True


def log_focus_session(minutes, mode, completion_id=None):
    minutes = max(1, int(minutes))
    completion_id = completion_id or ("focus_" + hashlib.sha256(f"{mode}|{minutes}|{_now()}".encode()).hexdigest()[:24])
    with db() as con:
        try:
            con.execute(
                "INSERT INTO focus_sessions(started_at,minutes,mode,completed,completion_id) VALUES(?,?,?,1,?)",
                (_now(), minutes, mode, completion_id),
            )
        except sqlite3.IntegrityError:
            return 0
    reward = max(5, min(40, round((minutes // 5 * 2) * focus_multiplier(db()))))
    award_xp(reward, minutes, source="focus", note=f"Completed {minutes}-minute focus session", completion_id=completion_id)
    evaluate_achievements()
    return reward


def create_card(subject, front, back):
    with db() as con:
        con.execute("INSERT INTO revision_cards(subject,front,back,due,created_at) VALUES(?,?,?,?,?)",
                    (subject.strip() or "General", front.strip(), back.strip(), date.today().isoformat(), _now()))


def review_card(card_id, rating):
    with db() as con:
        card = con.execute("SELECT * FROM revision_cards WHERE id=?", (card_id,)).fetchone()
        if not card:
            return
        ease = float(card["ease"])
        reps = int(card["repetitions"])
        interval = int(card["interval_days"])
        if rating == "Again":
            reps = 0
            interval = 1
            ease = max(1.3, ease - 0.20)
        elif rating == "Hard":
            reps += 1
            interval = max(1, round(interval * 1.2))
            ease = max(1.3, ease - 0.10)
        elif rating == "Good":
            reps += 1
            interval = 1 if reps == 1 else (3 if reps == 2 else max(1, round(interval * ease)))
        else:  # Easy
            reps += 1
            interval = 4 if reps == 1 else max(2, round(interval * ease * 1.3))
            ease = min(3.2, ease + 0.10)
        interval = max(1, round(interval * revision_interval_multiplier(db()))) if rating in ("Good", "Easy") else interval
        due = (date.today() + timedelta(days=interval)).isoformat()
        con.execute("""UPDATE revision_cards SET interval_days=?,ease=?,repetitions=?,due=?,last_reviewed=? WHERE id=?""",
                    (interval,ease,reps,due,_now(),card_id))
        con.execute("INSERT INTO review_log(card_id,rating,reviewed_at) VALUES(?,?,?)", (card_id,rating,_now()))


def _parse_json_array(text):
    if not text:
        return None
    raw = text.strip()
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else None
    except Exception:
        start = raw.find("[")
        end = raw.rfind("]")
        if start >= 0 and end > start:
            try:
                data = json.loads(raw[start:end+1])
                return data if isinstance(data, list) else None
            except Exception:
                return None
    return None


def generate_quiz_questions(subject, count, difficulty):
    prompt = (f"Create exactly {count} multiple-choice questions for a study game about {subject}. "
              f"Difficulty: {difficulty}. Return ONLY a JSON array, no markdown. Each object must contain "
              'q, options (exactly 4 strings), answer (0-3 integer), explain (short string). ' 
              "Questions must be factually correct and suitable for a college student.")
    try:
        raw = ask_ollama(prompt, "You create reliable educational multiple-choice questions. Follow the requested JSON schema exactly. Never include markdown fences.")
        data = _parse_json_array(raw)
        clean = []
        if data:
            for item in data:
                if not isinstance(item, dict):
                    continue
                opts = item.get("options")
                ans = item.get("answer")
                q = str(item.get("q", "")).strip()
                exp = str(item.get("explain", "")).strip()
                if q and isinstance(opts, list) and len(opts) == 4 and isinstance(ans, int) and 0 <= ans < 4:
                    clean.append({"q":q,"options":[str(x) for x in opts],"answer":ans,"explain":exp or "Review the concept and try again."})
        if len(clean) >= max(3, count-1):
            return clean[:count], "AI"
    except Exception:
        pass
    key = subject.strip().lower()
    bank = None
    for name, items in DUNGEON_BANK.items():
        if name in key or key in name:
            bank = items
            break
    if bank is None:
        bank = [
            {"q":f"Which study action best improves recall for {subject}?","options":["Passive rereading only","Active self-testing","Avoiding practice","Studying everything at once"],"answer":1,"explain":"Active recall is generally more effective than passive rereading for strengthening retrieval."},
            {"q":f"What is a useful first step when learning {subject}?","options":["Define the core concepts","Skip fundamentals","Memorize without context","Study only the hardest topic"],"answer":0,"explain":"A clear foundation makes later material easier to connect and review."},
            {"q":f"Which approach is best when you get a question wrong in {subject}?","options":["Ignore it","Review the explanation and retry later","Quit the topic","Memorize the option letter"],"answer":1,"explain":"Reviewing the reason for the error and retrying supports durable learning."},
            {"q":f"Which method helps spread practice for {subject} across time?","options":["Spaced repetition","Cramming once","Skipping review","Only watching videos"],"answer":0,"explain":"Spaced repetition revisits information at increasing intervals."},
            {"q":f"What should a good study session for {subject} usually include?","options":["One clear objective","Many unrelated tabs","No breaks ever","Only passive reading"],"answer":0,"explain":"A focused objective makes the session easier to complete and measure."},
        ]
    rng = random.Random(subject.lower() + date.today().isoformat())
    bank = bank[:]
    rng.shuffle(bank)
    return bank[:min(count, len(bank))], "Practice Bank"


def save_dungeon_run(subject, difficulty, questions, correct, xp, perfect, boss_rank="", completion_id=None):
    completion_id = completion_id or make_completion_id("dungeon")
    try:
        with db() as con:
            con.execute("INSERT INTO dungeon_runs(subject,difficulty,questions,correct,xp_earned,perfect,played_at,boss_rank,completion_id) VALUES(?,?,?,?,?,?,?,?,?)",
                        (subject,difficulty,questions,correct,xp,int(perfect),_now(),boss_rank,completion_id))
    except sqlite3.IntegrityError:
        # A reconnect/retry can replay the same dungeon completion; do not duplicate it.
        return False
    evaluate_achievements()
    return True


def render_shadow_unlock_ceremony():
    """Display the cinematic Shadow Army unlock animation after a dungeon victory."""
    event = st.session_state.get("shadow_unlock_event")
    if not event:
        return

    shadow = event.get("shadow")
    if not shadow:
        st.session_state.pop("shadow_unlock_event", None)
        return

    shadow_name = shadow.get("name", "Unknown Shadow")
    shadow_title = shadow.get("title", "Shadow Soldier")
    shadow_emoji = shadow.get("emoji", "👤")
    shadow_ability = shadow.get("ability", "Unknown ability")

    st.markdown(
        f"""
        <div class="sb-unlock">
            <div class="sb-scan-line"></div>
            <div style="padding:42px 30px;text-align:center;position:relative;overflow:hidden;">
                <div class="sb-pulse-ring" style="width:180px;height:180px;position:absolute;left:50%;top:35px;transform:translateX(-50%);pointer-events:none;"></div>
                <div class="sb-unlock-seal" style="width:110px;height:110px;margin:0 auto 22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:58px;background:radial-gradient(circle,rgba(103,232,249,.18),rgba(8,13,28,.9));border:1px solid rgba(103,232,249,.35);box-shadow:0 0 35px rgba(103,232,249,.18),inset 0 0 25px rgba(167,139,250,.10);">
                    {shadow_emoji}
                </div>
                <div style="font-size:13px;letter-spacing:4px;color:#67e8f9;font-weight:800;margin-bottom:10px;">SHADOW EXTRACTION COMPLETE</div>
                <div style="font-size:38px;font-weight:900;letter-spacing:1px;margin-bottom:5px;">{shadow_name}</div>
                <div style="font-size:16px;color:#a78bfa;font-weight:700;margin-bottom:20px;">{shadow_title}</div>
                <div style="display:inline-block;padding:9px 18px;border-radius:999px;border:1px solid rgba(103,232,249,.25);background:rgba(103,232,249,.06);color:#dffcff;font-weight:700;margin-bottom:16px;">⚔️ SHADOW AWAKENED</div>
                <div style="max-width:520px;margin:0 auto;padding:14px 18px;border-radius:14px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.07);">
                    <div style="color:#67e8f9;font-size:12px;letter-spacing:2px;font-weight:800;margin-bottom:5px;">ABILITY</div>
                    <div style="font-size:17px;font-weight:700;">{shadow_ability}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div data-sb-motion="shadow-unlock"></div>', unsafe_allow_html=True)

    if st.button("⚔️ Continue", key="shadow_unlock_continue"):
        st.session_state.pop("shadow_unlock_event", None)
        st.rerun()


def finish_dungeon():
    run = st.session_state.get("dungeon_run")
    if not run or run.get("finished"):
        return 0
    before_profile = get_profile()
    before_battles = dungeon_battle_count()
    before_ids = {s["id"] for s in unlocked_shadows(before_profile["xp"], before_battles)}
    correct = run["correct"]
    total = len(run["questions"])
    perfect = correct == total
    base = 10 + correct * 10
    difficulty_bonus = {"Easy":0,"Normal":5,"Hard":12,"Nightmare":20}.get(run["difficulty"], 0)
    perfect_bonus = 20 if perfect else 0
    boss_bonus = DUNGEON_BOSSES.get(run.get("boss_id", "igrit"), DUNGEON_BOSSES["igrit"])["bonus"]
    xp = base + difficulty_bonus + perfect_bonus + boss_bonus
    completion_id = run.get("completion_id") or make_completion_id("dungeon")
    run["completion_id"] = completion_id
    awarded = award_xp(xp, max(15, total * 5), source="dungeon", note="Boss defeated", completion_id=completion_id)
    save_dungeon_run(run["subject"], run["difficulty"], total, correct, awarded or xp, perfect, DUNGEON_BOSSES.get(run.get("boss_id", "igrit"), DUNGEON_BOSSES["igrit"])["rank"], completion_id=completion_id)
    grant_currency(db, coins=25 + correct * 5, gems=1 if perfect else 0)
    run["finished"] = True
    run["xp_earned"] = awarded or xp
    run["perfect"] = perfect
    st.session_state["dungeon_run"] = run
    after_profile = get_profile()
    after_battles = dungeon_battle_count()
    after_ids = {s["id"] for s in unlocked_shadows(after_profile["xp"], after_battles)}
    newly_unlocked = [s for s in SHADOW_ARMY if s["id"] in (after_ids - before_ids)]
    if newly_unlocked:
        st.session_state["shadow_unlock_event"] = [
            {"name": s["name"], "title": s["title"], "emoji": s["emoji"], "level": s["level"], "dungeons": s.get("dungeons", 1)}
            for s in newly_unlocked
        ]
    return xp


def guild_data():
    with db() as con:
        guild = dict(con.execute("SELECT * FROM guild WHERE id=1").fetchone())
        if not guild.get("code"):
            code = create_guild_code(guild["name"])
            con.execute("UPDATE guild SET code=? WHERE id=1", (code,))
            guild["code"] = code
        members = [dict(r) for r in con.execute("SELECT * FROM guild_members ORDER BY weekly_xp DESC, name").fetchall()]
    return guild, members


def guild_weekly_xp():
    week_start = current_week_start().isoformat()
    with db() as con:
        row = con.execute("SELECT COALESCE(SUM(amount),0) FROM xp_log WHERE amount>0 AND substr(happened_at,1,10)>=?", (week_start,)).fetchone()
    return int(row[0] or 0)


def create_guild_code(name):
    return "SB-" + hashlib.sha1((name + _now()).encode()).hexdigest()[:6].upper()


# ---------- Sidebar / navigation ----------
shadow_access = dungeon_battle_count() >= 1 and level_for(get_profile()["xp"]) >= 2
pages = [
    "🏠 Hunter Dashboard",
    "📅 Quest Schedule",
    "⚔️ Dungeon Battles",
    "🗺️ Dungeon Map",
    "🎙️ Voice Study Mode",
    "⏱️ Focus Room",
    "🧠 Revision Lab",
    "✨ Gemma Study Lab",
    "🏆 Achievements",
    "📊 Hunter Report",
    "🎯 Study Intelligence",
    "📈 Progress Calendar",
    "🌳 Skill Tree",
    "🎓 Exam Command Center",
    "🤖 AI System Assistant",
    "👥 Shadow Army" if shadow_access else "🔒 Shadow Army",
    "👑 Anime RPG",
    "🤝 Guild Hall",
    "📚 Important PDFs",
    "🧬 Character & Power",
    "⚙️ Settings",
]
with st.sidebar:
    st.markdown(
        "<div class='sidebar-brand'>"
        "<div class='sidebar-brand-name'>⚔️ STUDY<span>BUDDY</span></div>"
        "<div class='sidebar-brand-sub'>Level Up Protocol</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='sidebar-section-label'>Navigation</div>", unsafe_allow_html=True)
    _nav_target = st.session_state.get("nav_page", pages[0])
    if _nav_target not in pages:
        _nav_target = pages[0]
    page = st.radio("Navigation", pages, index=pages.index(_nav_target), label_visibility="collapsed")
    st.session_state["nav_page"] = page
    render_offline_indicator()
    render_offline_console()
    render_offline_journal()
    st.divider()

    st.markdown("<div class='sidebar-section-label'>Gemma AI · Google Cloud</div>", unsafe_allow_html=True)

    _key_from_secrets = False
    try:
        if hasattr(st, "secrets"):
            _sk = st.secrets.get("GEMINI_API_KEY")
            if _sk and isinstance(_sk, str) and _sk.strip():
                _key_from_secrets = True
    except Exception:
        pass
    _key_from_env = bool(os.getenv("GEMINI_API_KEY", "").strip())
    _key_from_session = bool(st.session_state.get("gemini_api_key", "").strip())

    if has_api_key():
        _status_icon = "✓"
        _status_class = "ai-status connected"
        _status_text = "Gemma AI: Connected"
        if _key_from_secrets:
            _src = "Streamlit secrets"
        elif _key_from_env:
            _src = "Env / .env"
        else:
            _src = "Session key"
    else:
        _status_icon = "✕"
        _status_class = "ai-status disconnected"
        _status_text = "Gemma AI: Not connected"
        _src = "Setup needed"

    st.markdown(
        f"<div class='{_status_class}'>"
        f"<span class='status-dot' style='margin-right:6px'></span>"
        f"<b>{_status_icon}</b> &nbsp; <span>{_status_text}</span>"
        f"</div>"
        f"<div class='muted' style='font-size:0.7rem;margin-top:4px;margin-bottom:10px;padding-left:2px'>via {_src}</div>",
        unsafe_allow_html=True,
    )

    if not _key_from_secrets and not _key_from_env:
        with st.expander("🔗 Connect StudyBuddy AI", expanded=not has_api_key()):
            st.markdown(
                "<div style='padding:4px 2px 10px 2px'>"
                "<div style='font-weight:600;color:#e6eefb;margin-bottom:6px'>Connect StudyBuddy AI</div>"
                "<div class='muted' style='font-size:0.75rem;line-height:1.45'>StudyBuddy uses Google Gemma through the Gemini API — no local install or downloads needed. Get a free key from Google AI Studio, then paste it below.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.link_button("🔑 Get Google AI API Key", "https://aistudio.google.com/app/apikey", use_container_width=True)
            with st.form("gemma_key_form", clear_on_submit=False):
                candidate = st.text_input(
                    "Google AI API Key",
                    type="password",
                    placeholder="Paste your key here…",
                    help="Never share or commit your API key. This stays in your browser session only.",
                    label_visibility="collapsed",
                )
                connect = st.form_submit_button("Connect AI", type="primary", use_container_width=True)
            if connect:
                if not candidate.strip():
                    st.error("Please paste an API key first.")
                else:
                    with st.spinner("Validating your key…"):
                        ok, msg = validate_api_key(candidate)
                    if ok:
                        st.session_state["gemini_api_key"] = candidate.strip()
                        st.session_state["gemma_key_validated_at"] = _now()
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            if _key_from_session:
                st.caption("Using the session key you connected. It will be cleared when you close this tab.")
                if st.button("Disconnect session key", key="gemma_disconnect", use_container_width=True):
                    st.session_state.pop("gemini_api_key", None)
                    st.session_state.pop("gemma_key_validated_at", None)
                    st.rerun()
            elif not has_api_key():
                st.caption("Tip: for Streamlit Cloud deployments, add GEMINI_API_KEY in ☰ → Settings → Secrets.")
    else:
        st.caption("Key is already loaded from " + _src + ". Use the selector below to change models.")

    st.divider()

    st.markdown("<div class='sidebar-section-label'>AI Model</div>", unsafe_allow_html=True)
    available = get_available_models()
    saved_model = get_selected_model()
    if saved_model not in available:
        available = [saved_model] + available
    default_index = available.index(saved_model) if saved_model in available else 0
    selected_model = st.selectbox(
        "Hosted Gemma model",
        available,
        index=default_index,
        key="gemma_model_picker",
        help="Choose which hosted Gemma variant sends your study requests.",
        label_visibility="collapsed",
    )
    if selected_model != saved_model:
        save_selected_model(selected_model)
    st.caption(f"Active · {selected_model}")
    st.divider()

    st.markdown("<div class='sidebar-section-label'>Hunter</div>", unsafe_allow_html=True)
    profile = get_profile()
    st.markdown(
        f"<div class='sidebar-hunter'><span class='status-dot'></span><b>{profile['name']}</b> "
        f"<span class='muted' style='font-size:0.75rem'> ONLINE</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<span class='rank'>{rank_for(profile['xp'])}</span>", unsafe_allow_html=True)
    st.caption(f"Level {level_for(profile['xp'])} · {profile['xp']} XP")
    st.progress(xp_progress(profile['xp']) / 100)

# Reset the main viewport when switching tabs so every module opens from its true top.
_previous_page = st.session_state.get("_previous_page")
if _previous_page != page:
    components.html(
        """
        <script>
        (function () {
          const goTop = () => {
            try {
              window.parent.scrollTo({top: 0, left: 0, behavior: "instant"});
              window.top.scrollTo({top: 0, left: 0, behavior: "instant"});
            } catch (e) {}
          };
          goTop();
          setTimeout(goTop, 40);
          setTimeout(goTop, 180);
        })();
        </script>
        """,
        height=0,
        scrolling=False,
    )
    st.session_state["_previous_page"] = page

profile = get_profile()
try:
    maybe_award_daily_bonus()
except Exception:
    pass
new_achievements = evaluate_achievements()
if new_achievements:
    st.session_state["achievement_event"] = new_achievements
profile = get_profile()
rank = rank_for(profile["xp"])
level = level_for(profile["xp"])
sync_hunter_level(db, level, _now())

# One-shot progression ceremony: appears immediately after the Dungeon victory rerun.
render_shadow_unlock_ceremony()

# ---------- Dashboard ----------
if page == "🏠 Hunter Dashboard":
    render_workflow(0)
    render_next_action("⚡", "Adaptive Hunter Route", "Your dashboard now connects planning, training, testing, review and progression.", "SYSTEM FLOW")

    metrics = get_activity_metrics()
    with db() as con:
        today_q = con.execute("SELECT COUNT(*) FROM quests WHERE due=? AND completed=0", (date.today().isoformat(),)).fetchone()[0]
        today_done = con.execute("SELECT COUNT(*) FROM quests WHERE due=? AND completed=1", (date.today().isoformat(),)).fetchone()[0]
        today_focus = con.execute("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions WHERE completed=1 AND substr(started_at,1,10)=?", (date.today().isoformat(),)).fetchone()[0]
        ach_count = con.execute("SELECT COUNT(*) FROM achievements").fetchone()[0]
    hunter_wallet = wallet(db)
    power = profile["xp"] + profile["focus"]*10 + profile["discipline"]*10 + profile["knowledge"]*10 + profile["energy"]*5

    st.markdown(
        f"""<div class='video-command-hero'>
          <video autoplay muted loop playsinline preload='auto'>
            <source src='{HERO_VIDEO_URL}' type='video/mp4'>
          </video>
          <div class='video-scanline'></div>
          <div class='video-glass'>
            <div class='video-kicker'>SYSTEM ONLINE · CINEMATIC HUNTER COMMAND CENTER</div>
            <div class='video-title'>Welcome back, {profile['name']}.</div>
            <div class='video-copy'>Your study world is now presented as an interactive anime system: missions, dungeon combat, focus training, memory, Gemma intelligence and hunter progression in one command layer.</div>
            <div class='video-hud-row'>
              <div class='video-hud-chip'>RANK · {rank}</div>
              <div class='video-hud-chip'>LEVEL · {level}</div>
              <div class='video-hud-chip'>XP · {profile['xp']:,}</div>
              <div class='video-hud-chip'>POWER · {power:,}</div>
              <div class='video-hud-chip'>STREAK · {profile['streak']}</div>
              <div class='video-hud-chip'>COINS · {hunter_wallet['coins']}</div>
              <div class='video-hud-chip'>GEMS · {hunter_wallet['gems']}</div>
            </div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class='motion-grid'>
          <div class='motion-tile'><div class='motion-tile-icon'>⚡</div><div class='motion-tile-title'>IMPACT FEEDBACK</div><div class='motion-tile-copy'>XP, streak and completion actions use sharp motion cues.</div></div>
          <div class='motion-tile'><div class='motion-tile-icon'>◈</div><div class='motion-tile-title'>DEPTH LAYERS</div><div class='motion-tile-copy'>Glass panels, depth, glow and parallax separate UI from video.</div></div>
          <div class='motion-tile'><div class='motion-tile-icon'>◉</div><div class='motion-tile-title'>SYSTEM FLOW</div><div class='motion-tile-copy'>Every module shares the same cinematic HUD language.</div></div>
        </div>""",
        unsafe_allow_html=True,
    )

    if st.session_state.get("level_up_event"):
        ev = st.session_state.pop("level_up_event")
        st.markdown(f"<div class='level-up-banner'><div class='level-up-kicker'>✦ LEVEL UP DETECTED ✦</div><div class='level-up-title'>Level {ev['old']} → Level {ev['new']}</div><div class='muted'>Your training has made you stronger.</div></div>", unsafe_allow_html=True)
    if st.session_state.get("daily_bonus_event"):
        st.session_state.pop("daily_bonus_event")
        st.markdown("<div class='reward-banner'>◈ DAILY BOARD CLEARED · +25 BONUS XP</div>", unsafe_allow_html=True)
    if st.session_state.get("achievement_event"):
        unlocked_events = st.session_state.pop("achievement_event")
        names = " · ".join(a["icon"] + " " + a["name"] for a in unlocked_events)
        st.markdown(f"<div class='reward-banner'>🏆 ACHIEVEMENT UNLOCKED · {names}</div>", unsafe_allow_html=True)

    render_module_hud(page)

    commands = [
        ("⚔️","Dungeon Battles","Fight a knowledge boss.","⚔️ Dungeon Battles"),
        ("📅","Quest Schedule","Deploy today's missions.","📅 Quest Schedule"),
        ("⏱️","Focus Room","Start deep work.","⏱️ Focus Room"),
        ("🧠","Revision Lab","Train recall.","🧠 Revision Lab"),
        ("✨","Gemma Study Lab","Generate study content.","✨ Gemma Study Lab"),
        ("🤖","AI Assistant","Ask the system.","🤖 AI System Assistant"),
        ("👥","Shadow Army","Manage companions.","👥 Shadow Army"),
        ("👑","Anime RPG","Open RPG progression.","👑 Anime RPG"),
        ("🏆","Achievements","Track milestones.","🏆 Achievements"),
        ("📊","Hunter Report","Analyze performance.","📊 Hunter Report"),
        ("🌳","Skill Tree","Unlock study abilities.","🌳 Skill Tree"),
        ("🤝","Guild Hall","Manage your study party.","🤝 Guild Hall"),
        ("🧬","Character & Power","Upgrade your hunter.","🧬 Character & Power"),
    ]
    st.markdown("### ◈ Intelligence Brief")
    _due_now = metrics["due_cards"]
    _next = "Clear due revision cards" if _due_now else ("Run a 25-minute focus session" if today_focus < 25 else "Deploy your next quest")
    st.markdown(f"<div class='system-next'><span class='muted'>ADAPTIVE NEXT ACTION</span><b>{_next}</b><div class='muted'>Study Intelligence combines your real activity, memory queue and mission completion to choose the next useful action.</div></div>", unsafe_allow_html=True)
    if st.button("🎯 Open Study Intelligence", use_container_width=True):
        st.session_state["nav_page"]="🎯 Study Intelligence"
        st.rerun()

    d1, d2 = st.columns([2, 1])
    with d1:
        if st.button("⚔️ CONTINUE DUNGEON", type="primary", use_container_width=True):
            st.session_state["nav_page"] = "⚔️ Dungeon Battles"
            st.rerun()
    with d2:
        with db() as _sp_con:
            _sp_row = _sp_con.execute("SELECT COALESCE(max_level_seen,1)-COALESCE(skill_points_spent,0) AS available FROM hunter_progress WHERE id=1").fetchone()
        _available_sp = int(_sp_row["available"] if _sp_row else max(0, level-1))
    st.markdown(f"<div class='system-next'><span class='muted'>SKILL POINTS</span><b>{max(0,_available_sp)}</b><div class='muted'>Open Skill Tree</div></div>", unsafe_allow_html=True)

    st.markdown("### ◈ Weekly XP")
    with db() as con:
        _week_start = current_week_start().isoformat()
        _xp_days = []
        for _i in range(7):
            _day = current_week_start() + timedelta(days=_i)
            _val = con.execute("SELECT COALESCE(SUM(amount),0) FROM xp_log WHERE amount>0 AND substr(happened_at,1,10)=?", (_day.isoformat(),)).fetchone()[0]
            _xp_days.append(( _day.strftime("%a"), int(_val or 0) ))
    _max_xp = max([v for _,v in _xp_days] + [1])
    _bars = "".join(f"<div style='flex:1;text-align:center'><div style='height:90px;display:flex;align-items:flex-end;justify-content:center'><div style='width:70%;height:{max(6,int(v/_max_xp*100))}%;border-radius:7px 7px 2px 2px;background:linear-gradient(180deg,#67e8f9,#7c3aed);box-shadow:0 0 14px rgba(103,232,249,.12)'></div></div><div class='muted'>{d}</div><div style='font-size:.65rem;color:#67e8f9'>{v} XP</div></div>" for d,v in _xp_days)
    st.markdown(f"<div class='panel'><div class='panel-title'>WEEKLY XP OUTPUT</div><div style='display:flex;gap:10px;align-items:flex-end'>{_bars}</div></div>", unsafe_allow_html=True)

    st.markdown("### ◈ Command Deck")
    for row in range(0, len(commands), 4):
        cols = st.columns(4, gap="medium")
        for col, item in zip(cols, commands[row:row+4]):
            icon, title, desc, target = item
            with col:
                st.markdown(f"<div class='hud-card'><div class='hud-icon'>{icon}</div><div class='hud-label'>{title}</div><div class='hud-desc'>{desc}</div></div>", unsafe_allow_html=True)
                if st.button(f"OPEN · {title}", key=f"dash_nav_{row}_{title}", use_container_width=True):
                    st.session_state["nav_page"] = target
                    st.rerun()

    st.markdown("### ◈ Hunter Core")
    core_cols = st.columns(4)
    core_data = [
        ("XP PROGRESS", f"{xp_progress(profile['xp'])}%", f"Level {level} → next"),
        ("TODAY'S QUESTS", f"{today_done}/{today_done+today_q}", f"{today_q} remaining"),
        ("FOCUS TIME", f"{int(today_focus)}m", "Completed today"),
        ("READY REVISION", str(metrics["due_cards"]), "Cards due now"),
    ]
    for col, item in zip(core_cols, core_data):
        label, value, sub = item
        with col:
            st.markdown(f"<div class='stat'><div class='stat-label'>{label}</div><div class='stat-value'>{value}</div><div class='muted'>{sub}</div></div>", unsafe_allow_html=True)

    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown("<div class='panel'><div class='panel-title'>⚡ EXPERIENCE CORE</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex;justify-content:space-between'><b>LEVEL {level}</b><span class='muted'>{xp_progress(profile['xp'])}/100 XP</span></div><div class='xp-track'><div class='xp-fill' style='width:{xp_progress(profile['xp'])}%'></div></div><div class='muted'>Rank progression · {rank}</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'><div class='panel-title'>📜 ACTIVE MISSIONS</div>", unsafe_allow_html=True)
        with db() as con:
            rows = con.execute("SELECT * FROM quests WHERE due=? ORDER BY completed, id", (date.today().isoformat(),)).fetchall()
        if not rows:
            st.info("No quests scheduled for today. Open Quest Schedule to deploy missions.")
        for q in rows:
            st.markdown(f"<div class='quest {'quest-done' if q['completed'] else ''}'><b>{'✓ ' if q['completed'] else '◈ '}{q['title']}</b><div class='muted'>{q['subject'] or 'General'} · {q['minutes']} min · {q['difficulty']} · +{q['reward']} XP</div></div>", unsafe_allow_html=True)
            if not q["completed"] and st.button(f"COMPLETE · +{q['reward']} XP", key=f"dash_done_{q['id']}", use_container_width=False):
                complete_quest(q["id"])
                st.success(f"Quest cleared! +{q['reward']} XP")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='panel'><div class='panel-title'>🧬 HUNTER STATUS</div>", unsafe_allow_html=True)
        char_icons = {"Shadow Hunter":"🗡️","Mage":"🔮","Knight":"🛡️","Archer":"🏹"}
        st.markdown(f"<div style='font-family:Rajdhani;font-size:1.55rem;font-weight:700'>{char_icons.get(profile['character'],'⚔️')} {profile['character']}</div><div class='muted'>Power {power:,} · {profile['title']}</div>", unsafe_allow_html=True)
        for label, key in [("Focus","focus"),("Discipline","discipline"),("Knowledge","knowledge"),("Energy","energy")]:
            val = profile[key]
            st.markdown(f"<div style='display:flex;justify-content:space-between;margin-top:10px'><span class='muted'>{label}</span><b>{val}</b></div><div class='xp-track' style='height:7px'><div class='xp-fill' style='width:{min(val,99)}%'></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        next_action = "Start a 25-minute Focus session" if today_focus == 0 else ("Review your ready flashcards" if metrics["due_cards"] else "Enter a Dungeon and test your mastery")
        st.markdown(f"<div class='system-next'><span class='muted'>NEXT RECOMMENDED ACTION</span><b>{next_action}</b></div>", unsafe_allow_html=True)
        st.markdown("<div class='panel'><div class='panel-title'>🧭 SYSTEM TIP</div><div class='muted'>Use the Command Deck as your control center. Every real study action contributes to hunter progression.</div></div>", unsafe_allow_html=True)
        if profile.get("penalty_enabled",1):
            st.warning(f"Penalty protocol active: overdue quests can cost {profile.get('penalty_amount',10)} XP each.")
        else:
            st.info("Penalty protocol is disabled.")

# ---------- AI System Assistant ----------

# ---------- Study Intelligence ----------
elif page == "📈 Progress Calendar":
    render_module_hud(page)
    render_progress_calendar(db, profile)

# ---------- Study Intelligence ----------
elif page == "🎯 Study Intelligence":
    render_module_hud(page)
    render_ai_intelligence(st, db, profile, ask_ollama, has_api_key, get_selected_model())


elif page == "🌳 Skill Tree":
    render_module_hud(page)
    render_skill_tree(db, profile, _now())

elif page == "🎓 Exam Command Center":
    render_module_hud(page)
    render_exam_center(st, db, profile, ask_ollama, has_api_key)

elif page == "🤖 AI System Assistant":
    render_module_hud(page)
    model_name = get_selected_model()
    _ai_connected = has_api_key()
    st.markdown(
        f"""<div class='hero'>
          <div class='hero-kicker'>System Intelligence · Hosted Gemma</div>
          <div class='hero-title'>AI System Assistant</div>
          <p class='hero-sub'>Your AI mentor suggests study quests, builds plans, and coaches progress. XP is earned by completing scheduled missions.</p>
          <div class='hero-meta'>
            <span class='system-chip'>Model · {model_name}</span>
            <span class='system-chip purple'>{"✓ Gemma Connected" if _ai_connected else "Connect AI in sidebar"}</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    st.caption("Change the active model anytime from the sidebar · Inference runs through Google Gemma on Google Cloud")
    render_system_guide(db, ask_ollama if _ai_connected else None)

    plan_tab, mentor_tab = st.tabs(["⚡ Generate Today's Quests", "🗡️ Ask the Shadow Mentor"])

    with plan_tab:
        with st.form("ai_quest_form"):
            a, b = st.columns([1.4, 1])
            with a:
                subjects = st.text_input("Subjects / topics", placeholder="e.g. Python, DBMS, Software Engineering")
            with b:
                available_time = st.selectbox(
                    "Available study time", [30, 60, 90, 120, 180, 240], index=2, format_func=lambda x: f"{x} minutes"
                )
            priority = st.text_input(
                "Priority or exam target (optional)",
                placeholder="e.g. Practice Python loops for tomorrow's lab",
            )
            make_plan = st.form_submit_button("✨ Generate study quests", type="primary")
        if make_plan:
            if not subjects.strip():
                st.warning("Enter at least one subject or topic.")
            else:
                prompt = (
                    "Create a realistic study plan for today. Subjects/topics: "
                    + subjects.strip()
                    + ". Total available time: "
                    + str(available_time)
                    + " minutes. Priority: "
                    + (priority.strip() or "not specified")
                    + ". Give 3 to 5 short quests that fit within the time limit. For each, use this exact format: "
                    "Quest: [clear task] | Subject: [subject] | Duration: [minutes] | Difficulty: [Easy/Normal/Hard/Boss]. "
                    "Keep durations realistic and total duration within the limit. Then add one short system-style tip. Do not summarize documents."
                )
                with st.spinner("Generating quests with Gemma AI…"):
                    try:
                        st.session_state["ai_plan_result"] = ask_ollama(prompt)
                    except RuntimeError as exc:
                        st.error(str(exc))
        if st.session_state.get("ai_plan_result"):
            st.markdown("#### 📜 Generated mission plan")
            st.markdown(st.session_state["ai_plan_result"])
            st.info("Create these missions in Quest Schedule to track progress and earn XP · AI suggestions do not change progress automatically.")

    with mentor_tab:
        if "mentor_messages" not in st.session_state:
            st.session_state["mentor_messages"] = []

        if not st.session_state["mentor_messages"]:
            st.markdown(
                "<div class='chat-empty'>"
                "<div class='chat-empty-icon'>🗡️</div>"
                "<div class='chat-empty-title'>Ask the Shadow Mentor</div>"
                "<div class='muted'>Get study advice, revision strategies, or help choosing your next mission.</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.caption("Try one of these:")
            suggestions = [
                "What should I study first today?",
                "Give me a 3-step revision routine",
                "How do I stay focused for 90 minutes?",
                "Review my pending quests and rank them",
            ]
            cols = st.columns(2)
            for i, s in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(s, key=f"mentor_sug_{i}", use_container_width=True):
                        st.session_state["mentor_suggestion"] = s

        for item in st.session_state["mentor_messages"]:
            with st.chat_message(item["role"]):
                st.markdown(item["content"])

        with st.form("mentor_chat_form", clear_on_submit=True):
            default_q = st.session_state.pop("mentor_suggestion", "") if "mentor_suggestion" in st.session_state else ""
            user_question = st.text_input(
                "Message the Shadow Mentor",
                value=default_q,
                placeholder="What should I study first today?",
            )
            send = st.form_submit_button("Send message", type="primary")
        if send:
            if not user_question.strip():
                st.warning("Type a message first.")
            else:
                with db() as con:
                    pending = con.execute(
                        "SELECT title,subject,due,minutes,difficulty FROM quests WHERE completed=0 ORDER BY due,id LIMIT 8"
                    ).fetchall()
                task_context = (
                    "; ".join(
                        [
                            f"{q['title']} ({q['subject'] or 'General'}, due {q['due']}, {q['minutes']} min, {q['difficulty']})"
                            for q in pending
                        ]
                    )
                    or "No pending quests"
                )
                context = (
                    f"Hunter level: {level}; rank: {rank}; total XP: {profile['xp']}; streak: {profile['streak']}. "
                    f"Pending quests: {task_context}. User asks: {user_question.strip()}"
                )
                st.session_state["mentor_messages"].append({"role": "user", "content": user_question.strip()})
                with st.spinner("Shadow Mentor is thinking…"):
                    try:
                        reply = ask_ollama(
                            context,
                            "You are a concise, supportive study mentor called the Shadow Mentor. Give practical study advice based on the provided progress and tasks. Use a subtle RPG system tone, but do not claim to control the app, change XP, or access PDFs. Keep answers focused and reasonably short.",
                        )
                        st.session_state["mentor_messages"].append({"role": "assistant", "content": reply})
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(str(exc))
                        st.session_state["mentor_messages"].pop()
        if st.session_state["mentor_messages"]:
            if st.button("Clear conversation"):
                st.session_state["mentor_messages"] = []
                st.rerun()


# ---------- Gemma Study Lab ----------
elif page == "✨ Gemma Study Lab":
    render_module_hud(page)
    _ai_ready = has_api_key()
    st.markdown(
        f"""<div class='hero'>
          <div class='hero-kicker'>Open-Weight Model Lab · Gemma</div>
          <div class='hero-title'>Gemma Study Lab</div>
          <p class='hero-sub'>Run learning tasks with Google's hosted Gemma models and optionally compare output and timing side-by-side with a second Gemma variant.</p>
          <div class='hero-meta'>
            <span class='system-chip'>Gemma · Hosted via Google Cloud</span>
            <span class='system-chip purple'>{"✓ AI Connected" if _ai_ready else "Connect AI in sidebar"}</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    all_models = get_available_models()
    gemma_models = [m for m in all_models]
    if not gemma_models:
        gemma_models = list(SUPPORTED_GEMMA_MODELS)
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("<div class='system-panel'><div class='panel-title'>◈ Gemma runtime</div><div class='muted'>Runs through Google's hosted Gemma API. No local downloads or Ollama required.</div></div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("<div class='system-panel'><div class='panel-title'>◈ Evaluation mode</div><div class='muted'>Optional side-by-side timing comparison against a second hosted Gemma variant.</div></div>", unsafe_allow_html=True)
    if not _ai_ready:
        st.warning("Gemma Study Lab is open, but StudyBuddy AI is not connected yet.")
        st.markdown("**To enable the Gemma Study Lab:**")
        steps = [
            "Open the sidebar and find **Gemma AI · Google Cloud**.",
            "Click **🔑 Get Google AI API Key** to open aistudio.google.com/app/apikey.",
            "Create a key, paste it into **Connect StudyBuddy AI**, then click **Connect AI**.",
            "Once connected, return here to run study tasks."
        ]
        for i, s in enumerate(steps, 1):
            st.markdown(f"{i}. {s}")
    else:
        default_gemma = DEFAULT_GEMMA_MODEL
        if default_gemma not in gemma_models:
            gemma_models = [default_gemma] + gemma_models
        gemma_model = st.selectbox("Primary Gemma model", gemma_models,
                                   index=(gemma_models.index(default_gemma) if default_gemma in gemma_models else 0),
                                   key="gemma_lab_model")
        baseline_candidates = [m for m in gemma_models if m != gemma_model]
        baseline = st.selectbox("Comparison model (optional)", ["None"] + baseline_candidates,
                                index=(baseline_candidates.index(FALLBACK_GEMMA_MODEL) + 1 if FALLBACK_GEMMA_MODEL in baseline_candidates else 0),
                                key="gemma_baseline")
        task = st.selectbox("Study task", ["Generate a quiz", "Explain a concept", "Create a revision plan", "Make flashcards"], key="gemma_task")
        subject = st.text_input("Subject or topic", placeholder="e.g. Spearman rank correlation", key="gemma_subject")
        notes = st.text_area("Your notes or context (optional)", placeholder="Paste a short excerpt or describe what you are learning...", height=130, key="gemma_notes")
        level = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Exam-ready"], index=1, key="gemma_difficulty")
        count = st.slider("Question/card count", 3, 10, 5, key="gemma_count")
        compare = st.checkbox("Compare response time with second model", value=(baseline != "None"), key="gemma_compare")
        if st.button("✦ Run Gemma Study Task", type="primary", use_container_width=True, key="run_gemma_task"):
            if not subject.strip():
                st.warning("Enter a subject or topic first.")
            else:
                task_instructions = {
                    "Generate a quiz": f"Create {count} multiple-choice questions at {level} level. Give four options per question, clearly mark the correct answer, and explain why it is correct.",
                    "Explain a concept": f"Teach this topic at {level} level. Start with a simple explanation, then give one worked example and three key takeaways.",
                    "Create a revision plan": f"Create a practical revision plan for this topic at {level} level. Break it into short sessions, include active recall and spaced review, and finish with a self-checklist.",
                    "Make flashcards": f"Create {count} concise question-and-answer flashcards at {level} level. Format as numbered Front / Back pairs.",
                }
                prompt = (f"Study topic: {subject.strip()}\nContext/notes: {notes.strip()[:6000] or 'No notes provided.'}\n\n"
                          + task_instructions[task]
                          + "\nBe accurate. If the supplied notes do not contain enough information, say what is missing rather than inventing details.")
                sys_prompt = "You are Gemma acting as a precise, supportive study tutor inside StudyBuddy. Use clear structure and avoid unnecessary filler."
                with st.spinner(f"{gemma_model} is working on your study task..."):
                    try:
                        t0 = time.perf_counter()
                        gemma_result = ask_ollama(prompt, sys_prompt, model_override=gemma_model)
                        gemma_seconds = time.perf_counter() - t0
                        st.session_state["gemma_lab_result"] = {"text": gemma_result, "model": gemma_model, "seconds": gemma_seconds, "task": task, "subject": subject.strip()}
                        if compare and baseline != "None":
                            t1 = time.perf_counter()
                            baseline_result = ask_ollama(prompt, sys_prompt, model_override=baseline)
                            baseline_seconds = time.perf_counter() - t1
                            st.session_state["gemma_lab_comparison"] = {"text": baseline_result, "model": baseline, "seconds": baseline_seconds}
                        else:
                            st.session_state.pop("gemma_lab_comparison", None)
                    except RuntimeError as exc:
                        st.error(str(exc))
        result = st.session_state.get("gemma_lab_result")
        if result:
            st.divider()
            st.markdown("### ✦ Study output")
            m1, m2, m3 = st.columns(3)
            m1.metric("Model", result["model"])
            m2.metric("Task", result["task"])
            m3.metric("Response time", f"{result['seconds']:.1f}s")
            st.markdown(result["text"])
            comparison = st.session_state.get("gemma_lab_comparison")
            if comparison:
                st.markdown("### ⚖️ Model comparison")
                left, right = st.columns(2)
                with left:
                    st.markdown(f"**Primary · {result['seconds']:.1f}s**")
                    st.write(result["text"])
                with right:
                    st.markdown(f"**{comparison['model']} · {comparison['seconds']:.1f}s**")
                    st.write(comparison["text"])
                st.caption("Timing is a single hosted run, not a controlled benchmark. Compare answer quality manually; speed alone does not measure learning accuracy.")


# ---------- Shadow Army ----------
elif page in ("👥 Shadow Army", "🔒 Shadow Army"):
    render_module_hud(page)
    if not shadow_access:
        st.markdown("""<div class='sb-unlock' style='animation:sbUnlockIn .55s both'>
          <div class='sb-unlock-seal'>🔒</div>
          <div class='sb-unlock-kicker'>SYSTEM LOCK · DUNGEON GATE</div>
          <div class='sb-unlock-title'>SHADOW ARMY LOCKED</div>
          <div class='sb-unlock-sub'>Complete 1 Dungeon battle and reach Level 2 to awaken your first shadow.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("⚔️ Enter Dungeon Battles", type="primary", use_container_width=True):
            st.session_state["nav_page"]="⚔️ Dungeon Battles"
            st.rerun()
    else:
        available = unlocked_shadows(profile["xp"])

        st.markdown(
            f"""<div class='hero'>
              <div class='hero-kicker'>Shadow Extraction · Companion System</div>
              <div class='hero-title'>Shadow Army</div>
              <p class='hero-sub'>Unlock loyal study companions as you level up. Each soldier has a distinct AI personality and helps you train.</p>
              <div class='hero-meta'>
                <span class='system-chip'>{len(available)}/{len(SHADOW_ARMY)} Awakened</span>
                <span class='system-chip purple'>Level {level}</span>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
        battles = dungeon_battle_count()
        st.markdown(f"**Army strength · {len(available)}/{len(SHADOW_ARMY)} shadows awakened** · **{battles} dungeon clears**")
        st.progress(len(available) / len(SHADOW_ARMY))
        st.markdown("<div class='system-panel'><div class='panel-title'>◈ SHADOW AWAKENING PROTOCOL</div><div class='muted'>Every companion requires a Hunter level AND completed Dungeon clears. Clear battles to awaken the next shadow.</div></div>", unsafe_allow_html=True)
        cols = st.columns(2)
        for idx, soldier in enumerate(SHADOW_ARMY):
            unlocked = soldier in available
            with cols[idx % 2]:
                opacity = "1" if unlocked else ".48"
                status = "🟢 AWAKENED" if unlocked else f"🔒 LV {soldier['level']} + {soldier.get('dungeons',1)} DUNGEON CLEARS"
                # Only reveal character art after the soldier is unlocked.
                art = load_shadow_image(SHADOW_IMAGES[soldier["id"]]) if unlocked and soldier["id"] in SHADOW_IMAGES else None
                if art:
                    st.image(art, use_container_width=True)
                else:
                    st.markdown(
                        "<div style='height:170px;display:flex;align-items:center;justify-content:center;"
                        "border:1px solid rgba(132,177,235,.2);border-radius:16px;"
                        "background:radial-gradient(circle,rgba(71,95,150,.35),rgba(8,13,28,.8));"
                        "font-size:56px;text-shadow:0 0 24px #67e8f966'>"
                        + (soldier["emoji"] if unlocked else "🔒") + "</div>",
                        unsafe_allow_html=True,
                    )
                description = soldier["description"] if unlocked else (
                    f"Clear {soldier.get('dungeons', 1)} Dungeon battle(s) and reach "
                    f"Level {soldier['level']} to awaken this shadow."
                )
                display_name = soldier["name"] if unlocked else "???"
                display_title = soldier["title"] if unlocked else "Unknown shadow"
                display_ability = soldier["ability"] if unlocked else "Hidden ability"
                st.markdown(
                    f"<div class='panel' style='min-height:175px;opacity:{opacity}'>"
                    f"<div class='panel-title' style='margin:0'>{display_name}</div>"
                    f"<div class='muted'>{display_title}</div>"
                    f"<div style='margin-top:12px;color:#67e8f9;font-weight:700'>{status}</div>"
                    f"<div style='margin-top:7px'><b>{display_ability}</b></div>"
                    f"<div class='muted' style='margin-top:5px'>{description}</div></div>",
                    unsafe_allow_html=True,
                )
        st.divider()
        if not available:
            st.info("Clear your first Dungeon battle and reach Level 2 to awaken Igris.")
        else:
            reaction_pool = [
                ("Igris", "⚔️ Igris stands ready. One clear objective. No excuses. "),
                ("Tank", "🐻 Tank remembers your progress. A little study today is still progress."),
                ("Iron", "🛡️ Iron has raised the Focus Shield. Close the distractions and begin."),
                ("Tusk", "🔮 Tusk senses knowledge waiting to be mastered. Bring him one difficult topic."),
                ("Beru", "👑 Beru is delighted by your effort, my master. Now let us make that effort count!")
            ]
            favored = reaction_pool[min(level-1, len(reaction_pool)-1)]
            st.markdown(f"<div class='shadow-reaction'><span>{favored[0]}</span><b>{favored[1]}</b></div>", unsafe_allow_html=True)
            st.subheader("💬 Speak with your shadow")
            selected_name = st.selectbox("Choose an awakened soldier", [x["name"] for x in available])
            soldier = next(x for x in available if x["name"] == selected_name)
            st.caption(f"{soldier['emoji']} {soldier['ability']} — {soldier['description']}")
            art = load_shadow_image(SHADOW_IMAGES[soldier["id"]]) if soldier["id"] in SHADOW_IMAGES else None
            if art:
                st.image(art, width=260)
            chat_key = f"shadow_chat_{soldier['id']}"
            if chat_key not in st.session_state:
                st.session_state[chat_key] = []
            for item in st.session_state[chat_key]:
                with st.chat_message(item["role"]):
                    st.markdown(item["content"])
            with st.form(f"shadow_chat_form_{soldier['id']}", clear_on_submit=True):
                message = st.text_input("Message your shadow", placeholder=f"Ask {soldier['name']} for study help...")
                send_shadow = st.form_submit_button("Send message", type="primary")
            if send_shadow:
                if not message.strip():
                    st.warning("Type a message first.")
                else:
                    with db() as con:
                        pending = con.execute("SELECT title,subject,due,minutes,difficulty FROM quests WHERE completed=0 ORDER BY due,id LIMIT 6").fetchall()
                    pending_text = "; ".join([f"{q['title']} ({q['subject'] or 'General'}, due {q['due']}, {q['minutes']} min, {q['difficulty']})" for q in pending]) or "No pending quests"
                    player_context = (f"Player level: {level}; rank: {rank}; XP: {profile['xp']}; streak: {profile['streak']}. "
                                      f"Pending quests: {pending_text}. Player's message: {message.strip()}")
                    st.session_state[chat_key].append({"role":"user", "content":message.strip()})
                    with st.spinner(f"{soldier['name']} is responding..."):
                        try:
                            reply = ask_ollama(player_context, soldier["persona"] + " Use the player's progress and pending quests when relevant. Keep replies short and useful.")
                            st.session_state[chat_key].append({"role":"assistant", "content":reply})
                            st.rerun()
                        except RuntimeError as exc:
                            st.error(str(exc))
                            st.session_state[chat_key].pop()
            if st.button(f"Clear {soldier['name']} conversation", key=f"clear_shadow_{soldier['id']}"):
                st.session_state[chat_key] = []
                st.rerun()
            st.caption("Shadow conversations use your hosted Gemma model. Chatting does not award XP; complete scheduled quests to earn rewards.")

# ---------- Schedule ----------
elif page == "📅 Quest Schedule":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>Mission Control</div>
          <div class='hero-title'>Quest Calendar</div>
          <p class='hero-sub'>Plan your study missions, track workload, and clear quests to level up.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Month calendar controls
    today = date.today()
    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = today.replace(day=1)
    if "calendar_selected_day" not in st.session_state:
        st.session_state.calendar_selected_day = today
    month_value = st.session_state.calendar_month
    nav_l, month_col, nav_r = st.columns([1, 4, 1])
    with nav_l:
        if st.button("← Previous", key="calendar_prev", use_container_width=True):
            y, m = month_value.year, month_value.month - 1
            if m == 0: y, m = y - 1, 12
            st.session_state.calendar_month = date(y, m, 1)
            st.rerun()
    with month_col:
        st.markdown(f"<h3 style='text-align:center;margin:5px 0 15px'>{calendar.month_name[month_value.month]} {month_value.year}</h3>", unsafe_allow_html=True)
    with nav_r:
        if st.button("Next →", key="calendar_next", use_container_width=True):
            y, m = month_value.year, month_value.month + 1
            if m == 13: y, m = y + 1, 1
            st.session_state.calendar_month = date(y, m, 1)
            st.rerun()

    with db() as con:
        month_quests = con.execute("SELECT * FROM quests WHERE due >= ? AND due <= ? ORDER BY due,id", (date(month_value.year, month_value.month, 1).isoformat(), date(month_value.year, month_value.month, calendar.monthrange(month_value.year, month_value.month)[1]).isoformat())).fetchall()
        all_quests = con.execute("SELECT * FROM quests ORDER BY due,id").fetchall()
    indian_events = indian_calendar_events(month_value.year)
    indian_by_day = {}
    for event in indian_events:
        indian_by_day.setdefault(event["date"].day, []).append(event)

    by_day = {}
    for quest in month_quests:
        by_day.setdefault(date.fromisoformat(quest["due"]).day, []).append(quest)

    st.markdown("<div class='panel' style='padding:12px 18px;margin:8px 0 14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px'><span style='color:#eaf5ff;font-weight:700'>◈ MISSION TIMELINE</span><span class='muted'>🔵 quests · 🪔 Indian festival · 🇮🇳 holiday · 🌺 West Bengal/Kolkata</span></div>", unsafe_allow_html=True)
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    head = st.columns(7)
    for col, label in zip(head, weekdays):
        col.markdown(f"<div style='text-align:center;color:#8fc8e8;font-weight:700'>{label}</div>", unsafe_allow_html=True)
    weeks = calendar.monthcalendar(month_value.year, month_value.month)
    for week_index, week in enumerate(weeks):
        cells = st.columns(7)
        for col, day_num in zip(cells, week):
            with col:
                if day_num == 0:
                    st.markdown("<div style='height:62px'></div>", unsafe_allow_html=True)
                else:
                    day_date = date(month_value.year, month_value.month, day_num)
                    quests_that_day = by_day.get(day_num, [])
                    done_count = sum(1 for item in quests_that_day if item["completed"])
                    open_count = len(quests_that_day) - done_count
                    selected = st.session_state.calendar_selected_day == day_date
                    event_count = len(indian_by_day.get(day_num, []))
                    marker = (f"● {open_count} active" if open_count else "No quests")
                    if done_count:
                        marker += f"\n✓ {done_count} cleared"
                    if event_count:
                        marker += f"\n🪔 {event_count} event{'s' if event_count != 1 else ''}"
                    label = f"{day_num:02d}\n{marker}"
                    if st.button(label, key=f"cal_{month_value.year}_{month_value.month}_{day_num}", use_container_width=True, type="primary" if selected else "secondary"):
                        st.session_state.calendar_selected_day = day_date
                        st.rerun()
    selected_day = st.session_state.calendar_selected_day
    if selected_day.year != month_value.year or selected_day.month != month_value.month:
        selected_day = date(month_value.year, month_value.month, 1)
        st.session_state.calendar_selected_day = selected_day
    selected_quests = [q for q in all_quests if q["due"] == selected_day.isoformat()]
    selected_events = [e for e in indian_events if e["date"] == selected_day]
    done_today = sum(1 for q in selected_quests if q["completed"])
    pending_today = len(selected_quests) - done_today
    planned_minutes = sum(q["minutes"] for q in selected_quests if not q["completed"])
    st.markdown(f"<div class='hero' style='padding:18px 22px;margin-top:18px'><div class='hero-kicker'>SELECTED DAY · MISSION AGENDA</div><div style='font-family:Orbitron,Rajdhani,sans-serif;font-size:22px;font-weight:700;color:#fff;margin-top:6px'>{selected_day.strftime('%A, %d %B %Y')}</div><div class='hero-sub' style='margin-top:5px'>Your daily plan, progress, and rewards in one place.</div></div>", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Missions", len(selected_quests))
    m2.metric("Completed", done_today)
    m3.metric("Planned time left", f"{planned_minutes} min")
    if selected_events:
        st.markdown("<div class='panel' style='padding:16px 18px;margin:10px 0;border-color:rgba(251,191,36,.25);background:linear-gradient(135deg,rgba(251,191,36,.06),rgba(167,139,250,.05))'><div style='color:#fbbf24;font-weight:800;letter-spacing:1px;font-size:.72rem'>🇮🇳 INDIAN EVENT AGENDA</div></div>", unsafe_allow_html=True)
        for event in selected_events:
            badge = "HOLIDAY" if event["kind"] == "holiday" else "FESTIVAL"
            st.markdown(f"<div class='quest' style='border-color:rgba(251,191,36,.22);'><div class='quest-title'>{event['title']}</div><div class='muted'>{badge} · {event['region']} · {event['date'].strftime('%A, %d %B %Y')}</div></div>", unsafe_allow_html=True)

    if selected_quests:
        for q in selected_quests:
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"**{'✓' if q['completed'] else '◈'} {q['title']}**")
                    st.caption(f"{q['subject'] or 'General'} · {q['minutes']} min · {q['difficulty']} · +{q['reward']} XP")
                with right:
                    if q["completed"]:
                        st.success("Cleared")
                    elif st.button("Complete", key=f"cal_complete_{q['id']}", use_container_width=True):
                        earned = complete_quest(q["id"])
                        st.toast(f"Quest cleared: +{earned} XP", icon="⚡")
                        st.rerun()
    else:
        st.info("No missions scheduled for this date. Add a quest below to fill this day.")

    with st.expander("＋ Create a new quest", expanded=True):
        with st.form("new_quest", clear_on_submit=True):
            a,b = st.columns(2)
            title = a.text_input("Quest name", placeholder="e.g. Revise Python loops")
            subject = b.text_input("Subject", placeholder="e.g. Python")
            c,d,e = st.columns(3)
            due = c.date_input("Scheduled date", value=selected_day)
            minutes = d.selectbox("Duration", [15,30,45,60,90,120], index=2, format_func=lambda x:f"{x} minutes")
            difficulty = e.selectbox("Difficulty", ["Easy","Normal","Hard","Boss"])
            base = {"Easy":15,"Normal":30,"Hard":50,"Boss":80}[difficulty]
            reward = base + max(0,(minutes-30)//15*5)
            st.caption(f"Reward preview: +{reward} XP")
            submitted = st.form_submit_button("Add quest to calendar", type="primary")
            if submitted:
                if not title.strip(): st.error("Enter a quest name first.")
                else:
                    with db() as con:
                        con.execute("INSERT INTO quests(title,subject,due,minutes,difficulty,reward) VALUES(?,?,?,?,?,?)", (title.strip(),subject.strip(),due.isoformat(),minutes,difficulty,reward))
                    st.success("Quest added to your calendar."); st.rerun()

    st.divider()
    with st.expander("🇮🇳 Indian calendar sources & accuracy", expanded=False):
        st.caption("Government holidays and festival observances are labeled separately. Festival dates can vary by region, tradition, moon sighting, or local authority.")
        for source_name, source_url in INDIAN_CALENDAR_SOURCES.items():
            st.markdown(f"- [{source_name}]({source_url})")
        st.caption("West Bengal/Kolkata observances are highlighted separately, especially Durga Puja and related events.")

    st.subheader("Mission list")
    mode = st.selectbox("Show quests", ["Upcoming", "All", "Completed"], index=0)
    with db() as con:
        if mode == "Completed": rows=con.execute("SELECT * FROM quests WHERE completed=1 ORDER BY due DESC,id DESC").fetchall()
        elif mode == "Upcoming": rows=con.execute("SELECT * FROM quests WHERE completed=0 ORDER BY due,id").fetchall()
        else: rows=con.execute("SELECT * FROM quests ORDER BY due DESC,id DESC").fetchall()
    if not rows: st.info("Nothing here yet. Create a quest above.")
    for q in rows:
        with st.container(border=True):
            l,r=st.columns([4,1])
            with l:
                st.markdown(f"**{'✓ ' if q['completed'] else '◈ '}{q['title']}**")
                due_date = date.fromisoformat(q['due'])
                overdue = (not q['completed']) and due_date < date.today()
                status_text = " · ⚠️ OVERDUE" if overdue else (" · Penalty applied" if q['penalty_applied'] else "")
                st.caption(f"{q['subject'] or 'General'} · {due_date.strftime('%d %b %Y')} · {q['minutes']} min · {q['difficulty']} · Reward: {q['reward']} XP{status_text}")
            with r:
                if q["completed"]: st.success("Cleared")
                elif st.button("Clear quest", key=f"sched_done_{q['id']}", use_container_width=True):
                    complete_quest(q["id"]); st.success(f"+{q['reward']} XP earned"); st.rerun()
                if not q["completed"]:
                    if st.button("Delete", key=f"del_{q['id']}", use_container_width=True):
                        with db() as con: con.execute("DELETE FROM quests WHERE id=?",(q['id'],))
                        st.rerun()

# ---------- Dungeon Battles ----------
elif page == "⚔️ Dungeon Battles":
    render_module_hud(page)
    video_uri = local_video_data_uri()
    if not st.session_state.get("dungeon_run"):
        st.markdown(
            """<div class='dungeon-gate'>
              <div class='dungeon-gate-content'>
                <div class='dungeon-kicker'>INSTANCE GATE · SHADOW ARMY</div>
                <div class='dungeon-gate-title'>Dungeon Battles</div>
                <div class='dungeon-gate-sub'>A cinematic interactive study battle. Select your shadow, configure the raid, then enter a live knowledge arena.</div>
                <div class='hero-meta'><span class='system-chip'>3D SHADOW SELECT</span><span class='system-chip purple'>LIVE COMBAT HUD</span><span class='system-chip'>GEMMA QUIZ ENGINE</span></div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        if "dungeon_boss_choice" not in st.session_state:
            st.session_state["dungeon_boss_choice"] = "igrit"

        ids = list(DUNGEON_BOSSES.keys())
        selected_id = st.session_state["dungeon_boss_choice"]
        if selected_id not in ids:
            selected_id = ids[0]
            st.session_state["dungeon_boss_choice"] = selected_id
        idx = ids.index(selected_id)
        prev_id = ids[(idx-1) % len(ids)]
        next_id = ids[(idx+1) % len(ids)]

        st.markdown("<div class='shadow-carousel-wrap'><div class='shadow-carousel-bg'></div>", unsafe_allow_html=True)
        if video_uri:
            st.markdown(
                f"<video class='cinematic-video' autoplay muted loop playsinline src='{video_uri}'></video><div class='cinematic-video-overlay'></div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            "<div class='shadow-carousel-title'><div class='eyebrow'>SHADOW ARMY · SELECT YOUR CHAMPION</div><h2>Choose Your Boss</h2><p>Swipe the roster with the controls below. The center card is the active shadow.</p></div>",
            unsafe_allow_html=True,
        )

        cards = [prev_id, selected_id, next_id]
        card_classes = ["left","center","right"]
        cols = st.columns([0.9,1.15,0.9], gap="small")
        import base64
        for col, boss_id, cls in zip(cols, cards, card_classes):
            boss = DUNGEON_BOSSES[boss_id]
            with col:
                art = load_shadow_image(boss["image"])
                if art:
                    b64 = base64.b64encode(art).decode("ascii")
                    st.markdown(
                        f"""<div class='shadow-stage' style='min-height:350px'>
                          <div class='shadow-card {cls}'>
                            <img src='data:image/jpeg;base64,{b64}' alt='{boss['name']}'>
                            <div class='shadow-card-glow'></div>
                            <div class='shadow-card-copy'>
                              <div class='shadow-card-rank'>{boss['rank']} · {boss['element']}</div>
                              <div class='shadow-card-name'>{boss['name']}</div>
                              <div class='shadow-card-meta'>+{boss['bonus']} XP · {boss['attack']}</div>
                            </div>
                          </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(f"<div class='shadow-card {cls}'><div style='height:100%;display:flex;align-items:center;justify-content:center;color:#9fb2cb'>{boss['name']}</div></div>", unsafe_allow_html=True)
                if cls == "center":
                    if st.button("✓ SELECTED SHADOW", key="select_active_shadow", use_container_width=True, type="primary"):
                        pass

        nav1,nav2,nav3 = st.columns([1,1,1])
        with nav1:
            if st.button("‹ PREVIOUS", key="shadow_prev", use_container_width=True):
                st.session_state["dungeon_boss_choice"] = prev_id
                st.rerun()
        with nav2:
            st.markdown(
                "<div class='carousel-nav'><span class='carousel-dot active'></span><span class='carousel-dot'></span><span class='carousel-dot'></span><span class='carousel-dot'></span><span class='carousel-dot'></span></div><div class='carousel-hint'>Interactive shadow roster</div>",
                unsafe_allow_html=True,
            )
        with nav3:
            if st.button("NEXT ›", key="shadow_next", use_container_width=True):
                st.session_state["dungeon_boss_choice"] = next_id
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='system-panel' style='margin-top:16px'><div class='panel-title'>◈ RAID CONFIGURATION</div><div class='muted'>Correct answers deal damage. Build your combo, preserve your shields, and clear the selected shadow to earn XP.</div></div>", unsafe_allow_html=True)
        with st.form("dungeon_launch"):
            a,b,c = st.columns(3)
            subject = a.text_input("Study subject", placeholder="e.g. Python, DBMS, Maths")
            difficulty = b.selectbox("Threat level", ["Easy","Normal","Hard","Nightmare"], index=1)
            count = c.selectbox("Targets", [5,7,10], index=0)
            launch = st.form_submit_button(f"⚔️ ENTER {DUNGEON_BOSSES[selected_id]['name'].upper()}'S INSTANCE", type="primary", use_container_width=True)

        with db() as con:
            recent = con.execute("SELECT subject,difficulty,correct,questions,xp_earned,played_at FROM dungeon_runs ORDER BY id DESC LIMIT 5").fetchall()
        if recent:
            st.markdown("### Recent clears")
            for r in recent:
                pct = int(100*r['correct']/max(1,r['questions']))
                st.markdown(f"<div class='quest'><b>{r['subject']}</b><div class='muted'>{r['difficulty']} · {r['correct']}/{r['questions']} correct · {pct}% mastery · +{r['xp_earned']} XP · {r['played_at'][:10]}</div></div>", unsafe_allow_html=True)

        if launch:
            if not subject.strip():
                st.warning("Enter a subject first.")
            else:
                questions, source = generate_quiz_questions(subject.strip(), count, difficulty)
                st.session_state["dungeon_run"] = {
                    "subject":subject.strip(),"difficulty":difficulty,"questions":questions,
                    "source":source,"boss_id":selected_id,"index":0,"correct":0,"combo":0,"damage":0,
                    "max_hp":count*100,"shield":3,"answered":False,"last_result":None,"finished":False
                }
                st.rerun()
    else:
        run = st.session_state["dungeon_run"]
        boss_id = run.get("boss_id","igrit")
        boss = DUNGEON_BOSSES.get(boss_id,DUNGEON_BOSSES["igrit"])
        if run.get("finished"):
            st.markdown(
                f"""<div class='dungeon-result'>
                  <div class='focus-badge'>INSTANCE CLEARED · VICTORY</div>
                  <div class='level-up-title' style='margin-top:8px'>{boss['name']} DEFEATED</div>
                  <div class='muted'>{run['subject']} · {run['difficulty']} · {run['correct']}/{len(run['questions'])} correct · {round(100*run['correct']/max(1,len(run['questions'])))}% accuracy · {run.get('damage',0)} damage</div>
                  <div style='font:800 34px Orbitron;color:#fbbf24;margin-top:12px'>+{run.get('xp_earned',0)} XP</div>
                </div>""",
                unsafe_allow_html=True,
            )
            if run.get("perfect"):
                st.success("✦ PERFECT CLEAR · Achievement progress updated.")
            if st.button("↩ Return to Dungeon Hub", type="primary", use_container_width=True):
                st.session_state.pop("dungeon_run", None)
                st.rerun()
        else:
            total = len(run["questions"])
            qidx = run["index"]
            q = run["questions"][qidx]
            max_hp = int(run.get("max_hp", total * 100))
            damage = int(run.get("damage", run["correct"] * 100))
            hp_pct = int(100 * max(0, max_hp - damage) / max(1, max_hp))
            phase = "PHASE III" if hp_pct <= 33 else ("PHASE II" if hp_pct <= 66 else "PHASE I")
            art = load_shadow_image(boss["image"])

            left,right = st.columns([1.18,0.82], gap="large")
            with left:
                if art:
                    import base64
                    art_b64 = base64.b64encode(art).decode("ascii")
                    st.markdown(
                        f"""<div class='dungeon-battle-shell'><div class='dungeon-art-frame'>
                          <img src='data:image/jpeg;base64,{art_b64}' alt='{boss['name']} boss artwork'>
                          {boss_visual(boss_id)}
                        </div></div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("The official boss artwork could not be loaded.")
            with right:
                st.markdown("<div class='dungeon-hud'>", unsafe_allow_html=True)
                st.markdown(f"<div class='focus-badge'>{boss['rank']} · {boss['element']} CLASS</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='dungeon-hud-title'>{boss['name']}</div><div class='dungeon-hud-sub'>{boss['description']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='dungeon-hp-label'><span>BOSS VITALITY · {phase}</span><b>{max(0,max_hp-damage)}/{max_hp}</b></div><div class='dungeon-hp'><div style='width:{max(0,hp_pct)}%'></div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='dungeon-stat-grid'><div class='dungeon-stat'><b>x{run['combo']}</b><span>Combo</span></div><div class='dungeon-stat'><b>{damage}</b><span>Damage</span></div><div class='dungeon-stat'><b>{run['correct']}/{qidx}</b><span>Hits</span></div><div class='dungeon-stat'><b>{'♥'*run['shield']}</b><span>Shield</span></div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='muted'>SIGNATURE ATTACK · <b style='color:#e6eefb'>{boss['attack']}</b> · BONUS +{boss['bonus']} XP</div>", unsafe_allow_html=True)
                if run.get("last_result") is None:
                    st.markdown(f"<div class='dungeon-question'><div class='dungeon-question-label'>TARGET {qidx+1} / {total} · SELECT YOUR STRIKE</div><div class='dungeon-question-text'>{q['q']}</div></div>", unsafe_allow_html=True)
                    with st.form(f"dungeon_question_{qidx}"):
                        choice = st.radio("Choose your answer", q["options"], index=None)
                        strike = st.form_submit_button("⚡ STRIKE BOSS", type="primary", use_container_width=True)
                    if strike:
                        if choice is None:
                            st.warning("Choose an answer first.")
                        else:
                            selected = q["options"].index(choice)
                            correct = selected == q["answer"]
                            run["last_result"] = {"correct":correct,"answer":q["options"][q["answer"]],"explain":q.get("explain","")}
                            if correct:
                                run["correct"] += 1
                                run["combo"] += 1
                                run["damage"] = int(run.get("damage", 0) + 100 * combo_multiplier(db, run["combo"]))
                            else:
                                # A miss breaks the combo, but never removes earned damage, XP, quests, or prior progress.
                                run["combo"] = 0
                                # Close the learning loop: every dungeon miss becomes a due-now revision card.
                                with db() as con:
                                    created = create_revision_from_miss(
                                        db,
                                        run["subject"],
                                        q["q"],
                                        q["options"][q["answer"]],
                                        q.get("explain", ""),
                                    )
                                run["miss_card_created"] = bool(created)
                            st.session_state["dungeon_run"] = run
                            st.rerun()
                else:
                    result = run["last_result"]
                    if result["correct"]:
                        st.success(f"⚡ CRITICAL HIT · {boss['name']} staggered! Combo x{run['combo']}")
                    else:
                        st.error(f"🛡 BLOCKED · Correct answer: {result['answer']}")
                        if result.get("correct") is False and run.get("miss_card_created"):
                            st.info("🧠 Learning loop activated · this mistake was added to your Revision Lab and is due now.")
                    st.markdown(f"<div class='system-panel'><div class='panel-title'>Battle analysis</div><div class='muted'>{result['explain']}</div></div>", unsafe_allow_html=True)
                    if qidx + 1 < total:
                        if st.button("NEXT TARGET →", type="primary", use_container_width=True):
                            run["index"] += 1
                            run["last_result"] = None
                            st.session_state["dungeon_run"] = run
                            st.rerun()
                    else:
                        if st.button("🏆 CLAIM VICTORY REWARDS", type="primary", use_container_width=True):
                            finish_dungeon()
                            st.rerun()

# ---------- Premium interactive layers ----------
elif page == "🗺️ Dungeon Map":
    render_module_hud(page)
    render_dungeon_map(db, lambda target: st.session_state.update(nav_page=target))

elif page == "🎙️ Voice Study Mode":
    render_module_hud(page)
    st.markdown("<div class='ph-shell'><div class='ph-kicker'>Hands-Free Training</div><div class='ph-title'>Voice Study Mode</div><div class='ph-copy'>Browser-native speech controls with visible transcript confirmation and keyboard/button fallback.</div></div>", unsafe_allow_html=True)
    render_voice_study_mode()
    render_sound_settings()

# ---------- Focus Room ----------
elif page == "⏱️ Focus Room":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>Focus Chamber · Pomodoro Protocol</div>
          <div class='hero-title'>Focus Room</div>
          <p class='hero-sub'>Study inside a dedicated room, finish a timer, and convert focused minutes into progression.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    mode_map = {"Quick Focus":15,"Classic Pomodoro":25,"Deep Work":50,"Long Session":90}
    a,b = st.columns([1,2])
    with a:
        mode = st.selectbox("Session mode", list(mode_map.keys()))
        minutes = mode_map[mode]
        custom = st.checkbox("Use custom duration")
        if custom:
            minutes = st.slider("Minutes", 5, 120, 25, 5)
        st.markdown(f"<div class='system-panel'><div class='focus-badge'>CURRENT PROTOCOL</div><div style='font:800 28px Orbitron;color:white;margin-top:8px'>{minutes} MIN</div><div class='muted'>Complete the session, then claim your focus XP.</div></div>", unsafe_allow_html=True)
        if st.button("▶️ START TRAINING", type="primary", use_container_width=True):
            st.session_state["focus_training"] = {
                "started_at": time.time(), "minutes": int(minutes), "mode": mode,
                "completion_id": "focus_" + hashlib.sha256(f"{mode}|{minutes}|{time.time()}".encode()).hexdigest()[:24]
            }
            st.rerun()
        _training = st.session_state.get("focus_training")
        _complete_ready = False
        _remaining = int(minutes * 60)
        if _training:
            _now_ts = time.time()
            _paused_total = float(_training.get("paused_total", 0))
            if _training.get("paused_at"):
                _elapsed = int(_training["paused_at"] - _training["started_at"] - _paused_total)
            else:
                _elapsed = int(_now_ts - _training["started_at"] - _paused_total)
            _remaining = max(0, int(_training["minutes"] * 60 - _elapsed))
            _complete_ready = _remaining <= 0 and not _training.get("paused_at")
            _mm, _ss = divmod(_remaining, 60)
            _status = "PAUSED" if _training.get("paused_at") else ("COMPLETE" if _complete_ready else "TRAINING")
            _time_label = "COMPLETE" if _complete_ready else f"{_mm:02d}:{_ss:02d} remaining"
            st.markdown(f"<div class='system-panel'><div class='focus-badge'>{_status}</div><div style='font:800 24px Orbitron;color:white;margin-top:8px'>{_time_label}</div><div class='muted'>Server-gated completion · XP is awarded only after the full active duration.</div></div>", unsafe_allow_html=True)
            if _complete_ready:
                if st.button("🏆 CLAIM COMPLETED SESSION", type="primary", use_container_width=True):
                    reward = log_focus_session(_training["minutes"], _training["mode"], _training["completion_id"])
                    st.session_state.pop("focus_training", None)
                    st.success(f"Focus session logged · +{reward} XP")
                    st.rerun()
            elif _training.get("paused_at"):
                if st.button("▶️ RESUME TRAINING", type="primary", use_container_width=True):
                    _training["paused_total"] = float(_training.get("paused_total", 0)) + (time.time() - _training["paused_at"])
                    _training.pop("paused_at", None)
                    st.session_state["focus_training"] = _training
                    st.rerun()
                if st.button("✕ END TRAINING", use_container_width=True):
                    st.session_state.pop("focus_training", None)
                    st.rerun()
            else:
                if st.button("⏸️ PAUSE TRAINING", use_container_width=True):
                    _training["paused_at"] = time.time()
                    st.session_state["focus_training"] = _training
                    st.rerun()
                if st.button("↻ REFRESH TIMER STATUS", use_container_width=True):
                    st.rerun()
                if st.button("✕ END TRAINING", use_container_width=True):
                    st.session_state.pop("focus_training", None)
                    st.rerun()

    with b:
        timer_html = f"""<!doctype html><html><body style="margin:0;background:transparent;font-family:Inter,Arial;color:#eef6ff"><div style="text-align:center;padding:10px"><div id="badge" style="font-size:11px;letter-spacing:3px;color:#67e8f9;font-weight:800">FOCUS PROTOCOL</div><div id="timer" style="font:800 74px Orbitron,Arial;margin:18px 0;text-shadow:0 0 25px #67e8f955">{_remaining//60:02d}:{_remaining%60:02d}</div><div style="height:8px;background:#17243a;border-radius:99px;overflow:hidden"><div id="bar" style="height:100%;width:100%;background:linear-gradient(90deg,#38bdf8,#a78bfa);border-radius:99px"></div></div><div style="margin-top:18px"><button id="start" style="border:1px solid #67e8f966;background:#12345acc;color:white;border-radius:10px;padding:10px 18px;font-weight:700;cursor:pointer">START</button><button id="reset" style="margin-left:8px;border:1px solid #ffffff18;background:#0b1526cc;color:#cbdcf0;border-radius:10px;padding:10px 18px;font-weight:700;cursor:pointer">RESET</button></div><div id="status" style="margin-top:13px;color:#9db4cc;font-size:13px">Start when you are ready.</div></div><script>let total={max(1,_remaining)}, left=total, timer=null;const t=document.getElementById('timer'),b=document.getElementById('bar'),s=document.getElementById('status');function render(){{let m=Math.floor(left/60),sec=left%60;t.textContent=String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');b.style.width=(left/total*100)+'%';}}document.getElementById('start').onclick=()=>{{if(timer)return;s.textContent='Session active — one task, one target.';timer=setInterval(()=>{{if(left<=0){{clearInterval(timer);timer=null;s.textContent='Session complete — claim your focus XP in the panel.';try{{new AudioContext().resume();const c=new AudioContext(),o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=660;g.gain.value=.03;o.start();o.stop(c.currentTime+.35);}}catch(e){{}}return;}}left--;render();}},1000)}};document.getElementById('reset').onclick=()=>{{if(timer){{clearInterval(timer);timer=null}}left=total;s.textContent='Timer reset.';render()}};render();</script></body></html>"""
        components.html(timer_html, height=300, scrolling=False)
    with db() as con:
        recent = con.execute("SELECT * FROM focus_sessions ORDER BY id DESC LIMIT 10").fetchall()
        week = con.execute("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions WHERE completed=1 AND substr(started_at,1,10)>=?", (current_week_start().isoformat(),)).fetchone()[0]
    st.subheader("Focus history")
    st.metric("This week", f"{int(week)} minutes")
    for s in recent:
        st.markdown(f"<div class='quest'><b>⏱️ {s['mode']}</b><div class='muted'>{s['minutes']} minutes · {s['started_at'][:16].replace('T',' · ')}</div></div>", unsafe_allow_html=True)

# ---------- Revision Lab ----------
elif page == "🧠 Revision Lab":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>Memory Core · Spaced Repetition</div>
          <div class='hero-title'>Revision Lab</div>
          <p class='hero-sub'>Build flashcards, review only what is due, and let the scheduler space repetition for you.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    metrics = get_activity_metrics()
    a,b,c = st.columns(3)
    a.metric("Due now", metrics['due_cards'])
    c.metric("Reviews", metrics['reviews'])
    with db() as con:
        total_cards = con.execute("SELECT COUNT(*) FROM revision_cards").fetchone()[0]
    b.metric("Total cards", total_cards)
    create_tab, ai_tab, review_tab = st.tabs(["＋ Create Card","✨ AI Card Forge","🧠 Review Due"])
    with create_tab:
        with st.form("create_card"):
            a,b = st.columns(2)
            subject = a.text_input("Subject", placeholder="Python")
            front = b.text_input("Question / Front", placeholder="What does len() return?")
            back = st.text_area("Answer / Back", placeholder="The number of items in an object such as a list.")
            add = st.form_submit_button("Add flashcard", type="primary")
        if add:
            if not front.strip() or not back.strip(): st.error("Both front and back are required.")
            else:
                create_card(subject, front, back); st.success("Flashcard created and due now."); st.rerun()
    with ai_tab:
        with st.form("ai_cards"):
            topic = st.text_input("Topic", placeholder="e.g. Python lists")
            number = st.selectbox("Number of cards", [3,5,8], index=1)
            forge = st.form_submit_button("Forge cards with Gemma", type="primary")
        if forge:
            if not topic.strip():
                st.warning("Enter a topic.")
            else:
                prompt = f"Create exactly {number} concise flashcards about {topic}. Return ONLY JSON array. Each object must have subject, front, back. Keep answers correct and study-focused."
                with st.spinner("Forging memory cards..."):
                    try:
                        raw = ask_ollama(prompt, "You create accurate flashcards. Return only a JSON array with subject, front, back fields.")
                        cards = _parse_json_array(raw) or []
                        valid = [x for x in cards if isinstance(x,dict) and str(x.get('front','')).strip() and str(x.get('back','')).strip()]
                        if valid:
                            for card in valid[:number]: create_card(str(card.get('subject') or topic), str(card['front']), str(card['back']))
                            st.success(f"Added {min(number,len(valid))} AI flashcards."); st.rerun()
                        else: st.error("The selected model did not return usable cards. Try a stronger installed model or create cards manually.")
                    except RuntimeError as exc: st.error(str(exc))
    with review_tab:
        with db() as con:
            due_cards = con.execute("SELECT * FROM revision_cards WHERE due<=? ORDER BY due,id LIMIT 1", (date.today().isoformat(),)).fetchall()
        if not due_cards:
            st.markdown("<div class='review-card' style='text-align:center'><div style='font-size:60px'>🌙</div><div class='review-front'>Memory Core is clear.</div><div class='muted' style='margin-top:8px'>No cards are due right now. Create more cards or return when your next review is scheduled.</div></div>", unsafe_allow_html=True)
        else:
            card = due_cards[0]
            st.markdown(f"<div class='review-card'><div class='focus-badge'>{card['subject'] or 'GENERAL'} · DUE NOW</div><div class='review-front' style='margin-top:15px'>{card['front']}</div><div class='review-back'>Flip in your head before revealing: <b>What is the answer?</b><br><br>{card['back']}</div></div>", unsafe_allow_html=True)
            st.caption(f"Current interval: {card['interval_days']} day(s) · Ease {card['ease']:.2f}")
            r1,r2,r3,r4 = st.columns(4)
            if r1.button("Again · 1d", key=f"again_{card['id']}", use_container_width=True): review_card(card['id'], "Again"); st.rerun()
            if r2.button("Hard", key=f"hard_{card['id']}", use_container_width=True): review_card(card['id'], "Hard"); st.rerun()
            if r3.button("Good", key=f"good_{card['id']}", use_container_width=True): review_card(card['id'], "Good"); st.rerun()
            if r4.button("Easy", key=f"easy_{card['id']}", use_container_width=True): review_card(card['id'], "Easy"); st.rerun()
    st.divider()
    with db() as con:
        upcoming = con.execute("SELECT * FROM revision_cards ORDER BY due,id LIMIT 12").fetchall()
    st.subheader("Memory schedule")
    for card in upcoming:
        status = "DUE" if card['due'] <= date.today().isoformat() else card['due']
        st.markdown(f"<div class='quest'><b>{card['subject'] or 'General'} · {card['front'][:70]}</b><div class='muted'>{status} · interval {card['interval_days']}d · repetitions {card['repetitions']}</div></div>", unsafe_allow_html=True)

# ---------- Achievements ----------
elif page == "🏆 Achievements":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>Hunter Record · Collection System</div>
          <div class='hero-title'>Achievements</div>
          <p class='hero-sub'>Every milestone is a permanent record of what you actually accomplished.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    evaluate_achievements()
    with db() as con:
        unlocked = {r['id']:r['unlocked_at'] for r in con.execute("SELECT * FROM achievements ORDER BY unlocked_at").fetchall()}
    pct = len(unlocked)/len(ACHIEVEMENTS) if ACHIEVEMENTS else 0
    m1,m2,m3 = st.columns(3)
    m1.metric("Unlocked", f"{len(unlocked)}/{len(ACHIEVEMENTS)}")
    m2.metric("Collection", f"{int(pct*100)}%")
    m3.metric("Current rank", rank)
    st.progress(pct)
    cols = st.columns(3)
    for i,ach in enumerate(ACHIEVEMENTS):
        ok = ach['id'] in unlocked
        with cols[i%3]:
            st.markdown(f"<div class='achievement-card {' ' if ok else 'achievement-locked'}'><div class='achievement-icon'>{ach['icon'] if ok else '🔒'}</div><div class='achievement-name'>{ach['name']}</div><div class='muted' style='margin-top:5px'>{ach['desc']}</div><div style='margin-top:9px;color:{'#86efac' if ok else '#718096'};font-size:12px'>{'UNLOCKED · '+unlocked[ach['id']][:10] if ok else 'LOCKED'}</div></div>", unsafe_allow_html=True)

# ---------- Hunter Report ----------
elif page == "📊 Hunter Report":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>Intelligence Report · Last 7 Days</div>
          <div class='hero-title'>Hunter Report</div>
          <p class='hero-sub'>A clear weekly review of your study effort, wins, weak spots, and next training priorities.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    start = current_week_start()
    days = [(start + timedelta(days=i)) for i in range(7)]
    with db() as con:
        day_rows=[]
        for d in days:
            ds=d.isoformat()
            q=con.execute("SELECT COUNT(*) AS total, COALESCE(SUM(completed),0) AS done FROM quests WHERE due=?", (ds,)).fetchone()
            f=con.execute("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions WHERE completed=1 AND substr(started_at,1,10)=?", (ds,)).fetchone()[0]
            x=con.execute("SELECT COALESCE(SUM(amount),0) FROM xp_log WHERE substr(happened_at,1,10)=?", (ds,)).fetchone()[0]
            day_rows.append((d,q['total'],q['done'],int(f or 0),int(x or 0)))
    total_q=sum(x[1] for x in day_rows); done_q=sum(x[2] for x in day_rows); focus=sum(x[3] for x in day_rows); net_xp=sum(x[4] for x in day_rows)
    with db() as con:
        subject_rows = con.execute("SELECT COALESCE(subject,'General') AS subject, COUNT(*) AS total, COALESCE(SUM(completed),0) AS done FROM quests GROUP BY COALESCE(subject,'General') ORDER BY total DESC LIMIT 8").fetchall()
    subject_payload = "; ".join([f"{r['subject']}: {r['done']}/{r['total']} complete" for r in subject_rows]) or "No quest subject data yet"
    a,b,c,d = st.columns(4)
    a.metric("Quest completion", f"{int(100*done_q/max(1,total_q))}%")
    b.metric("Focus time", f"{focus} min")
    c.metric("Net XP this week", f"{net_xp:+d}")
    d.metric("Current streak", f"{profile['streak']} days")
    st.markdown("### Weekly activity")
    for day, total, done, mins, xp in day_rows:
        ratio = done/max(1,total)
        st.markdown(f"<div class='report-day'><div style='width:76px'><b>{day.strftime('%a')}</b><div class='muted'>{day.strftime('%d %b')}</div></div><div class='day-bar'><div class='day-fill' style='width:{ratio*100:.0f}%'></div></div><div style='width:140px;text-align:right' class='muted'>{done}/{total} quests · {mins}m · {xp:+} XP</div></div>", unsafe_allow_html=True)
    st.markdown("### Subject mastery")
    if subject_rows:
        for r in subject_rows:
            ratio = r['done']/max(1,r['total'])
            st.markdown(f"<div class='report-day'><div style='width:160px'><b>{r['subject']}</b></div><div class='day-bar'><div class='day-fill' style='width:{ratio*100:.0f}%'></div></div><div style='width:100px;text-align:right' class='muted'>{r['done']}/{r['total']}</div></div>", unsafe_allow_html=True)
    else:
        st.caption("Complete some quests to generate subject-level mastery insights.")
    st.markdown("### AI Hunter Report")
    if st.button("✨ Generate my weekly analysis", type="primary"):
        payload = "; ".join([f"{d.strftime('%a %d')}: {done}/{total} quests, {mins}m focus, {xp:+} XP" for d,total,done,mins,xp in day_rows])
        prompt = f"Analyze this student's 7-day study activity: {payload}. Subject completion snapshot: {subject_payload}. Current rank {rank}, level {level}, streak {profile['streak']}. Write a concise report with: 1) strongest pattern, 2) weakest subject/pattern, 3) one concrete priority for next week, 4) one realistic habit. Do not invent data and explicitly say when the data is insufficient."
        with st.spinner("The system is analyzing your week..."):
            try:
                st.session_state['hunter_report'] = ask_ollama(prompt)
            except RuntimeError as exc: st.error(str(exc))
    if st.session_state.get('hunter_report'):
        st.markdown(f"<div class='system-panel'>{st.session_state['hunter_report']}</div>", unsafe_allow_html=True)
    st.info("This report is local and uses only your StudyBuddy activity data. No cloud account is required.")

# ---------- Guild Hall ----------
elif page == "🤝 Guild Hall":
    render_module_hud(page)
    guild, members = guild_data()
    st.markdown(
        f"<div class='guild-banner'>"
        f"<div class='hero-kicker'>Guild Network · Study Party</div>"
        f"<div class='hero-title'>{guild['name']}</div>"
        f"<p class='hero-sub'>{guild['motto']}</p>"
        f"<div class='hero-meta'>"
        f"<span class='guild-code' style='font-size:1.05rem'>{guild['code']}</span>"
        f"<span class='muted' style='align-self:center'>Local invite code · party stored on this computer</span>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    weekly = guild_weekly_xp(); goal = guild['weekly_goal']
    a,b,c = st.columns(3)
    a.metric("Guild XP this week", weekly)
    b.metric("Weekly objective", goal)
    c.metric("Party members", len(members)+1)
    st.progress(min(1,weekly/max(1,goal)))
    with st.expander("⚙️ Guild settings"):
        with st.form("guild_settings"):
            name = st.text_input("Guild name", value=guild['name'])
            motto = st.text_input("Guild motto", value=guild['motto'])
            goal_value = st.slider("Weekly XP goal", 100, 5000, int(guild['weekly_goal']), 50)
            save_guild = st.form_submit_button("Save guild")
        if save_guild:
            code = guild['code'] or create_guild_code(name.strip() or guild['name'])
            with db() as con: con.execute("UPDATE guild SET name=?,motto=?,weekly_goal=?,code=? WHERE id=1", (name.strip() or "Awakened Scholars",motto.strip() or "Study together. Rise together.",goal_value,code))
            st.success("Guild updated."); st.rerun()
    with st.expander("＋ Add a study party member"):
        with st.form("guild_member"):
            n = st.text_input("Member name")
            role = st.selectbox("Role", ["Hunter","Strategist","Quiz Master","Focus Captain"])
            mxp = st.number_input("Weekly XP", min_value=0, max_value=5000, value=0, step=10)
            add = st.form_submit_button("Add member")
        if add:
            if not n.strip(): st.error("Enter a name.")
            else:
                with db() as con: con.execute("INSERT INTO guild_members(name,role,weekly_xp,added_at) VALUES(?,?,?,?)", (n.strip(),role,int(mxp),_now()))
                st.success("Member added to the local party."); st.rerun()
    st.subheader("Guild leaderboard")
    st.markdown(f"<div class='quest quest-done'><b>👑 {profile['name']} · You</b><div class='muted'>Current rank {rank} · {weekly} guild XP from this installation this week</div></div>", unsafe_allow_html=True)
    for i,m in enumerate(members,1):
        st.markdown(f"<div class='quest'><b>#{i+1} {m['name']}</b><div class='muted'>{m['role']} · {m['weekly_xp']} weekly XP · {m['focus_minutes']} focus minutes</div></div>", unsafe_allow_html=True)
    st.info("Guild Hall is intentionally local-first in this version. It provides a complete party/leaderboard experience on one installation without pretending to offer real-time cloud multiplayer.")

# ---------- Important PDFs ----------
elif page == "📚 Important PDFs":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>Knowledge Archive</div>
          <div class='hero-title'>Important PDFs</div>
          <p class='hero-sub'>Keep your question papers, notes, and reference PDFs in one local library.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    with st.form("pdf_upload", clear_on_submit=True):
        uploaded=st.file_uploader("Upload a PDF", type=["pdf"])
        a,b=st.columns(2)
        title=a.text_input("Display name", placeholder="e.g. Python solved question papers")
        subject=b.text_input("Subject / category", placeholder="e.g. Python")
        add=st.form_submit_button("Save to Important PDFs", type="primary")
        if add:
            if uploaded is None: st.error("Choose a PDF first.")
            else:
                raw=uploaded.getvalue(); digest=hashlib.sha256(raw).hexdigest()
                safe_name=f"{digest[:12]}_{Path(uploaded.name).name}"
                dest=PDF_DIR/safe_name
                try:
                    # Check whether the PDF can be opened before storing it.
                    reader=PdfReader(uploaded)
                    page_count=len(reader.pages)
                    if not dest.exists(): dest.write_bytes(raw)
                    with db() as con:
                        con.execute("INSERT OR IGNORE INTO pdfs(title,subject,filename,stored_path,file_hash,added_at) VALUES(?,?,?,?,?,?)", (title.strip() or Path(uploaded.name).stem,subject.strip(),uploaded.name,str(dest),digest,datetime.now().isoformat(timespec="seconds")))
                    st.success(f"Saved. {page_count} pages detected."); st.rerun()
                except Exception as err: st.error(f"Could not save this PDF: {err}")
    st.subheader("🛠️ PDF Converter")
    st.caption("Convert a text-based PDF into an editable DOCX file. Original PDFs stay untouched.")
    convert_file = st.file_uploader("Choose a PDF to convert", type=["pdf"], key="pdf_converter_upload")
    convert_name = st.text_input("Output filename", value="study_notes.docx", key="pdf_converter_name")
    if convert_file is not None and st.button("🔄 Convert PDF → DOCX", type="primary", key="pdf_to_docx"):
        try:
            from docx import Document
            from docx.shared import Pt
            from io import BytesIO
            reader = PdfReader(convert_file)
            doc = Document()
            normal = doc.styles["Normal"]
            normal.font.name = "Aptos"
            normal.font.size = Pt(10.5)
            doc.add_heading(Path(convert_file.name).stem, level=1)
            extracted = 0
            for page_no, pdf_page in enumerate(reader.pages, start=1):
                page_text = (pdf_page.extract_text() or "").strip()
                if page_no > 1:
                    doc.add_page_break()
                doc.add_heading(f"Page {page_no}", level=2)
                if page_text:
                    for paragraph in page_text.split("\n\n"):
                        if paragraph.strip():
                            doc.add_paragraph(paragraph.strip())
                            extracted += len(paragraph.strip())
                else:
                    doc.add_paragraph("[No extractable text on this page]")
            output = BytesIO()
            doc.save(output)
            output.seek(0)
            out_name = Path(convert_name.strip() or "study_notes.docx").name
            if not out_name.lower().endswith(".docx"):
                out_name += ".docx"
            st.success(f"Converted {len(reader.pages)} pages. Extracted approximately {extracted:,} characters.")
            st.download_button("⬇️ Download converted DOCX", data=output.getvalue(), file_name=out_name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True, key="pdf_docx_download")
        except ImportError:
            st.error("DOCX support is not installed. Run: pip install python-docx")
        except Exception as err:
            st.error(f"Conversion failed: {err}")

    st.divider()
    st.subheader("Saved documents")
    search=st.text_input("Search library", placeholder="Search by title or subject")
    with db() as con:
        docs=con.execute("SELECT * FROM pdfs ORDER BY added_at DESC").fetchall()
    docs=[d for d in docs if search.lower() in (d['title']+' '+(d['subject'] or '')+' '+d['filename']).lower()]
    if not docs: st.info("Your library is empty. Upload an important PDF above.")
    for d in docs:
        with st.container(border=True):
            a,b,c=st.columns([4,1,1])
            with a:
                st.markdown(f"**📄 {d['title']}**")
                st.caption(f"{d['subject'] or 'Uncategorized'} · {d['filename']} · Added {d['added_at'][:10]}")
            path=Path(d['stored_path'])
            if path.exists():
                with b: st.download_button("Download", data=path.read_bytes(), file_name=d['filename'], mime="application/pdf", key=f"pdf_dl_{d['id']}", use_container_width=True)
            with c:
                if st.button("Remove", key=f"pdf_rm_{d['id']}", use_container_width=True):
                    with db() as con: con.execute("DELETE FROM pdfs WHERE id=?",(d['id'],))
                    # Leave the physical file in place to avoid deleting a duplicate file still referenced elsewhere.
                    st.rerun()

# ---------- Character / power ----------
elif page == "🧬 Character & Power":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>Awakening & Growth</div>
          <div class='hero-title'>Character & Power</div>
          <p class='hero-sub'>Your hunter evolves through real study progress. This is a study progression system, not a combat simulator.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    a,b=st.columns([1,1.5])
    with a:
        char_icons={"Shadow Hunter":"🗡️","Mage":"🔮","Knight":"🛡️","Archer":"🏹"}
    power=profile['xp'] + profile['focus']*10 + profile['discipline']*10 + profile['knowledge']*10 + profile['energy']*5
    st.markdown(f"<div class='panel' style='text-align:center;padding:30px 15px'><div style='font-size:76px'>{char_icons.get(profile['character'],'⚔️')}</div><div style='font-family:Rajdhani;font-size:29px;font-weight:700'>{profile['name']}</div><div class='muted'>{profile['character']}</div><div class='rank'>{rank}</div><h2 style='margin:12px 0 0'>LEVEL {level}</h2><div class='muted'>{profile['title']} · Power {power:,}</div><br><div class='xp-track'><div class='xp-fill' style='width:{xp_progress(profile['xp'])}%'></div></div><div class='muted'>{xp_progress(profile['xp'])}/100 XP to next level</div></div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='panel'><div class='panel-title'>⚡ Power Status</div>", unsafe_allow_html=True)
        stat_info=[("🧠 Intelligence","knowledge","Knowledge gained from study quests"),("🎯 Focus","focus","Consistency in completing missions"),("🛡️ Discipline","discipline","Quest completion and routine"),("🔥 Energy","energy","Activity and study momentum")]
        for label,key,desc in stat_info:
            val=profile[key]
            st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;margin-top:15px'><b>{label}</b><b style='color:#5ee7f5'>{val}</b></div><div class='xp-track' style='height:9px'><div class='xp-fill' style='width:{min(val,99)}%'></div></div><div class='muted'>{desc}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel'><div class='panel-title'>🎒 Hunter Loadout</div><div class='muted'>Cosmetic progression only — studying remains the source of real power.</div></div>", unsafe_allow_html=True)
    aura_options = ["Azure System Aura","Void Purple Aura","Monarch Gold Aura","Crimson Awakening"]
    saved_aura = None
    with db() as con:
        row = con.execute("SELECT value FROM app_settings WHERE key='aura'").fetchone()
        saved_aura = row["value"] if row else aura_options[0]
    aura = st.selectbox("Equip an aura", aura_options, index=aura_options.index(saved_aura) if saved_aura in aura_options else 0)
    if aura != saved_aura:
        with db() as con: con.execute("INSERT INTO app_settings(key,value) VALUES('aura',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (aura,))
        st.toast(f"Equipped: {aura}", icon="✨")

    next_rank = next((name for threshold,name in RANKS if profile['xp'] < threshold), None)
    if next_rank:
        threshold = next(threshold for threshold,name in RANKS if name == next_rank)
        st.markdown(f"<div class='panel'><div class='panel-title'>📈 Rank Roadmap</div><b>{rank}</b> → <b style='color:#f5c451'>{next_rank}</b><div class='xp-track'><div class='xp-fill' style='width:{min(100,max(5,profile['xp']/threshold*100))}%'></div></div><div class='muted'>{max(0,threshold-profile['xp'])} XP until {next_rank}</div></div>", unsafe_allow_html=True)
    st.subheader("Titles unlocked")
    titles=[(1,"New Awakening"),(3,"Daily Grinder"),(5,"Quest Breaker"),(10,"Shadow Scholar"),(20,"Monarch of Knowledge")]
    cols=st.columns(len(titles))
    for col,(lv,t) in zip(cols,titles):
        with col:
            unlocked=level>=lv
            st.markdown(f"<div class='panel' style='text-align:center;min-height:100px;opacity:{1 if unlocked else .4}'><div style='font-size:22px'>{'🏅' if unlocked else '🔒'}</div><b>{t}</b><div class='muted'>Level {lv}</div></div>",unsafe_allow_html=True)
    if st.button("Equip highest unlocked title"):
        available=[t for lv,t in titles if level>=lv]
        with db() as con: con.execute("UPDATE profile SET title=? WHERE id=1",(available[-1],))
        st.success(f"Title equipped: {available[-1]}"); st.rerun()

# ---------- Anime RPG ----------
elif page == "👑 Anime RPG":
    render_module_hud(page)
    render_anime_rpg(DB_PATH, profile, award_xp, ask_ollama)

# ---------- Settings ----------
elif page == "⚙️ Settings":
    render_module_hud(page)
    st.markdown(
        """<div class='hero'>
          <div class='hero-kicker'>System Configuration</div>
          <div class='hero-title'>Settings</div>
          <p class='hero-sub'>Customize your hunter profile and manage local data.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    with st.form("profile_settings"):
        new_name=st.text_input("Hunter name", value=profile['name'])
        character=st.selectbox("Choose your character class", ["Shadow Hunter","Mage","Knight","Archer"], index=["Shadow Hunter","Mage","Knight","Archer"].index(profile.get('character','Shadow Hunter')))
        save=st.form_submit_button("Save profile", type="primary")
        if save:
            with db() as con: con.execute("UPDATE profile SET name=?, character=? WHERE id=1",(new_name.strip() or "Hunter",character))
            st.success("Profile updated."); st.rerun()
    st.markdown("### ⚠️ Penalty Protocol")
    st.caption("Missed quests can reduce XP after their scheduled date. Penalties are one-time per quest and capped at 30 XP per day. Existing overdue quests are not penalized when this feature is first added.")
    with st.form("penalty_settings"):
        penalty_on = st.checkbox("Enable missed-quest penalties", value=bool(profile.get("penalty_enabled", 1)))
        penalty_value = st.select_slider("XP lost per missed quest", options=[5, 10, 15, 20, 25, 30], value=int(profile.get("penalty_amount", 10)))
        save_penalty = st.form_submit_button("Save penalty rules")
        if save_penalty:
            with db() as con:
                con.execute("UPDATE profile SET penalty_enabled=?, penalty_amount=? WHERE id=1", (int(penalty_on), int(penalty_value)))
            st.success("Penalty rules saved.")
            st.rerun()
    with db() as con:
        penalty_rows = con.execute("SELECT note,amount,applied_on FROM penalty_log ORDER BY id DESC LIMIT 8").fetchall()
    with st.expander("Recent penalty history"):
        if penalty_rows:
            for item in penalty_rows:
                st.write(f"-{item['amount']} XP · {item['note']} · {item['applied_on']}")
        else:
            st.caption("No penalties recorded.")

    st.markdown("### 🌙 Healthy progression")
    st.caption("StudyBuddy rewards consistency without forcing endless sessions. Take breaks, pause timers, and use the penalty switch only when it helps your routine.")

    st.markdown("### 🧠 Gemma AI")
    st.caption("StudyBuddy uses Google's hosted Gemma models through the Gemini API. You can choose a model and connect your key from the sidebar (Gemma AI · Google Cloud).")
    if has_api_key():
        st.success("Gemma AI is connected. You're good to go.")
    else:
        st.info("Open the sidebar to paste or load your Google AI API key from Streamlit secrets, the GEMINI_API_KEY env var, or a .env file.")
    st.caption("Current model: " + get_selected_model())
    st.caption("To override the model for all users on this deployment, set the STUDYBUDDY_MODEL environment variable.")

    st.markdown("### Local storage")
    st.caption(f"Database: {DB_PATH}")
    st.caption(f"Important PDFs folder: {PDF_DIR}")
    st.warning("Your schedule, XP, profile, and saved PDF library are stored locally on this computer. Keep the study_data folder if you move or back up the app.")
    with st.expander("Reset progress (careful)"):
        st.warning("This permanently deletes quests and resets your XP and stats. Your saved PDFs are kept.")
        confirm=st.checkbox("I understand and want to reset my study progress")
        if st.button("Reset progress", disabled=not confirm):
            with db() as con:
                con.execute("DELETE FROM quests")
                con.execute("DELETE FROM exams")
                con.execute("DELETE FROM exam_topics")
                con.execute("DELETE FROM mastery_events")
                con.execute("UPDATE profile SET xp=0,focus=1,discipline=1,knowledge=1,energy=1,streak=0,last_study=NULL,title='New Awakening' WHERE id=1")
            st.success("Progress reset."); st.rerun()

st.sidebar.divider()
st.sidebar.caption("StudyBuddy Level Up · Local-first study tracker")
