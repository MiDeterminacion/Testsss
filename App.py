import streamlit as st

st.set_page_config(page_title="Worm estilo 'espina + patas'", layout="wide")
st.title("Gusano/espinazo con patas articuladas (toca o arrastra)")

html_code = """
<style>
  #wrap{
    width:100%; height:80vh; background:#000;
    border-radius:16px; overflow:hidden; display:flex;
  }
  canvas{ width:100%; height:100%; display:block; touch-action:none; }
  .hint{ color:#aaa; text-align:center; margin-top:.5rem; font:14px system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;}
</style>

<div id="wrap"><canvas id="cv"></canvas></div>
<div class="hint">Toca o arrastra dentro del lienzo. (Funciona en móvil y desktop.)</div>

<script>
// ================= Canvas con escala de dispositivo =================
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

// ================= Modelo IK estable (cabeza -> cola) =================
class Node{ constructor(x,y,len){ this.x=x; this.y=y; this.len=len; } }

class Worm {
  constructor(n, x, y, params){
    this.p = params;
    // 0 = cabeza ... N-1 = cola
    this.nodes = [];
    let L = this.p.segLenStart;
    for(let i=0;i<n;i++){
      this.nodes.push(new Node(x,y, Math.max(this.p.segLenMin, L)));
      L *= this.p.segLenDecay;
    }
    this.tx = x; this.ty = y;             // objetivo suavizado
  }

  step(targetX, targetY){
    // suaviza objetivo para evitar tirones
    this.tx += (targetX - this.tx) * this.p.targetLerp;
    this.ty += (targetY - this.ty) * this.p.targetLerp;

    // cabeza al objetivo
    this.nodes[0].x = this.tx; this.nodes[0].y = this.ty;

    // cola mantiene distancia fija → evita “nudos”
    for(let i=1;i<this.nodes.length;i++){
      const prev = this.nodes[i-1], cur = this.nodes[i];
      let dx = cur.x - prev.x, dy = cur.y - prev.y;
      const dist = Math.hypot(dx, dy) || 1e-6;
      const need = cur.len;
      const s = need / dist;
      cur.x = prev.x + dx * s;
      cur.y = prev.y + dy * s;
    }
  }

  draw(ctx){
    // línea espinal
    ctx.lineWidth = this.p.spineWidth;
    ctx.strokeStyle = this.p.colMain;
    ctx.beginPath();
    ctx.moveTo(this.nodes[0].x, this.nodes[0].y);
    for(let i=1;i<this.nodes.length;i++) ctx.lineTo(this.nodes[i].x, this.nodes[i].y);
    ctx.stroke();

    // costillas cortas en cada segmento
    ctx.lineWidth = this.p.ribWidth;
    ctx.strokeStyle = this.p.colRibs;
    for(let i=1;i<this.nodes.length;i++){
      const a = this.nodes[i-1], b = this.nodes[i];
      const ang = Math.atan2(b.y - a.y, b.x - a.x);
      const nx = Math.cos(ang + Math.PI/2), ny = Math.sin(ang + Math.PI/2);
      const cx = b.x, cy = b.y;
      const len = Math.max(this.p.ribMin, b.len * this.p.ribScale);
      // una costilla por lado (como en el video)
      ctx.beginPath();
      ctx.moveTo(cx, cy); ctx.lineTo(cx + nx*len, cy + ny*len);
      ctx.moveTo(cx, cy); ctx.lineTo(cx - nx*len, cy - ny*len);
      ctx.stroke();
    }

    // patas articuladas cada N segmentos, alternando lados
    ctx.lineWidth = this.p.legWidth;
    ctx.strokeStyle = this.p.colLegs;
    for(let i=this.p.legEvery; i<this.nodes.length-1; i+=this.p.legEvery){
      const a = this.nodes[i-1], b = this.nodes[i];
      const ang = Math.atan2(b.y - a.y, b.x - a.x);
      const side = (Math.floor(i/this.p.legEvery) % 2 === 0) ? 1 : -1; // alterna
      this.drawLeg(ctx, b.x, b.y, ang, side, b.len);
    }

    // puntito cabeza
    ctx.fillStyle = this.p.colHead;
    ctx.beginPath();
    ctx.arc(this.nodes[0].x, this.nodes[0].y, this.p.headRadius, 0, Math.PI*2);
    ctx.fill();
  }

  // pata de dos tramos + flecha, inspirada en el diseño del clip
  drawLeg(ctx, x, y, spineAngle, side, baseLen){
    const nx = Math.cos(spineAngle + side*Math.PI/2);
    const ny = Math.sin(spineAngle + side*Math.PI/2);

    // longitudes relativas
    const L1 = Math.max(12, baseLen * this.p.legL1);
    const L2 = Math.max(10, baseLen * this.p.legL2);
    const tip = Math.max(6,  baseLen * this.p.legTip);

    // primer tramo (un poco inclinado hacia atrás)
    const a1 = spineAngle + side*(Math.PI/2 - this.p.legAng1);
    const x1 = x + Math.cos(a1)*L1, y1 = y + Math.sin(a1)*L1;

    // segundo tramo (genera codo)
    const a2 = a1 + side*this.p.legAng2;
    const x2 = x1 + Math.cos(a2)*L2, y2 = y1 + Math.sin(a2)*L2;

    ctx.beginPath();
    ctx.moveTo(x,y); ctx.lineTo(x1,y1); ctx.lineTo(x2,y2);
    ctx.stroke();

    // flechita en la punta
    const ah = this.p.arrowAng;
    const aL = tip;
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 + Math.cos(a2 + Math.PI - ah)*aL, y2 + Math.sin(a2 + Math.PI - ah)*aL);
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 + Math.cos(a2 + Math.PI + ah)*aL, y2 + Math.sin(a2 + Math.PI + ah)*aL);
    ctx.stroke();
  }
}

// ================= Entrada táctil/mouse =================
const mouse = {x: 180, y: 160};
let active = false;

function setFrom(eX,eY){
  const r = canvas.getBoundingClientRect();
  mouse.x = eX - r.left; mouse.y = eY - r.top;
}

canvas.addEventListener('pointerdown', e => { active=true; setFrom(e.clientX,e.clientY); canvas.setPointerCapture?.(e.pointerId); e.preventDefault(); }, {passive:false});
canvas.addEventListener('pointermove', e => { if(!active && e.pointerType==='mouse' && e.buttons===0) return; setFrom(e.clientX,e.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener('pointerup',   () => { active=false; }, {passive:false});
canvas.addEventListener('touchstart', e => { const t=e.touches[0]; setFrom(t.clientX,t.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener('touchmove',  e => { const t=e.touches[0]; setFrom(t.clientX,t.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener('click', e => setFrom(e.clientX,e.clientY));
window.addEventListener('pointermove', e => { if(active) setFrom(e.clientX,e.clientY); }, {passive:true});

// ================= Parámetros de estilo =================
const params = {
  // Cinemática
  targetLerp: 0.28,       // 0..1 seguimiento; más alto = más pegado al dedo
  segLenStart: 16,        // longitud del primer segmento
  segLenMin: 6,
  segLenDecay: 0.94,

  // Estética
  colMain: "#E6E6E6",
  colRibs: "#D8D8D8",
  colLegs: "#E6E6E6",
  colHead: "#FFFFFF",
  spineWidth: 2,
  ribWidth: 1,
  legWidth: 1.5,
  ribScale: 0.32,         // tamaño de costillas vs. segmento
  ribMin: 3,

  // Patas
  legEvery: 6,            // cada cuántos segmentos aparece una pata
  legL1: 1.3,             // longitud tramo 1 relativo al segmento
  legL2: 1.1,             // longitud tramo 2 relativo al segmento
  legTip: 0.55,           // tamaño de la flecha en la punta
  legAng1: Math.PI/6,     // inclinación del primer tramo respecto a la normal
  legAng2: Math.PI/5,     // giro del segundo tramo respecto al primero
  arrowAng: Math.PI/7,    // ángulo de las aletas de la flecha

  // Cabeza
  headRadius: 2.2
};

// ================= Animación =================
const worm = new Worm(44, mouse.x, mouse.y, params);

function loop(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  worm.step(mouse.x, mouse.y);
  worm.draw(ctx);
  requestAnimationFrame(loop);
}
loop();
</script>
"""

st.components.v1.html(html_code, height=650)
