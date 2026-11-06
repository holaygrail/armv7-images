# Homepage for linux/arm/v7, built from the upstream source tag.
# Build context: a checkout of gethomepage/homepage at the release tag.
#
# Differences from the upstream Dockerfile:
# - the Next.js build runs on the build host's native platform (standalone
#   output is plain JavaScript; images are unoptimized, so no sharp);
# - Node 22 runtime, because node:24-alpine has no arm/v7 image.

FROM --platform=$BUILDPLATFORM node:24-slim AS builder
WORKDIR /app
RUN mkdir config
COPY . .
ARG BUILDTIME
ARG VERSION
ARG REVISION
RUN corepack enable \
 && pnpm install --frozen-lockfile \
 && NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_BUILDTIME=$BUILDTIME \
    NEXT_PUBLIC_VERSION=$VERSION \
    NEXT_PUBLIC_REVISION=$REVISION \
    pnpm run build


FROM node:22-alpine
WORKDIR /app

COPY --link --chown=1000:1000 /public ./public/
COPY --link --chmod=755 docker-entrypoint.sh /usr/local/bin/
COPY --link --from=builder --chown=1000:1000 /app/.next/standalone/ ./
COPY --link --from=builder --chown=1000:1000 /app/.next/static/ ./.next/static

RUN apk add --no-cache su-exec iputils-ping shadow

USER root
ENV NODE_ENV=production \
    HOSTNAME=:: \
    PORT=3000
EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s \
  CMD wget --no-verbose --tries=1 --spider -Y off http://127.0.0.1:$PORT/api/healthcheck || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["node", "server.js"]
