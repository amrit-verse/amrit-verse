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


def make_triquetra(stroke_color, bg_color, tx=85, ty=82, scale=0.55):
    """Render the iconic interlaced Triquetra and circle knot from DARK."""
    return (
        f'<g transform="translate({tx}, {ty}) scale({scale})">'
        f'<g transform="translate(-124,739.7) scale(0.1,-0.1)" fill="none">'
        f'<circle cx="3000" cy="5382.05" r="1164" stroke-width="336" stroke="{bg_color}" />'
        f'<circle cx="3000" cy="5382.05" r="1164" stroke-width="168" stroke="{stroke_color}" />'
        f'<path d="M4512.79,4400.08 C4456.01,5193.68,3795.63,5808.51,3000,5808.51 C2204.37,5808.51,1543.99,5193.69,1487.21,4400.09 M1393.2,4562.92 C1599.7,4462.61,1826.28,4410.49,2055.86,4410.49 C2893.48,4410.49,3572.52,5089.52,3572.52,5927.15 C3572.52,6430.48,3322.81,6901.02,2905.99,7183.15 M3094.01,7183.15 C2677.19,6901.02,2427.48,6430.48,2427.48,5927.15 C2427.48,5089.52,3106.51,4410.49,3944.14,4410.49 C4173.72,4410.49,4400.3,4462.61,4606.81,4562.92" stroke-width="336" stroke="{bg_color}" />'
        f'<path d="M4507.93,4454.3 C4424.95,5224.59,3774.75,5808.51,3000,5808.51 C2225.26,5808.51,1575.06,5224.6,1492.07,4454.31 M1442.59,4540.01 C1635.76,4454.61,1844.65,4410.49,2055.86,4410.49 C2893.48,4410.49,3572.52,5089.52,3572.52,5927.15 C3572.52,6411.25,3341.42,6866.27,2950.52,7151.83 M3049.49,7151.83 C2658.58,6866.27,2427.48,6411.25,2427.48,5927.15 C2427.48,5089.52,3106.51,4410.49,3944.14,4410.49 C4155.36,4410.49,4364.24,4454.61,4557.42,4540.02" stroke-width="168" stroke="{stroke_color}" />'
        f'<path d="M2581.95,5749.76 C2488.58,5722.98,2398,5687.3,2311.45,5643.2 M3527.47,5560.24 C3550.96,5654.49,3565.35,5750.78,3570.44,5847.78 M2890.58,4836.16 C2960.45,4768.68,3036.65,4708.08,3118.11,4655.17 M3778.87,6247.07 C3616.77,6393.02,3416.93,6490.49,3202.13,6528.37 M1861.44,5624.06 C1844.53,5544.5,1836,5463.39,1836,5382.05 C1836,5246.27,1859.76,5111.53,1906.2,4983.94 M3359.7,4275.02 C3567.14,4342.42,3751.47,4466.76,3891.68,4633.85" stroke-width="336" stroke="{bg_color}" />'
        f'<path d="M2607.46,5756.83 C2496.54,5727.11,2389.36,5684.89,2287.97,5630.98 M3520.84,5534.61 C3550.56,5645.53,3567.59,5759.46,3571.59,5874.22 M2871.7,4854.71 C2952.9,4773.52,3043.05,4701.8,3140.44,4640.95 M3808.58,6219.36 C3631.76,6390.12,3405.42,6500.51,3162,6534.72 M1870.58,5663.65 C1847.61,5571.54,1836,5476.98,1836,5382.05 C1836,5232.61,1864.78,5084.57,1920.76,4946.01 M3320.84,4263.14 C3557.13,4330.9,3765.91,4471.72,3917.24,4665.42" stroke-width="168" stroke="{stroke_color}" />'
        f'</g>'
        f'</g>'
    )


PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "symbol": "#58a6ff",      # Tech Cyan knot stroke
        "symbol_bg": "#0d1117",   # Interlace cutout mask
        "ring_dash": "#30363d",   # Outer dashed time ring
        "ring_solid": "#21262d",  # Concentric outer ring
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
        "symbol": "#0969da",      # Deep Tech Blue knot stroke
        "symbol_bg": "#ffffff",   # Interlace cutout mask
        "ring_dash": "#d0d7de",   # Outer dashed time ring
        "ring_solid": "#eaeef2",  # Concentric outer ring
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

    # Render outer celestial / time-loop orbital rings
    out.append(
        f'<circle cx="182" cy="193" r="105" fill="none" stroke="{p["ring_dash"]}" stroke-width="1.2" stroke-dasharray="3 3" />'
    )
    out.append(
        f'<circle cx="182" cy="193" r="114" fill="none" stroke="{p["ring_solid"]}" stroke-width="0.8" />'
    )

    # Render iconic DARK Triquetra and circle knot
    out.append(make_triquetra(p["symbol"], p["symbol_bg"], tx=85, ty=82, scale=0.55))

    # Inscription & labels
    out.append(
        f'<text x="182" y="322" text-anchor="middle" fill="{p["gold"]}" font-weight="bold" font-size="13px" letter-spacing="2.5px" xml:space="preserve">SIC MUNDUS CREATUS EST</text>'
    )
    out.append(
        f'<text x="182" y="347" text-anchor="middle" fill="{p["h"]}" font-weight="bold" font-size="12px" letter-spacing="1.5px" xml:space="preserve">// AMRIT-VERSE //</text>'
    )
    out.append(
        f'<text x="182" y="368" text-anchor="middle" fill="{p["sub"]}" font-size="11px" letter-spacing="2px" xml:space="preserve">1953 · 1986 · 2019</text>'
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
