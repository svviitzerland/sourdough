<script>
  import { Baby, Blocks, Backpack, GraduationCap, LoaderCircle, Check } from "@lucide/svelte"
  import { baby, createBaby } from "./baby.svelte.js"
  import { COLORS } from "./colors.js"
  import Avatar from "./Avatar.svelte"

  // first: the welcome screen when no baby exists yet. Otherwise a sheet.
  let { first = false, onclose = () => {} } = $props()

  const packs = { newborn: Baby, toddler: Blocks, preschooler: Backpack, kid: GraduationCap }
  let name = $state("")
  let about = $state("")
  let color = $state("peach")
  let level = $state("newborn")
  let saving = $state(false)
  let error = $state("")

  const valid = $derived(/^[\w.-]{1,40}$/.test(name.trim()))
  const taken = $derived(baby.babies.some((b) => b.name.toLowerCase() == name.trim().toLowerCase()))

  async function submit(e) {
    e.preventDefault()
    if (!valid || taken) return
    saving = true
    error = ""
    try {
      await createBaby({ name: name.trim(), about, color, level })
      onclose()
    } catch (err) {
      error = err.message
    } finally {
      saving = false
    }
  }

  const field = "h-11 w-full rounded-[10px] bg-fill px-3.5 text-[15px] placeholder:text-faint focus:outline-none focus:ring-2 focus:ring-blue/40"
</script>

<div role="dialog" aria-modal="true" aria-label="Create a baby"
  class="fixed inset-0 z-40 grid place-items-center overflow-y-auto p-4 sm:p-6 {first ? 'bg-bg' : 'bg-black/30'}">
  {#if !first}<button class="absolute inset-0 cursor-default" onclick={onclose} aria-label="Close"></button>{/if}
  <form onsubmit={submit} class="animate-appear relative grid w-full max-w-lg gap-5 rounded-[28px] bg-surface p-6 shadow-card sm:p-8">
    <div class="grid justify-items-center gap-2 text-center">
      <Avatar profile={{ color }} size={72} />
      <h2 class="title mt-1 text-[28px]">{first ? "Meet your first Sourdough" : "New baby"}</h2>
      <p class="max-w-sm text-[15px] text-mute">Every Sourdough is born knowing nothing and learns only from you.</p>
    </div>

    <div class="grid gap-2.5">
      <input bind:value={name} maxlength="40" placeholder="Name" aria-label="Name" autocomplete="off" required class={field} />
      {#if name && !valid}<span class="px-1 text-[12px] text-red">Letters, numbers, dots, dashes or underscores, no spaces.</span>
      {:else if taken}<span class="px-1 text-[12px] text-red">There is already a baby called {name}.</span>{/if}
      <input bind:value={about} maxlength="200" placeholder="Who is it? (optional)" aria-label="Who is it" class={field} />
    </div>

    <div class="flex items-center justify-between px-1">
      <span class="text-[15px]">Color</span>
      <div class="flex gap-2.5">
        {#each Object.entries(COLORS) as [key, c]}
          <button type="button" onclick={() => (color = key)} title={c.name} aria-pressed={color == key}
            class="grid size-7 place-items-center rounded-full {c.bg} ring-offset-2 ring-offset-surface transition {color == key ? 'ring-2 ring-ink/50' : ''}">
            {#if color == key}<Check class="size-3.5 text-white" strokeWidth={3.5} />{/if}
          </button>
        {/each}
      </div>
    </div>

    <div class="grid gap-2">
      <span class="px-1 text-[13px] text-mute">How it starts</span>
      <div class="divide-y divide-line overflow-hidden rounded-xl bg-fill">
        {#each baby.levels as l}
          {@const Icon = packs[l.name] || Blocks}
          <button type="button" onclick={() => (level = l.name)} class="flex w-full items-center gap-3 px-3.5 py-3 text-left">
            <span class="grid size-8 shrink-0 place-items-center rounded-[9px] text-white {l.name == 'newborn' ? 'bg-accent' : 'bg-blue'}"><Icon class="size-4" /></span>
            <span class="min-w-0 flex-1">
              <span class="block text-[15px] font-medium">{l.name == "newborn" ? "Newborn" : `${l.title} starter pack`}</span>
              <span class="block text-[13px] leading-snug text-mute">{l.name == "newborn" ? "Knows nothing. Every word comes from you." : l.about}</span>
            </span>
            {#if level == l.name}<Check class="size-5 shrink-0 text-blue" strokeWidth={3} />{/if}
          </button>
        {/each}
      </div>
      <p class="px-1 text-[12px] text-faint">A starter pack runs its lessons once, now. After that, it only learns from you.</p>
    </div>

    {#if error}<p class="text-[13px] text-red">{error}</p>{/if}

    <div class="flex gap-2">
      {#if !first}<button type="button" onclick={onclose} class="h-11 flex-1 rounded-[12px] bg-fill text-[15px] font-medium">Cancel</button>{/if}
      <button type="submit" disabled={!valid || taken || saving}
        class="flex h-11 flex-[2] items-center justify-center gap-2 rounded-[12px] bg-blue text-[15px] font-semibold text-white">
        {#if saving}<LoaderCircle class="size-4 animate-spin" />{level == "newborn" ? "Bringing it to life" : "Running its lessons"}{:else}Create{/if}
      </button>
    </div>
  </form>
</div>
