<script>
  import { onMount } from "svelte"
  import { baby, boot, toggleVoice } from "./lib/baby.svelte.js"
  import Icon from "./lib/Icon.svelte"
  import Logo from "./lib/Logo.svelte"
  import Mind from "./lib/Mind.svelte"
  import Talk from "./lib/Talk.svelte"
  import Teach from "./lib/Teach.svelte"
  import Diary from "./lib/Diary.svelte"
  import Picker from "./lib/Picker.svelte"

  const tabs = [["talk", "Talk"], ["teach", "Teach"], ["diary", "Diary"]]
  let tab = $state("talk")
  let picking = $state(false)
  let failed = $state("")

  onMount(async () => {
    try {
      await boot()
    } catch (e) {
      failed = e.message
      return
    }
    let seen = false
    try { seen = localStorage.getItem("sourdough.picked") == "1" } catch (e) { }
    picking = !seen
  })

  function picked() {
    picking = false
    tab = "talk"
    try { localStorage.setItem("sourdough.picked", "1") } catch (e) { }
  }
</script>

<div class="app">
  <header>
    <div class="brand"><Logo /><b>Sourdough</b></div>
    {#if baby.state}
      <button class="who plain" onclick={() => (picking = true)} title="Switch baby">
        <span class="avatar">{baby.name.slice(0, 1).toUpperCase()}</span>
        <span class="name">{baby.name}</span>
        <span class="meta">{baby.state.stage} · {baby.state.vocabulary.length} words · feels {baby.state.feeling}</span>
        <Icon name="chevron" />
      </button>
    {/if}
    <span class="spacer"></span>
    <button class="plain round" onclick={toggleVoice} aria-pressed={baby.voice}
      title={baby.voice ? "It speaks out loud" : "It is silent"}>
      <Icon name={baby.voice ? "voice" : "mute"} />
    </button>
  </header>

  <main>
    <section class="mind" aria-label="Its mind">
      <Mind />
    </section>

    <section class="panel">
      <nav aria-label="What to do">
        {#each tabs as [id, label]}
          <button class:active={tab == id} onclick={() => (tab = id)} aria-current={tab == id}>{label}</button>
        {/each}
      </nav>
      {#if failed}
        <p class="failed">Cannot reach its brain. Start it with <code>sourdough</code> and reload. ({failed})</p>
      {:else if tab == "talk"}
        <Talk />
      {:else if tab == "teach"}
        <Teach />
      {:else}
        <Diary />
      {/if}
    </section>
  </main>

  {#if picking}
    <Picker onclose={picked} />
  {/if}
</div>

<style>
  .app { height: 100%; display: grid; grid-template-rows: auto minmax(0, 1fr); }

  header { display: flex; align-items: center; gap: 14px; padding: 12px 18px; }
  .brand { display: flex; align-items: center; gap: 10px; }
  .brand b { font-size: 17px; font-weight: 700; letter-spacing: -0.01em; }
  .who { height: 44px; padding: 0 12px 0 6px; gap: 10px; border-radius: 22px; color: var(--muted); font-weight: 400; }
  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, var(--accent), var(--rose));
    color: var(--accent-ink);
    font-weight: 700;
    font-size: 14px;
  }
  .name { color: var(--text); font-weight: 600; }
  .meta { font-size: 13px; }
  .spacer { flex: 1; }
  .round { width: 40px; padding: 0; border-radius: 50%; }

  main { display: grid; grid-template-columns: minmax(0, 1fr) minmax(360px, 430px); gap: 12px; padding: 0 12px 12px; min-height: 0; }
  .mind {
    position: relative;
    min-height: 0;
    border-radius: 22px;
    overflow: hidden;
    background:
      radial-gradient(60% 70% at 45% 50%, rgba(98, 112, 255, 0.14), transparent 70%),
      radial-gradient(40% 50% at 80% 30%, rgba(255, 140, 120, 0.08), transparent 70%),
      #0c1020;
    border: 1px solid var(--line);
  }
  .panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 22px;
    display: grid;
    grid-template-rows: auto minmax(0, 1fr);
    min-height: 0;
    min-width: 0;
    overflow: hidden;
  }
  nav {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
    margin: 12px;
    padding: 4px;
    background: var(--bg);
    border-radius: 14px;
  }
  nav button { height: 36px; border: 0; background: transparent; color: var(--muted); border-radius: 10px; }
  nav button:hover:not(:disabled) { background: transparent; color: var(--text); }
  nav button.active { background: var(--card-hi); color: var(--text); }
  .failed { padding: 24px; color: var(--muted); }

  @media (max-width: 900px) {
    header { padding: 10px 12px; }
    .brand b, .meta { display: none; }
    main { grid-template-columns: 1fr; grid-template-rows: 36vh minmax(0, 1fr); padding: 0 8px 8px; gap: 8px; }
  }
</style>
