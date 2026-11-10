<script>
  // One small set of line icons, drawn on a 16 unit grid with the same stroke.
  let { name } = $props()

  const paths = {
    camera: '<rect x="1.5" y="4" width="13" height="9" rx="1.5"/><path d="M5.5 4 6.5 2h3l1 2"/><circle cx="8" cy="8.5" r="2.5"/>',
    picture: '<rect x="1.5" y="2.5" width="13" height="11" rx="1.5"/><path d="m1.5 11 4-4 3 3 2-2 4 4"/><circle cx="11" cy="5.5" r="1"/>',
    mic: '<rect x="5.5" y="1.5" width="5" height="8" rx="2.5"/><path d="M3 7.5a5 5 0 0 0 10 0M8 12.5v2"/>',
    send: '<path d="M2 8h11M9 4l4 4-4 4"/>',
    voice: '<path d="M2 6h3l4-3v10L5 10H2z"/><path d="M11.5 5.5a3.5 3.5 0 0 1 0 5M13.5 3.5a6.5 6.5 0 0 1 0 9"/>',
    mute: '<path d="M2 6h3l4-3v10L5 10H2z"/><path d="m11 6 4 4M15 6l-4 4"/>',
    close: '<path d="m4 4 8 8M12 4l-8 8"/>',
    check: '<path d="M2.5 8.5 6 12l7.5-8"/>',
    cross: '<path d="m4 4 8 8M12 4l-8 8"/>',
    moon: '<path d="M13 10A6 6 0 0 1 6 3a6 6 0 1 0 7 7z"/>',
    chevron: '<path d="m4 6 4 4 4-4"/>',
  }
</script>

<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"
  stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  {@html paths[name]}
</svg>
