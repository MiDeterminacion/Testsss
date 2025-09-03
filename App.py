import streamlit as st

st.set_page_config(page_title="Worm/Nodes Demo", layout="wide")
st.title("Animación tipo 'worm' (toca o arrastra)")

html_code = """
<style>
  body { margin:0; }
  #wrap {
    width:100%;
    height:80vh;
    background:#000;
    display:flex;
    align-items:center;
    justify-content:center;
    border-radius:16px;
    overflow:hidden;
  }
  canvas {
    display:block; width:100%; height:100%;
    touch-action: none;          /* vital en móvil */
    -ms-touch-action: none;
  }
  .hint{
    color:#aaa; text-align:center; font:14px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    margin-top:.5rem;
  }
</style>

<div id="wrap">
  <canvas id="cv"></canvas>
</div>
<div class="hint">Toca o arrastra dentro del lienzo (si no responde, toca otra vez).</div>

<script>
// ---------- Canvas con DPI correcto ----------
const wrap = document.getElementById("wrap");
const canvas = document.getElementById("cv");
const ctx = canvas.getContext("2d");

function fitCanvasToParent() {
  const r = wrap.getBoundingClientRect();
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  const cssW = Math.max(400, Math.floor(r.width));
  const cssH = Math.max(300, Math.floor(r.height));
  canvas.style.width = cssW + "px";
  canvas.style.height = cssH + "px";
  canvas.width  = Math.floor(cssW * dpr);
  canvas.height = Math.floor(cssH * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0); // escala el dibujo -> coords en CSS px
}
fitCanvasToParent();
// a veces el tamaño llega tarde en iframe; ajusta un frame después:
requestAnimationFrame(fitCanvasToParent);
window.addEventListener("resize", fitCanvasToParent);

// ---------- Lógica del “worm” ----------
class Node {
  constructor(x, y, size) { this.x = x; this.y = y; this.size = size; }
}

class Worm {
  constructor(n, x, y) {
    this.nodes = [];
    this.end = {x, y};
    this.speed = 6;
    let len = 18;
    for (let i=0;i<n;i++) {
      this.nodes.push(new Node(x, y, Math.max(6, len)));
      len *= 0.92;
    }
  }
  moveTo(x, y) {
    let dist = ((x - this.end.x) ** 2 + (y - this.end.y) ** 2) ** 0.5;
    let len = Math.max(0, dist - this.speed);
    for (let i = this.nodes.length - 1; i >= 0; i--) {
      let node = this.nodes[i];
      let ang = Math.atan2(node.y - y, node.x - x);
      node.x = x + len * Math.cos(ang);
      node.y = y + len * Math.sin(ang);
      x = node.x; y = node.y; len = node.size;
    }
    this.end.x = x; this.end.y = y;
  }
  draw(ctx) {
    // línea principal
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#ddd";
    ctx.beginPath();
    ctx.moveTo(this.nodes[0].x, this.nodes[0].y);
    for (let i=1;i<this.nodes.length;i++) ctx.lineTo(this.nodes[i].x, this.nodes[i].y);
    ctx.stroke();
    // espinas
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#bbb";
    for (let i = 2; i < this.nodes.length; i += 2) {
      const a = this.nodes[i-1], b = this.nodes[i];
      const ang = Math.atan2(b.y - a.y, b.x - a.x);
      const nx = Math.cos(ang + Math.PI/2), ny = Math.sin(ang + Math.PI/2);
      const s = Math.max(3, b.size * 0.35);
      ctx.beginPath();
      ctx.moveTo(b.x, b.y); ctx.lineTo(b.x + nx*s, b.y + ny*s);
      ctx.moveTo(b.x, b.y); ctx.lineTo(b.x - nx*s, b.y - ny*s);
      ctx.stroke();
    }
    // cabeza (punto) para confirmar que se ve
    const head = this.nodes[this.nodes.length-1];
    ctx.fillStyle = "#fff";
    ctx.beginPath(); ctx.arc(head.x, head.y, 2.2, 0, Math.PI*2); ctx.fill();
  }
}

// ---------- Entrada: pointer + touch + mouse + window fallback ----------
const mouse = { x: 100, y: 100 };
let pointerActive = false;

function setFromClient(eX, eY) {
  const r = canvas.getBoundingClientRect();
  mouse.x = eX - r.left;
  mouse.y = eY - r.top;
}

canvas.addEventListener("pointerdown", (e)=>{ pointerActive=true; setFromClient(e.clientX,e.clientY); try{canvas.setPointerCapture(e.pointerId);}catch{} e.preventDefault(); }, {passive:false});
canvas.addEventListener("pointermove", (e)=>{ if(!pointerActive && e.pointerType==="mouse" && e.buttons===0) return; setFromClient(e.clientX,e.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener("pointerup",   ()=>{ pointerActive=false; }, {passive:false});

// fallbacks
canvas.addEventListener("touchstart",(e)=>{ const t=e.touches[0]; setFromClient(t.clientX,t.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener("touchmove", (e)=>{ const t=e.touches[0]; setFromClient(t.clientX,t.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener("click", (e)=> setFromClient(e.clientX,e.clientY));
// respaldo absoluto por si el canvas no capta eventos dentro del iframe
window.addEventListener("pointermove", (e)=>{ if(pointerActive) setFromClient(e.clientX, e.clientY); }, {passive:true});

// ---------- Animación ----------
const worm = new Worm(34, mouse.x, mouse.y);

function loop(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  worm.moveTo(mouse.x, mouse.y);
  worm.draw(ctx);
  requestAnimationFrame(loop);
}
loop();
</script>
"""

st.components.v1.html(html_code, height=650)
