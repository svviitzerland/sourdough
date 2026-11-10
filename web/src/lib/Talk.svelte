<script>
  import { tick } from "svelte"
  import { Camera, CameraOff, Image, Mic, ArrowUp, X, Check, Zap, Plus, Volume2, VolumeX } from "@lucide/svelte"
  import {
    baby, say, judge, correct, answer, startCamera, showPicture, closeView, setMedia, cameraStream,
    note, toggleVoice,
  } from "./baby.svelte.js"
  import Face from "./Face.svelte"

  let text = $state("")
  let list
  let picker
  let video = $state(null)
  let listening = $state(null)
  let menu = $state(false)
  let fixing = $state(0)
  let fix = $state("")
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition

  const latest = $derived([...baby.messages].reverse().find((m) => m.from == "baby")?.id ?? 0)
  const open = (m) => m.id == latest && baby.settled < m.id
  const asks = (m) => m.mode == "ask" && m.image
  const judgeable = (m) => ["speak", "imitate", "do", "practice"].includes(m.mode)
  const teachable = (m) => !judgeable(m) && !!m.prompt
  const feelings = {
    happy: "is happy", upset: "is upset", curious: "is curious", bored: "is bored",
    confused: "is puzzled", sleepy: "is sleepy", calm: "is calm",
  }

  $effect(() => {
    baby.messages.length
    baby.thinking
    tick().then(() => list && list.scrollTo({ top: list.scrollHeight, behavior: "smooth" }))
  })

  $effect(() => {
    if (video && baby.view?.kind == "camera") {
      video.srcObject = cameraStream()
      setMedia(video)
    }
  })

  function submit(e) {
    e.preventDefault()
    const words = text.trim()
    if (!words && !baby.view) return
    text = ""
    say(words)
  }

  function sendFix(e, m) {
    e.preventDefault()
    const words = fix.trim()
    if (!words) return
    fix = ""
    fixing = 0
    if (asks(m)) answer(m, words)
    else correct(m, words)
  }

  async function camera() {
    menu = false
    if (baby.view?.kind == "camera") return closeView()
    try {
      await startCamera()
    } catch (e) {
      note(`The camera is not available. ${e.message}`)
    }
  }

  function listen() {
    if (listening) return listening.stop()
    if (!Recognition) return note("This browser cannot listen. Type instead, or try Chrome or Edge.")
    const rec = new Recognition()
    rec.lang = baby.lang == "id" ? "id-ID" : "en-US"
    rec.interimResults = true
    rec.onresult = (e) => {
      const result = e.results[e.results.length - 1]
      text = result[0].transcript
      if (result.isFinal) {
        text = ""
        say(result[0].transcript)
      }
    }
    rec.onend = () => { listening = null; baby.listening = false }
    rec.onerror = (e) => note(`Could not hear you. ${e.error}`)
    listening = rec
    baby.listening = true
    rec.start()
  }

  function pictureLoaded(e) {
    setMedia(e.currentTarget)
    say("")
  }
</script>

<div class="grid min-h-0 grid-rows-[auto_minmax(0,1fr)_auto]">
  <header class="grid justify-items-center gap-1 px-6 pb-3 pt-6">
    <div class="relative">
      <Face size={150} />
      <button onclick={toggleVoice} title={baby.voice ? "It speaks out loud" : "It is silent"}
        class="absolute -right-1 bottom-2 grid size-8 place-items-center rounded-full border border-line bg-surface text-mute shadow-card hover:text-ink">
        {#if baby.voice}<Volume2 class="size-4" />{:else}<VolumeX class="size-4" />{/if}
      </button>
    </div>
    <h2 class="title mt-1 text-[26px]">{baby.name}</h2>
    <p class="text-[13px] text-mute">
      {baby.state?.stage} · {baby.state?.vocabulary.length} {baby.state?.vocabulary.length == 1 ? "word" : "words"} · {feelings[baby.state?.feeling] || "is calm"}
    </p>
  </header>

  <ol bind:this={list} aria-live="polite"
    class="flex min-h-0 flex-col gap-1.5 overflow-y-auto px-4 pb-4 pt-2 [mask-image:linear-gradient(transparent,black_24px)] sm:px-8">
    {#if baby.messages.length <= 1}
      <li class="animate-arrive mx-auto my-6 max-w-sm text-center text-[15px] text-mute">
        {#if baby.profile?.about}<p class="mb-2 italic">{baby.profile.about}</p>{/if}
        <p>It learns like a small child. Show it something and say what it is, ask it things, and tell it the right answer when it gets something wrong.</p>
      </li>
    {/if}

    {#each baby.messages as m (m.id)}
      {#if m.from == "you"}
        <li class="animate-arrive grid max-w-[75%] justify-items-end gap-1 self-end">
          {#if m.image}<img src={m.image} alt="What you showed it" class="w-44 rounded-[18px] shadow-card" />{/if}
          {#if m.text}<p class="rounded-[20px] rounded-br-[6px] bg-blue px-3.5 py-2 text-[15px] leading-snug text-white">{m.text}</p>{/if}
        </li>
      {:else if m.from == "baby"}
        <li class="animate-arrive mt-1 grid max-w-[80%] justify-items-start gap-1 self-start">
          {#if m.initiative}<span class="px-1 text-[11px] font-medium uppercase tracking-wide text-faint">On its own</span>{/if}
          {#if asks(m)}<img src={m.image} alt="What it is asking about" class="w-36 rounded-[18px] shadow-card" />{/if}
          <p class="rounded-[20px] rounded-bl-[6px] bg-bubble px-3.5 py-2 text-[17px] font-medium leading-snug">
            {#if m.action}<span class="mr-1 inline-flex items-center gap-1 text-[13px] font-semibold text-green"><Zap class="size-3.5" />{m.action}</span>{/if}
            {m.words.join(" ") || (m.action ? "" : "...")}
          </p>

          {#if open(m) && asks(m)}
            <form onsubmit={(e) => sendFix(e, m)} class="animate-appear mt-1 flex w-72 max-w-full items-center gap-1.5 rounded-full bg-fill p-1 pl-4">
              <input bind:value={fix} placeholder="What is it?" aria-label="What is it?"
                class="h-8 min-w-0 flex-1 bg-transparent text-[15px] placeholder:text-mute focus:outline-none" />
              <button type="submit" class="grid size-8 place-items-center rounded-full bg-blue text-white"><ArrowUp class="size-4" strokeWidth={2.6} /></button>
            </form>
          {:else if open(m) && (judgeable(m) || teachable(m))}
            {#if fixing == m.id}
              <form onsubmit={(e) => sendFix(e, m)} class="animate-appear mt-1 grid w-80 max-w-full gap-1.5">
                <div class="flex items-center gap-1.5 rounded-full bg-fill p-1 pl-4">
                  <!-- svelte-ignore a11y_autofocus -->
                  <input bind:value={fix} autofocus aria-label="The right answer"
                    placeholder={teachable(m) ? `What should it say to "${m.prompt}"?` : "What is right?"}
                    class="h-8 min-w-0 flex-1 bg-transparent text-[15px] placeholder:text-mute focus:outline-none" />
                  <button type="submit" class="grid size-8 place-items-center rounded-full bg-blue text-white"><ArrowUp class="size-4" strokeWidth={2.6} /></button>
                </div>
                {#if judgeable(m)}
                  <button type="button" onclick={() => { fixing = 0; judge(m, false) }} class="justify-self-start px-3 text-[13px] text-mute hover:text-ink">Just tell it no</button>
                {/if}
              </form>
            {:else if teachable(m)}
              <button onclick={() => { fixing = m.id; fix = "" }} class="mt-1 rounded-full bg-fill px-3.5 py-1.5 text-[13px] font-medium text-blue hover:bg-fill-strong">
                Teach it what to say
              </button>
            {:else}
              <div class="mt-1 flex gap-1.5">
                <button onclick={() => judge(m, true)} class="flex items-center gap-1 rounded-full bg-green/15 px-3.5 py-1.5 text-[13px] font-semibold text-green hover:bg-green/25">
                  <Check class="size-3.5" strokeWidth={3} />Right
                </button>
                <button onclick={() => { fixing = m.id; fix = "" }} class="flex items-center gap-1 rounded-full bg-red/12 px-3.5 py-1.5 text-[13px] font-semibold text-red hover:bg-red/20">
                  <X class="size-3.5" strokeWidth={3} />Wrong
                </button>
              </div>
            {/if}
          {/if}
        </li>
      {:else}
        <li class="animate-arrive my-2 grid justify-items-center gap-1.5 self-center text-center text-xs text-mute">
          {#if m.image}<img src={m.image} alt="" class="w-16 rounded-xl" />{/if}
          <p class="max-w-sm">{m.text}</p>
        </li>
      {/if}
    {/each}

    {#if baby.thinking}
      <li class="mt-1 flex gap-1 self-start rounded-[20px] rounded-bl-[6px] bg-bubble px-4 py-3" aria-label="Thinking">
        {#each [0, 0.18, 0.36] as delay}
          <i class="size-2 animate-breathe rounded-full bg-mute" style:animation-delay="{delay}s"></i>
        {/each}
      </li>
    {/if}
  </ol>

  <footer class="grid gap-2 px-4 pb-4 pt-1 sm:px-8">
    {#if baby.view}
      <div class="animate-appear flex items-center gap-3 self-start rounded-2xl bg-fill p-1.5 pr-2">
        <div class="relative size-14 overflow-hidden rounded-xl bg-bg">
          {#if baby.view.kind == "camera"}
            <!-- svelte-ignore a11y_media_has_caption -->
            <video bind:this={video} autoplay muted playsinline class="size-full object-cover"></video>
          {:else}
            <img src={baby.view.src} alt="What it is looking at" class="size-full object-cover"
              onload={baby.view.kind == "picture" ? pictureLoaded : null} />
          {/if}
          <span class="absolute inset-[20%] rounded border-[1.5px] border-white/90" aria-hidden="true"></span>
        </div>
        <p class="text-[13px] text-mute">{baby.view.note}</p>
        <button onclick={closeView} title="Stop showing" class="grid size-7 place-items-center rounded-full text-mute hover:bg-fill-strong"><X class="size-4" /></button>
      </div>
    {/if}

    {#if baby.suggestions.length && !text}
      <div class="flex flex-wrap gap-1.5" aria-label="Things to try">
        {#each baby.suggestions as idea}
          <button onclick={() => say(idea)} class="rounded-full border border-line px-3 py-1.5 text-[13px] text-mute hover:bg-fill hover:text-ink">{idea}</button>
        {/each}
      </div>
    {/if}

    <form onsubmit={submit} autocomplete="off" class="flex items-end gap-2">
      <div class="relative">
        <button type="button" onclick={() => (menu = !menu)} title="Show it something" aria-expanded={menu}
          class="grid size-10 place-items-center rounded-full bg-fill text-mute transition hover:bg-fill-strong hover:text-ink">
          <Plus class="size-5 transition {menu ? 'rotate-45' : ''}" strokeWidth={2.2} />
        </button>
        {#if menu}
          <div class="material animate-appear absolute bottom-12 left-0 z-20 w-56 origin-bottom-left rounded-2xl border border-line p-1.5 shadow-card">
            <button type="button" onclick={camera} class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[15px] hover:bg-fill">
              {#if baby.view?.kind == "camera"}<CameraOff class="size-5 text-red" />Turn camera off{:else}<Camera class="size-5 text-blue" />Show with camera{/if}
            </button>
            <button type="button" onclick={() => { menu = false; picker.click() }} class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[15px] hover:bg-fill">
              <Image class="size-5 text-green" />Show a picture
            </button>
          </div>
        {/if}
      </div>
      <div class="flex min-h-10 flex-1 items-center rounded-[20px] border border-line bg-surface pl-4 pr-1 shadow-sm focus-within:border-blue/50">
        <input type="text" bind:value={text} placeholder="Message {baby.name}" aria-label="Say something"
          class="h-10 min-w-0 flex-1 bg-transparent text-[15px] placeholder:text-faint focus:outline-none" />
        {#if text}
          <button type="submit" title="Send" class="animate-appear grid size-8 place-items-center rounded-full bg-blue text-white">
            <ArrowUp class="size-[18px]" strokeWidth={2.6} />
          </button>
        {:else}
          <button type="button" onclick={listen} title={listening ? "Listening" : "Talk out loud"}
            class="grid size-8 place-items-center rounded-full transition {listening ? 'bg-red text-white' : 'text-mute hover:text-ink'}">
            <Mic class="size-[18px]" />
          </button>
        {/if}
      </div>
    </form>
    <input type="file" accept="image/*" hidden bind:this={picker}
      onchange={(e) => { showPicture(e.currentTarget.files[0]); e.currentTarget.value = "" }} />
  </footer>
</div>
