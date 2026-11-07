#!/bin/sh
# Run as PUID:PGID (default 1000:1000) like linuxserver images.
set -e
umask "${UMASK:-002}"
if [ "$(id -u)" = "0" ]; then
  mkdir -p /config
  [ "$(stat -c %u:%g /config)" = "${PUID}:${PGID}" ] || chown -R "${PUID}:${PGID}" /config
  exec setpriv --reuid="${PUID}" --regid="${PGID}" --clear-groups "$@"
fi
exec "$@"
