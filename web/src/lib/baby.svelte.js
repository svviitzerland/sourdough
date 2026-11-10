// Everything the app knows about the open baby, and every way to talk to it.
// Components read `baby` and call the functions below. Nothing else talks to the API.

import { api } from "./api.js"

let media = null    // the <video> or <img> the baby is looking at
let stream = null   // the live camera, when it is on
let nextId = 1
let timers = []

export const baby = $state({
  ready: false,        // the first answer from the server has arrived
  name: null,          // null until a baby exists
  profile: null,
  state: null,
  babies: [],
  levels: [],
  lessons: [],
  graph: { nodes: [], edges: [], active: [] },
  suggestions: [],
  messages: [],
  view: null,          // what is in front of its eyes: { kind, src, note }
  busy: false,
  thinking: false,     // waiting for an answer to something you said or showed
  listening: false,    // the microphone is on
  moment: null,        // the latest thing that happened to its face: { kind, at, words, surprise, action }
  voice: true,
  lang: "en",
  thinkingAt: 0,
  settled: 0,          // the id of the last message that was answered, judged or corrected
})

export const yes = () => (baby.lang == "id" ? "iya" : "yes")
export const no = () => (baby.lang == "id" ? "bukan" : "no")

// Starting up.

export async function boot() {
  const [status, lessons, list] = await Promise.all([api("/api/state"), api("/api/lessons"), api("/api/babies")])
  baby.lessons = lessons.lessons
  baby.babies = list.babies
  baby.levels = list.levels
  if (status.name) settle(status)
  baby.ready = true
  timers.forEach(clearInterval)
  timers = [setInterval(tick, 5000), setInterval(() => { if (stream) observe({ passive: true }) }, 1500)]
}

function settle(status) {
  closeView()
  baby.name = status.name
  baby.profile = status.profile
  baby.messages = []
  baby.settled = 0
  apply(status.state)
  note(status.state.age ? `${status.name} is awake and listening` : `${status.name} was just born and knows nothing yet`)
  refresh()
}

function apply(state) {
  baby.state = state
  if (state.language) baby.lang = state.language
}

export async function refresh() {
  if (!baby.name) return
  const [graph, ideas] = await Promise.all([api("/api/graph"), api("/api/suggestions")])
  baby.graph = graph
  baby.suggestions = ideas.prompts
}

// Characters.

export async function loadBabies() {
  const list = await api("/api/babies")
  baby.babies = list.babies
  baby.levels = list.levels
  return list
}

export async function createBaby({ name, about, color, level }) {
  settle(await api("/api/babies", { name, about, color, level }))
  await loadBabies()
}

export async function openBaby(name) {
  settle(await api("/api/baby", { name }))
  await loadBabies()
}

export async function editBaby({ about, color }) {
  const status = await api("/api/baby/edit", { about, color })
  baby.profile = status.profile
  await loadBabies()
}

export async function deleteBaby(name) {
  const list = await api("/api/baby/delete", { name })
  baby.babies = list.babies
  if (list.current) {
    if (list.current != baby.name) settle(await api("/api/state"))
  } else {
    baby.name = null
    baby.profile = null
    baby.state = null
    baby.messages = []
  }
}

// Talking and showing.

function push(message) {
  baby.messages.push({ id: nextId++, ...message })
  if (baby.messages.length > 150) baby.messages.shift()
}

export function note(text, image = null) {
  push({ from: "note", text, image })
}

// What it said, plus what it was answering, so a correction can teach the right thing.
function receive(r, context = {}) {
  if (r.mode == "silent") return
  push({
    from: "baby",
    words: r.words,
    action: r.action,
    mode: r.mode,
    face: r.expression.replace(/\*/g, ""),
    initiative: r.initiative,
    prompt: context.prompt || "",
    image: context.image || null,
  })
  baby.thinkingAt = performance.now()
  feel(r.mode, { words: r.words.filter((w) => w != "?").length, surprise: r.surprise || 0, action: r.action })
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

async function send(path, body, context, mine = null) {
  if (mine) push(mine)
  baby.busy = true
  baby.thinking = !body.passive
  try {
    const data = await api(path, body)
    apply(data.state)
    receive(data.response, context)
    consequence(data)
    if (data.response.mode != "silent" || !body.passive) refresh()
    return data
  } catch (e) {
    note(`Something went wrong. ${e.message}`)
  } finally {
    baby.busy = false
    baby.thinking = false
  }
}

export async function observe({ text = "", passive = false, outcome_of = null } = {}) {
  if (passive && baby.busy) return
  const image = baby.view && baby.view.kind != "found" ? snapshot() : null
  if (!text && !image) return
  const mine = !passive && !outcome_of ? { from: "you", text, image } : null
  return send("/api/observe", { text, image, passive, outcome_of }, { prompt: text, image }, mine)
}

export const say = (text) => observe({ text })

// Something its face should react to.
function feel(kind, details = {}) {
  baby.moment = { kind, at: performance.now(), words: 0, surprise: 0, action: null, ...details }
}

export function judge(message, right) {
  baby.settled = message.id
  feel(right ? "praised" : "corrected")
  return observe({ text: right ? yes() : no() })
}

// It was wrong: say no and teach the right answer in one step.
export function correct(message, answer) {
  baby.settled = message.id
  feel("corrected")
  const mine = { from: "you", text: `${no()}, ${answer}`, image: null }
  const body = { answer, prompt: message.prompt, image: message.image }
  return send("/api/correct", body, { prompt: message.prompt, image: message.image }, mine)
}

// It asked "?" about something: tell it what it is.
export function answer(message, word) {
  baby.settled = message.id
  const mine = { from: "you", text: word, image: message.image }
  return send("/api/teach", { kind: "name", answer: word, image: message.image }, { image: message.image }, mine)
}

// The Teach tab's forms: name a picture, an answer, an action.
export async function teach(form) {
  const shown = { name: `This is ${form.answer}`, reply: `When I say "${form.prompt}", you say "${form.answer}"`,
    action: `When I say "${form.prompt}", you ${form.action}` }[form.kind]
  return send("/api/teach", form, { prompt: form.prompt, image: form.image }, { from: "you", text: shown, image: form.image })
}

function consequence(data) {
  const found = data.outcome
  if (found) {
    baby.view = { kind: "found", src: found.image, note: `found ${found.file}` }
    note(`It explored its folder and found ${found.file}${found.text ? `: "${found.text}"` : ""}`, found.image)
    receive(found.response, { image: found.image, prompt: found.text || "" })
  }
  if (data.response.action == "glance" && stream) {
    setTimeout(() => observe({ outcome_of: "glance" }), 600)
  }
}

async function tick() {
  if (!baby.name || baby.busy || document.hidden) return
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

// Lessons, actions, sleep and the diary.

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

export async function sleep() {
  const data = await api("/api/sleep", {})
  apply(data.state)
  note(`${baby.name} slept and replayed ${data.report.replayed} memories`)
  feel("sleep")
  refresh()
}

export const journal = () => api("/api/journal")

// Feeding from outside: pairs, named pictures, or another AI.

export const feeders = () => api("/api/feeders")

export async function feedFrom(body) {
  baby.busy = true
  baby.thinking = true
  try {
    const data = await api("/api/feed", body)
    apply(data.state)
    const what = body.source == "ai" ? `${body.provider} taught it about ${body.topic || "everyday things"}`
      : body.source == "pictures" ? "It learned from your pictures" : "It learned from your file"
    note(`${what}: ${data.report.correct} of ${data.report.taught} right`)
    if (data.report.correct) feel("praised")
    refresh()
    return data.report
  } finally {
    baby.busy = false
    baby.thinking = false
  }
}

// Reading a picture file into a data URL, for the teach forms.
export function readPicture(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}
