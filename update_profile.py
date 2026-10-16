"""Regenerate dark_mode.svg and light_mode.svg with live GitHub stats.

Terminal-inspired profile card for amrit-verse featuring an original
8-bit cyber companion motif with shades and verified system metrics.
Runs automatically via GitHub Actions or locally with the gh CLI.
Stdlib only — zero external package dependencies.
"""
import calendar
import html
import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone

USER = "amrit-verse"
JOINED_YEAR = 2025  # GitHub account creation year
W = 54              # Information column width in monospace characters

# Original 16x16 pixel-art cyber companion wearing shades
COMPANION_GRID = [
    "..##........##..",
    ".####......####.",
    ".######..######.",
    ".##############.",
    "################",
    "##WWWW####WWWW##",
    "##WLLWWWWWWLLW##",
    "##WLLWWWWWWLLW##",
    "##WWWW####WWWW##",
    "################",
    "###RR##MM##RR###",  # Cheeks with nose in center
    "#####MM##MM#####",  # Symmetric smile wings (:3)
    ".##############.",
    "..############..",
    "...##########...",
    "....##....##....",
]

PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "#": "#58a6ff",      # Cyber Blue body
        "W": "#ffffff",      # White sunglasses frame
        "L": "#0d1117",      # Dark lenses
        "R": "#f85149",      # Red/coral blush cheeks
        "M": "#0d1117",      # Dark mouth
        "h": "#58a6ff",      # Accent Blue
        "k": "#ffa657",      # Key Orange/Amber
        "v": "#c9d1d9",      # Value White
        "d": "#484f58",      # Dot Leader Gray
        "sub": "#484f58",    # Subtitle gray
        "g": "#3fb950",      # Green
        "r": "#f85149",      # Red
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "#": "#0969da",      # Rich Blue body
        "W": "#24292f",      # Dark sunglasses frame
        "L": "#ffffff",      # White lenses
        "R": "#cf222e",      # Coral blush cheeks
        "M": "#24292f",      # Dark mouth
        "h": "#0969da",      # Accent Blue
        "k": "#953800",      # Key Warm Brown
        "v": "#24292f",      # Value Dark
        "d": "#afb8c1",      # Dot Leader Gray
        "sub": "#afb8c1",    # Subtitle gray
        "g": "#1a7f37",      # Green
        "r": "#cf222e",      # Red
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
            "User-Agent": "amrit-verse-card-updater",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, json.loads(r.read() or "{}")


def graphql(query, variables=None, token=None):
    _, resp = gh(
        "https://api.github.com/graphql",
        {"query": query, "variables": variables or {}},
        token,
    )
    if resp.get("errors"):
        print("GraphQL warning:", resp["errors"])
        return None
    return resp.get("data")


def fetch_stats():
    """Fetch verified dynamic statistics from GitHub GraphQL API."""
    fallback = {
        "followers": 5,
        "repos": 19,
        "contributed": 4,
        "stars": 1,
        "commits": 201,
    }

    if not TOKEN and not PRIV_TOKEN:
        return fallback

    try:
        current_year = datetime.now(timezone.utc).year
        yr_aliases = "\n".join(
            f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y + 1}-01-01T00:00:00Z")'
            " { totalCommitContributions restrictedContributionsCount }"
            for y in range(JOINED_YEAR, current_year + 1)
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
            followers {{ totalCount }}
            repositories(first: 100, ownerAffiliations: OWNER) {{
              totalCount
              nodes {{ stargazerCount isFork }}
            }}
            repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {{
              totalCount
            }}
          }}
        }}""",
            token=PRIV_TOKEN,
        )

        if not u_data or not u_data.get("user"):
            return fallback

        u = u_data["user"]
        repos_nodes = u["repositories"]["nodes"]
        return {
            "followers": u["followers"]["totalCount"],
            "repos": u["repositories"]["totalCount"],
            "contributed": u["repositoriesContributedTo"]["totalCount"],
            "stars": sum(n["stargazerCount"] for n in repos_nodes),
            "commits": commits,
        }

    except Exception as e:
        print(f"Error fetching stats dynamically: {e}; using fallback.")
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
        kv("Identity", "Amritesh Mishra (CS Undergrad)"),
        kv("Environment", "Debian GNU/Linux (Bare Metal)"),
        kv("Shell & Tools", "Bash, Zsh, Neovim, Docker"),
        kv("Core Focus", "Backend Systems, APIs, Networking"),
        [],
        kv("Languages", "Java, TypeScript, Python, SQL, Bash"),
        kv("Backend", "Spring Boot, Node.js, Express, Next.js"),
        kv("Databases", "PostgreSQL, MySQL, MongoDB, Prisma"),
        kv("Infrastructure", "Docker Compose, Nginx, KVM/QEMU, Scapy"),
        [],
        rule("Contact & Profiles"),
        kv("Website", "amritesh.com.np"),
        kv("Email", "contact@amritesh.com.np"),
        kv("LinkedIn", "in/amriteshmishra0"),
        [],
        rule("Verified GitHub Metrics"),
        kv2("Repositories", f"{s['repos']} (Contributed: {s['contributed']})", "Stars Earned", n(s["stars"])),
        kv2("Contributions", f"{n(s['commits'])} commits", "Followers", n(s["followers"])),
    ]


def render(mode, stats):
    p = PALETTES[mode]
    font_stack = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, 'Liberation Mono', monospace"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="870" height="475" viewBox="0 0 870 475" '
        f'font-family="{font_stack}" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="869" height="474" rx="12" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]

    # Render original 8-bit cyber companion wearing shades
    ps = 11
    start_x = 75
    start_y = 110
    pixel_rects = []
    for r, row in enumerate(COMPANION_GRID):
        for c, ch in enumerate(row):
            if ch in p and ch != "bg":
                pixel_rects.append(
                    f'<rect x="{start_x + c * ps}" y="{start_y + r * ps}" width="{ps}" height="{ps}" fill="{p[ch]}" rx="1.5"/>'
                )
    out.append("".join(pixel_rects))

    out.append(
        f'<text x="95" y="325" fill="{p["h"]}" font-weight="bold" font-size="13px" letter-spacing="1px" xml:space="preserve">// AMRIT-VERSE //</text>'
    )
    out.append(
        f'<text x="105" y="348" fill="{p["sub"]}" font-weight="bold" font-size="12px" xml:space="preserve">terminal · companion</text>'
    )

    # Render system & verified metrics on the right
    for i, segs in enumerate(info_lines(stats)):
        if not segs:
            continue
        spans = "".join(f'<tspan fill="{p[c]}">{html.escape(t)}</tspan>' for t, c in segs)
        out.append(f'<text x="365" y="{45 + i * 21}" xml:space="preserve">{spans}</text>')

    out.append("</svg>")
    return "\n".join(out)


def selfcheck():
    assert len("".join(t for t, _ in kv("Environment", "Debian GNU/Linux (Bare Metal)"))) == W


if __name__ == "__main__":
    selfcheck()
    stats = fetch_stats()
    print("Fetched verified stats:", stats)

    for mode in PALETTES:
        svg_content = render(mode, stats)
        filename = f"{mode}_mode.svg"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Generated {filename}")
