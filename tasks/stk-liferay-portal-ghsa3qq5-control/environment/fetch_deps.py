#!/usr/bin/env python3
"""Populate a directory with the project's declared third-party jars.

Usage: fetch_deps.py <dependencies.properties> <output-dir>

The project declares each jar as <name>=<group>:<artifact>:<version>[:<classifier>] and expects
it at <output-dir>/<name>.jar. Maven Central carries most of them; Liferay's public repository
carries the patched artifacts.
"""
import os
import sys
import time
import urllib.request

BASES = (
    "https://repo1.maven.org/maven2/",
    "https://repository-cdn.liferay.com/nexus/content/groups/public/",
)


def main():
    properties, output = sys.argv[1], sys.argv[2]

    os.makedirs(output, exist_ok=True)

    failed = []
    fetched = 0

    with open(properties) as stream:
        for line in stream:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            name, _, coordinate = line.partition("=")
            name = name.strip()
            coordinate = coordinate.strip()

            parts = coordinate.split(":")
            group, artifact, version = parts[:3]
            classifier = parts[3] if len(parts) > 3 else None

            target = os.path.join(output, name + ".jar")

            if os.path.isfile(target) and os.path.getsize(target) > 1000:
                continue

            file_name = "%s-%s%s.jar" % (
                artifact, version, ("-" + classifier) if classifier else "")
            path = "%s/%s/%s/%s" % (
                group.replace(".", "/"), artifact, version, file_name)

            for base in BASES:
                try:
                    with urllib.request.urlopen(base + path, timeout=120) as response:
                        data = response.read()

                    if len(data) < 1000:
                        raise ValueError("short response")

                    with open(target, "wb") as stream_out:
                        stream_out.write(data)

                    fetched += 1
                    break
                except Exception:
                    time.sleep(0.2)
            else:
                failed.append("%s (%s)" % (name, coordinate))

    print("fetched %d jars into %s" % (fetched, output))

    if failed:
        print("missing: " + ", ".join(failed))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
