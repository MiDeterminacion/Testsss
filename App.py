    import streamlit as st

st.set_page_config(page_title="Worm/Nodes Demo", layout="wide")
st.title("Animación tipo 'worm' siguiendo el mouse (HTML + JS dentro de Streamlit)")

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
    border-radius:12px;
    overflow:hidden;
  }
  canvas { display:block; width:100%; height:100%; }
  .hint {
    color:#aaa; font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
    font-size:14px; margin-top:.5rem; text-align:center;
  }
</style>

<div id="wrap">
  <canvas id="cv"></canvas>
</div>
<div class="hint">Mueve el mouse o toca (en móvil) dentro del lienzo.</div>

<script>
// ---------- Canvas y tamaño ----------
const wrap = document.getElementById("wrap");
const canvas = document.getElementById("cv");
const ctx = canvas.getContext("2d");

function resize() {
  const r = wrap.getBoundingClientRect();
  // resolución real del canvas (no solo CSS)
  canvas.width  = Math.max(400, Math.floor(r.width));
  canvas.height = Math.max(300, Math.floor(r.height));
}
resize();
window.addEventListener("resize", resize);

// ---------- Clases ----------
class Node {
  constructor(x, y, size) {
    this.x = x; this.y = y;
    this.size = size; // distancia hasta el siguiente segmento
  }
}

class Worm {
  constructor(n, startX, startY) {
    this.nodes = [];
    this.end = { x: startX, y: startY }; // última posición objetivo
    this.speed = 6;                       // holgura/elasticidad

    // crear segmentos decrecientes
    let len = 18;
    for (let i = 0; i < n; i++) {
      this.nodes.push(new Node(startX, startY, Math.max(6, len)));
      len *= 0.92;
    }
  }

  // --- Transcripción/port del snippet de la imagen ---
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

  // --- Dibujo COMPLETO (línea + “espinas”) ---
  draw(ctx) {
    // línea principal (conecta todos los nodos)
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#dddddd";
    ctx.beginPath();
    ctx.moveTo(this.nodes[0].x, this.nodes[0].y);
    for (let i = 1; i < this.nodes.length; i++) {
      ctx.lineTo(this.nodes[i].x, this.nodes[i].y);
    }
    ctx.stroke();

    // “espinas” laterales para estilo esquelético
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#cccccc";
    for (let i = 2; i < this.nodes.length; i += 2) {
      const a = this.nodes[i - 1], b = this.nodes[i];
      const ang = Math.atan2(b.y - a.y, b.x - a.x);
      const nx = Math.cos(ang + Math.PI / 2), ny = Math.sin(ang + Math.PI / 2);
      const cx = b.x, cy = b.y, s = Math.max(3, b.size * 0.35);

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + nx * s, cy + ny * s);
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx - nx * s, cy - ny * s);
      ctx.stroke();
    }
  }
}

// ---------- Interacción ----------
const mouse = { x: canvas.width * 0.5, y: canvas.height * 0.5 };

function setMouseFromEvent(clientX, clientY) {
  const r = canvas.getBoundingClientRect();
  mouse.x = clientX - r.left;
  mouse.y = clientY - r.top;
}

canvas.addEventListener("mousemove", (e) => setMouseFromEvent(e.clientX, e.clientY));
canvas.addEventListener("touchstart", (e) => { const t = e.touches[0]; setMouseFromEvent(t.clientX, t.clientY); e.preventDefault(); }, {passive:false});
canvas.addEventListener("touchmove",  (e) => { const t = e.touches[0]; setMouseFromEvent(t.clientX, t.clientY); e.preventDefault(); }, {passive:false});

// ---------- Animación ----------
const worm = new Worm(34, mouse.x, mouse.y);

function loop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  worm.moveTo(mouse.x, mouse.y);
  worm.draw(ctx);
  requestAnimationFrame(loop);
}
loop();
</script>
"""

st.components.v1.html(html_code, height=650)
