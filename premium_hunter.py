"""Additive premium hunter UX for StudyBuddy."""
import html
import os
import json
import urllib.request
import urllib.error
import streamlit as st
import streamlit.components.v1 as components

def inject_premium_css():
    st.markdown("""<style>
.ph-shell{padding:22px;border:1px solid rgba(103,232,249,.22);border-radius:24px;background:radial-gradient(circle at 90% 10%,rgba(167,139,250,.16),transparent 28%),linear-gradient(145deg,rgba(9,16,32,.94),rgba(25,13,45,.86));box-shadow:0 24px 65px rgba(0,0,0,.34)}
.ph-kicker{font:800 .62rem Orbitron,sans-serif;letter-spacing:2px;color:#67e8f9;text-transform:uppercase}.ph-title{font:800 clamp(1.35rem,3vw,2.1rem) Orbitron,sans-serif;color:#fff;margin:5px 0}.ph-copy{color:#91a4bd;font-size:.82rem}.ph-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}.ph-card{padding:15px;border:1px solid rgba(116,181,255,.18);border-radius:17px;background:linear-gradient(145deg,rgba(18,30,53,.72),rgba(7,12,25,.72));transition:transform .22s,border-color .22s}.ph-card:hover{transform:translateY(-3px);border-color:rgba(103,232,249,.38)}.ph-node{padding:16px;border-radius:18px;border:1px solid rgba(126,177,235,.17);background:linear-gradient(145deg,rgba(15,27,50,.88),rgba(9,13,27,.86));min-height:145px}.ph-node.locked{opacity:.52}.ph-node.done{border-color:rgba(74,222,128,.34)}.ph-node.next{border-color:rgba(103,232,249,.55)}.ph-track{height:7px;background:#17243a;border-radius:99px;overflow:hidden;margin-top:10px}.ph-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#22d3ee,#8b5cf6)}.ph-chip{display:inline-flex;padding:5px 8px;border:1px solid rgba(255,255,255,.08);border-radius:999px;background:rgba(2,7,18,.45);color:#bcd0e8;font-size:.62rem}@media(max-width:800px){.ph-grid{grid-template-columns:1fr}}@media(prefers-reduced-motion:reduce){.ph-card:hover{transform:none}}
</style>""",unsafe_allow_html=True)

def _esc(v): return html.escape(str(v or ""))

def render_offline_console():
    components.html("""<div id="ph-status" style="font:600 13px Inter,Arial;color:#b9c9e3;padding:7px 0"></div><script>(function(){const e=document.getElementById('ph-status');function r(){e.innerHTML=navigator.onLine?'<span style="color:#86efac">● Online</span> · local safety queue enabled':'<span style="color:#fda4af">● Offline — progress is safely saved on this device.</span>'}addEventListener('online',r);addEventListener('offline',r);r()})();</script>""",height=32,scrolling=False)

def render_dungeon_map(db,navigate=None):
    with db() as con: rows=con.execute("SELECT subject,COUNT(*) total,SUM(CASE WHEN completed=1 THEN 1 ELSE 0 END) done FROM quests GROUP BY COALESCE(subject,'General') ORDER BY subject").fetchall()
    nodes=[(str(r['subject'] or 'General'),int(r['total'] or 0),int(r['done'] or 0)) for r in rows][:12] or [('First Awakening',1,0)]
    st.markdown("<div class='ph-shell'><div class='ph-kicker'>Hunter Route · Knowledge Frontier</div><div class='ph-title'>Interactive Dungeon Map</div><div class='ph-copy'>Regions are derived from your existing study missions. Existing quest and dungeon data remains authoritative.</div></div>",unsafe_allow_html=True)
    cols=st.columns(3)
    for i,(subject,total,done) in enumerate(nodes):
        pct=int(100*done/max(1,total)); locked=i>0 and int(100*nodes[i-1][2]/max(1,nodes[i-1][1]))<50; cls='locked' if locked else ('done' if pct>=100 else 'next'); icon='🔒' if locked else ('✦' if pct>=100 else '◇')
        with cols[i%3]:
            st.markdown(f"<div class='ph-node {cls}'><div style='font-size:1.45rem'>{icon}</div><b>{_esc(subject)}</b><div style='color:#7386a1;font-size:.68rem;margin-top:4px'>{'LOCKED' if locked else 'OPEN'} · {done}/{total} missions</div><div class='ph-track'><div class='ph-fill' style='width:{pct}%'></div></div><div style='color:#7386a1;font-size:.68rem;margin-top:4px'>{pct}% route progress</div></div>",unsafe_allow_html=True)
            if not locked and st.button('Enter region',key=f'ph_map_{i}',use_container_width=True) and navigate: navigate('⚔️ Dungeon Battles')

def render_system_guide(db,ai_callback=None):
    with db() as con:
        weak=con.execute("SELECT subject,COUNT(*) misses FROM mastery_events WHERE event_type IN ('wrong','incorrect','miss') GROUP BY subject ORDER BY misses DESC LIMIT 5").fetchall()
    st.markdown("<div class='ph-shell'><div class='ph-kicker'>System Guide · Adaptive Mentor</div><div class='ph-title'>Your next study move</div><div class='ph-copy'>Hint-first guidance and weak-topic analysis. Quiz answers are never auto-submitted here.</div></div>",unsafe_allow_html=True)
    if weak:
        for r in weak: st.markdown(f"<div class='ph-card'><b>{_esc(r['subject'] or 'General')}</b> <span class='ph-chip'>{int(r['misses'])} missed attempts</span><div style='color:#7386a1;font-size:.7rem'>Train this topic before increasing difficulty.</div></div>",unsafe_allow_html=True)
    else: st.info('Complete a few quizzes and the System Guide will identify weak topics.')
    prompt=st.text_input('Ask the System Guide',placeholder='Explain my weakest topic simply…',key='ph_guide_prompt')
    hint=st.checkbox('Hint mode — never reveal the final answer',True,key='ph_hint_mode')
    if st.button('Consult the Guide',type='primary',key='ph_consult'):
        if not prompt.strip(): st.warning('Enter a topic or study question first.')
        elif ai_callback is None: st.info('AI is unavailable. StudyBuddy remains usable.')
        else:
            instruction=('You are StudyBuddy System Guide. Explain simply. '+('Give only a hint/reasoning path, never the final answer.' if hint else 'Only answer after the student has attempted it.')+f' Request: {prompt.strip()}')
            try:
                with st.spinner('The System Guide is analyzing…'): answer=ai_callback(instruction,'You are a concise study mentor. Never invent facts.')
                st.markdown(f"<div class='ph-card'><b>Guide transmission</b><br>{_esc(answer).replace(chr(10),'<br>')}</div>",unsafe_allow_html=True); st.toast('Guide response ready',icon='✦')
            except Exception as exc: st.error(f'AI unavailable: {exc}')

def render_voice_study_mode():
    components.html("""<div style="font-family:Inter,Arial;color:#e6eefb;background:linear-gradient(145deg,rgba(9,16,32,.92),rgba(25,13,45,.82));border:1px solid rgba(103,232,249,.22);border-radius:20px;padding:18px"><b style="color:#67e8f9;letter-spacing:2px">VOICE STUDY MODE</b><h2 style="color:white;margin:5px 0">Hunter Voice Console</h2><p style="color:#91a4bd;font-size:13px">Speech is processed by your browser. The detected transcript is shown before a command is mapped.</p><button id="listen">🎙 Start listening</button> <button id="speak">🔊 Speak sample</button><button id="stop">Stop</button><div id="heard" style="margin-top:14px;padding:12px;background:#080e1d;border-radius:12px;min-height:25px">Waiting for microphone input…</div><div id="mapped" style="margin-top:8px;color:#67e8f9"></div><small style="color:#71839f">Commands: start focus session · pause timer · repeat question · show hint · submit answer · open dungeon map. Keyboard/buttons remain the fallback.</small><script>(function(){const R=window.SpeechRecognition||window.webkitSpeechRecognition,h=document.getElementById('heard'),m=document.getElementById('mapped'),map={'start focus session':'Start Focus Session','pause timer':'Pause Timer','repeat question':'Repeat Question','show hint':'Show Hint','submit answer':'Submit Answer','open dungeon map':'Open Dungeon Map'};let r=null;if(R){r=new R();r.continuous=false;r.interimResults=false;r.lang='en-US';r.onresult=e=>{const t=e.results[0][0].transcript;h.textContent=t;const k=Object.keys(map).find(x=>t.toLowerCase().includes(x));m.textContent=k?'Mapped command: '+map[k]:'Transcript only — no command mapped.'}}document.getElementById('listen').onclick=()=>{if(!r){h.textContent='Speech recognition is unavailable in this browser.';return}try{r.start()}catch(e){}};document.getElementById('stop').onclick=()=>{try{r&&r.stop()}catch(e){}};document.getElementById('speak').onclick=()=>{const u=new SpeechSynthesisUtterance('System Guide online. Choose your next study mission.');speechSynthesis.cancel();speechSynthesis.speak(u)}})()</script></div>""",height=330,scrolling=False)

def render_sound_settings():
    with st.expander('🔊 Sound & voice settings'):
        st.checkbox('Voice narration',True,key='ph_voice_on'); st.slider('Voice volume',0,100,80,5,key='ph_volume'); st.slider('Voice speed',60,150,100,5,key='ph_speed'); st.checkbox('Battle sounds',False,key='ph_battle_sounds'); st.caption('Ambient sound is off by default.')
