// The five colors a character can have, mapped to Apple's system colors.
// Full class names are written out so Tailwind keeps them.
export const COLORS = {
  peach: { css: "var(--accent)", name: "Orange", bg: "bg-accent", text: "text-accent" },
  sky: { css: "var(--blue)", name: "Blue", bg: "bg-blue", text: "text-blue" },
  lilac: { css: "var(--purple)", name: "Purple", bg: "bg-purple", text: "text-purple" },
  mint: { css: "var(--green)", name: "Green", bg: "bg-green", text: "text-green" },
  rose: { css: "var(--pink)", name: "Pink", bg: "bg-pink", text: "text-pink" },
}

export const colorOf = (profile) => COLORS[profile?.color] || COLORS.peach
