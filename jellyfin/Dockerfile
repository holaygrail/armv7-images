# Jellyfin for linux/arm/v7, built from the upstream source tag.
# Jellyfin dropped 32-bit ARM builds in 10.11 for performance reasons, but
# .NET still supports linux-arm. Server and web are built on the build host's
# native platform (the server is cross-compiled for linux-arm).
# Runtime: Debian 12 (32-bit time_t, see servarr/Dockerfile) with Debian's
# ffmpeg 5.1 (jellyfin-ffmpeg has no armhf build; Jellyfin needs >= 4.4).
# Layout follows linuxserver/jellyfin: /config/{data,cache,log}.

FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:10.0 AS server
ARG VERSION
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1
RUN git clone --depth 1 --branch "v${VERSION}" https://github.com/jellyfin/jellyfin.git /src
WORKDIR /src
RUN dotnet publish Jellyfin.Server --configuration Release --runtime linux-arm --self-contained \
      --output /server -p:DebugSymbols=false -p:DebugType=none


FROM --platform=$BUILDPLATFORM node:24-slim AS web
ARG VERSION
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates git \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "v${VERSION}" https://github.com/jellyfin/jellyfin-web.git /src
WORKDIR /src
RUN npm ci --no-audit --unsafe-perm \
 && npm run build:production \
 && mv dist /web


FROM debian:bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl ffmpeg fonts-dejavu-core libfontconfig1 libfreetype6 \
      libicu72 libjemalloc2 locales openssl tini tzdata \
 && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen \
 && rm -rf /var/lib/apt/lists/*

COPY --from=server /server /jellyfin
COPY --from=web /web /jellyfin/jellyfin-web
COPY entrypoint.sh /entrypoint.sh

ENV LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    JELLYFIN_DATA_DIR=/config/data \
    JELLYFIN_CONFIG_DIR=/config \
    JELLYFIN_CACHE_DIR=/config/cache \
    JELLYFIN_LOG_DIR=/config/log \
    JELLYFIN_WEB_DIR=/jellyfin/jellyfin-web \
    JELLYFIN_FFMPEG=/usr/bin/ffmpeg \
    XDG_CACHE_HOME=/config/cache \
    MALLOC_TRIM_THRESHOLD_=131072 \
    LD_PRELOAD=/usr/lib/arm-linux-gnueabihf/libjemalloc.so.2 \
    PUID=1000 \
    PGID=1000 \
    UMASK=002

EXPOSE 8096 7359/udp
VOLUME /config
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8096/health || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["/jellyfin/jellyfin"]
