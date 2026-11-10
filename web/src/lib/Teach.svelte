<script>
  import { tick } from "svelte"
  import {
    Palette, Shapes, Hand, User, PawPrint, Globe, ArrowLeftRight, Hash, Boxes, BookOpen,
    FolderSearch, Eye, Zap, Check, X, LoaderCircle, ImagePlus, MessageSquareReply, Image,
  } from "@lucide/svelte"
  import { baby, lesson, teach, readPicture } from "./baby.svelte.js"

  const lessonIcons = {
    colors: Palette, shapes: Shapes, routines: Hand, about_me: User, animals: PawPrint,
    world: Globe, opposites: ArrowLeftRight, counting: Hash, kinds: Boxes,
  }
  const actionInfo = {
    explore: { icon: FolderSearch, about: "opens a picture or text from its own folder" },
    glance: { icon: Eye, about: "looks through the camera, when it is on" },
  }
  const kinds = [
    { id: "name", label: "Name a picture", icon: Image },
    { id: "reply", label: "An answer", icon: MessageSquareReply },
    { id: "action", label: "An action", icon: Zap },
  ]

  let kind = $state("name")
  let picture = $state(null)
  let prompt = $state("")
  let answer = $state("")
  let action = $state("explore")
  let sending = $state(false)
  let done = $state("")
  let picker

  let report = $state(null)
  let running = $state("")
  let language = $state(baby.lang == "id" ? "id" : "en")
  let shown

  const ready = $derived(
    kind == "name" ? !!picture && !!answer.trim()
      : kind == "reply" ? !!prompt.trim() && !!answer.trim()
        : !!prompt.trim() && !!action,
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
        : kind == "reply" ? `Say "${prompt.trim()}" to it in Talk.` : `Say "${prompt.trim()}" and it will ${action}.`
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

  const field = "h-11 w-full rounded-xl border border-white/[0.07] bg-night-900/60 px-3 text-sm placeholder:text-fog focus:border-peach/50 focus:outline-none"
</script>

<div class="grid content-start gap-7 overflow-y-auto px-5 pb-6 pt-1">
  <section class="grid gap-3">
    <h2 class="text-lg font-bold">Teach it something</h2>
    <div class="grid grid-cols-3 gap-1 rounded-2xl bg-night-950/70 p-1">
      {#each kinds as k}
        <button onclick={() => { kind = k.id; done = "" }}
          class="flex h-9 items-center justify-center gap-1.5 rounded-xl text-[13px] font-medium transition {kind == k.id ? 'bg-night-700 text-ink' : 'text-mist hover:text-ink'}">
          <k.icon class="size-4" />{k.label}
        </button>
      {/each}
    </div>

    <form onsubmit={submit} class="grid gap-3 rounded-2xl border border-white/[0.06] bg-night-800 p-4">
      {#if kind == "name"}
        <p class="text-sm text-mist">Pick a picture and say what it is. One time is often enough.</p>
        <button type="button" onclick={() => picker.click()}
          ondragover={(e) => e.preventDefault()} ondrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files[0]) }}
          class="grid h-36 place-items-center overflow-hidden rounded-xl border border-dashed border-white/15 bg-night-900/60 text-sm text-mist transition hover:border-peach/40">
          {#if picture}
            <img src={picture} alt="The picture to name" class="h-full w-full object-contain" />
          {:else}
            <span class="grid justify-items-center gap-2"><ImagePlus class="size-6 text-fog" />Choose or drop a picture</span>
          {/if}
        </button>
        <input type="file" accept="image/*" hidden bind:this={picker} onchange={(e) => { choose(e.currentTarget.files[0]); e.currentTarget.value = "" }} />
        <input bind:value={answer} placeholder="What is it? For example: red, star, cat" class={field} />
      {:else if kind == "reply"}
        <p class="text-sm text-mist">Teach it what to answer when you say something.</p>
        <label class="grid gap-1.5 text-sm"><span class="text-fog">When I say</span>
          <input bind:value={prompt} placeholder="good morning" class={field} /></label>
        <label class="grid gap-1.5 text-sm"><span class="text-fog">it answers</span>
          <input bind:value={answer} placeholder="morning" class={field} /></label>
      {:else}
        <p class="text-sm text-mist">Its body can do a few things. It does not know what they are for until you show it, or it tries them itself and finds out.</p>
        <label class="grid gap-1.5 text-sm"><span class="text-fog">When I say</span>
          <input bind:value={prompt} placeholder="show me your pictures" class={field} /></label>
        <span class="text-sm text-fog">it does</span>
        <div class="grid gap-2">
          {#each baby.state?.actions || [] as a}
            {@const info = actionInfo[a.action] || { icon: Zap, about: "an action its body can do" }}
            <button type="button" onclick={() => (action = a.action)}
              class="flex items-center gap-3 rounded-xl border p-2.5 text-left transition {action == a.action ? 'border-mint/50 bg-mint/[0.07]' : 'border-white/[0.07] hover:bg-night-700'}">
              <span class="grid size-8 place-items-center rounded-lg bg-mint/10 text-mint"><info.icon class="size-4" /></span>
              <span class="flex-1 text-sm"><b class="font-semibold capitalize">{a.action}</b> <span class="text-fog">{info.about}</span></span>
              {#if a.triggers.length}<span class="text-xs text-mint">on "{a.triggers[0]}"</span>{/if}
            </button>
          {/each}
        </div>
      {/if}
      <button type="submit" disabled={!ready || sending}
        class="flex h-11 items-center justify-center gap-2 rounded-xl bg-peach font-semibold text-night-900 transition hover:bg-[#ffc4a3]">
        {#if sending}<LoaderCircle class="size-4 animate-spin" />{/if}Teach {baby.name}
      </button>
      {#if done}<p class="animate-arrive flex items-center gap-2 text-sm text-mint"><Check class="size-4" />{done}</p>{/if}
    </form>
  </section>

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
    <p class="text-sm text-mist">Ready made lessons that show and name many things at once, then quiz it.</p>
    <div class="grid grid-cols-2 gap-2">
      {#each baby.lessons as l}
        {@const Icon = lessonIcons[l.name] || BookOpen}
        <button disabled={!!running} onclick={() => run(l.name)}
          class="flex items-center gap-3 rounded-2xl border border-white/[0.06] bg-night-800 p-3 text-left transition hover:border-peach/30 hover:bg-night-700">
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
</div>
