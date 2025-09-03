import streamlit as st

st.set_page_config(page_title="Worm con patas caminando", layout="wide")
st.title("Gusano/espinazo con patas que caminan (toca o arrastra)")

html_code = """
<style>
  #wrap{ width:100%; height:80vh; background:#000; border-radius:16px; overflow:hidden; display:flex; }
  canvas{ width:100%; height:100%; display:block; touch-action:none; }
  .hint{ color:#aaa; text-align:center; margin-top:.5rem; font:14px system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
</style>

<div id="wrap"><canvas id="cv"></canvas></div>
<div class="hint">Toca o arrastra dentro del lienzo. Las patas caminan en sincronía.</div>

<script>
// ================= Canvas (DPR) =================
const wrap = document.getElementById('wrap');
const canvas = document.getElementById('cv');
const ctx = canvas.getContext('2d');

function fit(){
  const r = wrap.getBoundingClientRect();
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const w = Math.max(400, r.width|0), h = Math.max(300, r.height|0);
  canvas.style.width = w+"px"; canvas.style.height = h+"px";
  canvas.width = (w*dpr)|0; canvas.height = (h*dpr)|0;
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
fit(); requestAnimationFrame(fit); addEventListener('resize', fit);

// ================= IK estable =================
class Node{ constructor(x,y,len){ this.x=x; this.y=y; this.len=len; } }

class Worm {
  constructor(n, x, y, p){
    this.p = p;
    this.nodes = [];
    let L = p.segLenStart;
    for(let i=0;i<n;i++){
      this.nodes.push(new Node(x,y, Math.max(p.segLenMin, L)));
      L *= p.segLenDecay;
    }
    this.tx = x; this.ty = y;
    this.prevHead = {x, y};
    this.walkPhase = 0; // fase global de marcha
  }

  step(targetX, targetY, dt){
    // suaviza objetivo
    this.tx += (targetX - this.tx) * this.p.targetLerp;
    this.ty += (targetY - this.ty) * this.p.targetLerp;

    // cabeza al objetivo
    const head = this.nodes[0];
    head.x = this.tx; head.y = this.ty;

    // velocidad para modular frecuencia de paso
    const vx = head.x - this.prevHead.x, vy = head.y - this.prevHead.y;
    const speed = Math.hypot(vx, vy);
    this.prevHead.x = head.x; this.prevHead.y = head.y;

    // IK cola
    for(let i=1;i<this.nodes.length;i++){
      const prev = this.nodes[i-1], cur = this.nodes[i];
      let dx = cur.x - prev.x, dy = cur.y - prev.y;
      const dist = Math.hypot(dx, dy) || 1e-6;
      const s = cur.len / dist;
      cur.x = prev.x + dx * s;
      cur.y = prev.y + dy * s;
    }

    // avanzar fase de marcha (más rápido si se mueve más)
    const freq = this.p.stepFreqBase + this.p.stepFreqGain * Math.min(speed, 30);
    this.walkPhase += freq * dt;  // dt en segundos
  }

  draw(ctx, t){
    // espina
    ctx.lineWidth = this.p.spineWidth; ctx.strokeStyle = this.p.colMain;
    ctx.beginPath(); ctx.moveTo(this.nodes[0].x, this.nodes[0].y);
    for(let i=1;i<this.nodes.length;i++) ctx.lineTo(this.nodes[i].x, this.nodes[i].y);
    ctx.stroke();

    // costillas
    ctx.lineWidth = this.p.ribWidth; ctx.strokeStyle = this.p.colRibs;
    for(let i=1;i<this.nodes.length;i++){
      const a = this.nodes[i-1], b = this.nodes[i];
      const ang = Math.atan2(b.y - a.y, b.x - a.x);
      const nx = Math.cos(ang + Math.PI/2), ny = Math.sin(ang + Math.PI/2);
      const len = Math.max(this.p.ribMin, b.len * this.p.ribScale);
      ctx.beginPath();
      ctx.moveTo(b.x, b.y); ctx.lineTo(b.x + nx*len, b.y + ny*len);
      ctx.moveTo(b.x, b.y); ctx.lineTo(b.x - nx*len, b.y - ny*len);
      ctx.stroke();
    }

    // patas que CAMINAN (dos tramos + flecha)
    ctx.lineWidth = this.p.legWidth; ctx.strokeStyle = this.p.colLegs;
    for(let i=this.p.legEvery; i<this.nodes.length-1; i+=this.p.legEvery){
      const a = this.nodes[i-1], b = this.nodes[i];
      const spineAng = Math.atan2(b.y - a.y, b.x - a.x);
      const side = (Math.floor(i/this.p.legEvery) % 2 === 0) ? 1 : -1; // alterna
      // fase local: alterna por lado y se desfasa a lo largo del cuerpo (onda)
      const localPhase = this.walkPhase
                       + (side===1 ? 0 : Math.PI)               // izquierda vs derecha
                       + (i * this.p.legPhaseAlong);            // desfase a lo largo

      this.drawWalkingLeg(ctx, b.x, b.y, spineAng, side, b.len, localPhase);
    }

    // cabeza
    ctx.fillStyle = this.p.colHead;
    ctx.beginPath(); ctx.arc(this.nodes[0].x, this.nodes[0].y, this.p.headRadius, 0, Math.PI*2); ctx.fill();
  }

  drawWalkingLeg(ctx, x, y, spineAng, side, baseLen, phase){
    // oscilaciones (ciclo de marcha)
    const stepSwing = Math.sin(phase);      // -1..1
    const stepLift  = Math.max(0, Math.sin(phase + Math.PI/2)); // 0..1 (fase de vuelo)

    // ángulos base relativos a la normal de la espina
    const aNormal = spineAng + side*(Math.PI/2);

    // tramo 1: oscila hacia adelante/atrás (swing)
    const a1 = aNormal + side*(this.p.legAng1 + this.p.walkSwingAmp * stepSwing);
    const L1 = Math.max(12, baseLen * this.p.legL1);

    const x1 = x + Math.cos(a1)*L1, y1 = y + Math.sin(a1)*L1;

    // tramo 2: acompaña con leve cambio y “levanta” en la fase de vuelo
    const a2 = a1 + side*(this.p.legAng2 + this.p.walkKneeAmp * stepSwing);
    const L2 = Math.max(10, baseLen * (this.p.legL2 + this.p.walkLiftScale * stepLift));

    const x2 = x1 + Math.cos(a2)*L2, y2 = y1 + Math.sin(a2)*L2;

    // dibujar
    ctx.beginPath();
    ctx.moveTo(x,y); ctx.lineTo(x1,y1); ctx.lineTo(x2,y2);
    ctx.stroke();

    // flecha al final
    const ah = this.p.arrowAng, tip = Math.max(6, baseLen * this.p.legTip);
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 + Math.cos(a2 + Math.PI - ah)*tip, y2 + Math.sin(a2 + Math.PI - ah)*tip);
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 + Math.cos(a2 + Math.PI + ah)*tip, y2 + Math.sin(a2 + Math.PI + ah)*tip);
    ctx.stroke();
  }
}

// ================= Entrada táctil/mouse =================
const mouse = {x: 200, y: 180};
let active = false;

function setFrom(eX,eY){ const r = canvas.getBoundingClientRect(); mouse.x = eX - r.left; mouse.y = eY - r.top; }

canvas.addEventListener('pointerdown', e => { active=true; setFrom(e.clientX,e.clientY); canvas.setPointerCapture?.(e.pointerId); e.preventDefault(); }, {passive:false});
canvas.addEventListener('pointermove', e => { if(!active && e.pointerType==='mouse' && e.buttons===0) return; setFrom(e.clientX,e.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener('pointerup',   () => { active=false; }, {passive:false});
canvas.addEventListener('touchstart', e => { const t=e.touches[0]; setFrom(t.clientX,t.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener('touchmove',  e => { const t=e.touches[0]; setFrom(t.clientX,t.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener('click', e => setFrom(e.clientX,e.clientY));
window.addEventListener('pointermove', e => { if(active) setFrom(e.clientX,e.clientY); }, {passive:true});

// ================= Parámetros =================
const P = {
  // cinemática
  targetLerp: 0.28,
  segLenStart: 16, segLenMin: 6, segLenDecay: 0.94,

  // marcha
  stepFreqBase: 3.0/1000,   // ciclos/ms mínima
  stepFreqGain: 0.06/1000,  // + con la velocidad
  legPhaseAlong: 0.5,       // desfase a lo largo del cuerpo (onda)
  walkSwingAmp: 0.55,       // amplitud de swing
  walkKneeAmp:  0.25,       // “rodilla”
  walkLiftScale: 0.15,      // alarga tramo 2 en fase de vuelo

  // estilo
  colMain:"#E6E6E6", colRibs:"#D8D8D8", colLegs:"#E6E6E6", colHead:"#FFFFFF",
  spineWidth:2, ribWidth:1, legWidth:1.5,
  ribScale:0.32, ribMin:3,
  legEvery:6, legL1:1.25, legL2:1.05, legTip:0.55, legAng1:Math.PI/7, legAng2:Math.PI/5,
  arrowAng:Math.PI/7, headRadius:2.2
};

// ================= Animación =================
const worm = new Worm(44, mouse.x, mouse.y, P);
let last = performance.now();

function loop(now){
  const dt = (now - last) / 1000; last = now; // segundos
  ctx.clearRect(0,0,canvas.width,canvas.height);
  worm.step(mouse.x, mouse.y, dt);
  worm.draw(ctx, now/1000);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);
</script>
"""

st.components.v1.html(html_code, height=650)
