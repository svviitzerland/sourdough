// Everything the app knows about the baby it is showing, and every way to talk to it.
// Components read `baby` and call the functions below. Nothing else talks to the API.

import { api } from "./api.js"

let media = null    // the <video> or <img> the baby is looking at
let stream = null   // the live camera, when it is on
let nextId = 1

export const baby = $state({
  name: "",
  state: null,
  lessons: [],
  graph: { nodes: [], edges: [], active: [] },
  suggestions: [],
  messages: [],
  view: null,          // what is in front of its eyes: { kind, src, note }
  busy: false,
  thinking: false,     // waiting for an answer to something you said or showed
  voice: true,
  lang: "en",
  thinkingAt: 0,
  judged: 0,           // the id of the last message that was marked right or wrong
})

export const yes = () => (baby.lang == "id" ? "iya" : "yes")
export const no = () => (baby.lang == "id" ? "bukan" : "no")

// Starting up and switching babies.

export async function boot() {
  const [status, lessons] = await Promise.all([api("/api/state"), api("/api/lessons")])
  baby.lessons = lessons.lessons
  settle(status)
  setInterval(tick, 5000)
  setInterval(() => { if (stream) observe({ passive: true }) }, 1500)
}

export async function choose(name, level) {
  settle(await api("/api/baby", { name, level }))
}

export const babies = () => api("/api/babies")

function settle(status) {
  baby.name = status.name
  baby.messages = []
  baby.judged = 0
  apply(status.state)
  note(status.state.age ? `${status.name} is awake and listening` : `${status.name} was just born and knows nothing yet`)
  refresh()
}

function apply(state) {
  baby.state = state
  if (state.language) baby.lang = state.language
}

export async function refresh() {
  const [graph, ideas] = await Promise.all([api("/api/graph"), api("/api/suggestions")])
  baby.graph = graph
  baby.suggestions = ideas.prompts
}

// Talking and showing.

function push(message) {
  baby.messages.push({ id: nextId++, ...message })
  if (baby.messages.length > 150) baby.messages.shift()
}

export function note(text, image = null) {
  push({ from: "note", text, image })
}

function receive(r) {
  if (r.mode == "silent") return
  push({
    from: "baby",
    words: r.words,
    action: r.action,
    mode: r.mode,
    face: r.expression.replace(/\*/g, ""),
    initiative: r.initiative,
    judgeable: ["speak", "imitate", "do", "practice"].includes(r.mode),
  })
  baby.thinkingAt = performance.now()
  speak(r)
}

function snapshot() {
  if (!media) return null
  const w = media.videoWidth || media.naturalWidth
  const h = media.videoHeight || media.naturalHeight
  if (!w || !h) return null
  const scale = 320 / Math.max(w, h)
  const canvas = document.createElement("canvas")
  canvas.width = Math.round(w * scale)
  canvas.height = Math.round(h * scale)
  canvas.getContext("2d").drawImage(media, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL("image/jpeg", 0.85)
}

export async function observe({ text = "", passive = false, outcome_of = null } = {}) {
  if (passive && baby.busy) return
  const image = baby.view && baby.view.kind != "found" ? snapshot() : null
  if (!text && !image) return
  if (!passive && !outcome_of) push({ from: "you", text, image })
  baby.busy = true
  baby.thinking = !passive
  try {
    const data = await api("/api/observe", { text, image, passive, outcome_of })
    apply(data.state)
    receive(data.response)
    consequence(data)
    if (data.response.mode != "silent" || text) refresh()
  } catch (e) {
    note(`Could not reach its brain. ${e.message}`)
  } finally {
    baby.busy = false
    baby.thinking = false
  }
}

export const say = (text) => observe({ text })

export function judge(message, right) {
  baby.judged = message.id
  observe({ text: right ? yes() : no() })
}

function consequence(data) {
  const found = data.outcome
  if (found) {
    baby.view = { kind: "found", src: found.image, note: `found ${found.file}` }
    note(`It explored its world and found ${found.file}${found.text ? `: "${found.text}"` : ""}`, found.image)
    receive(found.response)
  }
  if (data.response.action == "glance" && stream) {
    setTimeout(() => observe({ outcome_of: "glance" }), 600)
  }
}

async function tick() {
  if (baby.busy || document.hidden) return
  try {
    const data = await api("/api/tick", { seconds: 5 })
    apply(data.state)
    if (data.response.mode != "silent") {
      receive(data.response)
      consequence(data)
      refresh()
    }
  } catch (e) {
    // the server may be restarting, the next beat will try again
  }
}

function speak(r) {
  if (!baby.voice || !("speechSynthesis" in window)) return
  const words = r.words.filter((w) => w != "?")
  if (!words.length) return
  const u = new SpeechSynthesisUtterance(words.join(" ") + (r.words.includes("?") ? "?" : ""))
  u.lang = baby.lang == "id" ? "id-ID" : "en-US"
  u.pitch = 1.7
  u.rate = 0.85
  speechSynthesis.cancel()
  speechSynthesis.speak(u)
}

export function toggleVoice() {
  baby.voice = !baby.voice
  if (!baby.voice && "speechSynthesis" in window) speechSynthesis.cancel()
}

// Its eyes.

export function setMedia(el) {
  media = el
}

export const cameraStream = () => stream

export async function startCamera() {
  stream = await navigator.mediaDevices.getUserMedia({ video: true })
  baby.view = { kind: "camera", src: null, note: "Hold something in the square and say what it is" }
}

export function showPicture(file) {
  if (!file || !file.type.startsWith("image/")) return
  stopCamera()
  baby.view = { kind: "picture", src: URL.createObjectURL(file), note: "Now say what it is" }
}

export function stopCamera() {
  if (stream) stream.getTracks().forEach((t) => t.stop())
  stream = null
}

export function closeView() {
  stopCamera()
  baby.view = null
  media = null
}

// Teaching, actions, sleep and the diary.

export async function lesson(name, language) {
  baby.busy = true
  try {
    const data = await api("/api/lesson", { name, language })
    apply(data.state)
    note(`Lesson ${data.lesson.lesson}: ${data.lesson.score} of ${data.lesson.total} right`)
    refresh()
    return data.lesson
  } finally {
    baby.busy = false
  }
}

export async function showAction(action) {
  const data = await api("/api/show", { action })
  apply(data.state)
  receive(data.response)
  consequence(data)
  refresh()
}

export async function sleep() {
  const data = await api("/api/sleep", {})
  apply(data.state)
  note(`${baby.name} slept and replayed ${data.report.replayed} memories`)
  refresh()
}

export const journal = () => api("/api/journal")
