<script>
  // Its mind: every concept it has formed, in layers from what it senses (left)
  // to what it says and does (right). Links glow as strands, tighter when stronger,
  // and pulses run along whatever it is thinking about right now.
  import { onMount, untrack } from "svelte"
  import { Brain, X, ZoomIn, ZoomOut, Maximize2 } from "@lucide/svelte"
  import { baby } from "./baby.svelte.js"

  const COLUMNS = [
    ["color", "Colors"], ["shape", "Shapes"], ["sound", "Sounds"], ["name", "Names"],
    ["hear", "Hears"], ["say", "Says"], ["action", "Actions"],
  ]
  const SENSES = new Set(["color", "shape", "sound"])
  // Each layer has its own system color, so the strands glow in many colors.
  // Light and dark mode each get their own set, like Apple's system colors.
  const THEMES = {
    light: {
      tint: { shape: "142, 142, 147", sound: "142, 142, 147", name: "0, 122, 255", hear: "175, 82, 222", say: "255, 149, 0", action: "52, 199, 89" },
      ink: "#1d1d1f", mute: "#8e8e93", surface: "#ffffff", ring: "rgba(0, 0, 0, 0.18)", pulse: "0, 122, 255", blend: "source-over", strength: 1.3,
    },
    dark: {
      tint: { shape: "152, 152, 157", sound: "152, 152, 157", name: "10, 132, 255", hear: "191, 90, 242", say: "255, 159, 10", action: "48, 209, 88" },
      ink: "#f5f5f7", mute: "#8e8e93", surface: "#1c1c1e", ring: "rgba(255, 255, 255, 0.8)", pulse: "255, 255, 255", blend: "lighter", strength: 1,
    },
  }
  const scheme = window.matchMedia("(prefers-color-scheme: dark)")
  let theme = THEMES[scheme.matches ? "dark" : "light"]
  scheme.addEventListener?.("change", (e) => (theme = THEMES[e.matches ? "dark" : "light"]))
  const FONT = "system-ui, -apple-system, sans-serif"

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
    return theme.tint[right.column] || theme.tint.shape
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
      ctx.fillStyle = `rgba(${theme.tint.say}, ${0.35 + 0.35 * breath})`
      ctx.arc(width / 2, height / 2 - 24, 6 + 5 * breath, 0, Math.PI * 2)
      ctx.fill()
      return
    }

    const { x, y, k } = view
    ctx.setTransform(ratio * k, 0, 0, ratio * k, ratio * x, ratio * y)
    const focus = pinned || hover
    const near = new Set(focus ? [focus.id, ...(focus.links || []).map((e) => other(e, focus).id)] : [])

    if (headers) {
      ctx.font = `600 11px ${FONT}`
      ctx.fillStyle = theme.mute
      ctx.textAlign = "center"
      for (const [kind, title] of columns) {
        const any = nodes.find((n) => n.column == kind)
        if (any) ctx.fillText(title.toUpperCase().split("").join(String.fromCharCode(8202)), any.x, 36)
      }
    }

    ctx.globalCompositeOperation = theme.blend
    for (const e of edges) {
      const a = byId.get(e.from)
      const b = byId.get(e.to)
      if (a.x == null || b.x == null) continue
      const lit = !focus || e.from == focus.id || e.to == focus.id
      const live = active.has(e.from) || active.has(e.to)
      const strands = e.weight > 0.6 ? 3 : e.weight > 0.3 ? 2 : 1
      const alpha = Math.min(1, (0.08 + e.weight * 0.4) * theme.strength) * breath * (lit ? 1 : 0.07) * (live ? 1 + thinking : 1)
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
          ctx.fillStyle = `rgba(${theme.pulse}, ${0.6 + 0.4 * thinking})`
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
        ctx.strokeStyle = `rgba(${theme.tint.say}, ${0.45 + 0.35 * Math.sin(t * 4)})`
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
    ctx.strokeStyle = theme.ring
    if (n.kind == "color") {
      ctx.beginPath()
      ctx.arc(n.x, n.y, 8, 0, Math.PI * 2)
      ctx.fillStyle = img && img.rgb ? `rgb(${img.rgb})` : theme.mute
      ctx.fill()
      ctx.stroke()
    } else if (n.kind == "shape" || n.kind == "sound") {
      ctx.beginPath()
      ctx.arc(n.x, n.y, 10, 0, Math.PI * 2)
      ctx.fillStyle = theme.surface
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
      ctx.fillStyle = `rgb(${theme.tint[n.column] || theme.tint.shape})`
      ctx.fill()
      if (labeled) {
        ctx.font = action ? `600 14px ${FONT}` : `500 13px ${FONT}`
        ctx.textAlign = "left"
        ctx.textBaseline = "middle"
        ctx.fillStyle = focused ? `rgb(${theme.tint.say})` : theme.ink
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

  function zoom(factor) {
    const k = Math.min(4, Math.max(0.4, view.k * factor))
    const cx = width / 2
    const cy = height / 2
    view = { k, x: cx - ((cx - view.x) / view.k) * k, y: cy - ((cy - view.y) / view.k) * k }
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

<div class="absolute inset-0 overflow-hidden" bind:this={box} bind:clientWidth={width} bind:clientHeight={height}>
  <canvas bind:this={canvas} onpointerdown={down} onpointermove={move} onpointerup={up}
    onpointerleave={() => { hover = null; tip = null }} onwheel={wheel} ondblclick={() => (view = { x: 0, y: 0, k: 1 })}
    class="block size-full touch-none {tip ? 'cursor-pointer' : 'cursor-grab active:cursor-grabbing'}"
    aria-label="Its concept network"></canvas>

  {#if !nodes.length}
    <div class="pointer-events-none absolute inset-x-0 top-1/2 mt-6 grid justify-items-center gap-1 text-center">
      <Brain class="mb-1 size-6 text-faint" />
      <p class="font-semibold">Its mind is still empty</p>
      <p class="max-w-xs text-sm text-mute">Talk to it and show it things. Every word it learns grows here.</p>
    </div>
  {/if}

  {#if tip}
    <span class="pointer-events-none absolute translate-x-3.5 translate-y-3.5 whitespace-nowrap rounded-lg bg-ink px-2.5 py-1.5 text-[13px] text-surface"
      style:left="{tip.x}px" style:top="{tip.y}px">{tip.text}</span>
  {/if}

  {#if pinned}
    <aside class="material border border-line shadow-card animate-arrive absolute right-4 top-4 grid w-64 gap-1 rounded-2xl p-4 text-sm text-mute">
      <div class="flex items-start justify-between gap-2">
        <b class="text-xl font-bold text-ink">{describe(pinned)}</b>
        <button onclick={() => (pinned = null)} class="grid size-7 place-items-center rounded-full hover:bg-fill" title="Close">
          <X class="size-4" />
        </button>
      </div>
      <span class="text-xs text-faint">{pinned.kind}, {(pinned.links || []).length} links</span>
      {#if details.length}
        <ol class="mt-2 grid gap-1.5">
          {#each details as d}
            <li class="flex items-center justify-between gap-2">
              <span class="truncate">{d.name}{d.habit ? ", habit" : ""}</span>
              <span class="h-1 w-14 shrink-0 overflow-hidden rounded-full bg-fill-strong">
                <span class="block h-full rounded-full bg-accent" style:width="{Math.round(d.weight * 100)}%"></span>
              </span>
            </li>
          {/each}
        </ol>
      {/if}
    </aside>
  {/if}

  {#if nodes.length}
    <div class="pointer-events-none absolute bottom-4 left-4 right-4 flex items-end justify-between gap-3">
      <div class="material border border-line shadow-card pointer-events-auto flex items-center gap-1 rounded-xl p-1">
        <button onclick={() => zoom(1.25)} title="Zoom in" class="grid size-8 place-items-center rounded-lg text-mute hover:bg-fill hover:text-ink"><ZoomIn class="size-4" /></button>
        <button onclick={() => zoom(0.8)} title="Zoom out" class="grid size-8 place-items-center rounded-lg text-mute hover:bg-fill hover:text-ink"><ZoomOut class="size-4" /></button>
        <button onclick={() => (view = { x: 0, y: 0, k: 1 })} title="Fit" class="grid size-8 place-items-center rounded-lg text-mute hover:bg-fill hover:text-ink"><Maximize2 class="size-4" /></button>
        <span class="hidden px-2 text-xs text-faint xl:inline">Drag to move, click a concept</span>
      </div>
      <div class="material border border-line shadow-card hidden flex-wrap items-center gap-x-3 gap-y-1 rounded-xl px-3 py-2 text-xs text-mute lg:flex">
        <span class="flex items-center gap-1.5"><i class="size-2 rounded-full bg-blue"></i>names</span>
        <span class="flex items-center gap-1.5"><i class="size-2 rounded-full bg-purple"></i>hears</span>
        <span class="flex items-center gap-1.5"><i class="size-2 rounded-full bg-accent"></i>says</span>
        <span class="flex items-center gap-1.5"><i class="size-2 rounded-full bg-green"></i>actions</span>
      </div>
    </div>
  {/if}
</div>
