<script>
  import { onMount } from "svelte"
  import { LoaderCircle, PanelLeft, PanelRight } from "@lucide/svelte"
  import { baby, boot } from "./lib/baby.svelte.js"
  import Sidebar from "./lib/Sidebar.svelte"
  import Talk from "./lib/Talk.svelte"
  import Inspector from "./lib/Inspector.svelte"
  import CreateBaby from "./lib/CreateBaby.svelte"
  import Avatar from "./lib/Avatar.svelte"

  let creating = $state(false)
  let failed = $state("")
  let sidebar = $state(false)     // as a sheet, on small screens
  let inspector = $state(false)   // as a sheet, on medium screens

  onMount(async () => {
    try {
      await boot()
    } catch (e) {
      failed = e.message
    }
  })
</script>

{#if failed}
  <div class="grid h-full place-items-center p-6 text-center">
    <div class="grid max-w-sm justify-items-center gap-3">
      <Avatar profile={null} size={56} />
      <p class="title text-xl">Cannot reach its brain</p>
      <p class="text-mute">Start it with <code class="rounded-md bg-fill px-1.5 py-0.5 text-ink">sourdough</code> in a terminal, then reload this page.</p>
      <p class="text-xs text-faint">{failed}</p>
    </div>
  </div>
{:else if !baby.ready}
  <div class="grid h-full place-items-center"><LoaderCircle class="size-6 animate-spin text-faint" /></div>
{:else if !baby.name}
  <CreateBaby first />
{:else}
  <div class="grid h-full grid-cols-1 md:grid-cols-[260px_minmax(0,1fr)] xl:grid-cols-[260px_minmax(0,1fr)_400px]">
    <aside class="hidden min-h-0 border-r border-line md:block">
      <Sidebar oncreate={() => (creating = true)} />
    </aside>

    <main class="relative grid min-h-0 min-w-0 bg-surface">
      <div class="absolute left-3 right-3 top-3 z-10 flex justify-between">
        <button onclick={() => (sidebar = true)} title="Your babies"
          class="grid size-9 place-items-center rounded-full text-mute hover:bg-fill md:invisible">
          <PanelLeft class="size-5" />
        </button>
        <button onclick={() => (inspector = true)} title="Mind, teaching and diary"
          class="grid size-9 place-items-center rounded-full text-mute hover:bg-fill xl:invisible">
          <PanelRight class="size-5" />
        </button>
      </div>
      <Talk />
    </main>

    <aside class="hidden min-h-0 border-l border-line xl:block">
      <Inspector />
    </aside>
  </div>

  {#if sidebar}
    <div class="fixed inset-0 z-30 md:hidden">
      <button class="absolute inset-0 bg-black/30" onclick={() => (sidebar = false)} aria-label="Close"></button>
      <div class="animate-appear absolute inset-y-0 left-0 w-[280px] shadow-card">
        <Sidebar oncreate={() => { sidebar = false; creating = true }} onpick={() => (sidebar = false)} />
      </div>
    </div>
  {/if}

  {#if inspector}
    <div class="fixed inset-0 z-30 xl:hidden">
      <button class="absolute inset-0 bg-black/30" onclick={() => (inspector = false)} aria-label="Close"></button>
      <div class="animate-appear absolute inset-y-0 right-0 w-[min(420px,100vw)] shadow-card">
        <Inspector onclose={() => (inspector = false)} />
      </div>
    </div>
  {/if}
{/if}

{#if creating && baby.name}
  <CreateBaby onclose={() => (creating = false)} />
{/if}
