# openwrt-feed

Signed OpenWrt package feed for `mineextremely` packages.

- Site: <https://mineextremely.github.io/openwrt-feed/>
- Targets: OpenWrt 24.10 (`opkg`) and OpenWrt 25.12 (`apk`)
- Current packages: [`fastfetch`](https://github.com/mineextremely/Fastfetch4Openwrt) 2.70.0
- Signing key (opkg/usign): `38cd9e6814e2e69d`
- Signing key (apk): EC P-256, public key in [`keys/public-key.pem`](keys/public-key.pem)

## Supported architectures

| Architecture | 24.10 (opkg) | 25.12 (apk) |
|---|---|---|
| `aarch64_cortex-a53` | yes | yes |
| `aarch64_generic` | yes | yes |
| `x86_64` | yes | yes |

## Install

Replace `<arch>` with one of the values above.

### OpenWrt 24.10 (opkg)

```sh
wget -O /tmp/openwrt-feed.pub https://mineextremely.github.io/openwrt-feed/key-build.pub
opkg-key add /tmp/openwrt-feed.pub

echo "src/gz openwrt-feed https://mineextremely.github.io/openwrt-feed/24.10/<arch>" \
  >> /etc/opkg/customfeeds.conf

opkg update
opkg install fastfetch
```

### OpenWrt 25.12 (apk)

```sh
wget -O /etc/apk/keys/openwrt-feed.pem https://mineextremely.github.io/openwrt-feed/public-key.pem

echo "https://mineextremely.github.io/openwrt-feed/25.12/<arch>/packages.adb" \
  >> /etc/apk/repositories.d/customfeeds.list

apk update
apk add fastfetch
```

The apk key and the opkg key are separate key pairs; install the one that matches
the package manager on the device.

## Layout

```text
.
├── .nojekyll
├── key-build.pub                  # opkg/usign public key
├── public-key.pem                 # apk EC public key
├── 24.10/<arch>/
│   ├── Packages
│   ├── Packages.gz
│   ├── Packages.sig
│   ├── Packages.manifest
│   ├── Packages.bom.cdx.json
│   ├── index.json
│   └── fastfetch_*.ipk
└── 25.12/<arch>/
    ├── packages.adb
    ├── index.json
    └── fastfetch-*.apk
```

## Status

This repository currently mirrors the `feed` branch of
`mineextremely/Fastfetch4Openwrt` every six hours. The next step is to aggregate
the release artifacts of `luci-theme-aurora`, `luci-app-easytier`,
`TwitchDropsMiner` and `fastfetch` into this single signed feed.

The old Pages site of `Fastfetch4Openwrt` stays online during the migration;
new client configurations should use this repository's URL.

## Automation

- `.github/workflows/mirror-fastfetch-feed.yml` — scheduled mirror of the
  Fastfetch feed into `gh-pages`.
- Signing private keys live only in this repository's Actions secrets
  (`KEY_BUILD`, `PRIVATE_KEY`); they are never committed.
