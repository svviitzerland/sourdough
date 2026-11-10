// The five colors a character can have. Full class names, so Tailwind keeps them.
export const COLORS = {
  peach: { avatar: "from-peach to-rose", dot: "bg-peach", ring: "ring-peach" },
  sky: { avatar: "from-sky to-lilac", dot: "bg-sky", ring: "ring-sky" },
  lilac: { avatar: "from-lilac to-rose", dot: "bg-lilac", ring: "ring-lilac" },
  mint: { avatar: "from-mint to-sky", dot: "bg-mint", ring: "ring-mint" },
  rose: { avatar: "from-rose to-peach", dot: "bg-rose", ring: "ring-rose" },
}

export const colorOf = (profile) => COLORS[profile?.color] || COLORS.peach
