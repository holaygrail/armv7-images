#!/usr/bin/env python3
"""Decide which images need a build.

For every app in apps.json: look up the latest upstream GitHub release and
the "inputs" of its image: the digests of all base images in its Dockerfile,
the contents of its Dockerfile directory, its apps.json entry and extra tool
versions. An image is built when ghcr.io/<owner>/<app>:<version> is missing,
when its inputs label differs (base image update, Dockerfile change), or when
FORCE is set. Prints a GitHub Actions matrix (JSON) to stdout.

Env: GITHUB_TOKEN, IMAGE_PREFIX (e.g. ghcr.io/holaygrail), FORCE (true/false),
APPS (space-separated subset, empty = all).
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

INPUTS_LABEL = "io.github.holaygrail.armv7.inputs"
RUNTIME_PLATFORM = ("arm", "v7")
BUILD_PLATFORM = ("arm64", None)  # GitHub's ubuntu-24.04-arm runners


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


def imagetools(*args):
    r = subprocess.run(
        ["docker", "buildx", "imagetools", "inspect", *args],
        capture_output=True, text=True, timeout=120,
    )
    return r.stdout if r.returncode == 0 else None


def image_labels(ref):
    """Labels of a published single-platform image, None if it does not exist."""
    out = imagetools(ref, "--format", "{{json .Image}}")
    if out is None:
        return None
    image = json.loads(out)
    return (image.get("config") or {}).get("Labels") or {}


def platform_digest(ref, platform):
    """Digest of the given platform's manifest of a (multi-arch) image."""
    raw = imagetools(ref, "--raw")
    if raw is None:
        sys.exit(f"cannot inspect base image {ref}")
    index = json.loads(raw)
    if "manifests" not in index:  # single-platform image
        return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()
    arch, variant = platform
    for m in index["manifests"]:
        p = m.get("platform", {})
        if p.get("os") == "linux" and p.get("architecture") == arch and \
                (variant is None or p.get("variant") == variant):
            return m["digest"]
    sys.exit(f"base image {ref} has no linux/{arch} manifest")


def base_images(dockerfile):
    """(image, platform) for every external FROM in a Dockerfile."""
    args, stages, bases = {}, set(), []
    for line in Path(dockerfile).read_text().splitlines():
        line = line.strip()
        m = re.match(r"ARG\s+(\w+)=(\S+)", line)
        if m and not bases and not stages:
            args[m.group(1)] = m.group(2)
        m = re.match(r"FROM\s+(--platform=\S+\s+)?(\S+)(\s+AS\s+(\S+))?", line, re.I)
        if not m:
            continue
        image = re.sub(r"\$\{?(\w+)\}?", lambda v: args.get(v.group(1), ""), m.group(2))
        if image not in stages:
            platform = BUILD_PLATFORM if m.group(1) and "BUILDPLATFORM" in m.group(1) \
                else RUNTIME_PLATFORM
            bases.append((image, platform))
        if m.group(4):
            stages.add(m.group(4))
    return bases


def dir_hash(path):
    h = hashlib.sha256()
    for f in sorted(Path(path).rglob("*")):
        if f.is_file():
            h.update(str(f.relative_to(path)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def main():
    apps = json.load(open("apps.json"))
    prefix = os.environ["IMAGE_PREFIX"]
    force = os.environ.get("FORCE", "false") == "true"
    only = os.environ.get("APPS", "").split()

    par2 = latest_tag("animetosho/par2cmdline-turbo").lstrip("v")
    digests = {}
    matrix = []
    for name, app in apps.items():
        if only and name not in only:
            continue
        tag = latest_tag(app["upstream"])
        version = tag.lstrip("v")
        args = dict(app["build_args"])
        if not app.get("source"):
            args["VERSION"] = version
        if name == "sabnzbd":
            args["PAR2_VERSION"] = par2

        bases = {}
        for image, platform in base_images(app["dockerfile"]):
            key = (image, platform)
            if key not in digests:
                digests[key] = platform_digest(image, platform)
            bases[f"{image} ({'/'.join(p for p in platform if p)})"] = digests[key]
        inputs = hashlib.sha256(json.dumps({
            "bases": bases,
            "files": dir_hash(Path(app["dockerfile"]).parent),
            "app": app,
            "args": args,
        }, sort_keys=True).encode()).hexdigest()[:24]

        labels = image_labels(f"{prefix}/{name}:{version}")
        if labels is None:
            reason = "new version"
        elif labels.get(INPUTS_LABEL) != inputs:
            reason = "inputs changed (base image, Dockerfile or build args)"
        elif force:
            reason = "forced"
        else:
            reason = None
        print(f"{name}: upstream {tag}, inputs {inputs}: {reason or 'up to date'}",
              file=sys.stderr)
        if reason is None:
            continue
        matrix.append({
            "app": name,
            "upstream": app["upstream"],
            "tag": tag,
            "version": version,
            "inputs": inputs,
            "source": bool(app.get("source")),
            "context": app["context"],
            "dockerfile": app["dockerfile"],
            "port": app["port"],
            "health": app["health"],
            "smoke_minutes": app.get("smoke_minutes", 10),
            "smoke_log": app.get("smoke_log", ""),
            "smoke_may_exit": bool(app.get("smoke_may_exit")),
            "build_args": "\n".join(f"{k}={v}" for k, v in args.items()),
        })
    print(json.dumps({"include": matrix}))


if __name__ == "__main__":
    main()
