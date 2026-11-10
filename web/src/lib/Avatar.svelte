<script>
  import { colorOf } from "./colors.js"

  // A small, still version of a character's face, for lists.
  let { profile, size = 36 } = $props()
  const color = $derived(colorOf(profile).css)
</script>

<svg viewBox="0 0 40 40" width={size} height={size} aria-hidden="true" class="shrink-0">
  <circle cx="20" cy="20" r="19" fill={color} />
  <circle cx="20" cy="20" r="19" fill="url(#avatar-shine)" />
  <defs>
    <radialGradient id="avatar-shine" cx="35%" cy="28%" r="70%">
      <stop offset="0" stop-color="white" stop-opacity="0.45" />
      <stop offset="1" stop-color="white" stop-opacity="0" />
    </radialGradient>
  </defs>
  <ellipse cx="14.5" cy="18.5" rx="2.4" ry="2.9" fill="#1b130f" />
  <ellipse cx="25.5" cy="18.5" rx="2.4" ry="2.9" fill="#1b130f" />
  <path d="M15.5 25.5 Q20 28.5 24.5 25.5" stroke="#3b1a14" stroke-width="1.8" stroke-linecap="round" fill="none" />
</svg>
