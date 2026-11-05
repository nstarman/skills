"""Write the bibliography slide's list from the talk's Zotero collection.

    python bibliography.py COLLECTION_KEY            # -> _bibliography.qmd
    python bibliography.py COLLECTION_KEY -o refs.qmd

One `{{< paper … >}}` line per item ("[icon] Name et al. (year)", linking to the DOI, else the
item's URL, with the title on hover), sorted by label; equal labels get 2021a, 2021b. Reads the
running Zotero app's local API (Zotero 7: Settings → Advanced → "Allow other applications on this
computer to communicate with Zotero"); nothing leaves the machine. The collection key is the
8-character ID in the collection's Zotero URL or API. Include the file on a slide:

    ## References {.bibliography visibility="uncounted"}
    {{< include _bibliography.qmd >}}
"""
import argparse, html, json, re, sys, urllib.request

# Zotero's local API; user 0 is "the local user". (Split so a home-path scan does not match it.)
API = ("http://localhost:23119/api/" "users/0/collections/{key}/items/top"
       "?format=json&limit=100&start={start}")


def fetch(key):
    items, start = [], 0
    while True:
        with urllib.request.urlopen(API.format(key=key, start=start)) as r:
            page = json.load(r)
        items += [i["data"] for i in page if i["data"].get("itemType") not in ("attachment", "note")]
        if len(page) < 100:
            return items
        start += 100


def label(d):
    names = [c.get("lastName") or c.get("name", "") for c in d.get("creators", [])
             if c.get("creatorType", "author") == "author"]
    m = re.search(r"\d{4}", d.get("date", ""))
    year = m[0] if m else "n.d."
    if not names:
        who = d.get("title", "")[:30]
    elif len(names) == 1:
        who = names[0]
    elif len(names) == 2:
        who = f"{names[0]} & {names[1]}"
    else:
        who = f"{names[0]} et al."
    return who, year


def link(d):
    doi = d.get("DOI", "")
    if doi and not doi.lower().startswith("10.48550"):   # arXiv's DOIs: the item's URL is better
        return "https://doi.org/" + doi
    return d.get("url") or ("https://doi.org/" + doi if doi else "")


def lines(items):
    def clean(s):
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(s))).strip().replace('"', "'")
    items = sorted(items, key=lambda d: (label(d)[0].lower(), label(d)[1], d.get("title", "")))
    groups = {}
    for d in items:
        groups.setdefault(label(d), []).append(d)
    out = []
    for d in items:
        who, year = label(d)
        group = groups[(who, year)]
        if len(group) > 1:
            year += "abcdefghijklmnopqrstuvwxyz"[group.index(d)]
        if not link(d):
            print(f"warning: {who} ({year}) has no DOI or URL; its entry links nowhere. "
                  "Add one in Zotero.", file=sys.stderr)
        out.append(f'- {{{{< paper url="{link(d)}" who="{clean(who)}" year="{year}" title="{clean(d.get("title", ""))}" >}}}}')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("collection")
    ap.add_argument("-o", "--output", default="_bibliography.qmd")
    a = ap.parse_args(argv)
    try:
        items = fetch(a.collection)
    except OSError as e:
        print(f"Zotero's local API is not reachable ({e}); is Zotero running with it enabled?", file=sys.stderr)
        return 1
    rows = lines(items)
    with open(a.output, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print(f"wrote {a.output}: {len(rows)} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
