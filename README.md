# ELOR Global Hotels — Stage 2 local pilot

A working FastAPI backend, persistent SQLite database, and mobile-friendly hotel staff dashboard for three Signature properties. Includes hotel/room catalogue, date and occupancy validation, guest booking requests, staff confirmation/decline/completion workflow, and 3% illustrative completed-stay credits. All room types, prices and availability are simulated. **No real reservation, payment, OPERA sync, or crypto token.**

## Start on Windows

1. Install Python 3.10+ on a computer.
2. Open Command Prompt in this extracted folder.
3. `py -m pip install -r requirements.txt`
4. Set a strong pilot staff key: `set ELOR_ADMIN_KEY=replace-with-a-long-random-secret`
5. `py -m uvicorn main:app --host 127.0.0.1 --port 8000`
6. Open http://127.0.0.1:8000

On macOS/Linux use `python3 -m pip`, `export ELOR_ADMIN_KEY='...'`, and `python3 -m uvicorn ...`.

Bookings and rewards persist in `elor_stage2.sqlite3` across server restarts. Keep this file private and back it up. The admin key is required for listing/changing bookings and querying rewards. If no key is configured, staff actions are disabled. Do not use actual guest personal data during testing.

## Staff test

Create a demo request on the Explore Hotels tab, enter your admin key on the Hotel Dashboard tab, refresh, confirm the request, then mark it completed. The Rewards Wallet tab also requires the staff key for pilot lookup.

## Not production ready

The key is a simple shared pilot secret, **not** full authentication. There is no guest authentication, per-property permissions, live availability/inventory, concurrency-safe room allocation, payment processing, verified PMS confirmation, cancellation/refund rules, taxes, data retention policy, or hardened hosting. Do not expose to the internet or use for real reservations. For production, migrate to PostgreSQL and implement role-based staff accounts, session management, audit trails, privacy controls, real inventory checks, and OPERA/channel manager connectivity.
