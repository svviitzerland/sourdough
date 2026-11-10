<script>
  import { onMount } from "svelte"
  import { Baby, Blocks, Backpack, GraduationCap, ArrowRight, LoaderCircle } from "@lucide/svelte"
  import { baby, babies, choose } from "./baby.svelte.js"
  import Logo from "./Logo.svelte"

  let { onclose } = $props()
  let data = $state(null)
  let opening = $state("")

  const looks = {
    newborn: { icon: Baby, strands: 0 },
    toddler: { icon: Blocks, strands: 8 },
    preschooler: { icon: Backpack, strands: 16 },
    kid: { icon: GraduationCap, strands: 30 },
  }
  const hues = ["#8ab4ff", "#c4a1ff", "#ffb38a", "#7ee0b5", "#ff8f9c"]

  onMount(async () => { data = await babies() })

  async function open(name, level) {
    opening = name
    await choose(name, level)
    onclose()
  }

  function strands(n) {
    return Array.from({ length: n }, (_, i) => ({
      a: 10 + ((i * 37) % 60), b: 10 + ((i * 53 + 11) % 60), color: hues[i % hues.length],
    }))
  }
</script>

<div role="dialog" aria-modal="true" aria-label="Choose a baby"
  class="animate-fade fixed inset-0 z-10 grid place-items-center overflow-y-auto bg-night-900/90 p-6 backdrop-blur-lg">
  <div class="grid w-full max-w-5xl justify-items-center gap-3 text-center">
    <Logo size={56} />
    <h2 class="mt-2 text-3xl font-bold tracking-tight md:text-4xl">Choose a baby</h2>
    <p class="mb-5 max-w-xl text-mist">Every Sourdough is born knowing nothing. The older ones have simply lived through more lessons already. Start with one that knows a little, or raise one from nothing.</p>

    {#if data}
      <div class="grid w-full grid-cols-2 gap-3 lg:grid-cols-4">
        {#each data.levels as l}
          {@const look = looks[l.name] || looks.toddler}
          {@const exists = data.babies.some((b) => b.name == l.name)}
          <button disabled={!!opening} onclick={() => open(l.name, l.name)}
            class="group grid content-start gap-2 rounded-3xl border border-white/[0.06] bg-night-850 p-4 text-left transition duration-300 hover:-translate-y-1 hover:border-peach/30 hover:bg-night-800">
            <svg viewBox="0 0 200 80" aria-hidden="true" class="mb-2 h-20 w-full rounded-2xl bg-night-950/70">
              {#each strands(look.strands) as s}
                <path d="M14 {s.a} C 80 {s.a}, 120 {s.b}, 186 {s.b}" stroke={s.color} stroke-opacity="0.55" fill="none" />
              {/each}
              {#if !look.strands}<circle cx="100" cy="40" r="6" fill="#ffb38a" />{/if}
            </svg>
            <span class="flex items-center gap-2">
              <look.icon class="size-[18px] text-peach" />
              <b class="text-lg font-bold">{l.title}</b>
            </span>
            <span class="text-sm leading-relaxed text-mist">{l.about}</span>
            <span class="mt-2 flex items-center gap-1.5 text-sm font-semibold text-peach">
              {#if opening == l.name}<LoaderCircle class="size-4 animate-spin" />Opening
              {:else}{exists ? "Open" : "Start"}<ArrowRight class="size-4 transition group-hover:translate-x-0.5" />{/if}
            </span>
          </button>
        {/each}
      </div>

      {@const others = data.babies.filter((b) => !(b.name in looks))}
      {#if others.length}
        <div class="mt-3 flex flex-wrap items-center justify-center gap-2 text-sm text-fog">
          <span>Or continue with</span>
          {#each others as b}
            <button disabled={!!opening} onclick={() => open(b.name)}
              class="h-9 rounded-full border border-white/[0.07] bg-night-800 px-4 font-medium text-ink hover:bg-night-700">
              {b.name} <span class="font-normal text-fog">{b.words} words</span>
            </button>
          {/each}
        </div>
      {/if}

      <button onclick={onclose} class="mt-2 h-9 rounded-full px-4 text-sm text-mist hover:text-ink">Keep talking to {baby.name}</button>
    {:else}
      <LoaderCircle class="size-6 animate-spin text-fog" />
    {/if}
  </div>
</div>
