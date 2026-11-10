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
    if (m.event == "born") {
      return { icon: Baby, tint: "text-accent", text: m.level == "newborn" ? "Was born, knowing nothing" : `Was born with the ${m.level} starter pack` }
    }
    if (m.event == "sleep") return { icon: Moon, tint: "text-blue", text: `Slept, and let go of ${m.forgotten || 0} unused memories` }
    if (m.event == "lesson") return { icon: GraduationCap, tint: "text-purple", text: `Took the ${m.lesson} lesson, ${m.score} of ${m.total} right` }
    if (m.event == "feedback") {
      return m.amount > 0
        ? { icon: ThumbsUp, tint: "text-green", text: "Was told it was right" }
        : { icon: ThumbsDown, tint: "text-red", text: "Was told it was wrong" }
    }
    if (m.event == "taught") {
      const what = m.what == "name" ? `the word "${m.answer}" for a picture`
        : m.what == "reply" ? `to answer "${m.prompt}" with "${m.answer}"` : `to ${m.action} on "${m.prompt}"`
      return { icon: GraduationCap, tint: "text-accent", text: `Was taught ${what}` }
    }
    if (m.event == "corrected") return { icon: ThumbsDown, tint: "text-red", text: `Was corrected, the right answer is "${m.answer}"` }
    if (m.event == "fed") {
      const from = m.source == "ai" ? `an AI teacher${m.topic ? ` about ${m.topic}` : ""}` : m.source == "pictures" ? "pictures" : "a file"
      return { icon: GraduationCap, tint: "text-purple", text: `Learned from ${from}, ${m.correct} of ${m.taught} right` }
    }
    if (m.event == "explored") return { icon: FolderOpen, tint: "text-green", text: `Explored ${m.file}${m.said ? ` and said "${m.said}"` : ""}` }
    const heard = m.heard ? `Heard "${m.heard}"` : m.saw ? "Looked at something" : "Was quiet"
    const did = m.action ? `, then did ${m.action}` : m.said ? `, said "${m.said}"` : ""
    if (m.event == "initiative") return { icon: Sparkles, tint: "text-accent", text: `On its own${did}` }
    return { icon: MessageCircle, tint: "text-mute", text: `${heard}${did}` }
  }

  const time = (m) => new Date(m.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
</script>

<div class="grid gap-5 p-4 pb-8">
  {#if baby.state}
    <div class="grid grid-cols-3 gap-2">
      {#each [[Clock, baby.state.age, "moments lived", "text-blue"], [BookOpenText, baby.state.vocabulary.length, "words known", "text-accent"], [Waypoints, baby.state.links, "connections", "text-purple"]] as [Icon, value, label, tint]}
        <div class="grid gap-0.5 rounded-2xl bg-surface p-3 shadow-card">
          <Icon class="size-4 {tint}" />
          <b class="title mt-1 text-2xl">{value}</b>
          <span class="text-[12px] text-mute">{label}</span>
        </div>
      {/each}
    </div>

    <button onclick={async () => { await sleep(); load() }}
      class="flex items-center gap-3 rounded-2xl bg-surface p-3.5 text-left shadow-card hover:bg-raised">
      <span class="grid size-9 shrink-0 place-items-center rounded-[10px] bg-blue text-white"><Moon class="size-5" /></span>
      <span>
        <b class="block text-[15px] font-semibold">Put it to sleep</b>
        <span class="text-[13px] text-mute">Sleep turns today into lasting memory. It also sleeps by itself when tired.</span>
      </span>
    </button>
  {/if}

  <h2 class="title text-xl">Its life</h2>
  <ol class="divide-y divide-line overflow-hidden rounded-2xl bg-surface shadow-card">
    {#each moments as m}
      {@const d = describe(m)}
      <li class="grid grid-cols-[22px_1fr_auto] items-start gap-3 px-3.5 py-2.5">
        <d.icon class="mt-0.5 size-[18px] {d.tint}" />
        <p class="text-[13px]">{d.text}</p>
        <time class="text-[12px] text-faint">{time(m)}</time>
      </li>
    {:else}
      <li class="px-3.5 py-3 text-[13px] text-mute">Nothing has happened yet.</li>
    {/each}
  </ol>
</div>
