<script>
  import { onMount } from "svelte"
  import { Plus, Pencil, Trash2, X, LoaderCircle } from "@lucide/svelte"
  import { baby, openBaby, editBaby, deleteBaby, loadBabies } from "./baby.svelte.js"
  import { COLORS } from "./colors.js"
  import Avatar from "./Avatar.svelte"

  let { oncreate, onpick = () => {} } = $props()
  let mode = $state("list")   // list, edit or delete
  let about = $state("")
  let color = $state("peach")
  let working = $state("")

  onMount(loadBabies)

  async function pick(name) {
    if (name == baby.name) return onpick()
    working = name
    try {
      await openBaby(name)
      onpick()
    } finally {
      working = ""
    }
  }

  function startEdit() {
    about = baby.profile?.about || ""
    color = baby.profile?.color || "peach"
    mode = "edit"
  }

  async function saveEdit() {
    working = "edit"
    try {
      await editBaby({ about, color })
      mode = "list"
    } finally {
      working = ""
    }
  }

  async function remove() {
    working = "delete"
    try {
      await deleteBaby(baby.name)
      mode = "list"
    } finally {
      working = ""
    }
  }

  const words = (n) => `${n || 0} ${n == 1 ? "word" : "words"}`
</script>

<div class="material flex h-full flex-col">
  <div class="flex items-center justify-between px-5 pb-3 pt-5">
    <h1 class="title text-[22px]">Babies</h1>
    <button onclick={oncreate} title="New baby"
      class="grid size-8 place-items-center rounded-full bg-fill text-ink hover:bg-fill-strong">
      <Plus class="size-4" strokeWidth={2.4} />
    </button>
  </div>

  <ul class="flex-1 space-y-0.5 overflow-y-auto px-2.5">
    {#each baby.babies as b (b.name)}
      {@const current = b.name == baby.name}
      <li>
        <button onclick={() => pick(b.name)} disabled={!!working}
          class="flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors {current ? 'bg-blue text-white' : 'hover:bg-fill'}">
          <Avatar profile={b} size={38} />
          <span class="min-w-0 flex-1">
            <span class="block truncate text-[15px] font-semibold">{b.name}</span>
            <span class="block truncate text-[13px] {current ? 'text-white/80' : 'text-mute'}">
              {b.about || `${b.stage || "newborn"}, ${words(b.words)}`}
            </span>
          </span>
          {#if working == b.name}<LoaderCircle class="size-4 animate-spin" />{/if}
        </button>
      </li>
    {/each}
  </ul>

  <div class="border-t border-line p-3">
    {#if mode == "list"}
      <div class="flex gap-1">
        <button onclick={startEdit} class="flex h-9 flex-1 items-center justify-center gap-1.5 rounded-lg text-[13px] text-mute hover:bg-fill hover:text-ink">
          <Pencil class="size-3.5" />Edit
        </button>
        <button onclick={() => (mode = "delete")} class="flex h-9 flex-1 items-center justify-center gap-1.5 rounded-lg text-[13px] text-mute hover:bg-fill hover:text-red">
          <Trash2 class="size-3.5" />Delete
        </button>
      </div>
    {:else if mode == "edit"}
      <div class="animate-appear grid gap-3">
        <div class="flex items-center justify-between">
          <span class="text-[13px] font-semibold">Edit {baby.name}</span>
          <button onclick={() => (mode = "list")} class="grid size-7 place-items-center rounded-full text-mute hover:bg-fill"><X class="size-4" /></button>
        </div>
        <input bind:value={about} maxlength="200" placeholder="Who is it?"
          class="h-9 rounded-lg bg-fill px-3 text-[13px] placeholder:text-faint focus:outline-none focus:ring-2 focus:ring-blue/40" />
        <div class="flex gap-2">
          {#each Object.entries(COLORS) as [key, c]}
            <button onclick={() => (color = key)} title={c.name} aria-pressed={color == key}
              class="size-6 rounded-full {c.bg} ring-offset-2 ring-offset-surface {color == key ? 'ring-2 ring-ink/60' : ''}"></button>
          {/each}
        </div>
        <button onclick={saveEdit} disabled={working == "edit"} class="h-9 rounded-lg bg-blue text-[13px] font-semibold text-white">Save</button>
      </div>
    {:else}
      <div class="animate-appear grid gap-2">
        <p class="text-[13px]"><b class="font-semibold">Delete {baby.name}?</b> <span class="text-mute">It moves to the trash in ~/.sourdough, so it can still be restored.</span></p>
        <div class="flex gap-2">
          <button onclick={() => (mode = "list")} class="h-9 flex-1 rounded-lg bg-fill text-[13px] font-medium">Keep</button>
          <button onclick={remove} disabled={working == "delete"} class="h-9 flex-1 rounded-lg bg-red text-[13px] font-semibold text-white">Delete</button>
        </div>
      </div>
    {/if}
  </div>
</div>
