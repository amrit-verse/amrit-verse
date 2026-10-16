"""Regenerate dark_mode.svg / light_mode.svg with live GitHub stats.

Terminal / neofetch-style profile card for amrit-verse.
Runs daily via GitHub Actions. Stdlib only, no third-party dependencies.
"""
import calendar
import html
import json
import os
import subprocess
import urllib.request
from datetime import date, datetime, timezone

USER = "amrit-verse"

# Customize your birthday (YYYY, MM, DD) below to calculate your uptime
BIRTHDAY = date(2005, 5, 10)

JOINED_YEAR = 2025  # account creation year
W = 56              # info column width in characters

# Choose active ASCII art style: "PORTRAIT" or "DEBIAN"
ACTIVE_ART = "PORTRAIT"

PORTRAIT_ART = r"""
              ..:::.
           .=*%@@@@%#=.
          -#%%%%%%@@@@%=
         -%#******#%@@@@*
        .+++++===--=+**##-
        **--*%#%#--=----=+
       .%#==+%@%%+##**+*#*:
       .*====+**+===+++#*+:
       .+=+****+==+++**##*:
        +%%%%##%#+*****##*
        .#*+***########%#:
         :#*#***%%%%%%%%-
       :=#%####%@%%%%%#*+=:
     :*%@@@%%%@@%%%%##**#%@*:
    =%@%%%%@@@%%%%#*****##%@@+
   +@%%%%%%%%%%%%%##***##%%%%@*
  =@%%@%%%%%%%%%%%%##*##%%%%%%@+
 .%%%%%%%@@@@%%%%%%%%*#%%%%%%%%@.
 :@%%%%%%%%%%%%@@%%%%%%%%%%%@%%%-
 :@%%%%%%%%%%%%%@%%%%@%%%@%%%%%%-
 .%%%%%%%%%%%%%%%%%%%%%%%%%%%%%@:
  =@%%%%%%%%%%%%%%%%%%%%%%%%%%@*
   *@%%%%%%%%%%%%%%%%%%%%%%%%@*
    =%%%%%%%%%%%%%%%%%%%%%%@@+
     :*%%%%%%%%%%%%%%%%%%%%#-
"""

DEBIAN_ART = r"""
          _,met$$$$$gg.
       ,g$$$$$$$$$$$$$$$P.
     ,g$$P"        """ + '"""' + r"""Y$$.".
    ,$$P'              `$$$.
   ',$$P       ,ggs.     `$$b:
   `d$$'     ,$P"'   .    $$$
    $$P      d$'     ,    $$$P
    $$:      $$.   -    ,d$$'
    $$;      Y$b._   _,d$P'
    Y$$.    `.`"Y$$$$P"'
    `$$b      "-.__
     `Y$$
      `Y$$.
        `$$b.
          `Y$$b.
             `"Y$b._
                 `"""

PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "art": "#8b949e",
        "h": "#58a6ff",
        "k": "#ffa657",
        "v": "#c9d1d9",
        "d": "#484f58",
        "g": "#3fb950",
        "r": "#f85149",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "art": "#57606a",
        "h": "#0969da",
        "k": "#953800",
        "v": "#24292f",
        "d": "#afb8c1",
        "g": "#1a7f37",
        "r": "#cf222e",
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
            "User-Agent": "terminal-profile-generator",
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


def age(b, t):
    years = t.year - b.year - ((t.month, t.day) < (b.month, b.day))
    months = (t.month - b.month - (t.day < b.day)) % 12
    if t.day >= b.day:
        days = t.day - b.day
    else:
        pm_year, pm = (t.year, t.month - 1) if t.month > 1 else (t.year - 1, 12)
        days = calendar.monthrange(pm_year, pm)[1] - b.day + t.day
    return years, months, days


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
        "commits": 198,
        "loc": 189854,
        "loc_add": 199443,
        "loc_del": 9589,
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
    left = kv(k1, v1, 30)
    return left + [(" | ", "d")] + kv(k2, v2, 23)


def rule(title=""):
    label = f"─ {title} " if title else ""
    return [(label, "h"), ("─" * (W - len(label)), "d")]


def info_lines(s):
    y, m, d = age(BIRTHDAY, date.today())
    n = lambda x: f"{x:,}"
    return [
        [(f"{USER.lower()}@github ", "h"), ("─" * (W - len(USER) - 8), "d")],
        [],
        kv("OS", "Linux (Debian)"),
        kv("Uptime", f"{y} years, {m} months, {d} days"),
        kv("Host", "Excel Engineering College"),
        kv("Kernel", "Full-Stack Developer"),
        kv("IDE", "VS Code, Neovim"),
        [],
        kv("Languages.Programming", "Java, Python, TypeScript, Bash"),
        kv("Languages.Real", "Nepali, English, Hindi"),
        kv("Hobbies", "Linux Ricing, DevOps, Networking"),
        [],
        rule("Contact"),
        kv("Email", "contact@amritesh.com.np"),
        kv("Portfolio", "amritesh.com.np"),
        kv("LinkedIn", "in/amriteshmishra0"),
        [],
        rule("GitHub Stats"),
        kv2(
            "Repos",
            f"{s['repos']} {{Contributed: {s['contributed']}}}",
            "Stars",
            n(s["stars"]),
        ),
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


def render(mode, stats, art):
    p = PALETTES[mode]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="850" height="515" viewBox="0 0 850 515" '
        'font-family="ui-monospace, SFMono-Regular, \'SF Mono\', Menlo, Monaco, Consolas, \'Liberation Mono\', monospace" font-size="13px">',
        f'<rect x="0.5" y="0.5" width="849" height="514" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>',
    ]
    for i, line in enumerate(art.strip("\n").split("\n")):
        out.append(
            f'<text x="25" y="{50 + i * 16}" fill="{p["art"]}" xml:space="preserve">{html.escape(line)}</text>'
        )
    for i, segs in enumerate(info_lines(stats)):
        if not segs:
            continue
        spans = "".join(f'<tspan fill="{p[c]}">{html.escape(t)}</tspan>' for t, c in segs)
        out.append(
            f'<text x="385" y="{45 + i * 21}" xml:space="preserve">{spans}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def selfcheck():
    assert len("".join(t for t, _ in kv("OS", "Linux (Debian)"))) == W


if __name__ == "__main__":
    selfcheck()
    stats = fetch_stats()
    print("Fetched stats:", stats)

    art = PORTRAIT_ART if ACTIVE_ART == "PORTRAIT" else DEBIAN_ART

    for mode in PALETTES:
        svg_content = render(mode, stats, art)
        filename = f"{mode}_mode.svg"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(svg_content)
        print(f"Wrote {filename}")
