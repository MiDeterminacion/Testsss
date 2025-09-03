import streamlit as st

st.set_page_config(page_title="Worm IK Preciso", layout="wide")
st.title("Worm/cola articulada con seguimiento preciso (toca o arrastra)")

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
<div class="hint">Toca o arrastra dentro del lienzo. Movimiento estable y preciso.</div>

<script>
// ---------- Canvas con escala de dispositivo ----------
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

// ---------- Modelo IK: cabeza -> cola mantiene distancias ----------
class Node{ constructor(x,y,len){ this.x=x; this.y=y; this.len=len; } }

class Worm {
  constructor(n, x, y){
    // orden: 0 = cabeza ... N-1 = cola
    this.nodes = [];
    // longitudes más cortas para evitar cruces
    let L = 14;                               // longitud inicial
    for(let i=0;i<n;i++){
      this.nodes.push(new Node(x,y, Math.max(6, L)));
      L *= 0.94;                              // reduce gradualmente
    }
    // parámetros de control
    this.lerp = 0.25;                         // suavizado del objetivo (0-1)
    this.spineEvery = 2;                      // frecuencia de espinas
  }

  step(targetX, targetY){
    // objetivo suavizado para que no “patine”
    if(!this.tx){ this.tx = targetX; this.ty = targetY; }
    this.tx += (targetX - this.tx) * this.lerp;
    this.ty += (targetY - this.ty) * this.lerp;

    // 1) cabeza al objetivo
    const head = this.nodes[0];
    head.x = this.tx; head.y = this.ty;

    // 2) cada segmento mantiene distancia al anterior (resuelve nudos)
    for(let i=1;i<this.nodes.length;i++){
      const prev = this.nodes[i-1], cur = this.nodes[i];
      let dx = cur.x - prev.x, dy = cur.y - prev.y;
      const dist = Math.hypot(dx, dy) || 1e-6;
      const need = cur.len;
      // coloca el segmento sobre la circunferencia a distancia 'need'
      const s = need / dist;
      cur.x = prev.x + dx * s;
      cur.y = prev.y + dy * s;
    }
  }

  draw(ctx){
    // línea central
    ctx.lineWidth = 2; ctx.strokeStyle = "#e5e5e5";
    ctx.beginPath();
    ctx.moveTo(this.nodes[0].x, this.nodes[0].y);
    for(let i=1;i<this.nodes.length;i++) ctx.lineTo(this.nodes[i].x, this.nodes[i].y);
    ctx.stroke();

    // espinas laterales (opcionales y estables)
    ctx.lineWidth = 1; ctx.strokeStyle = "#cfcfcf";
    for(let i=this.spineEvery;i<this.nodes.length;i+=this.spineEvery){
      const a = this.nodes[i-1], b = this.nodes[i];
      const ang = Math.atan2(b.y - a.y, b.x - a.x);
      const nx = Math.cos(ang + Math.PI/2), ny = Math.sin(ang + Math.PI/2);
      const s = Math.max(3, b.len*0.35);
      ctx.beginPath();
      ctx.moveTo(b.x, b.y); ctx.lineTo(b.x + nx*s, b.y + ny*s);
      ctx.moveTo(b.x, b.y); ctx.lineTo(b.x - nx*s, b.y - ny*s);
      ctx.stroke();
    }

    // puntito de la cabeza para referencia
    ctx.fillStyle = "#fff"; ctx.beginPath();
    ctx.arc(this.nodes[0].x, this.nodes[0].y, 2.2, 0, Math.PI*2); ctx.fill();
  }
}

// ---------- Entrada táctil/mouse precisa ----------
const mouse = {x: 120, y: 120};
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

// ---------- Animación ----------
const worm = new Worm(36, mouse.x, mouse.y);

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
