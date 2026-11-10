# Sourdough web app

The interface for raising a Sourdough baby: its mind on the left, a conversation on the right. Svelte 5 and Vite, nothing else.

```bash
npm install
npm run dev      # http://localhost:5173, needs the API: run `sourdough --no-browser`
npm run build    # writes ../sourdough/interface/static, which the Python server serves
```

* `src/lib/baby.svelte.js` holds all state and every call to the API.
* `src/lib/Mind.svelte` draws the concept network on a canvas.
* `src/lib/Talk.svelte`, `Teach.svelte`, `Diary.svelte` are the three tabs.
* `src/lib/Picker.svelte` chooses a baby level.
* `public/fonts` holds Plus Jakarta Sans, self hosted (SIL Open Font License).
* `src/app.css` holds the colors and base styles.
