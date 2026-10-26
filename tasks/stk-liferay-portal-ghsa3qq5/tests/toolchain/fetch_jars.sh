#!/usr/bin/env bash
# Fetch the jars a dependencies.properties file declares into <output>/<name>.jar.
# Usage: fetch_jars.sh <dependencies.properties> <output-dir>
set -u

properties="$1"
output="$2"

mkdir -p "$output"

missing=0

while IFS= read -r entry || [ -n "$entry" ]; do
	entry="${entry%%$'\r'}"

	case "$entry" in
		''|\#*) continue ;;
	esac

	name="${entry%%=*}"
	coordinate="${entry#*=}"

	group="${coordinate%%:*}"
	rest="${coordinate#*:}"
	artifact="${rest%%:*}"
	rest="${rest#*:}"
	version="${rest%%:*}"
	classifier=""

	if [ "$version" != "$rest" ]; then
		classifier="${rest#*:}"
	fi

	target="$output/$name.jar"

	if [ -s "$target" ]; then
		continue
	fi

	file_name="$artifact-$version.jar"

	if [ -n "$classifier" ]; then
		file_name="$artifact-$version-$classifier.jar"
	fi

	relative="$(printf '%s' "$group" | tr '.' '/')/$artifact/$version/$file_name"

	fetched=0

	for base in \
		"https://repo1.maven.org/maven2" \
		"https://repository-cdn.liferay.com/nexus/content/groups/public"
	do
		if curl -fsSL --retry 3 --connect-timeout 30 -o "$target.part" "$base/$relative"; then
			if [ "$(wc -c < "$target.part")" -gt 1000 ]; then
				mv "$target.part" "$target"
				fetched=1
				break
			fi
		fi

		rm -f "$target.part"
	done

	if [ "$fetched" -eq 0 ]; then
		echo "missing $name ($coordinate)" >&2

		missing=$((missing + 1))
	fi
done < "$properties"

if [ "$missing" -ne 0 ]; then
	exit 1
fi
