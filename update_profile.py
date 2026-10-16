"""Regenerate dark_mode.svg / light_mode.svg with live GitHub stats.

Debian-native terminal / fastfetch profile card for amrit-verse.
Runs automatically via GitHub Actions. Stdlib only.
"""
import calendar
import html
import json
import os
import subprocess
import urllib.request
from datetime import date, datetime, timezone

USER = "amrit-verse"
JOINED_YEAR = 2025  # account creation year
W = 54              # info column width in characters

DEBIAN_LINES = [
    r'        _,met$$$$$gg.',
    r'     ,g$$$$$$$$$$$$$$$P.',
    r'   ,g$$P"        """Y$$.".',
    r'  ,$$P\'              `$$$.',
    r' \',$$P       ,ggs.     `$$b:',
    r' `d$$\'     ,$P"\'   .    $$$',
    r'  $$P      d$\'     ,    $$$P',
    r'  $$:      $$.   -    ,d$$\'',
    r'  $$;      Y$b._   _,d$P\'',
    r'  Y$$.    `.`"Y$$$$P"\'',
    r'  `$$b      "-.__',
    r'   `Y$$',
    r'    `Y$$.',
    r'      `$$b.',
    r'        `Y$$b.',
    r'           `"Y$b._',
    r'               `"""',
]

PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "art": "#e9546b",    # Debian Red
        "h": "#58a6ff",      # Header Blue
        "k": "#ffa657",      # Key Orange/Amber
        "v": "#c9d1d9",      # Value White
        "d": "#484f58",      # Dot Gray
        "g": "#3fb950",      # Green additions
        "r": "#f85149",      # Red deletions
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "art": "#d70a53",    # Debian Red
        "h": "#0969da",      # Header Blue
        "k": "#953800",      # Key Brown
        "v": "#24292f",      # Value Dark
        "d": "#afb8c1",      # Dot Gray
        "g": "#1a7f37",      # Green additions
        "r": "#cf222e",      # Red deletions
    },
}


def get_tokens():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
    priv_token = os.environ.get("ACCESS_TOKEN") or token
    if not token:
        try:
            token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
            priv_token = priv_token or token
        except Exception:
            pass
    return token, priv_token


TOKEN, PRIV_TOKEN = get_tokens()


def gh(url, payload=None, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode() if payload else None,
        headers={
            "Authorization": f"Bearer {token or TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "debian-fastfetch-updater",
        },
    )
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read() or "{}")


def graphql(query, variables=None, token=None):
    _, resp = gh(
        "https://api.github.com/graphql",
        {"query": query, "variables": variables or {}},
        token,
    )
    if resp.get("errors"):
        print("GraphQL error:", resp["errors"])
        return None
    return resp.get("data")


LOC_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef { target { ... on Commit {
      history(first: 100, author: {id: $id}, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { additions deletions }
      }
    } } }
  }
}"""


def loc(repo_names, user_id):
    add = rem = 0
    for name in repo_names:
        cursor = None
        try:
            while True:
                data = graphql(
                    LOC_QUERY,
                    {"owner": USER, "name": name, "id": user_id, "cursor": cursor},
                    token=PRIV_TOKEN,
                )
                if not data or not data.get("repository"):
                    break
                ref = data["repository"].get("defaultBranchRef")
                if ref is None:
                    break
                h = ref["target"]["history"]
                add += sum(n["additions"] for n in h["nodes"])
                rem += sum(n["deletions"] for n in h["nodes"])
                if not h["pageInfo"]["hasNextPage"]:
                    break
                cursor = h["pageInfo"]["endCursor"]
        except Exception as e:
            print(f"loc {name}: {e}")
    return {"loc_add": add, "loc_del": rem, "loc": add - rem}


def fetch_stats():
    fallback = {
        "followers": 5,
        "repos": 19,
        "contributed": 4,
        "stars": 1,
        "commits": 199,
        "loc": 190230,
        "loc_add": 199919,
        "loc_del": 9689,
    }

    try:
        yr_aliases = "\n".join(
            f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z")'
            " { totalCommitContributions restrictedContributionsCount }"
            for y in range(JOINED_YEAR, datetime.now(timezone.utc).year + 1)
        )
        contrib_data = graphql(f'query {{ user(login: "{USER}") {{ {yr_aliases} }} }}')
        if contrib_data and contrib_data.get("user"):
            commits = sum(
                v["totalCommitContributions"] + v["restrictedContributionsCount"]
                for v in contrib_data["user"].values()
            )
        else:
            commits = fallback["commits"]

        u_data = graphql(
            f"""
        query {{
          user(login: "{USER}") {{
            id
            followers {{ totalCount }}
            repositories(first: 100, ownerAffiliations: OWNER) {{
              totalCount
              nodes {{ name stargazerCount isFork }}
            }}
            repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {{
              totalCount
            }}
          }}
        }}""",
            token=PRIV_TOKEN,
        )

        if not u_data or not u_data.get("user"):
            return fallback

        u = u_data["user"]
        stats = {
            "followers": u["followers"]["totalCount"],
            "repos": u["repositories"]["totalCount"],
            "contributed": u["repositoriesContributedTo"]["totalCount"],
            "stars": sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
            "commits": commits,
        }

        repo_names = [
            n["name"] for n in u["repositories"]["nodes"] if not n["isFork"]
        ]
        loc_stats = loc(repo_names, u["id"])
        stats.update(loc_stats)
        return stats

    except Exception as e:
        print(f"Error fetching stats: {e}, using fallback")
        return fallback


def kv(key, val, width=W):
    dots = "." * max(width - len(key) - len(str(val)) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (str(val), "v")]


def kv2(k1, v1, k2, v2):
    left = kv(k1, v1, 28)
    return left + [(" | ", "d")] + kv(k2, v2, 23)


def rule(title=""):
    label = f"─ {title} " if title else ""
    return [(label, "h"), ("─" * (W - len(label)), "d")]


def info_lines(s):
    n = lambda x: f"{x:,}"
    return [
        [(f"amrit@{USER} ", "h"), ("─" * (W - len(USER) - 7), "d")],
        [],
        kv("OS", "Debian GNU/Linux (bare-metal)"),
        kv("Shell", "bash, zsh"),
        kv("Editor", "Neovim, VS Code"),
        kv("Virtualization", "Docker, KVM / QEMU"),
        [],
        kv("Languages", "Java, TypeScript, Python, SQL, Bash"),
        kv("Frameworks", "Spring Boot, Next.js, Express"),
        kv("Databases", "PostgreSQL, MySQL, MongoDB"),
        kv("Systems Focus", "Backend APIs, Packet Analysis, Nginx"),
        [],
        rule("Contact & Links"),
        kv("Portfolio", "amritesh.com.np"),
        kv("Email", "contact@amritesh.com.np"),
        kv("LinkedIn", "in/amriteshmishra0"),
        [],
        rule("GitHub Verified Stats"),
        kv2("Repos", f"{s['repos']} (Contributed: {s['contributed']})", "Stars", n(s["stars"])),
        kv2("Commits", n(s["commits"]), "Followers", n(s["followers"])),
        [
            ("Lines of Code: ", "k"),
            (n(s["loc"]), "v"),
            (" ( ", "d"),
            (n(s["loc_add"]) + "++", "g"),
            (", ", "d"),
            (n(s["loc_del"]) + "--", "r"),
            (" )", "d"),
        ],
    ]


def render(mode, stats):
    p = PALETTES[mode]
    font_stack = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, 'Liberation Mono', monospace"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="870" height="490" viewBox="0 0 870 490" '
        f'font-family="{font_stack}" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="869" height="489" rx="12" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    # Draw Debian spiral centered on left
    for i, line in enumerate(DEBIAN_LINES):
        out.append(
            f'<text x="35" y="{85 + i * 19}" fill="{p["art"]}" font-weight="bold" xml:space="preserve">{html.escape(line)}</text>'
        )

    for i, segs in enumerate(info_lines(stats)):
        if not segs:
            continue
        spans = "".join(f'<tspan fill="{p[c]}">{html.escape(t)}</tspan>' for t, c in segs)
        out.append(f'<text x="365" y="{42 + i * 20}" xml:space="preserve">{spans}</text>')

    out.append("</svg>")
    return "\n".join(out)


def selfcheck():
    assert len("".join(t for t, _ in kv("OS", "Debian GNU/Linux (bare-metal)"))) == W


if __name__ == "__main__":
    selfcheck()
    stats = fetch_stats()
    print("Live stats:", stats)

    for mode in PALETTES:
        svg_content = render(mode, stats)
        filename = f"{mode}_mode.svg"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated {filename}")
