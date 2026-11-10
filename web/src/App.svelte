<script>
  import { onMount } from "svelte"
  import {
    MessageCircle, GraduationCap, BookOpen, Volume2, VolumeX, ChevronDown,
    Smile, Frown, Sparkles, Meh, CircleHelp, Moon, Circle,
  } from "@lucide/svelte"
  import { baby, boot, toggleVoice } from "./lib/baby.svelte.js"
  import Logo from "./lib/Logo.svelte"
  import Mind from "./lib/Mind.svelte"
  import Talk from "./lib/Talk.svelte"
  import Teach from "./lib/Teach.svelte"
  import Diary from "./lib/Diary.svelte"
  import Picker from "./lib/Picker.svelte"

  const tabs = [
    { id: "talk", label: "Talk", icon: MessageCircle },
    { id: "teach", label: "Teach", icon: GraduationCap },
    { id: "diary", label: "Diary", icon: BookOpen },
  ]
  const moods = {
    happy: { icon: Smile, color: "text-mint" },
    upset: { icon: Frown, color: "text-rose" },
    curious: { icon: Sparkles, color: "text-peach" },
    bored: { icon: Meh, color: "text-mist" },
    confused: { icon: CircleHelp, color: "text-lilac" },
    sleepy: { icon: Moon, color: "text-sky" },
    calm: { icon: Circle, color: "text-mist" },
  }

  let tab = $state("talk")
  let picking = $state(false)
  let failed = $state("")
  const mood = $derived(moods[baby.state?.feeling] || moods.calm)

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

<div class="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(60%_50%_at_30%_40%,rgba(98,112,255,0.10),transparent_70%),radial-gradient(40%_40%_at_85%_10%,rgba(255,150,120,0.08),transparent_70%)]"></div>

<div class="grid h-full grid-rows-[auto_minmax(0,1fr)]">
  <header class="flex items-center gap-3 px-4 py-3 md:px-5">
    <div class="flex items-center gap-2.5">
      <Logo />
      <span class="hidden text-[17px] font-bold tracking-tight sm:inline">Sourdough</span>
    </div>

    {#if baby.state}
      <button onclick={() => (picking = true)} title="Switch baby"
        class="group ml-2 flex h-11 items-center gap-2.5 rounded-full border border-white/[0.06] bg-night-800/70 py-1 pl-1 pr-3 transition hover:bg-night-700">
        <span class="grid size-9 place-items-center rounded-full bg-gradient-to-br from-peach to-rose text-sm font-bold text-night-900">
          {baby.name.slice(0, 1).toUpperCase()}
        </span>
        <span class="font-semibold">{baby.name}</span>
        <span class="hidden rounded-full bg-white/[0.06] px-2 py-0.5 text-xs text-mist md:inline">{baby.state.stage}</span>
        <span class="hidden text-sm text-mist md:inline">{baby.state.vocabulary.length} words</span>
        <span class="flex items-center gap-1 text-sm {mood.color}" title="It feels {baby.state.feeling}">
          <mood.icon class="size-4" />
          <span class="hidden lg:inline">{baby.state.feeling}</span>
        </span>
        <ChevronDown class="size-4 text-fog transition group-hover:text-ink" />
      </button>
    {/if}

    <span class="flex-1"></span>

    <button onclick={toggleVoice} aria-pressed={baby.voice} title={baby.voice ? "It speaks out loud" : "It is silent"}
      class="grid size-10 place-items-center rounded-full text-mist transition hover:bg-night-800 hover:text-ink">
      {#if baby.voice}<Volume2 class="size-5" />{:else}<VolumeX class="size-5" />{/if}
    </button>
  </header>

  <main class="grid min-h-0 grid-rows-[38vh_minmax(0,1fr)] gap-2 px-2 pb-2 md:grid-cols-[minmax(0,1fr)_minmax(370px,440px)] md:grid-rows-1 md:gap-3 md:px-3 md:pb-3">
    <section class="relative min-h-0 overflow-hidden rounded-3xl border border-white/[0.06] bg-[radial-gradient(60%_70%_at_45%_50%,rgba(98,112,255,0.14),transparent_70%),radial-gradient(40%_50%_at_80%_30%,rgba(255,140,120,0.07),transparent_70%)] bg-night-850" aria-label="Its mind">
      <Mind />
    </section>

    <section class="glass grid min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)] overflow-hidden rounded-3xl">
      <nav class="m-3 grid grid-cols-3 gap-1 rounded-2xl bg-night-950/70 p-1" aria-label="What to do">
        {#each tabs as t}
          <button onclick={() => (tab = t.id)} aria-current={tab == t.id}
            class="flex h-10 items-center justify-center gap-2 rounded-xl text-sm font-medium transition {tab == t.id ? 'bg-night-700 text-ink shadow-sm' : 'text-mist hover:text-ink'}">
            <t.icon class="size-4" />{t.label}
          </button>
        {/each}
      </nav>
      {#if failed}
        <p class="p-6 text-mist">Cannot reach its brain. Start it with <code class="text-peach">sourdough</code> and reload. ({failed})</p>
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
