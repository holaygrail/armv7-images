# Sonarr / Radarr for linux/arm/v7, built from the official release tarball.
FROM debian:trixie-slim

ARG APP
ARG VERSION
ARG BRANCH
ARG ASSET
ARG PORT

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl libicu76 libsqlite3-0 tini tzdata \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/bin \
 && curl -fsSL "https://github.com/${APP}/${APP}/releases/download/v${VERSION}/${APP}.${BRANCH}.${VERSION}.${ASSET}.tar.gz" \
    | tar -xz -C /app/bin --strip-components=1 \
 && rm -rf "/app/bin/${APP}.Update" \
 && printf 'PackageVersion=%s\nPackageAuthor=[holaygrail/armv7-images](https://github.com/holaygrail/armv7-images)\nUpdateMethod=docker\nBranch=%s\n' "$VERSION" "$BRANCH" > /app/package_info \
 && ln -s "/app/bin/${APP}" /app/bin/app \
 && chmod -R a+rX /app

COPY entrypoint.sh /entrypoint.sh

ENV XDG_CONFIG_HOME=/config \
    PORT=${PORT} \
    PUID=1000 \
    PGID=1000 \
    UMASK=002

EXPOSE ${PORT}
VOLUME /config
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s \
  CMD curl -fsS "http://127.0.0.1:${PORT}/ping" >/dev/null || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["/app/bin/app", "-nobrowser", "-data=/config"]
