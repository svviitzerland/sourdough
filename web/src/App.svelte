<script>
  import { onMount } from "svelte"
  import {
    MessageCircle, GraduationCap, BookOpen, Volume2, VolumeX, LoaderCircle,
    Smile, Frown, Sparkles, Meh, CircleHelp, Moon, Circle,
  } from "@lucide/svelte"
  import { baby, boot, toggleVoice } from "./lib/baby.svelte.js"
  import Logo from "./lib/Logo.svelte"
  import Mind from "./lib/Mind.svelte"
  import Talk from "./lib/Talk.svelte"
  import Teach from "./lib/Teach.svelte"
  import Diary from "./lib/Diary.svelte"
  import Switcher from "./lib/Switcher.svelte"
  import CreateBaby from "./lib/CreateBaby.svelte"

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
  let creating = $state(false)
  let failed = $state("")
  const mood = $derived(moods[baby.state?.feeling] || moods.calm)

  onMount(async () => {
    try {
      await boot()
    } catch (e) {
      failed = e.message
    }
  })

  // Switching babies always lands on the conversation.
  $effect(() => {
    baby.name
    tab = "talk"
  })
</script>

<div class="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(60%_50%_at_30%_40%,rgba(98,112,255,0.10),transparent_70%),radial-gradient(40%_40%_at_85%_10%,rgba(255,150,120,0.08),transparent_70%)]"></div>

{#if failed}
  <div class="grid h-full place-items-center p-6 text-center">
    <div class="grid max-w-sm justify-items-center gap-3">
      <Logo size={44} />
      <p class="font-semibold">Cannot reach its brain</p>
      <p class="text-sm text-mist">Start it with <code class="text-peach">sourdough</code> in a terminal, then reload this page. ({failed})</p>
    </div>
  </div>
{:else if !baby.ready}
  <div class="grid h-full place-items-center"><LoaderCircle class="size-6 animate-spin text-fog" /></div>
{:else if !baby.name}
  <CreateBaby first />
{:else}
  <div class="grid h-full grid-rows-[auto_minmax(0,1fr)]">
    <header class="flex items-center gap-3 px-3 py-3 md:px-5">
      <div class="flex items-center gap-2.5">
        <Logo />
        <span class="hidden text-[17px] font-bold tracking-tight sm:inline">Sourdough</span>
      </div>
      <span class="ml-1 hidden h-6 w-px bg-white/10 sm:block"></span>
      <Switcher oncreate={() => (creating = true)} />
      <span class="hidden items-center gap-1.5 text-sm md:flex {mood.color}" title="How it feels">
        <mood.icon class="size-4" />{baby.state?.feeling}
      </span>
      <span class="flex-1"></span>
      <button onclick={toggleVoice} aria-pressed={baby.voice} title={baby.voice ? "It speaks out loud" : "It is silent"}
        class="grid size-10 place-items-center rounded-full text-mist transition hover:bg-night-800 hover:text-ink">
        {#if baby.voice}<Volume2 class="size-5" />{:else}<VolumeX class="size-5" />{/if}
      </button>
    </header>

    <main class="grid min-h-0 grid-rows-[36vh_minmax(0,1fr)] gap-2 px-2 pb-2 md:grid-cols-[minmax(0,1fr)_minmax(370px,440px)] md:grid-rows-1 md:gap-3 md:px-3 md:pb-3">
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
        {#if tab == "talk"}
          <Talk />
        {:else if tab == "teach"}
          <Teach />
        {:else}
          <Diary />
        {/if}
      </section>
    </main>
  </div>
{/if}

{#if creating && baby.name}
  <CreateBaby onclose={() => (creating = false)} />
{/if}
