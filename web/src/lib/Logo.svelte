<script>
  // A round of dough with a few bubbles in it: a starter, alive.
  let { size = 28 } = $props()
</script>

<svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
  <defs>
    <radialGradient id="dough" cx="35%" cy="30%" r="75%">
      <stop offset="0" stop-color="#ffd9bf" />
      <stop offset="0.55" stop-color="#ffb38a" />
      <stop offset="1" stop-color="#e98b8f" />
    </radialGradient>
  </defs>
  <circle cx="16" cy="16" r="14" fill="url(#dough)" />
  <circle cx="11.5" cy="13" r="2.4" fill="#24130a" opacity="0.55" />
  <circle cx="19.5" cy="18.5" r="3.2" fill="#24130a" opacity="0.45" />
  <circle cx="18.5" cy="9.5" r="1.4" fill="#24130a" opacity="0.4" />
</svg>
