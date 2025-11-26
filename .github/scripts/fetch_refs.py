#!/usr/bin/env python3
"""
Fetch recent article metadata from CrossRef for the project topic and replace the
References placeholder block in doc/project_article.md with formatted IEEE-style
entries. Intended to run in CI (GitHub Actions). Commits the updated file back to
the repository using the provided GITHUB_TOKEN.

NOTE: This script depends on network access and the CrossRef public API.
"""
import os
import re
import sys
import json
from textwrap import shorten

import requests

CROSSREF_URL = "https://api.crossref.org/works"
QUERY_TERMS = [
    "mechanical liner cementing",
    "liner cementing",
    "4.5 inch liner cementing",
    "liner setting cementing mechanical liner",
]
MAX_RESULTS = 40
TARGET_COUNT = 20

DOC_PATH = "doc/project_article.md"


def query_crossref(q, rows=40, from_year=2020):
    params = {
        "query": q,
        "rows": rows,
        "filter": f"from-pub-date:{from_year}-01-01",
    }
    r = requests.get(CROSSREF_URL, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fmt_authors(cr_item):
    authors = cr_item.get("author", [])
    parts = []
    for a in authors:
        given = a.get("given", "")
        family = a.get("family", "")
        if given and family:
            initials = "".join([p[0].upper() + "." for p in given.split() if p])
            parts.append(f"{family} {initials}")
        elif family:
            parts.append(family)
    if not parts:
        return ""
    if len(parts) > 3:
        return parts[0] + " et al."
    return ", ".join(parts)


def fmt_year(cr_item):
    issued = cr_item.get("issued", {}).get("date-parts", [])
    if issued and issued[0]:
        return str(issued[0][0])
    return "n.d."


def fmt_title(cr_item):
    title = cr_item.get("title", [])
    if title:
        return title[0]
    return "Untitled"


def fmt_container(cr_item):
    cont = cr_item.get("container-title", [])
    if cont:
        return cont[0]
    return ""


def fmt_doi(cr_item):
    doi = cr_item.get("DOI", "")
    if doi:
        return f"https://doi.org/{doi}"
    return ""


def make_ieee_entry(idx, item):
    authors = fmt_authors(item)
    title = fmt_title(item)
    container = fmt_container(item)
    year = fmt_year(item)
    doi = fmt_doi(item)
    # Shorten long titles for neatness (but keep full title in MD with DOI link)
    short_title = shorten(title, 180)
    entry_lines = []
    if authors:
        entry = f"[{idx}] {authors}, \"{short_title}\", {container}, {year}."
    else:
        entry = f"[{idx}] \"{short_title}\", {container}, {year}."
    if doi:
        entry += f" DOI: {doi}"
    entry_lines.append(entry)
    return "\n".join(entry_lines)


def merge_unique(results):
    seen = set()
    out = []
    for r in results:
        doi = r.get("DOI")
        key = doi.lower() if doi else (fmt_title(r)[:100].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def fetch_candidates():
    all_items = []
    for q in QUERY_TERMS:
        try:
            data = query_crossref(q, rows=MAX_RESULTS)
        except Exception as e:
            print(f"Warning: CrossRef query failed for '{q}': {e}", file=sys.stderr)
            continue
        items = data.get("message", {}).get("items", [])
        all_items.extend(items)
    unique = merge_unique(all_items)
    # Filter to year >=2020
    filtered = []
    for it in unique:
        try:
            y = int(fmt_year(it))
        except Exception:
            y = 0
        if y >= 2020:
            filtered.append(it)
    return filtered[:TARGET_COUNT]


def update_doc_with_refs(ref_items):
    if not os.path.exists(DOC_PATH):
        print(f"Error: {DOC_PATH} not found", file=sys.stderr)
        return False
    with open(DOC_PATH, "r", encoding="utf-8") as f:
        md = f.read()

    # Find the References header and the Appendix header
    m = re.search(r"# References[\s\S]*?# Appendix", md)
    if not m:
        # Try alternate header
        m2 = re.search(r"# References \(placeholders.*\)\n\n(.*?)\n\n# Appendix", md, flags=re.S)
        if not m2:
            print("Could not locate References block to replace.", file=sys.stderr)
            return False
        start, end = m2.span()
    else:
        start, end = m.span()
    # Prepare formatted references
    lines = []
    for i, it in enumerate(ref_items, start=1):
        lines.append(make_ieee_entry(i, it))
    ref_block = "# References\n\n" + "\n\n".join(lines) + "\n\n# Appendix"

    # Replace the region between '# References' and '# Appendix'
    new_md = re.sub(r"# References[\s\S]*?# Appendix", ref_block, md)

    with open(DOC_PATH, "w", encoding="utf-8") as f:
        f.write(new_md)
    print(f"Updated {DOC_PATH} with {len(lines)} references.")
    return True


if __name__ == "__main__":
    print("Fetching candidate references from CrossRef...")
    refs = fetch_candidates()
    if not refs:
        print("No references found. Exiting.", file=sys.stderr)
        sys.exit(1)
    ok = update_doc_with_refs(refs)
    if not ok:
        sys.exit(1)

    # Commit changes back to the repository if running in CI with token
    github_actor = os.getenv("GITHUB_ACTOR")
    github_token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    if github_token and repo:
        print("Committing updated references back to the repository...")
        os.system("git config user.email \"action@github.com\"")
        os.system(f"git config user.name \"{github_actor or 'github-action'}\"")
        os.system("git add %s" % DOC_PATH)
        commit_msg = "chore(docs): update references via CrossRef search"
        os.system(f"git commit -m \"{commit_msg}\" || echo 'nothing to commit'")
        # Push using token
        origin = f"https://{github_actor}:{github_token}@github.com/{repo}.git"
        os.system(f"git push {origin} HEAD:main || echo 'push failed'")
    else:
        print("GITHUB_TOKEN or repo not available; not committing changes.")
