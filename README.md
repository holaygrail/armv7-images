# armv7-images

Docker images for **32-bit ARM (`linux/arm/v7`)** of media-server apps whose
official or popular images dropped armv7 support.

| Image | Built from |
| --- | --- |
| `ghcr.io/holaygrail/sonarr` | Official [Sonarr](https://github.com/Sonarr/Sonarr) `linux-arm` release |
| `ghcr.io/holaygrail/radarr` | Official [Radarr](https://github.com/Radarr/Radarr) `linux-core-arm` release |
| `ghcr.io/holaygrail/sabnzbd` | Official [SABnzbd](https://github.com/sabnzbd/sabnzbd) source release + [par2cmdline-turbo](https://github.com/animetosho/par2cmdline-turbo) |
| `ghcr.io/holaygrail/seerr` | [Seerr](https://github.com/seerr-team/seerr) source tag (upstream Dockerfile, adapted) |
| `ghcr.io/holaygrail/homepage` | [Homepage](https://github.com/gethomepage/homepage) source tag (upstream Dockerfile, adapted) |

Tags: `latest` and the upstream version (e.g. `sonarr:4.0.20.3014`).

## How it works

A GitHub Actions workflow runs daily, checks the latest upstream release of
each app and builds any version that is not published yet. Every image is
started under QEMU and must answer on its HTTP port before it is pushed.
All images are rebuilt weekly to pick up base-image updates, so tools like
Watchtower keep them current.

## Usage

Sonarr, Radarr and SABnzbd follow the linuxserver.io conventions: config in
`/config`, `PUID`/`PGID` (default 1000) and `TZ`. Sonarr and Radarr report
updates as "update via Docker".

Seerr and Homepage behave like their upstream images (Seerr: `/app/config`,
runs as uid 1000, Debian-based, so a compose healthcheck must use
`wget -q -O /dev/null` instead of `wget --spider`; Homepage: `/app/config`, `PUID`/`PGID`,
`HOMEPAGE_ALLOWED_HOSTS`).

Seerr and Homepage need Node.js 22, the last Node.js line with armv7 images
(end of life April 2027).

## License

The Dockerfiles and scripts in this repository are MIT licensed. The apps
inside the images keep their own licenses.
