# Godseye, as vendored into ZENO

This directory is [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view)
by Bilawal Sidhu, vendored in unmodified (MIT license, see `LICENSE` in this
folder — the original attribution is preserved). It's a real-time 3D-globe
console: live aircraft, ships, satellites, earthquakes, and public CCTV, with
optional hands-free voice control.

## Why it's here

ZENO's Python tool registry has a `sensing.ambient` entry registered as an
honest **STUB** (see `../CAPABILITIES.md`) — there is no camera/microphone
sensor-fusion pipeline built into the Python backend, and that stub's status
hasn't changed. What *has* changed: ZENO's web console (`zeno-web`) now
detects whether this companion app is running and links out to it, rather
than showing a bare "not connected" placeholder with nothing behind it. It's
a real, working, separately-run app — just not something the Python backend
implements itself.

## Running it

```bash
cd godseye
cp .env.example .env
# Edit .env and set GOOGLE_MAPS_API_KEY (required for the base map — see
# the "API Keys" section of README.md below for a free-tier link).
npm install
npm run dev
```

Then open **http://localhost:4173**. ZENO's web console polls this address
and shows a live "Open Godseye ↗" link the moment it detects the app running
— see `zeno/webui.py`'s `/api/godseye/status` endpoint.

Per the upstream README: most data layers (flights, ships, satellites,
earthquakes, CCTV, radio, bikeshare, space missions) run with **zero API
keys**. Only the Google Maps key above is required to start; a Cesium ion
token and an OpenAI key are optional extras for premium imagery and
voice control respectively — see the "🔑 API Keys" section of `README.md`
in this folder (unmodified from upstream) for the full breakdown.

