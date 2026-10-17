"""Regenerate dark_mode.svg and light_mode.svg with live GitHub stats.

Terminal-inspired profile card for amrit-verse featuring the iconic
'Sic Mundus Creatus Est' Triquetra motif from DARK and verified system metrics.
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


TRIQUETRA_PATH = (
    "M742 1423 c-198 -134 -306 -315 -347 -583 -4 -30 -15 -41 -67 -75 "
    "-184 -118 -282 -283 -318 -530 -15 -110 -15 -111 35 -141 170 -99 456 -111 "
    "684 -29 l68 25 58 -25 c105 -47 177 -59 345 -58 169 0 270 19 354 66 l41 23 "
    "-1 90 c-3 209 -93 392 -256 519 -39 30 -83 63 -99 72 -23 14 -30 26 -34 62 "
    "-23 184 -51 273 -114 373 -67 107 -230 249 -283 248 -7 -1 -37 -17 -66 -37z "
    "m134 -44 c61 -38 162 -158 205 -243 98 -198 104 -474 16 -661 -39 -82 -152 "
    "-235 -173 -235 -8 0 -32 12 -54 26 l-40 27 63 66 c112 119 170 269 170 441 -1 "
    "173 -57 313 -171 426 -36 35 -71 64 -77 64 -22 0 -94 -59 -135 -112 -55 -69 "
    "-85 -129 -114 -230 -23 -82 -24 -83 -70 -102 -25 -11 -48 -17 -51 -14 -9 9 42 "
    "191 73 260 38 84 78 143 139 204 105 105 154 123 219 83z m-13 -196 c26 -26 "
    "62 -76 81 -112 37 -71 73 -177 64 -187 -3 -3 -33 0 -67 7 -38 7 -113 10 -197 "
    "7 l-136 -5 5 40 c9 63 64 163 129 233 33 35 64 64 68 64 4 0 28 -21 53 -47z "
    "m34 -344 c113 -15 113 -15 113 -57 0 -60 -6 -63 -85 -45 -84 18 -239 12 -330 "
    "-11 -142 -38 -277 -130 -344 -235 -33 -51 -84 -181 -95 -243 -12 -67 46 -96 "
    "211 -105 84 -5 119 -2 203 17 l101 23 27 -27 c33 -32 29 -36 -73 -69 -60 -19 "
    "-92 -22 -220 -22 -133 0 -157 3 -215 24 -35 13 -81 34 -100 47 -36 24 -36 25 "
    "-32 82 18 272 199 501 464 586 135 43 241 53 375 35z m364 -140 c67 -43 168 "
    "-153 207 -226 39 -75 70 -187 73 -274 3 -63 2 -64 -31 -87 -62 -42 -133 -56 "
    "-285 -56 -149 -1 -208 9 -317 50 -184 70 -341 228 -425 428 -18 43 -32 80 -31 "
    "81 2 1 22 12 46 24 40 20 43 21 49 4 54 -156 101 -238 190 -327 109 -109 250 "
    "-171 410 -182 87 -5 213 10 276 35 25 10 27 14 21 53 -19 143 -78 253 -187 "
    "355 l-67 62 6 46 c4 25 9 45 12 45 3 0 27 -14 53 -31z m-320 -22 c42 -13 44 "
    "-15 43 -50 -2 -58 -60 -165 -125 -229 -32 -32 -64 -58 -72 -58 -20 0 -86 80 "
    "-125 150 -26 46 -62 146 -62 171 0 7 65 26 115 33 48 7 177 -3 226 -17z m-489 "
    "-205 c26 -53 72 -128 103 -166 30 -38 55 -73 55 -77 0 -14 -144 -41 -220 -42 "
    "-76 0 -176 18 -186 34 -9 15 25 119 63 191 34 66 110 158 129 158 5 -1 30 -45 "
    "56 -98z m797 43 c56 -53 102 -133 127 -224 17 -61 17 -64 0 -77 -26 -19 -107 "
    "-34 -182 -34 -72 0 -204 26 -204 41 0 5 25 41 56 81 51 66 134 219 134 246 0 "
    "22 21 12 69 -33z"
)


def make_triquetra(color, tx=82, ty=85, scale=1.25):
    """Render the pure interlaced Celtic Triquetra knot."""
    return (
        f'<g transform="translate({tx}, {ty}) scale({scale})">'
        f'<g transform="translate(0, 146) scale(0.1, -0.1)" fill="{color}">'
        f'<path d="{TRIQUETRA_PATH}"/>'
        f"</g></g>"
    )


PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "symbol": "#58a6ff",      # Tech Cyan Triquetra knot
        "gold": "#ffa657",        # Amber Gold ("Sic Mundus Creatus Est")
        "h": "#58a6ff",           # Accent Blue
        "k": "#ffa657",           # Key Orange/Amber
        "v": "#c9d1d9",           # Value White
        "d": "#484f58",           # Dot Leader Gray
        "sub": "#8b949e",         # Subtitle gray
        "g": "#3fb950",           # Green
        "r": "#f85149",           # Red
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "symbol": "#0969da",      # Deep Tech Blue Triquetra knot
        "gold": "#953800",        # Warm Bronze ("Sic Mundus Creatus Est")
        "h": "#0969da",           # Accent Blue
        "k": "#953800",           # Key Warm Brown
        "v": "#24292f",           # Value Dark
        "d": "#afb8c1",           # Dot Leader Gray
        "sub": "#6e7781",         # Subtitle gray
        "g": "#1a7f37",           # Green
        "r": "#cf222e",           # Red
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

    # Render pure Triquetra knot
    out.append(make_triquetra(p["symbol"], tx=82, ty=85, scale=1.25))

    # Inscription & labels
    out.append(
        f'<text x="182" y="318" text-anchor="middle" fill="{p["gold"]}" font-weight="bold" font-size="13px" letter-spacing="2.5px" xml:space="preserve">SIC MUNDUS CREATUS EST</text>'
    )
    out.append(
        f'<text x="182" y="343" text-anchor="middle" fill="{p["h"]}" font-weight="bold" font-size="12px" letter-spacing="1.5px" xml:space="preserve">// AMRIT-VERSE //</text>'
    )
    out.append(
        f'<text x="182" y="365" text-anchor="middle" fill="{p["sub"]}" font-size="11px" letter-spacing="2px" xml:space="preserve">1953 · 1986 · 2019</text>'
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
