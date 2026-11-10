<script>
  import { tick } from "svelte"
  import {
    Palette, Shapes, Hand, User, PawPrint, Globe, ArrowLeftRight, Hash, Boxes, BookOpen,
    FolderSearch, Eye, Zap, Check, X, LoaderCircle, ImagePlus, ChevronRight,
  } from "@lucide/svelte"
  import { baby, lesson, teach, readPicture } from "./baby.svelte.js"

  const lessonIcons = {
    colors: [Palette, "bg-pink"], shapes: [Shapes, "bg-purple"], routines: [Hand, "bg-accent"],
    about_me: [User, "bg-blue"], animals: [PawPrint, "bg-green"], world: [Globe, "bg-teal"],
    opposites: [ArrowLeftRight, "bg-red"], counting: [Hash, "bg-blue"], kinds: [Boxes, "bg-purple"],
  }
  const actionInfo = {
    explore: [FolderSearch, "opens a picture or text from its own folder"],
    glance: [Eye, "looks through the camera, when it is on"],
  }
  const kinds = [["name", "Name a picture"], ["reply", "An answer"], ["action", "An action"]]

  let kind = $state("name")
  let picture = $state(null)
  let prompt = $state("")
  let answer = $state("")
  let action = $state("explore")
  let sending = $state(false)
  let done = $state("")
  let picker = $state(null)
  let report = $state(null)
  let running = $state("")
  let language = $state(baby.lang == "id" ? "id" : "en")
  let shown = $state(null)

  const ready = $derived(
    kind == "name" ? !!picture && !!answer.trim()
      : kind == "reply" ? !!prompt.trim() && !!answer.trim() : !!prompt.trim() && !!action,
  )

  async function choose(file) {
    if (file && file.type.startsWith("image/")) picture = await readPicture(file)
  }

  async function submit(e) {
    e.preventDefault()
    if (!ready || sending) return
    sending = true
    try {
      await teach({ kind, image: picture, prompt: prompt.trim(), answer: answer.trim(), action })
      done = kind == "name" ? `It now links "${answer.trim()}" with that picture.`
        : kind == "reply" ? `Say "${prompt.trim()}" to it and see.` : `Say "${prompt.trim()}" and it will ${action}.`
      answer = ""
      prompt = ""
      picture = null
      setTimeout(() => (done = ""), 4000)
    } finally {
      sending = false
    }
  }

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

  const field = "h-10 w-full rounded-[10px] bg-fill px-3 text-[15px] placeholder:text-faint focus:outline-none focus:ring-2 focus:ring-blue/40"
</script>

<div class="grid gap-6 p-4 pb-8">
  <section class="grid gap-3">
    <h2 class="title text-xl">Teach it something</h2>
    <div class="grid grid-cols-3 rounded-[10px] bg-fill p-[3px]">
      {#each kinds as [id, label]}
        <button onclick={() => { kind = id; done = "" }}
          class="h-7 rounded-[8px] text-[13px] font-medium transition {kind == id ? 'bg-surface shadow-[0_1px_3px_rgba(0,0,0,0.12)]' : 'text-mute hover:text-ink'}">
          {label}
        </button>
      {/each}
    </div>

    <form onsubmit={submit} class="grid gap-3 rounded-2xl bg-surface p-4 shadow-card">
      {#if kind == "name"}
        <button type="button" onclick={() => picker.click()}
          ondragover={(e) => e.preventDefault()} ondrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files[0]) }}
          class="grid h-36 place-items-center overflow-hidden rounded-xl border border-dashed border-line text-[13px] text-mute hover:bg-fill">
          {#if picture}
            <img src={picture} alt="The picture to name" class="h-full w-full object-contain" />
          {:else}
            <span class="grid justify-items-center gap-1.5"><ImagePlus class="size-6 text-blue" />Choose or drop a picture</span>
          {/if}
        </button>
        <input type="file" accept="image/*" hidden bind:this={picker} onchange={(e) => { choose(e.currentTarget.files[0]); e.currentTarget.value = "" }} />
        <input bind:value={answer} placeholder="What is it? red, star, cat..." class={field} />
      {:else if kind == "reply"}
        <label class="grid gap-1 text-[13px] text-mute">When I say<input bind:value={prompt} placeholder="good morning" class={field} /></label>
        <label class="grid gap-1 text-[13px] text-mute">it answers<input bind:value={answer} placeholder="morning" class={field} /></label>
      {:else}
        <label class="grid gap-1 text-[13px] text-mute">When I say<input bind:value={prompt} placeholder="show me your pictures" class={field} /></label>
        <span class="text-[13px] text-mute">it does</span>
        <div class="divide-y divide-line overflow-hidden rounded-xl bg-fill">
          {#each baby.state?.actions || [] as a}
            {@const [Icon, about] = actionInfo[a.action] || [Zap, "an action its body can do"]}
            <button type="button" onclick={() => (action = a.action)} class="flex w-full items-center gap-3 px-3 py-2.5 text-left">
              <span class="grid size-7 place-items-center rounded-lg bg-green text-white"><Icon class="size-4" /></span>
              <span class="flex-1 text-[13px]"><b class="font-semibold capitalize">{a.action}</b> <span class="text-mute">{about}</span></span>
              {#if action == a.action}<Check class="size-4 text-blue" strokeWidth={3} />{/if}
            </button>
          {/each}
        </div>
      {/if}
      <button type="submit" disabled={!ready || sending}
        class="flex h-10 items-center justify-center gap-2 rounded-[10px] bg-blue text-[15px] font-semibold text-white">
        {#if sending}<LoaderCircle class="size-4 animate-spin" />{/if}Teach {baby.name}
      </button>
      {#if done}<p class="animate-arrive flex items-center gap-1.5 text-[13px] text-green"><Check class="size-4" />{done}</p>{/if}
    </form>
  </section>

  <section class="grid gap-3">
    <div class="flex items-center justify-between">
      <h2 class="title text-xl">Lessons</h2>
      <div class="flex rounded-[9px] bg-fill p-[2px]">
        {#each [["en", "EN"], ["id", "ID"]] as [code, name]}
          <button onclick={() => (language = code)} class="h-7 rounded-[7px] px-2.5 text-[12px] font-semibold {language == code ? 'bg-surface shadow-sm' : 'text-mute'}">{name}</button>
        {/each}
      </div>
    </div>
    <ul class="divide-y divide-line overflow-hidden rounded-2xl bg-surface shadow-card">
      {#each baby.lessons as l}
        {@const [Icon, tint] = lessonIcons[l.name] || [BookOpen, "bg-blue"]}
        <li>
          <button disabled={!!running} onclick={() => run(l.name)} class="flex w-full items-center gap-3 px-3.5 py-2.5 text-left hover:bg-fill">
            <span class="grid size-8 place-items-center rounded-[9px] text-white {tint}">
              {#if running == l.name}<LoaderCircle class="size-4 animate-spin" />{:else}<Icon class="size-4" />{/if}
            </span>
            <span class="flex-1 text-[15px]">{l.title[language] || l.title.en}</span>
            <span class="text-[13px] text-mute">{running == l.name ? "Teaching" : l.size}</span>
            <ChevronRight class="size-4 text-faint" />
          </button>
        </li>
      {/each}
    </ul>
  </section>

  {#if report}
    <section bind:this={shown} class="animate-arrive grid gap-3">
      <div class="flex items-baseline justify-between">
        <h3 class="text-[17px] font-semibold">{report.lesson}</h3>
        <span class="text-[13px] font-semibold {report.score == report.total ? 'text-green' : 'text-accent'}">{report.score} of {report.total} right</span>
      </div>
      <div class="grid grid-cols-[repeat(auto-fill,minmax(84px,1fr))] gap-2">
        {#each report.results as r}
          <div class="grid gap-1 rounded-xl bg-surface p-1.5 shadow-card {r.correct ? '' : 'ring-1 ring-red/50'}">
            {#if r.picture}
              <img src={r.picture} alt="" class="aspect-square w-full rounded-lg" />
            {:else}
              <span class="grid aspect-square place-items-center rounded-lg bg-fill p-1.5 text-center text-[12px] text-mute">"{r.prompt}"</span>
            {/if}
            <b class="px-1 text-[13px] font-semibold">{r.word}</b>
            <span class="flex items-center gap-1 px-1 text-[11px] text-mute">
              {#if r.correct}<Check class="size-3 shrink-0 text-green" />{:else}<X class="size-3 shrink-0 text-red" />{/if}
              <span class="truncate">{r.said || "no answer"}</span>
            </span>
          </div>
        {/each}
      </div>
    </section>
  {/if}
</div>
