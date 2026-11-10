<script>
  import { onMount } from "svelte"
  import { Sparkles, Images, FileText, LoaderCircle, Check, X, KeyRound, CircleCheck } from "@lucide/svelte"
  import { baby, feeders, feedFrom, readPicture } from "./baby.svelte.js"

  // Three ways to feed it from outside. Each becomes ordinary teaching:
  // it hears the question and the answer, or sees the picture while its word is said.
  const sources = [
    { id: "ai", label: "AI teacher", icon: Sparkles },
    { id: "pictures", label: "Pictures", icon: Images },
    { id: "file", label: "File", icon: FileText },
  ]
  let source = $state("ai")
  let providers = $state([])
  let provider = $state("openai")
  let model = $state("")
  let key = $state("")
  let url = $state("")
  let topic = $state("")
  let count = $state(12)
  let language = $state(baby.lang == "id" ? "id" : "en")
  let pictures = $state([])
  let pairs = $state([])
  let fileName = $state("")
  let running = $state(false)
  let report = $state(null)
  let error = $state("")

  const current = $derived(providers.find((p) => p.name == provider))

  onMount(async () => {
    providers = (await feeders()).providers
    pick(providers.find((p) => p.ready)?.name || "openai")
  })

  function pick(name) {
    provider = name
    model = providers.find((p) => p.name == name)?.model || ""
  }

  async function addPictures(files) {
    for (const file of files) {
      if (!file.type.startsWith("image/")) continue
      const label = file.name.replace(/\.[^.]+$/, "").replace(/[\d_\-.]+/g, " ").trim().toLowerCase()
      pictures = [...pictures, { image: await readPicture(file), label }]
    }
  }

  async function readFile(file) {
    if (!file) return
    fileName = file.name
    const text = await file.text()
    try {
      if (file.name.toLowerCase().endsWith(".csv")) {
        pairs = text.split(/\r?\n/).map((line) => line.split(",")).filter((r) => r.length >= 2 && r[0].trim())
          .map(([prompt, ...rest]) => ({ prompt: prompt.trim(), answer: rest.join(",").trim() }))
          .filter((p) => !["prompt", "question", "say", "when"].includes(p.prompt.toLowerCase()))
      } else {
        const data = JSON.parse(text)
        pairs = (Array.isArray(data) ? data : data.pairs || []).map((p) => ({
          prompt: p.prompt || p.say || p.question || "", answer: p.answer || p.reply || "",
        })).filter((p) => p.prompt && p.answer)
      }
      error = pairs.length ? "" : "No prompts and answers found in that file."
    } catch (e) {
      error = `Could not read that file. ${e.message}`
      pairs = []
    }
  }

  const ready = $derived(
    source == "ai" ? !!model && (current?.ready || !!key || provider == "custom")
      : source == "pictures" ? pictures.some((p) => p.label) : pairs.length > 0,
  )

  async function run() {
    running = true
    error = ""
    report = null
    try {
      const body = source == "ai"
        ? { source: "ai", provider, model, api_key: key || undefined, base_url: url || undefined, topic, count, language }
        : source == "pictures"
          ? { source: "pictures", pictures: pictures.filter((p) => p.label) }
          : { source: "pairs", pairs }
      report = await feedFrom(body)
      key = ""
    } catch (e) {
      error = e.message
    } finally {
      running = false
    }
  }

  const field = "h-10 w-full rounded-[10px] bg-fill px-3 text-[15px] placeholder:text-faint focus:outline-none focus:ring-2 focus:ring-blue/40"
</script>

<div class="grid gap-5 p-4 pb-8">
  <div>
    <h2 class="title text-xl">Feed it</h2>
    <p class="mt-1 text-[13px] text-mute">Bring in things to learn from outside. It still learns by experience: it hears each question and answer, or sees each picture while its word is said.</p>
  </div>

  <div class="grid grid-cols-3 gap-2">
    {#each sources as s}
      <button onclick={() => { source = s.id; report = null; error = "" }}
        class="grid justify-items-center gap-1.5 rounded-2xl border p-3 text-[13px] font-medium transition {source == s.id ? 'border-blue bg-blue/8 text-blue' : 'border-line bg-surface text-mute hover:text-ink'}">
        <s.icon class="size-5" />{s.label}
      </button>
    {/each}
  </div>

  <section class="grid gap-3 rounded-2xl bg-surface p-4 shadow-card">
    {#if source == "ai"}
      <p class="text-[13px] text-mute">Another AI writes short questions and answers about a topic, like a patient teacher.</p>
      <div class="flex flex-wrap gap-1.5">
        {#each [...providers.map((p) => p.name), "custom"] as name}
          <button onclick={() => pick(name)}
            class="rounded-full px-3 py-1.5 text-[13px] font-medium capitalize transition {provider == name ? 'bg-ink text-surface' : 'bg-fill text-mute hover:text-ink'}">
            {name == "openai" ? "OpenAI" : name == "openrouter" ? "OpenRouter" : name}
          </button>
        {/each}
      </div>
      <label class="grid gap-1 text-[13px] text-mute">Model<input bind:value={model} placeholder="model name" class={field} /></label>
      {#if provider == "custom"}
        <label class="grid gap-1 text-[13px] text-mute">Base URL<input bind:value={url} placeholder="https://api.example.com/v1" class={field} /></label>
      {/if}
      {#if current?.ready}
        <p class="flex items-center gap-1.5 text-[13px] text-green"><CircleCheck class="size-4" />{current.key ? `Ready, using ${current.key}` : "No key needed. It runs on this computer."}</p>
      {:else if provider != "ollama"}
        <label class="grid gap-1 text-[13px] text-mute">
          <span class="flex items-center gap-1.5"><KeyRound class="size-3.5" />API key</span>
          <input bind:value={key} type="password" placeholder={current?.key ? `or set ${current.key}` : "sk-..."} class={field} autocomplete="off" />
          <span class="text-[12px] text-faint">Kept in memory while Sourdough runs. Never saved to disk.</span>
        </label>
      {/if}
      <label class="grid gap-1 text-[13px] text-mute">Topic<input bind:value={topic} placeholder="animals and their sounds" class={field} /></label>
      <div class="flex items-center gap-3">
        <label class="flex flex-1 items-center gap-2 text-[13px] text-mute">
          {count} lessons
          <input type="range" min="4" max="30" bind:value={count} class="flex-1 accent-blue" />
        </label>
        <div class="flex rounded-[9px] bg-fill p-[2px]">
          {#each [["en", "EN"], ["id", "ID"]] as [code, name]}
            <button onclick={() => (language = code)} class="h-7 rounded-[7px] px-2.5 text-[12px] font-semibold {language == code ? 'bg-surface shadow-sm' : 'text-mute'}">{name}</button>
          {/each}
        </div>
      </div>
    {:else if source == "pictures"}
      <p class="text-[13px] text-mute">Each picture teaches the word in its name: <i>apple.jpg</i> teaches "apple". You can change the words below.</p>
      <label class="grid h-24 cursor-pointer place-items-center rounded-xl border border-dashed border-line text-[13px] text-mute hover:bg-fill">
        Choose pictures
        <input type="file" accept="image/*" multiple hidden onchange={(e) => { addPictures([...e.currentTarget.files]); e.currentTarget.value = "" }} />
      </label>
      {#if pictures.length}
        <div class="grid max-h-64 grid-cols-3 gap-2 overflow-y-auto">
          {#each pictures as p, i}
            <div class="relative grid gap-1">
              <img src={p.image} alt="" class="aspect-square w-full rounded-xl object-cover" />
              <input bind:value={p.label} class="h-7 rounded-md bg-fill px-2 text-[12px] focus:outline-none" />
              <button onclick={() => (pictures = pictures.filter((_, j) => j != i))} title="Remove"
                class="absolute right-1 top-1 grid size-5 place-items-center rounded-full bg-black/50 text-white"><X class="size-3" /></button>
            </div>
          {/each}
        </div>
      {/if}
    {:else}
      <p class="text-[13px] text-mute">A JSON file like <code class="text-ink">[{"{"}"prompt": "what do bees make", "answer": "honey"{"}"}]</code>, or a CSV with two columns: prompt, answer.</p>
      <label class="grid h-20 cursor-pointer place-items-center rounded-xl border border-dashed border-line text-[13px] text-mute hover:bg-fill">
        {fileName || "Choose a JSON or CSV file"}
        <input type="file" accept=".json,.csv,application/json,text/csv" hidden onchange={(e) => readFile(e.currentTarget.files[0])} />
      </label>
      {#if pairs.length}<p class="text-[13px] text-green">{pairs.length} prompts and answers found.</p>{/if}
    {/if}

    {#if error}<p class="text-[13px] text-red">{error}</p>{/if}
    <button onclick={run} disabled={!ready || running}
      class="flex h-10 items-center justify-center gap-2 rounded-[10px] bg-blue text-[15px] font-semibold text-white">
      {#if running}<LoaderCircle class="size-4 animate-spin" />{source == "ai" ? "Asking the teacher" : "Teaching"}{:else}Feed {baby.name}{/if}
    </button>
  </section>

  {#if report}
    <section class="animate-arrive grid gap-2">
      <p class="text-[15px] font-semibold">It got {report.correct} of {report.taught} right afterwards</p>
      <ul class="divide-y divide-line overflow-hidden rounded-2xl bg-surface shadow-card">
        {#each report.checked as c}
          <li class="flex items-center gap-2.5 px-3.5 py-2.5 text-[13px]">
            {#if c.correct}<Check class="size-4 shrink-0 text-green" />{:else}<X class="size-4 shrink-0 text-red" />{/if}
            <span class="min-w-0 flex-1 truncate text-mute">{c.prompt || "a picture"}</span>
            <span class="font-medium">{c.answer}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/if}
</div>
