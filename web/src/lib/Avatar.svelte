<script>
  import { colorOf } from "./colors.js"

  // A character's round badge: the first letter of its name on its color.
  let { profile, size = "size-9", text = "text-sm" } = $props()
</script>

<span class="grid shrink-0 place-items-center rounded-full bg-gradient-to-br font-bold text-night-900 {colorOf(profile).avatar} {size} {text}">
  {(profile?.name || "?").slice(0, 1).toUpperCase()}
</span>
