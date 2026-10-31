#!/bin/bash
# Runs inside the OpenWrt SDK container.
#
# Inputs:
#   /packages   packages for exactly one target (read-only mount)
#   /out        output directory (read-write mount)
#   ARCH        target architecture, e.g. aarch64_cortex-a53
#   FMT         opkg (24.10) or apk (25.12)
#   KEY_BUILD   usign private key (secret)
#   PRIVATE_KEY apk EC private key (secret)
set -euo pipefail

: "${ARCH:?ARCH is required}"
: "${FMT:?FMT is required}"

export PATH="/builder/staging_dir/host/bin:/builder/scripts:${PATH}"

umask 077
if [ -n "${KEY_BUILD:-}" ]; then
  printf '%s' "$KEY_BUILD" > /tmp/key-build
fi
if [ -n "${PRIVATE_KEY:-}" ]; then
  printf '%s' "$PRIVATE_KEY" > /tmp/private-key.pem
fi

WORK=/work
OUT=/out
rm -rf "$WORK"
mkdir -p "$WORK" "$OUT"
cd "$WORK"

shopt -s nullglob
packages=(/packages/*)
if [ "${#packages[@]}" -eq 0 ]; then
  echo "no packages staged for ${ARCH} (${FMT})" >&2
  exit 1
fi
cp /packages/* .

if [ "$FMT" = "opkg" ]; then
  [ -s /tmp/key-build ] || { echo "KEY_BUILD is empty" >&2; exit 1; }

  /builder/scripts/ipkg-make-index.sh . > Packages.manifest 2>/tmp/ipkg.err || {
    cat /tmp/ipkg.err >&2
    exit 1
  }
  cat /tmp/ipkg.err >&2 || true

  grep -vE '^(Maintainer|LicenseFiles|Source|SourceName|Require|SourceDateEpoch)' \
    Packages.manifest > Packages

  # Same padding workaround as OpenWrt's package/Makefile.
  size=$((64 + $(stat -L -c%s Packages)))
  if [ $((size % 128)) -eq 110 ] || [ $((size % 128)) -eq 111 ]; then
    printf '\n\n' >> Packages
  fi

  /builder/scripts/make-index-json.py -f opkg -a "$ARCH" Packages > index.json
  gzip -9nc Packages > Packages.gz
  usign -S -m Packages -s /tmp/key-build

  cp Packages Packages.gz Packages.sig Packages.manifest index.json "$OUT"/
  cp ./*.ipk "$OUT"/

  echo "opkg index: $(grep -c '^Package:' Packages) packages, signature:"
  head -n1 Packages.sig
else
  [ -s /tmp/private-key.pem ] || { echo "PRIVATE_KEY is empty" >&2; exit 1; }

  apk mkndx \
    --root /builder \
    --keys-dir /builder \
    --allow-untrusted \
    --sign /tmp/private-key.pem \
    --output packages.adb \
    ./*.apk

  apk adbdump --format json packages.adb > /tmp/packages.adb.json
  /builder/scripts/make-index-json.py -f apk -a "$ARCH" - < /tmp/packages.adb.json > index.json

  cp packages.adb index.json "$OUT"/
  cp ./*.apk "$OUT"/

  echo "apk index: $(grep -c '"name"' index.json || true) entries"
fi
