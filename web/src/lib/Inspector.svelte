<script>
  import { X } from "@lucide/svelte"
  import Mind from "./Mind.svelte"
  import Teach from "./Teach.svelte"
  import Feed from "./Feed.svelte"
  import Diary from "./Diary.svelte"

  let { onclose = null } = $props()
  const tabs = [["mind", "Mind"], ["teach", "Teach"], ["feed", "Feed"], ["diary", "Diary"]]
  let tab = $state("mind")
</script>

<div class="flex h-full flex-col bg-bg">
  <div class="flex items-center gap-2 p-3">
    <div class="grid flex-1 grid-cols-4 rounded-[10px] bg-fill p-[3px]" role="tablist">
      {#each tabs as [id, label]}
        <button role="tab" aria-selected={tab == id} onclick={() => (tab = id)}
          class="h-7 rounded-[8px] text-[13px] font-medium transition {tab == id ? 'bg-surface shadow-[0_1px_3px_rgba(0,0,0,0.12)]' : 'text-mute hover:text-ink'}">
          {label}
        </button>
      {/each}
    </div>
    {#if onclose}
      <button onclick={onclose} title="Close" class="grid size-8 place-items-center rounded-full text-mute hover:bg-fill"><X class="size-5" /></button>
    {/if}
  </div>

  <div class="relative min-h-0 flex-1">
    {#if tab == "mind"}
      <Mind />
    {:else}
      <div class="absolute inset-0 overflow-y-auto">
        {#if tab == "teach"}<Teach />{:else if tab == "feed"}<Feed />{:else}<Diary />{/if}
      </div>
    {/if}
  </div>
</div>
