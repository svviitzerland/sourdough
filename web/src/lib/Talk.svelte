<script>
  import { tick } from "svelte"
  import { Camera, CameraOff, ImagePlus, Mic, ArrowUp, X, Check, Zap } from "@lucide/svelte"
  import {
    baby, say, judge, startCamera, showPicture, closeView, setMedia, cameraStream, note,
  } from "./baby.svelte.js"
  import Logo from "./Logo.svelte"

  let text = $state("")
  let list
  let picker
  let video = $state(null)
  let listening = $state(null)
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition

  const lastJudgeable = $derived(
    [...baby.messages].reverse().find((m) => m.from == "baby" && m.judgeable)?.id ?? 0,
  )

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

  async function camera() {
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
    rec.onend = () => (listening = null)
    rec.onerror = (e) => note(`Could not hear you. ${e.error}`)
    listening = rec
    rec.start()
  }

  function pictureLoaded(e) {
    setMedia(e.currentTarget)
    say("")
  }
</script>

<div class="grid min-h-0 min-w-0 grid-rows-[minmax(0,1fr)_auto]">
  <ol bind:this={list} aria-live="polite" class="flex list-none flex-col gap-4 overflow-y-auto px-5 pb-4 pt-1">
    {#if baby.messages.length <= 1}
      <li class="animate-arrive mx-auto grid max-w-xs justify-items-center gap-2 py-8 text-center">
        <Logo size={52} />
        <h2 class="mt-1 text-xl font-bold">Say hi to {baby.name}</h2>
        <p class="text-sm text-mist">It learns like a small child. Talk to it, show it things and say what they are, then tell it if it got them right.</p>
      </li>
    {/if}

    {#each baby.messages as m (m.id)}
      {#if m.from == "you"}
        <li class="animate-arrive grid max-w-[85%] gap-2 self-end rounded-3xl rounded-br-md bg-night-600/70 px-4 py-2.5">
          {#if m.image}<img src={m.image} alt="What you showed it" class="w-36 rounded-2xl" />{/if}
          <p>{m.text || "Look at this"}</p>
        </li>
      {:else if m.from == "baby"}
        <li class="animate-arrive flex max-w-[88%] gap-3 self-start">
          <span class="mt-1 shrink-0"><Logo size={28} /></span>
          <div class="min-w-0">
            {#if m.initiative}<p class="text-xs font-medium text-fog">On its own</p>{/if}
            <p class="break-words text-[26px] font-bold leading-tight tracking-tight">
              {#if m.action}
                <span class="mr-1.5 inline-flex translate-y-[-3px] items-center gap-1 rounded-full bg-mint/15 px-2.5 py-1 align-middle text-xs font-semibold text-mint">
                  <Zap class="size-3" />does {m.action}
                </span>
              {/if}
              {m.words.join(" ") || (m.action ? "" : "...")}
            </p>
            {#if m.face}<p class="text-sm text-fog">{m.face}</p>{/if}
            {#if m.id == lastJudgeable && baby.judged < m.id}
              <div class="mt-3 flex gap-2">
                <button onclick={() => judge(m, true)}
                  class="flex h-9 items-center gap-1.5 rounded-full border border-mint/25 bg-mint/10 px-4 text-sm font-medium text-mint transition hover:bg-mint/20">
                  <Check class="size-4" />Right
                </button>
                <button onclick={() => judge(m, false)}
                  class="flex h-9 items-center gap-1.5 rounded-full border border-rose/25 bg-rose/10 px-4 text-sm font-medium text-rose transition hover:bg-rose/20">
                  <X class="size-4" />Wrong
                </button>
              </div>
            {/if}
          </div>
        </li>
      {:else}
        <li class="animate-arrive grid max-w-[92%] justify-items-center gap-2 self-center text-center text-[13px] text-fog">
          {#if m.image}<img src={m.image} alt="" class="w-20 rounded-xl" />{/if}
          <p>{m.text}</p>
        </li>
      {/if}
    {/each}

    {#if baby.thinking}
      <li class="flex items-center gap-3 self-start" aria-label="Thinking">
        <Logo size={28} />
        <span class="flex gap-1">
          <i class="size-2 animate-breathe rounded-full bg-peach"></i>
          <i class="size-2 animate-breathe rounded-full bg-peach [animation-delay:0.2s]"></i>
          <i class="size-2 animate-breathe rounded-full bg-peach [animation-delay:0.4s]"></i>
        </span>
      </li>
    {/if}
  </ol>

  <div class="grid gap-2.5 px-4 pb-4 pt-2">
    {#if baby.view}
      <div class="animate-arrive grid grid-cols-[64px_1fr_auto] items-center gap-3 rounded-2xl bg-night-800 p-2 text-sm text-mist">
        <div class="relative aspect-square overflow-hidden rounded-xl bg-night-950">
          {#if baby.view.kind == "camera"}
            <!-- svelte-ignore a11y_media_has_caption -->
            <video bind:this={video} autoplay muted playsinline class="size-full object-cover"></video>
          {:else}
            <img src={baby.view.src} alt="What it is looking at" class="size-full object-cover"
              onload={baby.view.kind == "picture" ? pictureLoaded : null} />
          {/if}
          <span class="absolute inset-[20%] rounded-md border-[1.5px] border-white/85" aria-hidden="true"></span>
        </div>
        <p>{baby.view.note}</p>
        <button onclick={closeView} title="Stop showing" class="grid size-9 place-items-center rounded-full text-mist hover:bg-night-700 hover:text-ink">
          <X class="size-4" />
        </button>
      </div>
    {/if}

    {#if baby.suggestions.length && !text}
      <div class="flex flex-wrap gap-1.5" aria-label="Things to try">
        {#each baby.suggestions as idea}
          <button onclick={() => say(idea)}
            class="h-8 rounded-full border border-white/[0.07] px-3 text-[13px] text-mist transition hover:border-peach/40 hover:text-ink">
            {idea}
          </button>
        {/each}
      </div>
    {/if}

    <div class="grid grid-cols-2 gap-2">
      <button onclick={camera}
        class="flex h-10 items-center justify-center gap-2 rounded-xl border text-[13px] font-medium transition {baby.view?.kind == 'camera' ? 'border-peach/40 bg-peach/10 text-peach' : 'border-white/[0.06] bg-night-800 text-mist hover:text-ink'}">
        {#if baby.view?.kind == "camera"}<CameraOff class="size-4" />Turn camera off{:else}<Camera class="size-4" />Show with camera{/if}
      </button>
      <button onclick={() => picker.click()}
        class="flex h-10 items-center justify-center gap-2 rounded-xl border border-white/[0.06] bg-night-800 text-[13px] font-medium text-mist transition hover:text-ink">
        <ImagePlus class="size-4" />Show a picture
      </button>
    </div>

    <form onsubmit={submit} autocomplete="off"
      class="flex items-center gap-1.5 rounded-2xl border border-white/[0.07] bg-night-800 py-1.5 pl-4 pr-1.5 transition focus-within:border-peach/50">
      <input type="text" bind:value={text} placeholder={`Say something to ${baby.name}`} aria-label="Say something"
        class="h-10 min-w-0 flex-1 bg-transparent text-[15px] placeholder:text-fog focus:outline-none" />
      <button type="button" onclick={listen} title={listening ? "Listening" : "Talk out loud"}
        class="grid size-10 place-items-center rounded-full transition {listening ? 'bg-peach/15 text-peach' : 'text-mist hover:bg-night-700 hover:text-ink'}">
        <Mic class="size-[18px]" />
      </button>
      <button type="submit" disabled={baby.busy && !text} title="Say it"
        class="grid size-10 place-items-center rounded-full bg-peach text-night-900 transition hover:bg-[#ffc4a3]">
        <ArrowUp class="size-[18px]" strokeWidth={2.5} />
      </button>
    </form>
    <input type="file" accept="image/*" hidden bind:this={picker}
      onchange={(e) => { showPicture(e.currentTarget.files[0]); e.currentTarget.value = "" }} />
  </div>
</div>
