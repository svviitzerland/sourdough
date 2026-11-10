<script>
  import { Baby, Blocks, Backpack, GraduationCap, LoaderCircle, X, Check } from "@lucide/svelte"
  import { baby, createBaby } from "./baby.svelte.js"
  import { COLORS } from "./colors.js"
  import Logo from "./Logo.svelte"
  import Avatar from "./Avatar.svelte"

  // first: the welcome screen when no baby exists yet. Otherwise a dialog.
  let { first = false, onclose = () => {} } = $props()

  const packs = { toddler: Blocks, preschooler: Backpack, kid: GraduationCap }
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
</script>

<div role="dialog" aria-modal="true" aria-label="Create a baby"
  class="animate-fade fixed inset-0 z-20 grid place-items-center overflow-y-auto bg-night-900/90 p-4 backdrop-blur-lg sm:p-6">
  <form onsubmit={submit} class="relative grid w-full max-w-xl gap-6 rounded-3xl border border-white/[0.06] bg-night-850 p-6 sm:p-8">
    {#if !first}
      <button type="button" onclick={onclose} title="Close"
        class="absolute right-4 top-4 grid size-9 place-items-center rounded-full text-mist hover:bg-night-700 hover:text-ink">
        <X class="size-5" />
      </button>
    {/if}

    <div class="grid justify-items-center gap-2 text-center">
      {#if first}<Logo size={52} />{:else}<Avatar profile={{ name: name || "?", color }} size="size-14" text="text-xl" />{/if}
      <h2 class="mt-1 text-2xl font-bold tracking-tight">{first ? "Meet your first Sourdough" : "A new baby"}</h2>
      <p class="max-w-md text-sm text-mist">
        Every Sourdough is born knowing nothing and learns only from you. Give it a name, and it will grow into its own character.
      </p>
    </div>

    <label class="grid gap-1.5">
      <span class="text-sm font-semibold">Name</span>
      <input bind:value={name} maxlength="40" placeholder="Kiki" autocomplete="off" required
        class="h-12 rounded-2xl border border-white/[0.07] bg-night-800 px-4 text-[15px] placeholder:text-fog focus:border-peach/50 focus:outline-none" />
      {#if name && !valid}
        <span class="text-xs text-rose">Use letters, numbers, dots, dashes or underscores, without spaces.</span>
      {:else if taken}
        <span class="text-xs text-rose">There is already a baby called {name}.</span>
      {/if}
    </label>

    <label class="grid gap-1.5">
      <span class="text-sm font-semibold">Who is it? <span class="font-normal text-fog">Optional</span></span>
      <input bind:value={about} maxlength="200" placeholder="A curious little robot who lives on my desk"
        class="h-12 rounded-2xl border border-white/[0.07] bg-night-800 px-4 text-[15px] placeholder:text-fog focus:border-peach/50 focus:outline-none" />
    </label>

    <div class="grid gap-2">
      <span class="text-sm font-semibold">Color</span>
      <div class="flex gap-3">
        {#each Object.entries(COLORS) as [key, c]}
          <button type="button" onclick={() => (color = key)} title={key} aria-pressed={color == key}
            class="grid size-9 place-items-center rounded-full bg-gradient-to-br {c.avatar} ring-offset-2 ring-offset-night-850 transition {color == key ? 'ring-2 ring-ink' : 'opacity-70 hover:opacity-100'}">
            {#if color == key}<Check class="size-4 text-night-900" strokeWidth={3} />{/if}
          </button>
        {/each}
      </div>
    </div>

    <div class="grid gap-2">
      <span class="text-sm font-semibold">How it starts</span>
      <button type="button" onclick={() => (level = "newborn")}
        class="flex items-center gap-3 rounded-2xl border p-4 text-left transition {level == 'newborn' ? 'border-peach/60 bg-peach/[0.07]' : 'border-white/[0.07] bg-night-800 hover:bg-night-700'}">
        <span class="grid size-10 shrink-0 place-items-center rounded-xl bg-peach/15 text-peach"><Baby class="size-5" /></span>
        <span class="flex-1">
          <b class="block font-semibold">Newborn <span class="ml-1 rounded-full bg-peach/15 px-2 py-0.5 text-xs font-medium text-peach">recommended</span></b>
          <span class="text-sm text-mist">Knows nothing. Every word it ever learns comes from you.</span>
        </span>
      </button>
      <p class="mt-2 text-xs text-fog">Or give it a starter pack. It runs the built-in lessons once, right now, then it is yours to raise.</p>
      <div class="grid grid-cols-3 gap-2">
        {#each baby.levels.filter((l) => l.name != "newborn") as l}
          {@const Icon = packs[l.name] || Blocks}
          <button type="button" onclick={() => (level = l.name)} title={l.about}
            class="grid gap-1 rounded-2xl border p-3 text-left transition {level == l.name ? 'border-peach/60 bg-peach/[0.07]' : 'border-white/[0.07] bg-night-800 hover:bg-night-700'}">
            <Icon class="size-[18px] text-mist" />
            <b class="text-sm font-semibold">{l.title}</b>
            <span class="text-xs leading-snug text-fog">{l.about}</span>
          </button>
        {/each}
      </div>
    </div>

    {#if error}<p class="text-sm text-rose">{error}</p>{/if}

    <button type="submit" disabled={!valid || taken || saving}
      class="flex h-12 items-center justify-center gap-2 rounded-2xl bg-peach font-semibold text-night-900 transition hover:bg-[#ffc4a3]">
      {#if saving}<LoaderCircle class="size-5 animate-spin" />{level == "newborn" ? "Bringing it to life" : "Running its lessons"}{:else}Create {name.trim() || "baby"}{/if}
    </button>
  </form>
</div>
