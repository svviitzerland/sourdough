<script>
  import { tick } from "svelte"
  import {
    Palette, Shapes, Hand, User, PawPrint, Globe, ArrowLeftRight, Hash, Boxes, BookOpen,
    FolderSearch, Eye, Zap, Check, X, LoaderCircle,
  } from "@lucide/svelte"
  import { baby, lesson, showAction } from "./baby.svelte.js"

  const icons = {
    colors: Palette, shapes: Shapes, routines: Hand, about_me: User, animals: PawPrint,
    world: Globe, opposites: ArrowLeftRight, counting: Hash, kinds: Boxes,
  }
  const actions = {
    explore: { icon: FolderSearch, about: "Opens a picture or text from its own folder" },
    glance: { icon: Eye, about: "Looks through the camera when it is on" },
  }

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

<div class="grid content-start gap-7 overflow-y-auto px-5 pb-6 pt-1">
  <section class="grid gap-3">
    <div class="flex items-center justify-between gap-3">
      <h2 class="text-lg font-bold">Lessons</h2>
      <div class="flex gap-0.5 rounded-xl bg-night-950/70 p-1" role="group" aria-label="Lesson language">
        {#each [["en", "English"], ["id", "Indonesia"]] as [code, name]}
          <button onclick={() => (language = code)}
            class="h-7 rounded-lg px-3 text-[13px] font-medium transition {language == code ? 'bg-night-700 text-ink' : 'text-mist hover:text-ink'}">
            {name}
          </button>
        {/each}
      </div>
    </div>
    <p class="text-sm text-mist">A lesson shows it things and names them for you, then quizzes it. It learns exactly as if you had done it yourself.</p>
    <div class="grid grid-cols-2 gap-2">
      {#each baby.lessons as l}
        {@const Icon = icons[l.name] || BookOpen}
        <button disabled={!!running} onclick={() => run(l.name)}
          class="group flex items-center gap-3 rounded-2xl border border-white/[0.06] bg-night-800 p-3 text-left transition hover:border-peach/30 hover:bg-night-700">
          <span class="grid size-9 shrink-0 place-items-center rounded-xl bg-night-950/60 text-peach">
            {#if running == l.name}<LoaderCircle class="size-[18px] animate-spin" />{:else}<Icon class="size-[18px]" />{/if}
          </span>
          <span class="min-w-0">
            <b class="block truncate text-sm font-semibold">{l.title[language] || l.title.en}</b>
            <span class="text-xs text-fog">{running == l.name ? "Teaching..." : `${l.size} things`}</span>
          </span>
        </button>
      {/each}
    </div>
  </section>

  {#if report}
    <section bind:this={shown} class="animate-arrive grid gap-3">
      <div class="flex items-baseline justify-between">
        <h3 class="text-lg font-bold">{report.lesson}</h3>
        <span class="text-sm font-semibold {report.score == report.total ? 'text-mint' : 'text-peach'}">{report.score} of {report.total} right</span>
      </div>
      <div class="grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-2">
        {#each report.results as r}
          <div class="grid gap-1 rounded-2xl border bg-night-800 p-1.5 pb-2 {r.correct ? 'border-transparent' : 'border-rose/40'}">
            {#if r.picture}
              <img src={r.picture} alt="" class="aspect-square w-full rounded-xl" />
            {:else}
              <span class="grid aspect-square place-items-center rounded-xl bg-night-950/60 p-2 text-center text-xs text-mist">"{r.prompt}"</span>
            {/if}
            <b class="px-1 text-sm font-semibold">{r.word}</b>
            <span class="flex items-center gap-1 px-1 text-xs text-fog">
              {#if r.correct}<Check class="size-3 shrink-0 text-mint" />{:else}<X class="size-3 shrink-0 text-rose" />{/if}
              <span class="truncate">{r.said || "no answer"}</span>
            </span>
          </div>
        {/each}
      </div>
    </section>
  {/if}

  <section class="grid gap-3">
    <h2 class="text-lg font-bold">Actions</h2>
    <p class="text-sm text-mist">Its body can do a few things, but it does not know what they are for. It tries them when bored and keeps doing whatever brings something new. Say a word, then show it here to teach it.</p>
    <div class="grid gap-2">
      {#each baby.state?.actions || [] as a}
        {@const info = actions[a.action] || { icon: Zap, about: "An action its body can do" }}
        <button onclick={() => showAction(a.action)}
          class="flex items-center gap-3 rounded-2xl border border-white/[0.06] bg-night-800 p-3 text-left transition hover:border-mint/30 hover:bg-night-700">
          <span class="grid size-9 shrink-0 place-items-center rounded-xl bg-mint/10 text-mint"><info.icon class="size-[18px]" /></span>
          <span class="min-w-0 flex-1">
            <b class="block text-sm font-semibold capitalize">{a.action}</b>
            <span class="text-xs text-fog">{info.about}</span>
          </span>
          {#if a.triggers.length}
            <span class="rounded-full bg-mint/10 px-2 py-0.5 text-xs text-mint">on "{a.triggers.join(", ")}"</span>
          {/if}
        </button>
      {/each}
    </div>
  </section>
</div>
