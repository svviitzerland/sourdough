<script>
  // Its face. Expressions are never scripted. They come from its feelings,
  // through the muscles of a face, the way Ekman's Facial Action Coding
  // System describes them:
  //
  //   smile      lip corner puller (AU12), stronger the more it learned to smile
  //   squint     cheek raiser (AU6), what makes a smile look real
  //   frown      lip corner depressor (AU15)
  //   browLower  brow lowerer (AU4), for upset and puzzled
  //   browRaise  brow raisers (AU1 and AU2), for curious and surprised
  //   lidRaise   upper lid raiser (AU5), wide eyes
  //   closed     eyes closed (AU43), tired or asleep
  //   jaw        jaw drop (AU26), for talking, surprise and yawns
  //
  // Each muscle moves on a critically damped spring, so faces flow from one
  // to the next and can change mid way. A newborn's face has little control:
  // small, imprecise expressions and big eyes. Range and control grow as it
  // matures (state.face.maturity), and its smile grows as people answer it.
  import { onMount } from "svelte"
  import { baby } from "./baby.svelte.js"
  import { colorOf } from "./colors.js"

  let { size = 180 } = $props()

  const MUSCLES = ["smile", "squint", "frown", "browLower", "browRaise", "lidRaise", "closed", "jaw", "tilt", "gazeX", "gazeY"]
  const RESPONSE = { jaw: 0.07, gazeX: 0.16, gazeY: 0.16, closed: 0.18 }   // seconds, the rest 0.35

  // A spring in Apple's terms: response (how quickly) and damping (1 means no bounce).
  function spring() {
    return { value: 0, velocity: 0 }
  }
  function step(s, target, dt, response = 0.35, damping = 1) {
    const stiffness = (2 * Math.PI / response) ** 2
    const friction = 4 * Math.PI * damping / response
    s.velocity += (-stiffness * (s.value - target) - friction * s.velocity) * dt
    s.value += s.velocity * dt
  }

  const springs = Object.fromEntries(MUSCLES.map((m) => [m, spring()]))
  const blinkSpring = spring()
  let f = $state(Object.fromEntries(MUSCLES.map((m) => [m, 0])))
  let blink = $state(0)
  let breath = $state(0)
  let time = $state(0)

  const uid = Math.random().toString(36).slice(2, 8)
  const color = $derived(colorOf(baby.profile).css)
  const maturity = $derived(baby.state?.face?.maturity ?? 0.2)
  const asleep = $derived((baby.state?.feelings?.tiredness ?? 0) > 0.95 || (baby.moment?.kind == "sleep" && time - baby.moment.at < 6000))

  let nextBlink = 0
  let blinkUntil = 0
  let glance = { x: 0, y: 0, until: 0 }

  function targets(now) {
    const feel = baby.state?.feelings || { joy: 0, curiosity: 0.5, boredom: 0, confusion: 0, tiredness: 0 }
    const learnedSmile = baby.state?.face?.smile ?? 0.15
    const moment = baby.moment || { at: -1e9 }
    const since = (now - moment.at) / 1000
    const joy = Math.max(0, feel.joy)
    const upset = Math.max(0, -feel.joy)
    const t = {
      smile: 0.1 + joy * (0.35 + 0.65 * learnedSmile),
      squint: 0,
      frown: upset * 0.8,
      browLower: upset * 0.6 + feel.confusion * 0.5,
      browRaise: feel.curiosity * 0.35,
      lidRaise: feel.curiosity * 0.2,
      closed: Math.max(0, (feel.tiredness - 0.7) / 0.3) * 0.6,
      jaw: 0,
      tilt: feel.confusion * 0.7,
      gazeX: 0,
      gazeY: 0,
    }

    if (moment.kind == "praised" && since < 2.2) { t.smile = 1; t.squint = 0.85 }
    if (moment.kind == "corrected" && since < 1.8) { t.frown = Math.max(t.frown, 0.75); t.browLower = Math.max(t.browLower, 0.55); t.gazeY = 0.6 }
    if (moment.surprise > 0.5 && since < 0.9) { t.lidRaise = 1; t.browRaise = 1; t.jaw = 0.35 }
    if (moment.kind == "ask" && since < 4) { t.tilt = Math.max(t.tilt, 0.9); t.browRaise = Math.max(t.browRaise, 0.65) }
    if (moment.action == "explore" && since < 2.2) { t.gazeX = Math.sin(since * 4.5) * 0.9; t.browRaise = Math.max(t.browRaise, 0.4) }
    if (baby.thinking) { t.gazeX = 0.45; t.gazeY = -0.6; t.browRaise = Math.max(t.browRaise, 0.3) }
    if (baby.listening) { t.lidRaise = Math.max(t.lidRaise, 0.45); t.browRaise = Math.max(t.browRaise, 0.45) }

    // Talking: the jaw moves with its syllables while it speaks.
    const speaking = moment.kind && moment.words > 0 && since < 0.35 * moment.words + 0.2
    if (speaking) t.jaw = Math.max(t.jaw, 0.22 + 0.38 * Math.abs(Math.sin(now / 1000 * 13 + Math.sin(now / 1000 * 4.3))))

    if (asleep) {
      Object.assign(t, { closed: 1, smile: 0.12, frown: 0, browRaise: 0, browLower: 0, gazeX: 0, gazeY: 0 })
      t.jaw = 0.12 + 0.06 * Math.sin(now / 1000 * 1.1)
    }

    // A real smile lifts the cheeks and narrows the eyes.
    t.squint = Math.max(t.squint, (t.smile - 0.4) * 0.8)

    // Idle glances, small and slow.
    if (now > glance.until) glance = { x: (Math.random() - 0.5) * 0.7, y: (Math.random() - 0.5) * 0.4, until: now + 1200 + Math.random() * 2400 }
    if (!asleep && !baby.thinking && !(moment.action == "explore" && since < 2.2)) {
      t.gazeX += glance.x * 0.6
      t.gazeY += glance.y * 0.6
    }

    // A young face has less control: smaller expressions and little twitches.
    const range = 0.45 + 0.55 * maturity
    const twitch = (1 - maturity) * 0.08
    for (const m of ["smile", "frown", "browLower", "browRaise", "lidRaise", "squint", "tilt"]) {
      t[m] = Math.max(0, t[m] * range + twitch * Math.sin(now / 1000 * 3.1 + m.length))
    }
    return t
  }

  onMount(() => {
    let last = performance.now()
    let frame
    const loop = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      const t = targets(now)
      for (const m of MUSCLES) step(springs[m], t[m], dt, RESPONSE[m] || 0.35)

      if (now > nextBlink && !asleep) {
        blinkUntil = now + 130
        nextBlink = now + 2200 + Math.random() * 4200
      }
      step(blinkSpring, now < blinkUntil ? 1 : 0, dt, 0.06)

      const next = {}
      for (const m of MUSCLES) next[m] = springs[m].value
      f = next
      blink = blinkSpring.value
      breath = Math.sin(now / 1000 * 1.6)
      time = now
      frame = requestAnimationFrame(loop)
    }
    frame = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(frame)
  })

  const eyeScale = $derived((1.14 - 0.16 * maturity) * (1 + 0.22 * f.lidRaise))
  const openness = $derived(Math.max(0, Math.min(1, 1 - f.closed - blink - f.squint * 0.55)))

  function eye(x) {
    const cx = x + f.gazeX * 4.5
    const cy = 96 + f.gazeY * 3.5
    return { cx, cy }
  }

  function brow(x, side) {
    const y = 69 - f.browRaise * 9 + f.browLower * 5
    const inner = x - side * 11
    const outer = x + side * 11
    const innerY = y + f.browLower * 7 - f.frown * 4
    return `M${outer} ${y + 1} Q${x} ${y - 4} ${inner} ${innerY}`
  }

  const mouth = $derived.by(() => {
    const cy = 137
    const w = 30 + 12 * f.smile + 4 * f.jaw
    const corner = cy - 9 * f.smile + 8 * f.frown
    const upper = cy + 3 * f.smile - 2 * f.frown - f.jaw * 2
    const lower = upper + 3 + 26 * f.jaw + 12 * f.smile * (1 - f.frown)
    const l = 100 - w / 2
    const r = 100 + w / 2
    return { d: `M${l} ${corner} Q100 ${upper} ${r} ${corner} Q100 ${lower} ${l} ${corner}Z`, open: lower - upper, lower }
  })
</script>

<svg viewBox="0 0 200 200" width={size} height={size} role="img" aria-label="{baby.name} feels {baby.state?.feeling}">
  <defs>
    <radialGradient id="skin-{uid}" cx="36%" cy="30%" r="78%">
      <stop offset="0" stop-color="color-mix(in srgb, {color} 35%, white)" />
      <stop offset="0.55" stop-color={color} />
      <stop offset="1" stop-color="color-mix(in srgb, {color} 78%, black)" />
    </radialGradient>
  </defs>

  <ellipse cx="100" cy="190" rx={56 - breath * 2} ry="5" fill="black" opacity="0.08" />

  <g transform="rotate({f.tilt * 11} 100 120) translate(0 {breath * 1.2})">
    <ellipse cx="100" cy="104" rx="84" ry={84 + breath * 0.8} fill="url(#skin-{uid})" />

    <ellipse cx="60" cy="126" rx="14" ry="8" fill="#ff5f7e" opacity={0.16 + f.squint * 0.35 + f.smile * 0.15} />
    <ellipse cx="140" cy="126" rx="14" ry="8" fill="#ff5f7e" opacity={0.16 + f.squint * 0.35 + f.smile * 0.15} />

    {#each [70, 130] as x, i}
      {@const e = eye(x)}
      {#if openness > 0.14}
        <ellipse cx={e.cx} cy={e.cy} rx={11 * eyeScale} ry={13 * eyeScale * openness} fill="#1b130f" />
        {#if openness > 0.45}
          <circle cx={e.cx + 3.6 * eyeScale} cy={e.cy - 4.6 * eyeScale * openness} r={3.4 * eyeScale} fill="white" opacity="0.95" />
          <circle cx={e.cx - 3.2 * eyeScale} cy={e.cy + 4 * eyeScale * openness} r={1.4 * eyeScale} fill="white" opacity="0.6" />
        {/if}
      {:else}
        <path d="M{x - 10} 96 Q{x} {f.smile > 0.45 && !asleep ? 88 : 102} {x + 10} 96" stroke="#1b130f" stroke-width="3.6" stroke-linecap="round" fill="none" />
      {/if}
      <path d={brow(x, i == 0 ? -1 : 1)} stroke="#1b130f" stroke-width="4" stroke-linecap="round" fill="none" opacity={0.18 + 0.72 * maturity} />
    {/each}

    <path d={mouth.d} fill="#3b1a14" stroke="#3b1a14" stroke-width="3" stroke-linejoin="round" />
    {#if mouth.open > 10}
      <ellipse cx="100" cy={mouth.lower - 4} rx={Math.min(11, mouth.open * 0.6)} ry={Math.min(5, mouth.open * 0.25)} fill="#ff6b81" />
    {/if}
  </g>

  {#if asleep}
    {#each [0, 1, 2] as i}
      {@const p = ((time / 1000 + i * 0.8) % 2.4) / 2.4}
      <text x={150 + p * 22 + i * 4} y={58 - p * 34} font-size={12 + p * 10} font-weight="700" fill="var(--mute)" opacity={1 - p}>z</text>
    {/each}
  {/if}
</svg>
