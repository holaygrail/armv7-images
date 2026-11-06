# SABnzbd for linux/arm/v7, built from the official source release.
FROM python:3.13-slim-trixie AS build

ARG VERSION
ARG PAR2_VERSION

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential ca-certificates curl libffi-dev unzip \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app \
 && curl -fsSL "https://github.com/sabnzbd/sabnzbd/releases/download/${VERSION}/SABnzbd-${VERSION}-src.tar.gz" \
    | tar -xz -C /app \
 && mv "/app/SABnzbd-${VERSION}" /app/sabnzbd

# sabctools has no armv7 wheel and is compiled here.
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip wheel \
 && /opt/venv/bin/pip install --no-cache-dir -r /app/sabnzbd/requirements.txt \
 && cd /app/sabnzbd && /opt/venv/bin/python tools/make_mo.py

RUN curl -fsSL "https://github.com/animetosho/par2cmdline-turbo/releases/download/v${PAR2_VERSION}/par2cmdline-turbo-${PAR2_VERSION}-linux-armhf.zip" -o /tmp/par2.zip \
 && unzip -o /tmp/par2.zip -d /usr/local/bin \
 && chmod 755 /usr/local/bin/par2


FROM python:3.13-slim-trixie

# unrar is in Debian's non-free component.
RUN sed -i 's/^Components: main$/Components: main non-free/' /etc/apt/sources.list.d/debian.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends 7zip ca-certificates curl tini tzdata unrar \
 && rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/venv /opt/venv
COPY --from=build /app/sabnzbd /app/sabnzbd
COPY --from=build /usr/local/bin/par2 /usr/local/bin/par2
COPY entrypoint.sh /entrypoint.sh

ENV HOME=/config \
    PUID=1000 \
    PGID=1000 \
    UMASK=002 \
    PYTHONIOENCODING=utf-8

EXPOSE 8080
VOLUME /config
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD curl -fsS "http://127.0.0.1:8080/api?mode=version" >/dev/null || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
CMD ["/opt/venv/bin/python", "-OO", "/app/sabnzbd/SABnzbd.py", "--config-file", "/config", "--server", "0.0.0.0:8080", "--browser", "0"]
