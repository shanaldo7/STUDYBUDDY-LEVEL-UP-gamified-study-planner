// StudyBuddy Motion JS — used by the unlock ceremony iframe.
// Kept framework-free because Streamlit does not mount an Angular component tree.
(function(){
  const root=document.querySelector('[data-sb-motion]');
  if(!root) return;
  const canvas=document.createElement('canvas');
  canvas.style.cssText='position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:3';
  root.appendChild(canvas);
  const ctx=canvas.getContext('2d');
  let particles=[],raf=0,start=performance.now();
  function resize(){canvas.width=Math.max(1,root.clientWidth*devicePixelRatio);canvas.height=Math.max(1,root.clientHeight*devicePixelRatio);ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);}
  function seed(){particles=Array.from({length:34},()=>({x:Math.random()*root.clientWidth,y:root.clientHeight*.55+Math.random()*root.clientHeight*.45,vx:(Math.random()-.5)*1.8,vy:-Math.random()*3.5-1.2,r:Math.random()*2.5+.7,a:1}));}
  function frame(t){
    const elapsed=t-start, w=root.clientWidth,h=root.clientHeight;
    ctx.clearRect(0,0,w,h);
    particles.forEach(p=>{p.x+=p.vx;p.y+=p.vy;p.vy+=.018;p.a-=.006;ctx.beginPath();ctx.fillStyle='rgba(103,232,249,'+Math.max(0,p.a)+')';ctx.shadowBlur=12;ctx.shadowColor='#67e8f9';ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fill();});
    particles=particles.filter(p=>p.a>0&&p.y<h+20);
    if(particles.length<18) seed();
    if(elapsed<2600) raf=requestAnimationFrame(frame); else ctx.clearRect(0,0,w,h);
  }
  resize();seed();requestAnimationFrame(frame);
  window.addEventListener('resize',resize,{passive:true});
  setTimeout(()=>cancelAnimationFrame(raf),3000);
})();