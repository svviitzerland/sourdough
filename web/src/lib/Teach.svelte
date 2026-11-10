<script>
  import { tick } from "svelte"
  import { baby, lesson, showAction } from "./baby.svelte.js"
  import Icon from "./Icon.svelte"

  let report = $state(null)
  let running = $state("")
  let language = $state(baby.lang == "id" ? "id" : "en")
  let shown

  async function run(name) {
    running = name
    try {
      report = await lesson(name, language)
      await tick()
      shown?.scrollIntoView({ behavior: "smooth", block: "start" })
    } finally {
      running = ""
    }
  }
</script>

<div class="teach">
  <section>
    <div class="head">
      <h2>Lessons</h2>
      <div class="lang" role="group" aria-label="Lesson language">
        <button class:active={language == "en"} onclick={() => (language = "en")}>English</button>
        <button class:active={language == "id"} onclick={() => (language = "id")}>Indonesia</button>
      </div>
    </div>
    <p>A lesson shows it things and names them for you, then quizzes it. It learns exactly as if you had done it yourself.</p>
    <div class="grid">
      {#each baby.lessons as l}
        <button class="lesson" disabled={!!running} onclick={() => run(l.name)}>
          <b>{l.title[language] || l.title.en}</b>
          <span>{running == l.name ? "Teaching..." : `${l.size} things`}</span>
        </button>
      {/each}
    </div>
  </section>

  {#if report}
    <section class="report" bind:this={shown}>
      <h3>{report.lesson}<span>{report.score} of {report.total} right</span></h3>
      <div class="cards">
        {#each report.results as r}
          <div class="card" class:miss={!r.correct}>
            {#if r.picture}<img src={r.picture} alt="" />{:else}<span class="prompt">"{r.prompt}"</span>{/if}
            <b>{r.word}</b>
            <small><Icon name={r.correct ? "check" : "cross"} />{r.said || "no answer"}</small>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  <section>
    <h2>Actions</h2>
    <p>Its body can do a few things, but it does not know what they are for. It tries them when it gets bored, and keeps doing whatever brings something new. Say a word first, then show it here to teach it.</p>
    <div class="actions">
      {#each baby.state?.actions || [] as a}
        <button onclick={() => showAction(a.action)}>
          <b>{a.action}</b>
          <span>{a.action == "explore" ? "opens a file from its own folder" : a.action == "glance" ? "looks through the camera" : "an action"}</span>
          {#if a.triggers.length}<i>when it hears {a.triggers.join(", ")}</i>{/if}
        </button>
      {/each}
    </div>
  </section>
</div>

<style>
  .teach { overflow-y: auto; padding: 4px 18px 20px; display: grid; gap: 28px; align-content: start; }
  section { display: grid; gap: 12px; }
  .head { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  h2 { font-size: 18px; font-weight: 700; }
  p { color: var(--muted); font-size: 14px; }

  .lang { display: flex; gap: 2px; padding: 3px; background: var(--bg); border-radius: 12px; }
  .lang button { height: 30px; padding: 0 10px; border: 0; background: transparent; color: var(--muted); font-size: 13px; border-radius: 9px; }
  .lang button.active { background: var(--card-hi); color: var(--text); }

  .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .lesson, .actions button {
    height: auto;
    padding: 14px;
    display: grid;
    justify-items: start;
    justify-content: stretch;
    gap: 2px;
    text-align: left;
    border-radius: 16px;
  }
  .lesson b, .actions b { font-size: 15px; font-weight: 600; }
  .lesson span, .actions span { color: var(--faint); font-size: 13px; font-weight: 400; }
  .actions { display: grid; gap: 8px; }
  .actions i { font-style: normal; color: var(--mint); font-size: 13px; font-weight: 400; }

  h3 { font-size: 18px; font-weight: 700; display: flex; justify-content: space-between; align-items: baseline; }
  h3 span { color: var(--mint); font-size: 14px; font-weight: 600; }
  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(86px, 1fr)); gap: 8px; }
  .card { background: var(--card); border-radius: 14px; padding: 6px 6px 8px; display: grid; gap: 4px; border: 1px solid transparent; }
  .card.miss { border-color: rgba(255, 143, 156, 0.45); }
  .card img, .prompt { width: 100%; aspect-ratio: 1; border-radius: 10px; }
  .prompt { display: grid; place-items: center; text-align: center; font-size: 13px; color: var(--muted); background: var(--bg); padding: 6px; }
  .card b { font-size: 14px; font-weight: 600; padding: 0 2px; }
  .card small { display: flex; gap: 4px; align-items: center; color: var(--faint); font-size: 12px; padding: 0 2px; }
  .card small :global(svg) { width: 13px; height: 13px; }
  .card:not(.miss) small :global(svg) { color: var(--mint); }
  .card.miss small :global(svg) { color: var(--rose); }
</style>
