<script>
  import { ChevronDown, Check, Plus, Pencil, Trash2, X, LoaderCircle } from "@lucide/svelte"
  import { baby, openBaby, editBaby, deleteBaby, loadBabies } from "./baby.svelte.js"
  import { COLORS } from "./colors.js"
  import Avatar from "./Avatar.svelte"

  let { oncreate } = $props()
  let open = $state(false)
  let mode = $state("list")   // list, edit or delete
  let about = $state("")
  let color = $state("peach")
  let working = $state("")

  async function toggle() {
    open = !open
    mode = "list"
    if (open) await loadBabies()
  }

  async function pick(name) {
    if (name == baby.name) return (open = false)
    working = name
    try {
      await openBaby(name)
      open = false
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
      open = false
      if (!baby.name) oncreate(true)
    } finally {
      working = ""
    }
  }
</script>

<div class="relative">
  <button onclick={toggle} aria-expanded={open} title="Your babies"
    class="group flex h-11 items-center gap-2.5 rounded-full border border-white/[0.06] bg-night-800/70 py-1 pl-1 pr-3 transition hover:bg-night-700">
    <Avatar profile={baby.profile} />
    <span class="font-semibold">{baby.name}</span>
    <span class="hidden rounded-full bg-white/[0.06] px-2 py-0.5 text-xs text-mist md:inline">{baby.state?.stage}</span>
    <span class="hidden text-sm text-mist lg:inline">{baby.state?.vocabulary.length} {baby.state?.vocabulary.length == 1 ? "word" : "words"}</span>
    <ChevronDown class="size-4 text-fog transition group-hover:text-ink {open ? 'rotate-180' : ''}" />
  </button>

  {#if open}
    <button class="fixed inset-0 z-20 cursor-default" onclick={() => (open = false)} aria-label="Close"></button>
    <div class="glass animate-arrive absolute left-0 top-14 z-30 w-[min(360px,calc(100vw-24px))] rounded-3xl p-2 shadow-2xl shadow-black/40">
      {#if mode == "list"}
        <p class="px-3 pb-1 pt-2 text-xs font-semibold uppercase tracking-wider text-fog">Your babies</p>
        <ul class="grid max-h-80 gap-0.5 overflow-y-auto">
          {#each baby.babies as b}
            <li>
              <button onclick={() => pick(b.name)} disabled={!!working}
                class="flex w-full items-center gap-3 rounded-2xl p-2 text-left transition hover:bg-night-700 {b.name == baby.name ? 'bg-night-700/60' : ''}">
                <Avatar profile={b} />
                <span class="min-w-0 flex-1">
                  <b class="block truncate font-semibold">{b.name}</b>
                  <span class="block truncate text-xs text-fog">{b.about || `${b.stage || "newborn"}, ${b.words || 0} ${b.words == 1 ? "word" : "words"}`}</span>
                </span>
                {#if working == b.name}<LoaderCircle class="size-4 animate-spin text-mist" />
                {:else if b.name == baby.name}<Check class="size-4 text-peach" />{/if}
              </button>
            </li>
          {/each}
        </ul>
        <div class="mt-1 grid gap-0.5 border-t border-white/[0.06] pt-1">
          <button onclick={() => { open = false; oncreate(false) }}
            class="flex items-center gap-3 rounded-2xl p-2.5 text-left text-sm font-medium hover:bg-night-700">
            <span class="grid size-9 place-items-center rounded-full border border-dashed border-white/20"><Plus class="size-4" /></span>
            New baby
          </button>
          <div class="flex gap-1 px-1 pb-1">
            <button onclick={startEdit} class="flex h-9 flex-1 items-center justify-center gap-2 rounded-xl text-sm text-mist hover:bg-night-700 hover:text-ink">
              <Pencil class="size-4" />Edit {baby.name}
            </button>
            <button onclick={() => (mode = "delete")} class="flex h-9 flex-1 items-center justify-center gap-2 rounded-xl text-sm text-mist hover:bg-rose/10 hover:text-rose">
              <Trash2 class="size-4" />Delete
            </button>
          </div>
        </div>
      {:else if mode == "edit"}
        <div class="grid gap-4 p-3">
          <div class="flex items-center justify-between">
            <b class="font-semibold">Edit {baby.name}</b>
            <button onclick={() => (mode = "list")} class="grid size-8 place-items-center rounded-full text-mist hover:bg-night-700"><X class="size-4" /></button>
          </div>
          <label class="grid gap-1.5">
            <span class="text-sm text-mist">Who is it?</span>
            <input bind:value={about} maxlength="200" placeholder="A curious little robot"
              class="h-11 rounded-xl border border-white/[0.07] bg-night-800 px-3 text-sm focus:border-peach/50 focus:outline-none" />
          </label>
          <div class="flex gap-2.5">
            {#each Object.entries(COLORS) as [key, c]}
              <button onclick={() => (color = key)} title={key} aria-pressed={color == key}
                class="size-8 rounded-full bg-gradient-to-br {c.avatar} ring-offset-2 ring-offset-night-850 {color == key ? 'ring-2 ring-ink' : 'opacity-60 hover:opacity-100'}"></button>
            {/each}
          </div>
          <button onclick={saveEdit} disabled={working == "edit"} class="h-10 rounded-xl bg-peach font-semibold text-night-900 hover:bg-[#ffc4a3]">Save</button>
        </div>
      {:else}
        <div class="grid gap-3 p-3">
          <b class="font-semibold">Delete {baby.name}?</b>
          <p class="text-sm text-mist">It moves to the trash folder in ~/.sourdough, so it can still be restored by hand. Everything it learned goes with it.</p>
          <div class="flex gap-2">
            <button onclick={() => (mode = "list")} class="h-10 flex-1 rounded-xl border border-white/[0.07] text-sm hover:bg-night-700">Keep it</button>
            <button onclick={remove} disabled={working == "delete"} class="flex h-10 flex-1 items-center justify-center gap-2 rounded-xl bg-rose/90 text-sm font-semibold text-night-900 hover:bg-rose">
              {#if working == "delete"}<LoaderCircle class="size-4 animate-spin" />{/if}Delete
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>
