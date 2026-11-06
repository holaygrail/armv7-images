#!/usr/bin/env python3
"""Decide which images need a build.

For every app in apps.json: look up the latest upstream GitHub release and
check whether ghcr.io/<owner>/<app>:<version> already exists. Prints a GitHub
Actions matrix (JSON) to stdout.

Env: GITHUB_TOKEN, IMAGE_PREFIX (e.g. ghcr.io/holaygrail), FORCE (true/false),
APPS (space-separated subset, empty = all).
"""
import json
import os
import subprocess
import sys
import urllib.request


def gh(path):
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def latest_tag(repo):
    return gh(f"repos/{repo}/releases/latest")["tag_name"]


def image_exists(ref):
    return subprocess.run(
        ["docker", "manifest", "inspect", ref],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0


def main():
    apps = json.load(open("apps.json"))
    prefix = os.environ["IMAGE_PREFIX"]
    force = os.environ.get("FORCE", "false") == "true"
    only = os.environ.get("APPS", "").split()

    par2 = latest_tag("animetosho/par2cmdline-turbo").lstrip("v")
    matrix = []
    for name, app in apps.items():
        if only and name not in only:
            continue
        tag = latest_tag(app["upstream"])
        version = tag.lstrip("v")
        exists = image_exists(f"{prefix}/{name}:{version}")
        print(f"{name}: upstream {tag}, image exists: {exists}", file=sys.stderr)
        if exists and not force:
            continue
        args = dict(app["build_args"])
        if not app.get("source"):
            args["VERSION"] = version
        if name == "sabnzbd":
            args["PAR2_VERSION"] = par2
        matrix.append({
            "app": name,
            "upstream": app["upstream"],
            "tag": tag,
            "version": version,
            "source": bool(app.get("source")),
            "context": app["context"],
            "dockerfile": app["dockerfile"],
            "port": app["port"],
            "health": app["health"],
            "smoke_minutes": app.get("smoke_minutes", 10),
            "build_args": "\n".join(f"{k}={v}" for k, v in args.items()),
        })
    print(json.dumps({"include": matrix}))


if __name__ == "__main__":
    main()
