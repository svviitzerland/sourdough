<script>
  import { tick } from "svelte"
  import {
    baby, say, judge, startCamera, showPicture, closeView, setMedia, cameraStream, note,
  } from "./baby.svelte.js"
  import Icon from "./Icon.svelte"
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

<div class="talk">
  <ol class="messages" bind:this={list} aria-live="polite">
    {#if baby.messages.length <= 1}
      <li class="welcome">
        <Logo size={44} />
        <h2>Say hi to {baby.name}</h2>
        <p>It learns like a small child. Talk to it, show it things and say what they are, then tell it if it got them right.</p>
      </li>
    {/if}
    {#each baby.messages as m (m.id)}
      {#if m.from == "you"}
        <li class="you">
          {#if m.image}<img src={m.image} alt="What you showed it" />{/if}
          {#if m.text}<p>{m.text}</p>{:else}<p class="quiet">Look at this</p>{/if}
        </li>
      {:else if m.from == "baby"}
        <li class="baby">
          <span class="face"><Logo size={26} /></span>
          <div>
            {#if m.initiative}<small>on its own</small>{/if}
            <p class="words">
              {#if m.action}<span class="act">{m.action}</span>{/if}
              {m.words.join(" ") || (m.action ? "" : "...")}
            </p>
            {#if m.face}<small>{m.face}</small>{/if}
            {#if m.id == lastJudgeable && baby.judged < m.id}
              <div class="judge">
                <button class="right" onclick={() => judge(m, true)}><Icon name="check" />Right</button>
                <button class="wrong" onclick={() => judge(m, false)}><Icon name="cross" />Wrong</button>
              </div>
            {/if}
          </div>
        </li>
      {:else}
        <li class="note">
          {#if m.image}<img src={m.image} alt="" />{/if}
          <p>{m.text}</p>
        </li>
      {/if}
    {/each}
  </ol>

  <div class="bottom">
    {#if baby.view}
      <div class="eye">
        <div class="view">
          {#if baby.view.kind == "camera"}
            <!-- svelte-ignore a11y_media_has_caption -->
            <video bind:this={video} autoplay muted playsinline></video>
          {:else}
            <img src={baby.view.src} alt="What it is looking at" onload={baby.view.kind == "picture" ? pictureLoaded : null} />
          {/if}
          <span class="focus" aria-hidden="true"></span>
        </div>
        <p>{baby.view.note}</p>
        <button class="plain close" onclick={closeView} title="Stop showing"><Icon name="close" /></button>
      </div>
    {/if}

    {#if baby.suggestions.length && !text}
      <div class="ideas" aria-label="Things to try">
        {#each baby.suggestions as idea}
          <button onclick={() => say(idea)}>{idea}</button>
        {/each}
      </div>
    {/if}

    <div class="show">
      <button class:on={baby.view?.kind == "camera"} onclick={camera}>
        <Icon name="camera" />{baby.view?.kind == "camera" ? "Camera on" : "Show with camera"}
      </button>
      <button onclick={() => picker.click()}><Icon name="picture" />Show a picture</button>
    </div>

    <form onsubmit={submit} autocomplete="off">
      <input type="text" bind:value={text} placeholder={`Say something to ${baby.name}`} aria-label="Say something" />
      <button type="button" class="plain round" class:on={listening} onclick={listen} title={listening ? "Listening" : "Talk out loud"}>
        <Icon name="mic" />
      </button>
      <button type="submit" class="primary round" disabled={baby.busy && !text} title="Say it"><Icon name="send" /></button>
    </form>
    <input type="file" accept="image/*" hidden bind:this={picker}
      onchange={(e) => { showPicture(e.currentTarget.files[0]); e.currentTarget.value = "" }} />
  </div>
</div>

<style>
  .talk { display: grid; grid-template-rows: minmax(0, 1fr) auto; min-height: 0; min-width: 0; }

  .messages {
    list-style: none;
    margin: 0;
    padding: 4px 18px 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .messages > li { max-width: 86%; animation: arrive 0.45s var(--ease); }
  @keyframes arrive { from { opacity: 0; transform: translateY(8px); } }

  .welcome {
    align-self: center;
    text-align: center;
    display: grid;
    justify-items: center;
    gap: 8px;
    padding: 28px 8px 10px;
    max-width: 320px !important;
  }
  .welcome h2 { font-size: 20px; font-weight: 700; }
  .welcome p { color: var(--muted); font-size: 14px; }

  .you {
    align-self: flex-end;
    background: var(--card-hi);
    border-radius: 18px 18px 6px 18px;
    padding: 10px 14px;
    display: grid;
    gap: 8px;
  }
  .you img { width: 140px; border-radius: 12px; }
  .quiet { color: var(--muted); }

  .baby { align-self: flex-start; display: grid; grid-template-columns: auto 1fr; gap: 10px; }
  .face { padding-top: 4px; }
  .baby small { display: block; color: var(--faint); font-size: 13px; }
  .words { font-size: 26px; font-weight: 700; letter-spacing: -0.01em; line-height: 1.2; word-break: break-word; }
  .act {
    font-size: 12px;
    font-weight: 600;
    color: var(--accent-ink);
    background: var(--mint);
    border-radius: 999px;
    padding: 3px 9px;
    vertical-align: middle;
    margin-right: 6px;
  }
  .act::before { content: "does "; font-weight: 400; }
  .judge { display: flex; gap: 8px; margin-top: 10px; }
  .judge button { height: 36px; border-radius: 999px; padding: 0 14px; }
  .judge .right { background: rgba(126, 224, 181, 0.12); color: var(--mint); border-color: rgba(126, 224, 181, 0.25); }
  .judge .right:hover { background: rgba(126, 224, 181, 0.22); }
  .judge .wrong { background: rgba(255, 143, 156, 0.1); color: var(--rose); border-color: rgba(255, 143, 156, 0.22); }
  .judge .wrong:hover { background: rgba(255, 143, 156, 0.2); }

  .note {
    align-self: center;
    text-align: center;
    color: var(--faint);
    font-size: 13px;
    display: grid;
    gap: 6px;
    justify-items: center;
  }
  .note img { width: 76px; border-radius: 12px; }

  .bottom { padding: 10px 14px 14px; display: grid; gap: 10px; }

  .eye {
    display: grid;
    grid-template-columns: 64px 1fr auto;
    gap: 12px;
    align-items: center;
    background: var(--card);
    border-radius: 16px;
    padding: 8px;
    color: var(--muted);
    font-size: 13px;
  }
  .view { position: relative; aspect-ratio: 1; border-radius: 10px; overflow: hidden; background: var(--bg); }
  .view video, .view img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .focus { position: absolute; inset: 20%; border: 1.5px solid rgba(255, 255, 255, 0.85); border-radius: 6px; }
  .close { width: 36px; padding: 0; }

  .ideas { display: flex; flex-wrap: wrap; gap: 6px; }
  .ideas button {
    height: 32px;
    padding: 0 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 400;
    color: var(--muted);
    background: transparent;
  }
  .ideas button:hover { color: var(--text); }

  .show { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .show button { height: 40px; font-size: 13px; color: var(--muted); }
  .show button:hover { color: var(--text); }
  .show button.on { color: var(--accent); border-color: rgba(255, 179, 138, 0.4); }

  form {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 6px 6px 6px 16px;
    transition: border-color 0.2s var(--ease);
  }
  form:focus-within { border-color: rgba(255, 179, 138, 0.5); }
  form input { flex: 1; height: 40px; }
  .round { width: 40px; padding: 0; border-radius: 50%; }
  .round.on { color: var(--accent); background: rgba(255, 179, 138, 0.12); }
</style>
