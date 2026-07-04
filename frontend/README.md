# ZeroDelay — Frontend

Marketing landing page + hands-free voice app shell for ZeroDelay, an
offline, voice-guided repair/maintenance copilot. Built with Next.js
(App Router), TypeScript, Tailwind CSS, and Framer Motion, with an Electron
wrapper for a real installable desktop app.

This is **frontend only**. The real Ollama/Gemma model, speech-to-text,
text-to-speech, and procedure/sensor engine are not wired up yet — every
integration point is stubbed and marked with `// TODO: real integration`
comments (see `lib/mock-data.ts`, `lib/useMicAmplitude.ts`,
`electron/main.js`).

## Structure

```
app/
  page.tsx            Landing page
  login/page.tsx       Company + access code gate before download
  app/page.tsx          Voice app shell (sidebar + voice UI)
  layout.tsx, globals.css
components/
  landing/              Landing page sections (Hero, Header, DownloadCta, ...)
  app-shell/            Sidebar, VoiceVisual, StepOverlay, LoginForm
lib/
  mock-data.ts           Demo procedure content + types
  types.ts
  useMicAmplitude.ts     Web Audio mic-level hook driving the voice visual
electron/
  main.js                Electron entry point — serves the static export
                         locally and opens straight to the app (no landing page)
build/
  icon.png               Source icon for the packaged app (used by electron-builder)
public/
  logo.png, diagrams/    Static assets
  downloads/             Where a built .dmg/.exe would be copied for the
                         website's download button (gitignored — see below)
```

## Requirements

- Node.js 18+
- npm

## Run the website locally

```bash
npm install
npm run dev
```

Open http://localhost:3000. Routes:
- `/` — landing page
- `/login?os=mac|pc` — company/access-code gate, auto-triggers the download on success
- `/app` — the voice app shell (also what the desktop app opens directly into)

## Build the desktop app (macOS)

```bash
npm run dist:mac
```

This runs `next build` (static export, see `next.config.mjs`) and then
`electron-builder`, producing an unsigned `.dmg`/`.app` in `dist/`. Since
it's unsigned, the first launch requires right-click → Open to bypass
Gatekeeper.

To make the website's "Download for macOS" button actually serve that
build, copy it into `public/downloads/`:

```bash
cp dist/ZeroDelay-*.dmg public/downloads/ZeroDelay-mac.dmg
```

**Note:** packaged binaries are gitignored (`public/downloads/*.dmg` etc.)
because they're much larger than GitHub's 100MB per-file limit. Distribute
real builds via GitHub Releases (or another host) and point the hrefs in
`components/landing/DownloadCta.tsx` and `app/login/page.tsx` at that URL
instead of the local static file.

A Windows build isn't packaged — cross-building an `.exe` from macOS needs
Wine or a Windows/CI machine. The `build.win` config in `package.json` can
be added once that's needed.

## Notes on the mock/demo state

- The voice app uses one hardcoded demo procedure (`lib/mock-data.ts`,
  adapted from `data/procedures/01-eva-prep-emu-airlock.md` in the parent
  repo) — every "New" session loads the same steps.
- The voice visual is driven by real microphone input (Web Audio API) once
  permission is granted, but step advancement uses simple voice-activity
  detection (speak, then pause) rather than real speech-to-text.
- The AI's own "speaking" turn is a synthetic animation, since there's no
  TTS playback wired up yet.
