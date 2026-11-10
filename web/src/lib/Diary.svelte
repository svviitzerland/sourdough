<script>
  import { onMount } from "svelte"
  import {
    Clock, BookOpenText, Waypoints, Moon, Baby, GraduationCap, ThumbsUp, ThumbsDown,
    FolderOpen, MessageCircle, Sparkles,
  } from "@lucide/svelte"
  import { baby, journal, sleep } from "./baby.svelte.js"

  let moments = $state([])

  async function load() {
    moments = (await journal()).moments.slice().reverse()
  }

  onMount(load)

  function describe(m) {
    if (m.event == "born") return { icon: Baby, tint: "text-peach", text: `Was born as a ${m.level}` }
    if (m.event == "sleep") return { icon: Moon, tint: "text-sky", text: `Slept, and let go of ${m.forgotten || 0} unused memories` }
    if (m.event == "lesson") return { icon: GraduationCap, tint: "text-lilac", text: `Took the ${m.lesson} lesson, ${m.score} of ${m.total} right` }
    if (m.event == "feedback") {
      return m.amount > 0
        ? { icon: ThumbsUp, tint: "text-mint", text: "Was told it was right" }
        : { icon: ThumbsDown, tint: "text-rose", text: "Was told it was wrong" }
    }
    if (m.event == "explored") return { icon: FolderOpen, tint: "text-mint", text: `Explored ${m.file}${m.said ? ` and said "${m.said}"` : ""}` }
    const heard = m.heard ? `Heard "${m.heard}"` : m.saw ? "Looked at something" : "Was quiet"
    const did = m.action ? `, then did ${m.action}` : m.said ? `, said "${m.said}"` : ""
    if (m.event == "initiative") return { icon: Sparkles, tint: "text-peach", text: `On its own${did}` }
    return { icon: MessageCircle, tint: "text-mist", text: `${heard}${did}` }
  }

  const time = (m) => new Date(m.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
</script>

<div class="grid content-start gap-5 overflow-y-auto px-5 pb-6 pt-1">
  {#if baby.state}
    <div class="grid grid-cols-3 gap-2">
      {#each [[Clock, baby.state.age, "moments lived"], [BookOpenText, baby.state.vocabulary.length, "words known"], [Waypoints, baby.state.links, "connections"]] as [Icon, value, label]}
        <div class="grid gap-1 rounded-2xl bg-night-800 p-3">
          <Icon class="size-4 text-fog" />
          <b class="text-2xl font-bold">{value}</b>
          <span class="text-xs text-fog">{label}</span>
        </div>
      {/each}
    </div>

    <button onclick={async () => { await sleep(); load() }}
      class="flex items-center gap-3 rounded-2xl border border-white/[0.06] bg-night-800 p-3.5 text-left transition hover:border-sky/30 hover:bg-night-700">
      <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-sky/10 text-sky"><Moon class="size-5" /></span>
      <span>
        <b class="block text-[15px] font-semibold">Put it to sleep</b>
        <span class="text-[13px] text-fog">Sleep turns today into lasting memory. It also sleeps by itself when tired.</span>
      </span>
    </button>
  {/if}

  <h2 class="mt-1 text-lg font-bold">Its life</h2>
  <ol class="relative grid gap-1 before:absolute before:bottom-3 before:left-[15px] before:top-3 before:w-px before:bg-white/[0.07]">
    {#each moments as m}
      {@const d = describe(m)}
      <li class="relative grid grid-cols-[32px_1fr_auto] items-start gap-3 py-1.5">
        <span class="grid size-8 place-items-center rounded-full bg-night-800 {d.tint}"><d.icon class="size-4" /></span>
        <p class="pt-1.5 text-sm text-mist">{d.text}</p>
        <time class="pt-1.5 text-xs text-fog">{time(m)}</time>
      </li>
    {:else}
      <li class="text-sm text-fog">Nothing has happened yet.</li>
    {/each}
  </ol>
</div>
