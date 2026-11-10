<script>
  import { onMount } from "svelte"
  import { baby, babies, choose } from "./baby.svelte.js"
  import Logo from "./Logo.svelte"

  let { onclose } = $props()
  let data = $state(null)
  let opening = $state("")

  // How full each level's little mind picture is.
  const density = { newborn: 0, toddler: 8, preschooler: 16, kid: 30 }
  const hues = ["#8ab4ff", "#c4a1ff", "#ffb38a", "#7ee0b5", "#ff8f9c"]

  onMount(async () => { data = await babies() })

  async function open(name, level) {
    opening = name
    await choose(name, level)
    onclose()
  }

  function strands(n) {
    const out = []
    for (let i = 0; i < n; i++) {
      out.push({ a: 10 + ((i * 37) % 60), b: 10 + ((i * 53 + 11) % 60), color: hues[i % hues.length] })
    }
    return out
  }
</script>

<div class="picker" role="dialog" aria-modal="true" aria-label="Choose a baby">
  <div class="inner">
    <Logo size={56} />
    <h2>Choose a baby</h2>
    <p class="lead">Every Sourdough is born knowing nothing. The older ones have simply lived through more lessons already. Start with one that knows a little, or raise one from nothing.</p>
    {#if data}
      <div class="levels">
        {#each data.levels as l}
          <button class="level" disabled={!!opening} onclick={() => open(l.name, l.name)}>
            <svg viewBox="0 0 200 80" aria-hidden="true">
              {#each strands(density[l.name] ?? 4) as s}
                <path d="M14 {s.a} C 80 {s.a}, 120 {s.b}, 186 {s.b}" stroke={s.color} stroke-opacity="0.55" fill="none" />
              {/each}
              <circle cx="100" cy="40" r={density[l.name] ? 0 : 6} fill="#ffb38a" />
            </svg>
            <b>{l.title}</b>
            <span>{l.about}</span>
            <i>{opening == l.name ? "Opening..." : data.babies.some((b) => b.name == l.name) ? "Open" : "Start"}</i>
          </button>
        {/each}
      </div>
      {@const others = data.babies.filter((b) => !(b.name in density))}
      {#if others.length}
        <div class="existing">
          <span>Or continue with</span>
          {#each others as b}
            <button disabled={!!opening} onclick={() => open(b.name)}>{b.name} <small>{b.words} words</small></button>
          {/each}
        </div>
      {/if}
      <button class="plain stay" onclick={onclose}>Keep talking to {baby.name}</button>
    {/if}
  </div>
</div>

<style>
  .picker {
    position: fixed;
    inset: 0;
    z-index: 10;
    background: rgba(10, 13, 22, 0.92);
    backdrop-filter: blur(10px);
    display: grid;
    place-items: center;
    padding: 24px;
    overflow-y: auto;
    animation: fade 0.35s var(--ease);
  }
  @keyframes fade { from { opacity: 0; } }
  .inner { width: min(1000px, 100%); display: grid; justify-items: center; gap: 14px; text-align: center; }
  h2 { font-size: clamp(28px, 4vw, 40px); font-weight: 700; letter-spacing: -0.02em; }
  .lead { color: var(--muted); max-width: 56ch; margin-bottom: 14px; }
  .levels { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; width: 100%; }
  .level {
    height: auto;
    padding: 16px 16px 18px;
    display: grid;
    gap: 6px;
    align-content: start;
    justify-items: start;
    text-align: left;
    border-radius: 20px;
    background: var(--panel);
    font-weight: 400;
  }
  .level:hover:not(:disabled) { background: var(--card); transform: translateY(-2px); }
  .level svg { width: 100%; height: 80px; margin-bottom: 6px; background: #0c1020; border-radius: 12px; }
  .level b { font-size: 18px; font-weight: 700; }
  .level span { color: var(--muted); font-size: 14px; line-height: 1.45; }
  .level i { margin-top: 8px; font-style: normal; font-weight: 600; color: var(--accent); }
  .existing { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; color: var(--faint); margin-top: 6px; }
  .existing button { height: 34px; border-radius: 999px; font-weight: 500; }
  .existing small { color: var(--faint); font-weight: 400; }
  .stay { color: var(--muted); font-weight: 400; }
  @media (max-width: 800px) { .levels { grid-template-columns: repeat(2, 1fr); } }
</style>
