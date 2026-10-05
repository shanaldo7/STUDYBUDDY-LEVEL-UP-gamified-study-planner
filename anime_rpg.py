"""Anime RPG expansion for StudyBuddy: real web artwork + study-powered raids."""
import html
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

CHARACTERS = [
    {"id":"jinwoo","name":"Sung Jin-Woo","title":"Shadow Monarch","rarity":"Mythic","unlock":1,"power":1000,
     "image":"https://sololeveling-anime.net/story/SYS/CONTENTS/story_3210_photo_1706598392208273160"},
    {"id":"igris","name":"Igris","title":"Blood-Red Commander","rarity":"Legendary","unlock":1,"power":920,
     "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/igrit.jpg"},
    {"id":"tank","name":"Tank","title":"Frost Bear","rarity":"Epic","unlock":2,"power":760,
     "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/tank.jpg"},
    {"id":"iron","name":"Iron","title":"Armored Guardian","rarity":"Epic","unlock":3,"power":800,
     "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/iron.jpg"},
    {"id":"kiba","name":"Kiba","title":"High Orc Shaman","rarity":"Rare","unlock":4,"power":700,
     "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/kiba.jpg"},
    {"id":"beru","name":"Beru","title":"Ant King","rarity":"Legendary","unlock":5,"power":960,
     "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/beru.jpg"},
    {"id":"kaisel","name":"Kaisel","title":"Wyvern","rarity":"Legendary","unlock":6,"power":900,
     "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/kaisel.jpg"},
    {"id":"chae","name":"Cha Hae-In","title":"Dancer of the Sword","rarity":"Mythic","unlock":7,"power":980,
     "image":""},
    {"id":"thomas","name":"Thomas Andre","title":"National Level Hunter","rarity":"Mythic","unlock":10,"power":1200,
     "image":""},
    {"id":"liu","name":"Liu Zhigang","title":"Chinese National-Level Hunter","rarity":"Mythic","unlock":12,"power":1180,
     "image":""},
    {"id":"ashborn","name":"Ashborn","title":"King of the Dead","rarity":"Transcendent","unlock":15,"power":1500,
     "image":""},
]

BOSSES = [
    {"id":"igris_raid","name":"Igris","title":"Blood-Red Knight","rank":"A-Rank","hp":1400,"level":8,
     "attack":38,"defense":22,"xp":300,"coins":120,"fragments":1,
     "image":"https://sololeveling-anime.net/assets/img/special/shadows-visual/igrit.jpg"},
    {"id":"baran_raid","name":"Baran","title":"Demon King","rank":"S-Rank","hp":2600,"level":25,
     "attack":64,"defense":40,"xp":650,"coins":260,"fragments":2,
     "image":"https://sololeveling-anime.net/story/SYS/CONTENTS/story_3939_photo_1739863041780474016"},
]

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_art(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"StudyBuddy-Level-Up/1.0"})
        with urllib.request.urlopen(req,timeout=5) as r:
            if not r.headers.get("Content-Type","").startswith("image/"):
                return None
            return r.read()
    except (urllib.error.URLError,TimeoutError,OSError):
        return None

def db(path):
    con=sqlite3.connect(path)
    con.row_factory=sqlite3.Row
    return con

def init(path):
    with db(path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS anime_rpg_state(
            id INTEGER PRIMARY KEY CHECK(id=1), selected_character TEXT NOT NULL DEFAULT 'jinwoo',
            active_boss TEXT NOT NULL DEFAULT 'igris_raid', defeats INTEGER NOT NULL DEFAULT 0,
            coins INTEGER NOT NULL DEFAULT 0, fragments INTEGER NOT NULL DEFAULT 0,
            chests INTEGER NOT NULL DEFAULT 0, last_claim_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS anime_boss_state(
            boss_id TEXT PRIMARY KEY, hp INTEGER NOT NULL, max_hp INTEGER NOT NULL,
            defeated INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL)""")
        con.execute("""CREATE TABLE IF NOT EXISTS anime_raid_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, boss_id TEXT,
            amount INTEGER NOT NULL DEFAULT 0, note TEXT NOT NULL, happened_at TEXT NOT NULL)""")
        now=datetime.now().isoformat(timespec="seconds")
        con.execute("INSERT OR IGNORE INTO anime_rpg_state(id,selected_character,active_boss,last_claim_at,updated_at) VALUES(1,'jinwoo','igris_raid',?,?)",(now,now))
        for b in BOSSES:
            con.execute("INSERT OR IGNORE INTO anime_boss_state(boss_id,hp,max_hp,updated_at) VALUES(?,?,?,?)",(b["id"],b["hp"],b["hp"],now))

def state(path):
    with db(path) as con:
        return dict(con.execute("SELECT * FROM anime_rpg_state WHERE id=1").fetchone())

def boss_state(path,boss_id):
    with db(path) as con:
        return dict(con.execute("SELECT * FROM anime_boss_state WHERE boss_id=?",(boss_id,)).fetchone())

def pending_activity(path,last_claim_at):
    with db(path) as con:
        f=con.execute("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions WHERE completed=1 AND started_at>?",(last_claim_at,)).fetchone()[0]
        q=con.execute("SELECT COUNT(*),COALESCE(SUM(reward),0) FROM quests WHERE completed=1 AND COALESCE(completed_at,'')>?",(last_claim_at,)).fetchone()
    return int(f or 0),int(q[0] or 0),int(q[1] or 0)

def damage_for(minutes,quest_count,quest_xp,streak):
    return max(0,minutes*5+(quest_xp//2)+(quest_count*10)+min(100,max(0,streak)*2))

def save_character(path,cid):
    with db(path) as con:
        con.execute("UPDATE anime_rpg_state SET selected_character=?,updated_at=? WHERE id=1",(cid,datetime.now().isoformat(timespec="seconds")))

def claim_damage(path,boss_id,damage,minutes,quest_count):
    now=datetime.now().isoformat(timespec="seconds")
    with db(path) as con:
        b=con.execute("SELECT * FROM anime_boss_state WHERE boss_id=?",(boss_id,)).fetchone()
        if not b: return 0,0,False
        applied=min(int(damage),int(b["hp"]))
        new_hp=max(0,int(b["hp"])-applied)
        was_defeated=bool(b["defeated"])
        con.execute("UPDATE anime_boss_state SET hp=?,updated_at=? WHERE boss_id=?",(new_hp,now,boss_id))
        con.execute("UPDATE anime_rpg_state SET last_claim_at=?,updated_at=? WHERE id=1",(now,now))
        con.execute("INSERT INTO anime_raid_log(event,boss_id,amount,note,happened_at) VALUES(?,?,?,?,?)",
                     ("damage",boss_id,applied,f"{minutes} focus min + {quest_count} completed quests",now))
        return applied,new_hp,(new_hp<=0 and not was_defeated)

def finish_boss(path,boss,award_xp):
    now=datetime.now().isoformat(timespec="seconds")
    with db(path) as con:
        con.execute("UPDATE anime_boss_state SET defeated=1,hp=0,updated_at=? WHERE boss_id=?",(now,boss["id"]))
        con.execute("""UPDATE anime_rpg_state SET defeats=defeats+1,coins=coins+?,
                       fragments=fragments+?,chests=chests+1,updated_at=? WHERE id=1""",
                     (boss["coins"],boss["fragments"],now))
        con.execute("INSERT INTO anime_raid_log(event,boss_id,amount,note,happened_at) VALUES(?,?,?,?,?)",
                    ("victory",boss["id"],boss["xp"],f"Defeated {boss['name']}",now))
    award_xp(boss["xp"],15,"anime_boss",f"Defeated {boss['name']} with study progress")

def replay_boss(path,boss_id):
    b=next(b for b in BOSSES if b["id"]==boss_id)
    now=datetime.now().isoformat(timespec="seconds")
    with db(path) as con:
        con.execute("UPDATE anime_boss_state SET hp=?,defeated=0,updated_at=? WHERE boss_id=?",(b["hp"],now,boss_id))
        con.execute("UPDATE anime_rpg_state SET active_boss=?,last_claim_at=?,updated_at=? WHERE id=1",(boss_id,now,now))

def render(path,profile,award_xp,ask_ai_fn=None):
    init(path)
    s=state(path)
    level=int(profile["xp"])//100+1
    current=next(b for b in BOSSES if b["id"]==s["active_boss"])
    bs=boss_state(path,current["id"])
    st.markdown("""<style>
    .system-status{
      position:relative;overflow:hidden;padding:18px 20px;margin:0 0 18px;
      border:1px solid rgba(180,225,255,.28);border-radius:18px;
      background:
        radial-gradient(circle at 50% -20%,rgba(94,234,212,.12),transparent 55%),
        linear-gradient(145deg,rgba(7,15,29,.94),rgba(14,21,39,.92));
      box-shadow:0 0 35px rgba(40,150,255,.08),inset 0 0 30px rgba(103,232,249,.035);
    }
    .system-status:after{
      content:"";position:absolute;inset:0;pointer-events:none;
      background:linear-gradient(100deg,transparent 35%,rgba(103,232,249,.08) 50%,transparent 65%);
      animation:systemSweep 5s linear infinite;
    }
    @keyframes systemSweep{from{transform:translateX(-80%)}to{transform:translateX(80%)}}
    .status-label{text-align:center;color:#cfeeff;letter-spacing:4px;font:700 .8rem Orbitron,sans-serif;border:1px solid rgba(180,225,255,.25);padding:6px 16px;margin:0 auto 12px;width:max-content}
    .status-core{display:flex;align-items:center;justify-content:center;gap:28px;flex-wrap:wrap}
    .status-level{font:900 3rem Orbitron,sans-serif;color:#e7f9ff;text-shadow:0 0 18px rgba(103,232,249,.65);line-height:1}
    .status-small{color:#91a8c3;font-size:.7rem;letter-spacing:1px}
    .status-meta b{color:#e7f2ff}.status-meta span{color:#91a8c3}
    .status-bars{display:grid;grid-template-columns:repeat(3,minmax(130px,1fr));gap:8px;margin:15px auto 10px;max-width:820px}
    .status-bar{border:1px solid rgba(180,225,255,.18);padding:8px 10px;border-radius:8px;background:rgba(255,255,255,.025)}
    .status-bar-head{display:flex;justify-content:space-between;font-size:.68rem;color:#dcecff;margin-bottom:4px}
    .status-track{height:6px;border-radius:99px;background:#162132;overflow:hidden}.status-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#67e8f9,#3b82f6);box-shadow:0 0 9px rgba(103,232,249,.55)}
    .status-fill.mp{background:linear-gradient(90deg,#a78bfa,#6366f1)}.status-fill.fatigue{background:linear-gradient(90deg,#fbbf24,#ef4444)}
    .status-stats{display:grid;grid-template-columns:repeat(6,minmax(70px,1fr));gap:7px;max-width:820px;margin:auto}
    .stat-box{border:1px solid rgba(180,225,255,.15);padding:8px;border-radius:8px;text-align:center;background:rgba(255,255,255,.018)}
    .stat-box b{display:block;color:#ecfaff;font:800 1.05rem Orbitron,sans-serif}.stat-box span{font-size:.62rem;color:#8298b3;letter-spacing:1px}
    .character-card{transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease;transform-style:preserve-3d}
    .character-card:hover{transform:perspective(800px) rotateX(2deg) rotateY(-2deg) translateY(-5px);box-shadow:0 18px 35px rgba(0,0,0,.3),0 0 24px rgba(103,232,249,.08)}
    .system-voice{border:1px solid rgba(103,232,249,.28);background:linear-gradient(90deg,rgba(103,232,249,.07),rgba(167,139,250,.07));padding:10px 14px;border-radius:12px;color:#dffaff;margin:10px 0}
    @media(max-width:700px){.status-bars,.status-stats{grid-template-columns:repeat(2,minmax(0,1fr))}.status-level{font-size:2.2rem}}
    @media(prefers-reduced-motion:reduce){.system-status:after{animation:none}.character-card{transition:none}.character-card:hover{transform:none}}
    """,unsafe_allow_html=True)

    st.markdown("""<style>
    .rpg-hero{padding:24px;border-radius:22px;border:1px solid rgba(94,234,212,.28);
    background:linear-gradient(115deg,rgba(10,31,54,.9),rgba(36,18,65,.88));margin-bottom:18px}
    .rpg-kicker{color:#5eead4;font:700 .7rem Orbitron,sans-serif;letter-spacing:2px;text-transform:uppercase}
    .rpg-title{color:#fff;font:800 clamp(1.5rem,3vw,2.2rem) Orbitron,sans-serif;margin-top:5px}
    .rpg-card{padding:14px;border-radius:18px;border:1px solid rgba(126,177,235,.18);background:linear-gradient(160deg,rgba(22,35,61,.7),rgba(10,17,31,.7));height:100%}
    .rpg-card:hover{border-color:rgba(94,234,212,.45);transform:translateY(-3px)}
    .rpg-muted{color:#8ea2bc;font-size:.8rem}
    .rpg-pill{display:inline-block;padding:3px 9px;border-radius:999px;border:1px solid rgba(251,191,36,.35);color:#fde68a;font:700 .65rem Orbitron,sans-serif}
    .rpg-boss{padding:18px;border-radius:22px;border:1px solid rgba(239,68,68,.25);background:linear-gradient(150deg,rgba(34,12,27,.92),rgba(10,15,29,.9))}
    .rpg-hp{height:14px;background:#271823;border-radius:999px;overflow:hidden;border:1px solid rgba(255,255,255,.06)}
    .rpg-hp>div{height:100%;background:linear-gradient(90deg,#ef4444,#f97316);transition:width .5s ease}
    @media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
    </style>""",unsafe_allow_html=True)
    # Status panel inspired by the supplied reference image, driven by real StudyBuddy telemetry.
    total_xp=int(profile["xp"]); streak=int(profile["streak"])
    level=max(1,total_xp//100+1); progress=total_xp%100
    chosen_for_status=next((x for x in CHARACTERS if x["id"]==s["selected_character"]), CHARACTERS[0])
    hp_max=1000+level*60; hp=min(hp_max,700+level*45+streak*18)
    mp_max=350+level*15; mp=min(mp_max,150+level*9+streak*4)
    fatigue=min(100,max(0,20+streak*2))
    base=10+level*2
    stats={"STR":base+streak*2,"VIT":base+level,"AGI":base+streak,"INT":base+level*2,"PER":base+min(30,progress//4)}
    available=max(0,level//5)
    st.markdown(f"""
    <div class="system-status">
      <div class="status-label">STATUS</div>
      <div class="status-core">
        <div><div class="status-level">{level}</div><div class="status-small">LEVEL</div></div>
        <div class="status-meta"><span>JOB:</span> <b>HUNTER</b><br><span>TITLE:</span> <b>{html.escape(chosen_for_status["title"])}</b></div>
      </div>
      <div class="status-bars">
        <div class="status-bar"><div class="status-bar-head"><b>✚ HP</b><span>{hp}/{hp_max}</span></div><div class="status-track"><div class="status-fill" style="width:{hp/hp_max*100:.0f}%"></div></div></div>
        <div class="status-bar"><div class="status-bar-head"><b>♙ MP</b><span>{mp}/{mp_max}</span></div><div class="status-track"><div class="status-fill mp" style="width:{mp/mp_max*100:.0f}%"></div></div></div>
        <div class="status-bar"><div class="status-bar-head"><b>◉ FATIGUE</b><span>{fatigue}/100</span></div><div class="status-track"><div class="status-fill fatigue" style="width:{fatigue}%"></div></div></div>
      </div>
      <div class="status-stats">
        <div class="stat-box"><b>{stats["STR"]}</b><span>STR</span></div>
        <div class="stat-box"><b>{stats["VIT"]}</b><span>VIT</span></div>
        <div class="stat-box"><b>{stats["AGI"]}</b><span>AGI</span></div>
        <div class="stat-box"><b>{stats["INT"]}</b><span>INT</span></div>
        <div class="stat-box"><b>{stats["PER"]}</b><span>PER</span></div>
        <div class="stat-box"><b>{available}</b><span>AVAILABLE</span></div>
      </div>
      <div style="max-width:820px;margin:10px auto 0;color:#6f88a5;font-size:.68rem;letter-spacing:1px;text-align:center">XP {progress}/100 · STREAK {streak} · TELEMETRY SYNCED</div>
    </div>
    """,unsafe_allow_html=True)
    st.markdown('<div class="system-voice">🔊 <b>SYSTEM VOICE</b> — Deep tactical voice · low pitch · slow cadence</div>',unsafe_allow_html=True)
    if st.button("🔊 SYSTEM ONLINE", key="system_voice_button", use_container_width=True):
        components.html("""
        <script>
        const speak = () => {
          const synth = window.parent.speechSynthesis;
          if (!synth) return;
          const u = new SpeechSynthesisUtterance(
            "System online. Hunter status synchronized. " +
            "Level established. Your attributes are ready. " +
            "New mission available. Arise, Hunter."
          );
          const voices = synth.getVoices();
          u.voice = voices.find(v => /en-US|en-GB/i.test(v.lang) && /David|Mark|Daniel|Guy|Alex/i.test(v.name))
                 || voices.find(v => /en/i.test(v.lang)) || null;
          u.rate = 0.76; u.pitch = 0.48; u.volume = 1.0;
          synth.cancel();
          synth.speak(u);
        };
        setTimeout(speak, 120);
        </script>
        """, height=1)

    st.markdown("<div class='rpg-hero'><div class='rpg-kicker'>Study → Power → Raid</div><div class='rpg-title'>Anime RPG Command Center</div><div style='color:#b9c9e3;margin-top:7px'>Real web artwork, study-powered boss battles, character collection and progress analytics.</div></div>",unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    a.metric("Hunter Level",level); b.metric("XP",f"{profile['xp']:,}"); c.metric("Streak",f"🔥 {profile['streak']}"); d.metric("Bosses Defeated",s["defeats"])

    chars,raid,charts,rewards=st.tabs(["👥 Characters","⚔️ Boss Raid","📊 Web Charts","🎁 Rewards"])

    with chars:
        cols=st.columns(4)
        for i,ch in enumerate(CHARACTERS):
            unlocked=level>=ch["unlock"]; selected=s["selected_character"]==ch["id"]
            with cols[i%4]:
                art=fetch_art(ch["image"]) if unlocked else None
                if art: st.image(art,use_container_width=True)
                else: st.markdown(f"<div class='rpg-card' style='height:220px;display:grid;place-items:center;font-size:60px'>{'🔒' if not unlocked else '⚔️'}</div>",unsafe_allow_html=True)
                st.markdown(f"<div class='rpg-card character-card'><b>{html.escape(ch['name'])}</b><div class='rpg-muted'>{html.escape(ch['title'])}</div><span class='rpg-pill'>{ch['rarity']}</span><div class='rpg-muted' style='margin-top:6px'>Power {ch['power']:,}</div><div class='rpg-muted'>{'🟢 Awakened' if unlocked else f'🔒 Level {ch["unlock"]}'}</div></div>",unsafe_allow_html=True)
                if unlocked and st.button("Selected" if selected else "Select",disabled=selected,key=f"rpg_char_{ch['id']}",use_container_width=True):
                    save_character(path,ch["id"]); st.rerun()
        chosen=next(x for x in CHARACTERS if x["id"]==s["selected_character"])
        st.info(f"Active companion: {chosen['name']} · {chosen['title']}")

    with raid:
        choices=[b for b in BOSSES if not boss_state(path,b["id"])["defeated"]]
        if not choices: choices=BOSSES
        names=[b["name"] for b in choices]
        selected_name=st.selectbox("Raid target",names,index=max(0,names.index(current["name"]) if current["name"] in names else 0))
        target=next(b for b in choices if b["name"]==selected_name)
        if target["id"]!=s["active_boss"] and st.button("Set raid target",use_container_width=True):
            with db(path) as con: con.execute("UPDATE anime_rpg_state SET active_boss=?,updated_at=? WHERE id=1",(target["id"],datetime.now().isoformat(timespec="seconds")))
            st.rerun()
        current=target; bs=boss_state(path,current["id"])
        art=fetch_art(current["image"])
        st.markdown("<div class='rpg-boss'>",unsafe_allow_html=True)
        if art: st.image(art,use_container_width=True)
        else: st.warning("This official image could not be loaded. The raid remains playable.")
        hp=int(bs["hp"]); pct=max(0,min(100,round(hp/current["hp"]*100)))
        st.markdown(f"<div class='rpg-kicker'>BOSS RAID · {current['rank']}</div><div class='rpg-title'>{html.escape(current['name'])}</div><div class='rpg-muted'>{html.escape(current['title'])} · Level {current['level']} · Attack {current['attack']} · Defense {current['defense']}</div><div class='rpg-hp' style='margin-top:12px'><div style='width:{pct}%'></div></div><div class='rpg-muted'>HP {hp:,} / {current['hp']:,}</div></div>",unsafe_allow_html=True)
        mins,qcount,qxp=pending_activity(path,s["last_claim_at"])
        dmg=min(current["hp"],damage_for(mins,qcount,qxp,int(profile["streak"])))
        x,y,z=st.columns(3); x.metric("Study minutes ready",mins); y.metric("Completed quests ready",qcount); z.metric("Damage ready",dmg)
        st.markdown(f"<div class='rpg-card'><b>DAMAGE CALCULATION</b><div class='rpg-muted' style='margin-top:6px'>({mins} min × 5) + ({qxp} quest XP ÷ 2) + ({qcount} quests × 10) + ({profile['streak']} streak × 2) = {dmg}</div></div>",unsafe_allow_html=True)
        if bs["defeated"]:
            st.success(f"🏆 {current['name']} already defeated.")
            if st.button("Replay for practice",use_container_width=True):
                replay_boss(path,current["id"]); st.rerun()
        elif st.button(f"⚡ Convert study progress into {dmg} damage",type="primary",disabled=dmg<=0,use_container_width=True):
            applied,new_hp,won=claim_damage(path,current["id"],dmg,mins,qcount)
            if applied:
                st.session_state["rpg_damage"]=applied
                if won:
                    finish_boss(path,current,award_xp)
                    st.session_state["rpg_win"]=current["name"]
            st.rerun()
        if st.session_state.pop("rpg_damage",None):
            st.toast("⚡ Boss damaged from your actual study progress!",icon="💥")
        if st.session_state.pop("rpg_win",None):
            st.balloons()
            st.success(f"🏆 BOSS DEFEATED · {current['name']} · +{current['xp']} XP · +{current['coins']} coins · +{current['fragments']} fragment · +1 chest")
        if ask_ai_fn and st.button("🤖 Ask Gemma for your raid strategy",use_container_width=True):
            try:
                reply=ask_ai_fn(f"Give a concise study-first raid plan. Player level {level}, XP {profile['xp']}, streak {profile['streak']}. Boss {current['name']} has {hp}/{current['hp']} HP. Recommend 3 study actions.")
                st.write(reply)
            except Exception as exc: st.error(str(exc))

    with charts:
        st.caption("Charts use your real StudyBuddy database history; no placeholder statistics.")
        with db(path) as con:
            xr=con.execute("SELECT substr(happened_at,1,10) d,SUM(amount) xp FROM xp_log GROUP BY d ORDER BY d DESC LIMIT 14").fetchall()
            fr=con.execute("SELECT substr(started_at,1,10) d,SUM(minutes) minutes FROM focus_sessions WHERE completed=1 GROUP BY d ORDER BY d DESC LIMIT 14").fetchall()
            sr=con.execute("SELECT COALESCE(subject,'General') s,SUM(completed) done,COUNT(*) total FROM quests GROUP BY s ORDER BY done DESC,total DESC LIMIT 8").fetchall()
            br=con.execute("SELECT substr(happened_at,1,10) d,SUM(amount) damage FROM anime_raid_log WHERE event='damage' GROUP BY d ORDER BY d DESC LIMIT 14").fetchall()
        if xr:
            st.subheader("XP trend · last recorded days"); st.line_chart([{"day":r["d"],"XP":int(r["xp"] or 0)} for r in reversed(xr)],x="day",y="XP")
        else: st.info("Complete a quest or focus session to populate the XP chart.")
        if fr:
            st.subheader("Study time"); st.bar_chart([{"day":r["d"],"Minutes":int(r["minutes"] or 0)} for r in reversed(fr)],x="day",y="Minutes")
        else: st.info("Complete a focus session to populate study-time charts.")
        if br:
            st.subheader("Boss damage"); st.line_chart([{"day":r["d"],"Damage":int(r["damage"] or 0)} for r in reversed(br)],x="day",y="Damage")
        if sr:
            st.subheader("Subject performance"); st.bar_chart([{"subject":r["s"],"Completed":int(r["done"] or 0)} for r in sr],x="subject",y="Completed")

    with rewards:
        s=state(path)
        a,b,c,d=st.columns(4); a.metric("Coins",s["coins"]); b.metric("Fragments",s["fragments"]); c.metric("Chests",s["chests"]); d.metric("Boss defeats",s["defeats"])
        with db(path) as con: logs=con.execute("SELECT * FROM anime_raid_log ORDER BY id DESC LIMIT 12").fetchall()
        for r in logs:
            st.markdown(f"<div class='rpg-card' style='margin:7px 0'><b>{html.escape(r['event'].title())}</b> · {r['amount']}<div class='rpg-muted'>{html.escape(r['note'])} · {r['happened_at'][:16].replace('T',' · ')}</div></div>",unsafe_allow_html=True)
