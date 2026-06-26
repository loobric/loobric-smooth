#!/usr/bin/env bash
#
# quickstart.sh — seed a Smooth account with a small demo, and learn to script
# the `smooth` CLI by reading it.
#
# This is nothing but a list of ordinary `smooth` commands. Read it top to
# bottom to see how the pieces fit together; run it to give a fresh account
# (e.g. the hosted sandbox) something to explore.
#
# ---------------------------------------------------------------------------
# Prerequisites (see docs/SANDBOX.md):
#
#   pip install loobric-smooth
#   export SMOOTH_BASE_URL=https://api.loobric.com
#   smooth register you@example.com
#   smooth login    you@example.com
#   smooth create-key sandbox --scopes "read write"
#   export SMOOTH_API_KEY=<the key it printed>     # the CLI reads this automatically
#
# Then run:   bash quickstart.sh
# ---------------------------------------------------------------------------
#
# Meant for a FRESH account. It's safe to re-run — the catalog records dedupe on
# their natural key (a re-run just reports them as already present) — but a
# re-run does create another demo machine and tool set. Wipe first with
# `smooth reset --yes` if you want a clean slate.

# Read no command's stdin from this script, so `cat quickstart.sh | bash` can't
# accidentally feed the script text into a command. Every value below is a flag.
exec < /dev/null

# Fail fast with a clear message if the environment isn't set up.
: "${SMOOTH_BASE_URL:?Set the server first, e.g. export SMOOTH_BASE_URL=https://api.loobric.com}"
if ! smooth whoami >/dev/null 2>&1; then
  echo "Not signed in. Create and export an API key first — see the header of this file." >&2
  exit 1
fi

echo "== Account =="
smooth whoami

echo
echo "== 1. A machine to bind tools against =="
smooth create-machine sandbox-mill --controller linuxcnc

echo
echo "== 2. A small catalog, across two manufacturers =="
# create-catalog-record needs an identity (name + manufacturer + product-code);
# --source is the actor the server stamps on every field as 'asserted:<source>'.
smooth create-catalog-record --source manufacturer:kennametal \
  --name "1/4in 2-flute flat endmill" --manufacturer Kennametal \
  --product-code B201 --diameter 6.35 --flutes 2
smooth create-catalog-record --source manufacturer:kennametal \
  --name "1/8in 2-flute flat endmill" --manufacturer Kennametal \
  --product-code B101 --diameter 3.175 --flutes 2
smooth create-catalog-record --source manufacturer:kennametal \
  --name "6mm 3-flute endmill" --manufacturer Kennametal \
  --product-code B306 --diameter 6.0 --flutes 3
smooth create-catalog-record --source manufacturer:kennametal \
  --name "5mm jobber drill" --manufacturer Kennametal \
  --product-code D050 --diameter 5.0
smooth create-catalog-record --source manufacturer:sandvik \
  --name "60deg V-bit engraver" --manufacturer Sandvik \
  --product-code V160 --diameter 6.0
smooth create-catalog-record --source manufacturer:sandvik \
  --name "90deg chamfer mill" --manufacturer Sandvik \
  --product-code C290 --diameter 6.0
smooth create-catalog-record --source manufacturer:sandvik \
  --name "3mm ball-nose endmill" --manufacturer Sandvik \
  --product-code BN030 --diameter 3.0 --flutes 2
smooth create-catalog-record --source manufacturer:sandvik \
  --name "50mm face mill" --manufacturer Sandvik \
  --product-code F500 --diameter 50.0 --flutes 5

echo
echo "== 3. Turn a couple of catalog entries into physical tools =="
# --from-catalog resolves by product code; the new instance is UNBOUND (not on
# any machine yet) and carries the catalog's nominal geometry.
smooth create-record --from-catalog B201 --name "1/4in endmill (stock)"
smooth create-record --from-catalog V160 --name "60deg V-bit (stock)"

echo
echo "== 4. Collect them in a tool set =="
smooth create-set "Sandbox demo set"
smooth add-to-set "Sandbox demo set" "1/4in endmill (stock)" "60deg V-bit (stock)"

echo
echo "== 5. Push a machine tool table (as a stand-in controller) =="
# Each --entry is N[:description[:diameter]]. This is the controller side of the
# loop; the server may then propose binding these entries to the tools above.
smooth push sandbox-mill --client linuxcnc-sim \
  --entry "1:1/4 downcut:6.35" --entry "2:60 vee:6.0"

echo
echo "== Done. Now explore what you built: =="
echo "  smooth list-catalog-records              # the seeded catalog"
echo "  smooth list-tools                        # your physical instances"
echo "  smooth show-tool-set \"Sandbox demo set\""
echo "  smooth show-machine sandbox-mill         # its tool table + linked sets"
echo "  smooth pending                           # binding proposals to review"
echo "  smooth audit --limit 20                  # the full provenance trail"
