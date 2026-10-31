# openwrt-feed

Signed OpenWrt package feed for `mineextremely` packages.

- Site: <https://mineextremely.github.io/openwrt-feed/>
- Targets: OpenWrt 24.10 (`opkg`) and OpenWrt 25.12 (`apk`)
- Signing key (opkg/usign): `38cd9e6814e2e69d`
- Signing key (apk): EC P-256, public key in [`keys/public-key.pem`](keys/public-key.pem)

## Packages

| Package | Version | 24.10 | 25.12 | Architectures |
|---|---|---|---|---|
| `fastfetch` | 2.70.0-r1 | yes | yes | aarch64_cortex-a53, aarch64_generic, x86_64 |
| `luci-theme-aurora` | 1.4.1-r20261031 | yes | yes | all |
| `luci-app-easytier` | 2.7.0-r1 | yes | yes | all |
| `easytier-noweb` | 2.7.0 | yes | yes | aarch64_cortex-a53, aarch64_generic, x86_64 |
| `luci-i18n-easytier-zh-cn` | 2.7.0 | yes | yes | all |
| `luci-app-twitchdropsminer` | 1.0.0-r1 | yes | yes | aarch64_generic |
| `luci-i18n-twitchdropsminer-zh-cn` | 26.300.48515~3f55790 | yes | yes | aarch64_generic |
| `twitch-drops-miner` | 16.0_pre-r1 | yes | yes | aarch64_generic |

## Install

Replace `<arch>` with one of:

- `aarch64_cortex-a53`
- `aarch64_generic`
- `x86_64`

### OpenWrt 24.10 (opkg)

```sh
wget -O /tmp/openwrt-feed.pub https://mineextremely.github.io/openwrt-feed/key-build.pub
opkg-key add /tmp/openwrt-feed.pub

echo "src/gz openwrt-feed https://mineextremely.github.io/openwrt-feed/24.10/<arch>" \
  >> /etc/opkg/customfeeds.conf

opkg update
opkg install luci-theme-aurora luci-app-easytier
```

If the official feed already installed `fastfetch`, remove it first so the
package names do not collide:

```sh
opkg remove fastfetch
opkg install fastfetch
```

### OpenWrt 25.12 (apk)

```sh
wget -O /etc/apk/keys/openwrt-feed.pem https://mineextremely.github.io/openwrt-feed/public-key.pem

echo "https://mineextremely.github.io/openwrt-feed/25.12/<arch>/packages.adb" \
  >> /etc/apk/repositories.d/customfeeds.list

apk update
apk add luci-theme-aurora luci-app-easytier
```

For `fastfetch` on 25.12:

```sh
apk del fastfetch
apk add fastfetch
```

The opkg and apk keys are separate key pairs; install the one that matches the
package manager on the device. Both are published from the Pages root.

## Layout

```text
.
├── .nojekyll
├── index.html                     # landing page
├── key-build.pub                  # opkg/usign public key
├── public-key.pem                 # apk EC public key
├── 24.10/<arch>/
│   ├── Packages
│   ├── Packages.gz
│   ├── Packages.sig
│   ├── Packages.manifest
│   ├── index.json
│   └── *.ipk
└── 25.12/<arch>/
    ├── packages.adb
    ├── index.json
    └── *.apk
```

## Automation

`.github/workflows/aggregate-feed.yml` runs every six hours (and on
`workflow_dispatch` / `repository_dispatch`):

1. reads [`feed-sources.json`](feed-sources.json);
2. downloads the matching `.ipk`/`.apk` assets from each source repository's
   release (pinned tag or `latest`);
3. stages packages for each `arch × SDK` combination;
4. builds and signs the index inside the matching `ghcr.io/openwrt/sdk` image;
5. publishes the whole tree to the `gh-pages` branch, which GitHub Pages serves.

The private signing keys live only in this repository's Actions secrets
(`KEY_BUILD`, `PRIVATE_KEY`); they are never committed.

`fastfetch`, `luci-theme-aurora` and `luci-app-easytier` follow their upstream
`latest` release. `twitch-drops-miner` is pinned to `v16.0_pre` because upstream
also publishes desktop-only releases that do not contain OpenWrt packages;
update its `release` field when a newer OpenWrt-enabled tag appears.

### Adding a package

Append an entry to `feed-sources.json`:

```json
{
  "name": "my-package",
  "repo": "mineextremely/my-package",
  "release": "latest",
  "kind": "raw",
  "formats": ["opkg", "apk"],
  "arch": "filename",
  "enabled": true
}
```

- `kind: "raw"` expects `.ipk` and/or `.apk` assets.
- `kind: "zip"` expects a zip containing one `.ipk`/`.apk`; the file name must
  contain the target architecture and SDK series, e.g.
  `fastfetch-2.70.0-aarch64_cortex-a53-24.10.6.zip`.
- `arch: "all"` means the package is architecture-independent; `"filename"`
  reads the architecture from the asset name; a concrete value limits it to
  that architecture (used by `twitch-drops-miner`).

## Migration note

The old feed under `mineextremely.github.io/Fastfetch4Openwrt/` is still online
and remains a fastfetch-only feed. New client configurations should use this
repository's URL. The previous mirror workflow has been replaced by the
aggregator above.
