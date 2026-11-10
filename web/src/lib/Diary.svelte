<script>
  import { onMount } from "svelte"
  import { baby, journal, sleep } from "./baby.svelte.js"
  import Icon from "./Icon.svelte"

  let moments = $state([])

  async function load() {
    moments = (await journal()).moments.slice().reverse()
  }

  onMount(load)

  function describe(m) {
    if (m.event == "born") return `Was born as a ${m.level}`
    if (m.event == "sleep") return `Slept, and let go of ${m.forgotten || 0} unused memories`
    if (m.event == "lesson") return `Took the ${m.lesson} lesson, ${m.score} of ${m.total} right`
    if (m.event == "feedback") return m.amount > 0 ? "Was told it was right" : "Was told it was wrong"
    if (m.event == "explored") return `Explored ${m.file}${m.said ? ` and said "${m.said}"` : ""}`
    const heard = m.heard ? `Heard "${m.heard}"` : m.saw ? "Looked at something" : "Was quiet"
    const did = m.action ? `, then did ${m.action}` : m.said ? `, said "${m.said}"` : ""
    return `${m.event == "initiative" ? "On its own" : heard}${did}`
  }

  const time = (m) => new Date(m.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
</script>

<div class="diary">
  {#if baby.state}
    <div class="facts">
      <div><b>{baby.state.age}</b><span>moments lived</span></div>
      <div><b>{baby.state.vocabulary.length}</b><span>words known</span></div>
      <div><b>{baby.state.links}</b><span>connections</span></div>
    </div>
    <button class="sleep" onclick={async () => { await sleep(); load() }}>
      <Icon name="moon" />
      <span><b>Put it to sleep</b>Sleep turns today into lasting memory. It also sleeps by itself when tired.</span>
    </button>
  {/if}
  <h2>Its life</h2>
  <ol>
    {#each moments as m}
      <li class:night={m.event == "sleep"}><time>{time(m)}</time><p>{describe(m)}</p></li>
    {:else}
      <li><p>Nothing has happened yet.</p></li>
    {/each}
  </ol>
</div>

<style>
  .diary { overflow-y: auto; padding: 4px 18px 20px; display: grid; gap: 16px; align-content: start; }
  .facts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .facts div { background: var(--card); border-radius: 16px; padding: 12px 14px; display: grid; }
  .facts b { font-size: 24px; font-weight: 700; }
  .facts span { color: var(--faint); font-size: 12px; }
  .sleep { height: auto; padding: 14px; gap: 12px; justify-content: flex-start; text-align: left; border-radius: 16px; font-weight: 400; color: var(--muted); }
  .sleep :global(svg) { color: var(--lilac); }
  .sleep span { display: grid; gap: 2px; font-size: 13px; line-height: 1.4; }
  .sleep b { color: var(--text); font-size: 15px; font-weight: 600; }
  h2 { font-size: 18px; font-weight: 700; margin-top: 6px; }
  ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }
  li { display: grid; grid-template-columns: 52px 1fr; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--line); }
  time { color: var(--faint); font-size: 13px; }
  li p { color: var(--muted); font-size: 14px; }
  li.night p { color: var(--lilac); }
</style>
