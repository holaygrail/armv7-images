# Seerr for linux/arm/v7, built from the upstream source tag.
# Build context: a checkout of seerr-team/seerr at the release tag.
#
# Differences from the upstream Dockerfile:
# - the Next.js/TypeScript build runs on the build host's native platform
#   (its output is plain JavaScript), so no slow WebAssembly SWC build on arm;
# - production dependencies are installed on arm/v7 with compilers, because
#   sqlite3 has no armv7 prebuild;
# - @next/swc-wasm-nodejs bundled (no native SWC for 32-bit ARM);
# - Debian (glibc) runtime instead of Alpine, because sharp only ships
#   32-bit ARM binaries for glibc.

ARG NODE_IMAGE=node:22-bookworm-slim

FROM --platform=$BUILDPLATFORM ${NODE_IMAGE} AS build
ARG COMMIT_TAG
ENV COMMIT_TAG=${COMMIT_TAG} \
    PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH
RUN corepack enable
WORKDIR /app
COPY . .
RUN CYPRESS_INSTALL_BINARY=0 pnpm install --frozen-lockfile \
 && pnpm build \
 && rm -rf .next/cache


FROM ${NODE_IMAGE} AS prod-deps
ENV PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH
RUN apt-get update \
 && apt-get install -y --no-install-recommends g++ make python3 \
 && rm -rf /var/lib/apt/lists/*
RUN corepack enable
WORKDIR /app
COPY . .
RUN CI=true pnpm install --prod --frozen-lockfile \
 && if [ -d node_modules/.pnpm ]; then \
      find node_modules/.pnpm -type d \( \
        -path "*ace-builds/src-noconflict" -o \
        -path "*ace-builds/src" -o \
        -path "*ace-builds/src-min" -o \
        -path "*country-flag-icons/react" -o \
        -path "*country-flag-icons/string" -o \
        -path "*country-flag-icons/1x1" -o \
        -path "*@heroicons/react/16" \
      \) -exec rm -rf {} + || true; \
    fi

# Next.js has no native SWC for 32-bit ARM and falls back to WebAssembly at
# runtime (Seerr's next.config.ts needs it). It looks for the package in
# <next>/wasm/@next/swc-wasm-nodejs and would otherwise download it on first
# start via pnpm (not in the image), so pre-install it there.
RUN NEXT_DIR=$(dirname "$(node -p "require.resolve('next/package.json')")") \
 && NEXT_VERSION=$(node -p "require('next/package.json').version") \
 && mkdir -p /tmp/swc && cd /tmp/swc \
 && npm install --no-save --no-package-lock --no-audit --no-fund "@next/swc-wasm-nodejs@${NEXT_VERSION}" \
 && mkdir -p "${NEXT_DIR}/wasm/@next" \
 && cp -a node_modules/@next/swc-wasm-nodejs "${NEXT_DIR}/wasm/@next/" \
 && ls "${NEXT_DIR}/wasm/@next/swc-wasm-nodejs/wasm.js" \
 && rm -rf /tmp/swc


FROM ${NODE_IMAGE}
ARG COMMIT_TAG
ENV NODE_ENV=production \
    COMMIT_TAG=${COMMIT_TAG}

RUN apt-get update \
 && apt-get install -y --no-install-recommends tini tzdata wget \
 && rm -rf /var/lib/apt/lists/*

USER node:node
WORKDIR /app

COPY --chown=node:node . .
COPY --chown=node:node --from=prod-deps /app/node_modules ./node_modules
COPY --chown=node:node --from=build /app/.next ./.next
COPY --chown=node:node --from=build /app/dist ./dist

RUN touch config/DOCKER \
 && echo "{\"commitTag\": \"${COMMIT_TAG}\"}" > committag.json

EXPOSE 5055
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s \
  CMD wget -q --spider "http://127.0.0.1:${PORT:-5055}/api/v1/status" || exit 1
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["npm", "start"]
