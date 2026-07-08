# ZeroDelay — Frontend

Marketing landing page + hands-free voice app shell for ZeroDelay, an
offline, voice-guided repair/maintenance copilot. Built with Next.js
(App Router), TypeScript, Tailwind CSS, and Framer Motion, with an Electron
wrapper for a real installable desktop app.

The voice app is **wired to the ZeroDelay backend** ([`../backend`](../backend)) over
HTTP: it records the mic, POSTs each turn to `/converse`, and plays back the reply —
real Gemma speech-to-text, retrieval, reasoning, diagram vision, and Piper TTS,
alongside a live telemetry panel driven by the `/sensors` endpoints. The only piece
still faked is the step checklist shown in the overlay (one hardcoded demo procedure);
see [the notes below](#notes-on-the-demo-state).

## Structure

```
app/
  page.tsx            Landing page
  login/page.tsx       Company + access code gate before download
  app/page.tsx          Voice app shell (sidebar + voice UI)
  layout.tsx, globals.css
components/
  landing/              Landing page sections (Hero, Header, DownloadCta, ...)
  app-shell/            Sidebar, VoiceVisual, StepOverlay, SensorsPanel, LoginForm
lib/
  api.ts                 Thin HTTP client for the FastAPI backend (+ diagram URLs)
  useVoiceLoop.ts        Hands-free loop: record mic -> /converse -> play TTS reply
  audio.ts               PCM -> WAV encode + base64-WAV decode helpers
  sessions.ts            On-device (localStorage) persistence for past discussions
  mock-data.ts           The one hardcoded demo procedure (drives the step overlay)
  types.ts               Shared types, incl. the backend decision/sensor contract
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

The landing page works on its own, but `/app` needs the backend running on
`http://127.0.0.1:8000` (see [`../backend/README.md`](../backend/README.md)). Point it
at a different host with `NEXT_PUBLIC_ZD_API`.

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

## Notes on the demo state

- Voice, retrieval, reasoning, diagrams, and speech are **real**: every turn is
  recorded, POSTed to the backend's `/converse`, transcribed by Gemma, answered as a
  structured decision, and played back as Piper TTS audio. The AI's "speaking" turn is
  that audio, not an animation. The telemetry panel and its "inject fault" buttons hit
  the live `/sensors` endpoints.
- Turn-taking is voice-activity detection (speak, then pause) rather than a wake word —
  a short pause ends your turn and sends the clip.
- The step checklist in the overlay is still one hardcoded demo procedure
  (`lib/mock-data.ts`, adapted from `data/procedures/01-eva-prep-emu-airlock.md`); the
  pointer just advances locally whenever the backend returns an `advance` decision.
- Sessions and their full threads are saved in `localStorage`, so past discussions
  survive a reload and nothing leaves the device.
