<script>
  // Its mind: every concept it has formed, in layers from what it senses (left)
  // to what it says and does (right). Links glow as strands, tighter when stronger,
  // and pulses run along whatever it is thinking about right now.
  import { onMount, untrack } from "svelte"
  import { baby } from "./baby.svelte.js"

  const COLUMNS = [
    ["color", "Colors"], ["shape", "Shapes"], ["sound", "Sounds"], ["name", "Names"],
    ["hear", "Hears"], ["say", "Says"], ["action", "Actions"],
  ]
  const SENSES = new Set(["color", "shape", "sound"])
  // Each layer has its own soft color, so the strands glow in many colors.
  const TINT = {
    shape: "236, 238, 245", sound: "236, 238, 245", name: "138, 180, 255",
    hear: "196, 161, 255", say: "255, 179, 138", action: "126, 224, 181",
  }

  let box
  let canvas
  let width = $state(0)
  let height = $state(0)
  let pinned = $state(null)
  let tip = $state(null)
  let view = { x: 0, y: 0, k: 1 }
  let hover = null
  let drag = null
  let columns = []
  let headers = true
  const images = new Map()

  const nodes = $derived(baby.graph.nodes.map((n) => ({ ...n })))
  const byId = $derived(new Map(nodes.map((n) => [n.id, n])))
  const edges = $derived(
    baby.graph.edges
      .filter((e) => byId.has(e.from) && byId.has(e.to))
      .map((e) => ({ ...e, seed: hash(e.from + e.to) })),
  )
  const active = $derived(new Set(baby.graph.active))

  $effect(() => {
    for (const n of nodes) {
      n.links = edges.filter((e) => e.from == n.id || e.to == n.id)
      if (n.picture && !images.has(n.picture)) {
        const img = new Image()
        img.onload = () => { img.rgb = averageColor(img) }
        img.src = n.picture
        images.set(n.picture, img)
      }
    }
    layout(width, height)
    untrack(() => { if (pinned) pinned = byId.get(pinned.id) || null })
  })

  function hash(s) {
    let h = 2166136261
    for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619)
    return ((h >>> 0) % 1000) / 1000
  }

  function averageColor(img) {
    const c = document.createElement("canvas")
    c.width = c.height = 1
    const ctx = c.getContext("2d")
    ctx.drawImage(img, 0, 0, 1, 1)
    const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data
    return `${r}, ${g}, ${b}`
  }

  const other = (e, n) => byId.get(e.from == n.id ? e.to : e.from)

  function layout(w, h) {
    if (!w || !h) return
    const groups = new Map(COLUMNS.map(([kind]) => [kind, []]))
    for (const n of nodes) {
      n.column = n.kind
      if (n.kind == "word") {
        const names = (n.links || []).some((e) => SENSES.has(other(e, n).kind))
        const answer = (n.links || []).some((e) => e.type == "habit" && e.to == n.id)
        n.column = names ? "name" : answer ? "say" : "hear"
      }
      if (groups.has(n.column)) groups.get(n.column).push(n)
    }
    columns = COLUMNS.filter(([kind]) => groups.get(kind).length)
    const left = Math.max(56, w * 0.07)
    const right = w - Math.max(110, w * 0.13)
    const step = columns.length > 1 ? (right - left) / (columns.length - 1) : 0
    headers = step == 0 || step >= 80
    columns.forEach(([kind], i) => { groups.get(kind).x = columns.length > 1 ? left + step * i : w / 2 })
    const top = 64
    const bottom = h - 48
    const place = (kind) => {
      const list = groups.get(kind)
      const gap = list.length > 1 ? Math.min(38, (bottom - top) / (list.length - 1)) : 38
      const start = (top + bottom) / 2 - (gap * (list.length - 1)) / 2
      list.forEach((n, i) => { n.x = list.x; n.y = start + gap * i; n.gap = gap })
    }
    const center = (n) => {
      const ys = (n.links || []).map((e) => other(e, n)).filter((o) => o.y != null && o.column != n.column).map((o) => o.y)
      return ys.length ? ys.reduce((a, b) => a + b, 0) / ys.length : 1e9
    }
    for (const kind of ["color", "shape", "sound"]) {
      groups.get(kind).sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }))
      place(kind)
    }
    for (const kind of ["name", "hear", "say", "action", "color", "shape", "sound", "name", "hear", "say"]) {
      groups.get(kind).sort((a, b) => center(a) - center(b))
      place(kind)
    }
  }

  function controls(a, b, spread) {
    if (a.column == b.column) {
      const bend = 40 + Math.abs(a.y - b.y) * 0.35 + spread * 10
      return [[a.x - bend, a.y + spread * 6], [b.x - bend, b.y - spread * 6]]
    }
    const dx = (b.x - a.x) * 0.5
    return [[a.x + dx, a.y + spread * 18], [b.x - dx, b.y - spread * 18]]
  }

  function pointOn(a, b, s) {
    const [p1, p2] = controls(a, b, 0)
    const u = 1 - s
    return [
      u * u * u * a.x + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s * s * s * b.x,
      u * u * u * a.y + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s * s * s * b.y,
    ]
  }

  function edgeColor(e) {
    const a = byId.get(e.from)
    const b = byId.get(e.to)
    const colored = [a, b].find((n) => n.kind == "color")
    const img = colored && images.get(colored.picture)
    if (img && img.rgb) return img.rgb
    const right = a.x > b.x ? a : b
    return TINT[right.column] || "236, 238, 245"
  }

  function draw() {
    const ratio = window.devicePixelRatio || 1
    if (canvas.width != Math.round(width * ratio) || canvas.height != Math.round(height * ratio)) {
      canvas.width = Math.round(width * ratio)
      canvas.height = Math.round(height * ratio)
      layout(width, height)
    }
    const ctx = canvas.getContext("2d")
    const t = performance.now() / 1000
    const f = baby.state ? baby.state.feelings : { tiredness: 0 }
    const breath = 0.86 + 0.14 * Math.sin(t * (f.tiredness > 0.8 ? 0.8 : 1.6))
    const thinking = Math.max(0, 1 - (performance.now() - baby.thinkingAt) / 1600)
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
    ctx.clearRect(0, 0, width, height)

    if (!nodes.length) {
      ctx.beginPath()
      ctx.fillStyle = `rgba(255, 179, 138, ${0.35 + 0.35 * breath})`
      ctx.arc(width / 2, height / 2 - 24, 6 + 5 * breath, 0, Math.PI * 2)
      ctx.fill()
      return
    }

    const { x, y, k } = view
    ctx.setTransform(ratio * k, 0, 0, ratio * k, ratio * x, ratio * y)
    const focus = pinned || hover
    const near = new Set(focus ? [focus.id, ...(focus.links || []).map((e) => other(e, focus).id)] : [])

    if (headers) {
      ctx.font = "600 11px 'Plus Jakarta Sans', sans-serif"
      ctx.fillStyle = "#6f7891"
      ctx.textAlign = "center"
      for (const [kind, title] of columns) {
        const any = nodes.find((n) => n.column == kind)
        if (any) ctx.fillText(title.toUpperCase().split("").join(String.fromCharCode(8202)), any.x, 36)
      }
    }

    ctx.globalCompositeOperation = "lighter"
    for (const e of edges) {
      const a = byId.get(e.from)
      const b = byId.get(e.to)
      if (a.x == null || b.x == null) continue
      const lit = !focus || e.from == focus.id || e.to == focus.id
      const live = active.has(e.from) || active.has(e.to)
      const strands = e.weight > 0.6 ? 3 : e.weight > 0.3 ? 2 : 1
      const alpha = (0.08 + e.weight * 0.4) * breath * (lit ? 1 : 0.07) * (live ? 1 + thinking : 1)
      ctx.strokeStyle = `rgba(${edgeColor(e)}, ${alpha})`
      ctx.lineWidth = (0.7 + e.weight * 1.4) / Math.sqrt(k)
      for (let i = 0; i < strands; i++) {
        const spread = (i - (strands - 1) / 2) * 0.7 + (e.seed - 0.5) * 0.8 + Math.sin(t * 0.7 + e.seed * 9 + i) * 0.25
        const [p1, p2] = controls(a, b, spread)
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.bezierCurveTo(p1[0], p1[1], p2[0], p2[1], b.x, b.y)
        ctx.stroke()
      }
      if (live) {
        for (let i = 0; i < 3; i++) {
          const [px, py] = pointOn(a, b, (t * (0.35 + thinking * 0.5) + i / 3 + e.seed) % 1)
          ctx.beginPath()
          ctx.fillStyle = `rgba(255, 255, 255, ${0.6 + 0.4 * thinking})`
          ctx.arc(px, py, 1.8 / Math.sqrt(k), 0, Math.PI * 2)
          ctx.fill()
        }
      }
    }
    ctx.globalCompositeOperation = "source-over"

    for (const n of nodes) {
      if (n.x == null) continue
      if (active.has(n.id)) {
        ctx.beginPath()
        ctx.strokeStyle = `rgba(255, 179, 138, ${0.45 + 0.35 * Math.sin(t * 4)})`
        ctx.lineWidth = 1.5
        ctx.arc(n.x, n.y, 14 + 2 * Math.sin(t * 4), 0, Math.PI * 2)
        ctx.stroke()
      }
      const labeled = n.gap * k >= 14 || n == focus || near.has(n.id) || active.has(n.id)
      drawNode(ctx, n, n == focus, focus && !near.has(n.id), labeled)
    }
  }

  function drawNode(ctx, n, focused, dimmed, labeled) {
    const img = images.get(n.picture)
    ctx.globalAlpha = dimmed ? 0.4 : 1
    ctx.lineWidth = focused ? 2 : 1.2
    ctx.strokeStyle = "rgba(255, 255, 255, 0.85)"
    if (n.kind == "color") {
      ctx.beginPath()
      ctx.arc(n.x, n.y, 8, 0, Math.PI * 2)
      ctx.fillStyle = img && img.rgb ? `rgb(${img.rgb})` : "#6f7891"
      ctx.fill()
      ctx.stroke()
    } else if (n.kind == "shape" || n.kind == "sound") {
      ctx.beginPath()
      ctx.arc(n.x, n.y, 10, 0, Math.PI * 2)
      ctx.fillStyle = "#0c1020"
      ctx.fill()
      if (img && img.complete && n.kind == "shape") {
        ctx.save()
        ctx.clip()
        ctx.imageSmoothingEnabled = false
        ctx.drawImage(img, n.x - 8, n.y - 8, 16, 16)
        ctx.restore()
      }
      ctx.stroke()
    } else {
      const action = n.kind == "action"
      ctx.beginPath()
      ctx.arc(n.x, n.y, action ? 6 : 3.5, 0, Math.PI * 2)
      ctx.fillStyle = `rgb(${TINT[n.column] || "236, 238, 245"})`
      ctx.fill()
      if (labeled) {
        ctx.font = action ? "600 14px 'Plus Jakarta Sans', sans-serif" : "500 13px 'Plus Jakarta Sans', sans-serif"
        ctx.textAlign = "left"
        ctx.textBaseline = "middle"
        ctx.fillStyle = focused ? "#ffb38a" : "#e6e9f2"
        ctx.fillText(n.label, n.x + 10, n.y + 1)
      }
    }
    ctx.globalAlpha = 1
  }

  function describe(n) {
    if (n.kind == "word" || n.kind == "action") return n.label
    const names = [...new Set((n.links || []).map((e) => other(e, n)).filter((o) => o.column == "name").map((o) => o.label))]
    return names.length ? `${n.kind} ${names.slice(0, 3).join(" / ")}` : `an unnamed ${n.kind}`
  }

  const details = $derived(
    pinned
      ? (pinned.links || [])
          .map((e) => ({ name: describe(other(e, pinned)), habit: e.type == "habit", weight: e.weight }))
          .sort((p, q) => q.weight - p.weight)
          .slice(0, 6)
      : [],
  )

  function local(e) {
    const r = canvas.getBoundingClientRect()
    return [e.clientX - r.left, e.clientY - r.top]
  }

  function hit(sx, sy) {
    const x = (sx - view.x) / view.k
    const y = (sy - view.y) / view.k
    let best = null
    let bestD = 12 / view.k + 4
    for (const n of nodes) {
      if (n.x == null) continue
      const d = Math.hypot(n.x - x, n.y - y)
      const onLabel = n.label && x > n.x && x < n.x + 12 + n.label.length * 8 && Math.abs(y - n.y) < 9
      if (d < bestD || onLabel) { best = n; bestD = onLabel ? 0 : d }
    }
    return best
  }

  function down(e) {
    const [sx, sy] = local(e)
    drag = { sx, sy, x: view.x, y: view.y, moved: false, hit: hit(sx, sy) }
    canvas.setPointerCapture(e.pointerId)
  }

  function move(e) {
    const [sx, sy] = local(e)
    if (drag) {
      if (Math.hypot(sx - drag.sx, sy - drag.sy) > 3) drag.moved = true
      if (drag.moved) view = { ...view, x: drag.x + sx - drag.sx, y: drag.y + sy - drag.sy }
      return
    }
    hover = hit(sx, sy)
    tip = hover ? { x: sx, y: sy, text: `${describe(hover)}, ${(hover.links || []).length} links` } : null
  }

  function up() {
    if (drag && !drag.moved) pinned = drag.hit && drag.hit != pinned ? drag.hit : null
    drag = null
  }

  function wheel(e) {
    e.preventDefault()
    const [sx, sy] = local(e)
    const k = Math.min(4, Math.max(0.4, view.k * Math.exp(-e.deltaY * 0.0015)))
    const wx = (sx - view.x) / view.k
    const wy = (sy - view.y) / view.k
    view = { k, x: sx - wx * k, y: sy - wy * k }
  }

  onMount(() => {
    let frame
    const loop = () => { draw(); frame = requestAnimationFrame(loop) }
    frame = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(frame)
  })
</script>

<div class="mind" bind:this={box} bind:clientWidth={width} bind:clientHeight={height}>
  <canvas bind:this={canvas} class:pointing={!!tip} onpointerdown={down} onpointermove={move}
    onpointerup={up} onpointerleave={() => { hover = null; tip = null }} onwheel={wheel}
    ondblclick={() => (view = { x: 0, y: 0, k: 1 })} aria-label="Its concept network"></canvas>

  {#if !nodes.length}
    <p class="empty">It knows nothing yet.<br />Talk to it and show it things, and its mind will grow here.</p>
  {/if}

  {#if tip}
    <span class="tip" style:left="{tip.x}px" style:top="{tip.y}px">{tip.text}</span>
  {/if}

  {#if pinned}
    <aside class="detail">
      <b>{describe(pinned)}</b>
      <span>{pinned.kind}, {(pinned.links || []).length} links</span>
      {#if details.length}
        <ol>
          {#each details as d}<li>{d.name}{d.habit ? ", habit" : ""} <em>{d.weight.toFixed(2)}</em></li>{/each}
        </ol>
      {/if}
    </aside>
  {/if}

  <p class="hint">Drag to move, scroll to zoom, click a concept</p>
</div>

<style>
  .mind { position: absolute; inset: 0; overflow: hidden; }
  canvas { width: 100%; height: 100%; display: block; cursor: grab; touch-action: none; }
  canvas:active { cursor: grabbing; }
  canvas.pointing { cursor: pointer; }
  .empty {
    position: absolute;
    left: 0;
    right: 0;
    top: 50%;
    margin-top: 10px;
    text-align: center;
    color: var(--muted);
    pointer-events: none;
  }
  .tip {
    position: absolute;
    transform: translate(14px, 14px);
    background: var(--text);
    color: var(--bg);
    font-size: 13px;
    padding: 6px 10px;
    border-radius: 8px;
    pointer-events: none;
    white-space: nowrap;
  }
  .detail {
    position: absolute;
    right: 16px;
    top: 16px;
    width: 260px;
    background: rgba(15, 19, 32, 0.92);
    backdrop-filter: blur(8px);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 14px 16px;
    color: var(--muted);
    font-size: 13px;
    display: grid;
    gap: 4px;
  }
  .detail b { font-size: 20px; color: var(--text); font-weight: 700; }
  .detail ol { margin: 6px 0 0; padding-left: 18px; display: grid; gap: 2px; }
  .detail li::marker { color: var(--accent); }
  .detail em { font-style: normal; color: var(--faint); }
  .hint { position: absolute; left: 18px; bottom: 14px; font-size: 12px; color: var(--faint); pointer-events: none; }
</style>
