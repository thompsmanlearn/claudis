#!/usr/bin/env python3
"""
AADP Stats Server — exposes Pi system metrics over HTTP.
Runs as a systemd service on port 9100.
Callable from n8n via http://host.docker.internal:9100/system_status
"""
import glob
import os
import subprocess
import urllib.request
import urllib.parse
import json as _json
from datetime import datetime, timezone, timedelta

import psutil
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

REPO = "/home/thompsman/aadp/claudis"


def _git(*args, check=False):
    """Run a git command in REPO, return (stdout, returncode)."""
    result = subprocess.run(
        ["git", "-C", REPO, *args],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout.strip(), result.returncode


def _push():
    out, rc = _git("push", "origin", "main")
    return rc == 0


def gh_cmd_dispatch(cmd: str, args: str) -> str:
    """Dispatch a /gh_* command to the appropriate git operation."""
    args = args.strip()

    if cmd == "gh_status":
        last, _ = _git("log", "-1", "--oneline")
        branches_raw, _ = _git("branch", "--list")
        attempt_branches = [b.strip() for b in branches_raw.splitlines() if "attempt/" in b]
        try:
            becoming = open(f"{REPO}/BECOMING.md").read()
            # Return the last dated section
            sections = [s.strip() for s in becoming.split("## 20") if s.strip()]
            last_section = ("## 20" + sections[-1]) if sections else "(no entries)"
            last_section_preview = "\n".join(last_section.splitlines()[:8])
        except Exception:
            last_section_preview = "(unreadable)"
        open_count = len(attempt_branches)
        branch_list = "\n".join(f"  {b}" for b in attempt_branches) if attempt_branches else "  (none)"
        return (
            f"📌 Last commit: {last}\n"
            f"🌿 Open attempt branches: {open_count}\n{branch_list}\n\n"
            f"📖 BECOMING (latest):\n{last_section_preview}"
        )

    elif cmd == "gh_becoming":
        try:
            return open(f"{REPO}/BECOMING.md").read()
        except Exception as e:
            return f"Error reading BECOMING.md: {e}"

    elif cmd == "gh_attempts":
        branches_raw, _ = _git("branch", "--list")
        attempt_branches = [b.strip() for b in branches_raw.splitlines() if "attempt/" in b]
        if not attempt_branches:
            return "No open attempt branches."
        lines = ["Open attempt branches:\n"]
        for branch in attempt_branches:
            first_commit, _ = _git("log", "--oneline", "--reverse", branch, "--", "--format=%s")
            first_line = first_commit.splitlines()[0] if first_commit else "(no commits)"
            lines.append(f"🌿 {branch}\n   Hypothesis: {first_line}")
        return "\n\n".join(lines)

    elif cmd == "gh_log":
        n = int(args) if args.isdigit() else 10
        log, _ = _git("log", f"-{n}", "--oneline", "--all")
        return f"📋 Last {n} commits:\n\n{log}" if log else "No commits found."

    elif cmd == "gh_review":
        branch = args.replace("attempt/", "")
        log, rc = _git("log", "--oneline", f"attempt/{branch}")
        if rc != 0 or not log:
            log, rc = _git("log", "--oneline", branch)
        return f"🔍 {branch}:\n\n{log}" if log else f"Branch not found: {branch}"

    elif cmd == "gh_keep":
        branch = args.replace("attempt/", "")
        tag = f"signal:keep/{branch}"
        _git("tag", tag, f"attempt/{branch}")
        out, rc = _git("push", "origin", tag)
        if rc == 0:
            return f"✅ signal:keep applied to attempt/{branch} and pushed."
        return f"⚠️ Tag applied locally but push failed. Run: git push origin {tag}"

    elif cmd == "gh_redirect":
        if not args:
            return "⚠️ Usage: /gh_redirect <note>"
        today = datetime.now().strftime("%Y-%m-%d")
        aspiration = f"\n## Aspiration — {today}\n\n{args}\n"
        try:
            with open(f"{REPO}/BECOMING.md", "a") as f:
                f.write(aspiration)
            _git("add", "BECOMING.md")
            _git("commit", "-m", f"redirect: {args[:60]}")
            if _push():
                return f"✅ Aspiration added to BECOMING.md and pushed."
            return "✅ Aspiration added and committed locally. Push failed — check credentials."
        except Exception as e:
            return f"Error: {e}"

    elif cmd == "gh_close":
        # args format: "branch_name|close note" or just "branch_name"
        parts = args.split("|", 1)
        branch = parts[0].strip().replace("attempt/", "")
        note = parts[1].strip() if len(parts) > 1 else "Closed from Telegram"
        today = datetime.now().isoformat()
        close_file = f"{REPO}/attempts/.closed_{branch.replace('/', '_')}.md"
        try:
            with open(close_file, "w") as f:
                f.write(f"# Close note: attempt/{branch}\n\n{note}\n\nClosed: {today}\n")
            _git("add", close_file)
            _git("commit", "-m", f"close: attempt/{branch} — {note[:50]}")
            if _push():
                return f"✅ Close note committed for attempt/{branch} and pushed."
            return "✅ Close note committed locally. Push failed — check credentials."
        except Exception as e:
            return f"Error: {e}"

    elif cmd == "gh_report":
        n = int(args) if args.isdigit() else 5
        session_dir = f"{REPO}/sessions"
        files = sorted(glob.glob(f"{session_dir}/[0-9]*.md"))[-n:]
        if not files:
            return "No session artifacts found yet."
        parts = []
        for fpath in files:
            fname = os.path.basename(fpath)
            try:
                content = open(fpath).read()
                parts.append(f"=== {fname} ===\n{content}")
            except Exception:
                pass
        return "\n\n".join(parts)

    return f"Unknown command: {cmd}"

app = FastAPI(title="AADP Stats", docs_url=None, redoc_url=None)


def get_system_status() -> dict:
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = int(datetime.now(timezone.utc).timestamp() - psutil.boot_time())

    temp_c = None
    try:
        temps = psutil.sensors_temperatures()
        for key in ("cpu_thermal", "coretemp", "acpitz"):
            if key in temps and temps[key]:
                temp_c = round(temps[key][0].current, 1)
                break
        if temp_c is None and temps:
            first_key = next(iter(temps))
            if temps[first_key]:
                temp_c = round(temps[first_key][0].current, 1)
    except Exception:
        pass

    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_gb": round(mem.used / 1e9, 2),
        "memory_total_gb": round(mem.total / 1e9, 2),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1e9, 2),
        "disk_total_gb": round(disk.total / 1e9, 2),
        "temperature_c": temp_c,
        "uptime_seconds": uptime,
        "uptime_human": f"{uptime // 3600}h {(uptime % 3600) // 60}m",
        "sampled_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/system_status")
def system_status():
    return JSONResponse(get_system_status())


@app.get("/healthz")
def healthz():
    return JSONResponse({"status": "ok"})


def _get_claimed_task():
    """Check Supabase for any currently claimed work_queue tasks."""
    try:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if not os.path.exists(env_path):
            env_path = "/home/thompsman/aadp/mcp-server/.env"
        sb_url, sb_key = None, None
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("SUPABASE_URL="):
                    sb_url = line.split("=", 1)[1].strip()
                elif line.startswith("SUPABASE_SERVICE_KEY=") or line.startswith("SUPABASE_KEY="):
                    sb_key = line.split("=", 1)[1].strip()
        if not sb_url or not sb_key:
            return None
        url = f"{sb_url}/rest/v1/work_queue?status=eq.claimed&select=task_type,claimed_at&limit=1"
        req = urllib.request.Request(url, headers={"apikey": sb_key, "Authorization": f"Bearer {sb_key}"})
        with urllib.request.urlopen(req, timeout=3) as r:
            data = _json.loads(r.read())
            return data[0] if data else None
    except Exception:
        return None


@app.api_route("/trigger_sentinel", methods=["GET", "POST"])
def trigger_sentinel(force: str = Query(default="")):
    # Check if already running — return early rather than blocking
    check = subprocess.run(
        ["systemctl", "is-active", "aadp-sentinel.service"],
        capture_output=True, text=True, timeout=5
    )
    if check.stdout.strip() in ("active", "activating"):
        # Check if mid-task and force not set
        if not force:
            claimed = _get_claimed_task()
            if claimed:
                return JSONResponse({
                    "status": "mid_task",
                    "task_type": claimed.get("task_type", "?"),
                    "claimed_at": claimed.get("claimed_at", "?"),
                    "hint": "Send /wake again with ?force=1 to interrupt"
                })
        return JSONResponse({"status": "already_running"})

    result = subprocess.run(
        ["sudo", "systemctl", "start", "--no-block", "aadp-sentinel.service"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode == 0:
        return JSONResponse({"status": "triggered"})
    return JSONResponse(
        {"status": "error", "detail": result.stderr.strip()},
        status_code=500
    )


@app.get("/gh")
def gh_command(cmd: str = Query(...), args: str = Query(default="")):
    return JSONResponse({"text": gh_cmd_dispatch(cmd, args)})


@app.post("/append_experiment")
def append_experiment(payload: dict):
    """Append content to an experiments/ file (creates if absent) and commit.
    Body: {path: str (relative to experiments/), content: str}
    """
    rel_path = payload.get("path", "")
    content  = payload.get("content", "")
    if not rel_path or not content:
        return JSONResponse({"error": "path and content required"}, status_code=400)
    import re
    if ".." in rel_path or rel_path.startswith("/"):
        return JSONResponse({"error": "invalid path"}, status_code=400)
    fpath = f"{REPO}/experiments/{rel_path}"
    os.makedirs(os.path.dirname(fpath), exist_ok=True)
    try:
        with open(fpath, "a") as f:
            f.write(content)
        _git("add", fpath)
        _git("commit", "-m", f"research: append to {rel_path}")
        pushed = _push()
        return JSONResponse({"status": "appended", "pushed": pushed, "path": fpath})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Daily Research Scout
# ---------------------------------------------------------------------------

_RESEARCH_TOPICS = [
    "AI agent architecture",
    "memory and retrieval systems for AI agents",
    "multi-agent coordination",
    "tool use and function calling in AI",
    "autonomous code generation",
    "agent evaluation and benchmarking",
    "self-improving and meta-learning AI systems",
]

_ENV_PATH = "/home/thompsman/aadp/mcp-server/.env"


def _read_env_simple():
    env = {}
    try:
        with open(_ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    except Exception:
        pass
    return env


def _sb_get(env, path):
    """GET from Supabase REST API."""
    url = f"{env['SUPABASE_URL']}/rest/v1/{path}"
    req = urllib.request.Request(url, headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}"
    })
    with urllib.request.urlopen(req, timeout=8) as r:
        return _json.loads(r.read())


def _sb_upsert(env, table, payload):
    """UPSERT to Supabase REST API."""
    url = f"{env['SUPABASE_URL']}/rest/v1/{table}"
    data = _json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }, method="POST")
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.status


def _fetch_arxiv(topic, max_results=3):
    import time, xml.etree.ElementTree as ET
    q = urllib.parse.quote(f'ti:"{topic}" OR abs:"{topic}"')
    url = f"http://export.arxiv.org/api/query?search_query={q}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    req = urllib.request.Request(url, headers={"User-Agent": "AADP-Claudis/1.0 (research scout; contact via github.com/thompsmanlearn/claudis)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            xml_data = r.read()
        time.sleep(3)  # arXiv rate limit courtesy
        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        results = []
        for entry in root.findall("atom:entry", ns):
            title   = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")[:400]
            link    = entry.find("atom:id", ns).text.strip()
            results.append({"title": title, "summary": summary, "url": link, "source": "arXiv", "topic": topic})
        return results
    except Exception as e:
        return []


def _fetch_hn(topic, max_results=3):
    q = urllib.parse.quote(topic)
    url = f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage={max_results}"
    req = urllib.request.Request(url, headers={"User-Agent": "AADP-Claudis/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = _json.loads(r.read())
        results = []
        for hit in data.get("hits", []):
            title = hit.get("title", "")
            link  = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            results.append({"title": title, "summary": title, "url": link, "source": "HN", "topic": topic})
        return results
    except Exception as e:
        return []


def _fetch_devto(tags, max_per_tag=3):
    results = []
    seen = set()
    for tag in tags:
        url = f"https://dev.to/api/articles?per_page={max_per_tag}&top=30&tag={urllib.parse.quote(tag)}"
        req = urllib.request.Request(url, headers={"User-Agent": "AADP-Claudis/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = _json.loads(r.read())
            for art in data:
                link = art.get("url", "")
                title = art.get("title", "")
                desc = art.get("description", "") or ""
                if link and title and link not in seen:
                    seen.add(link)
                    results.append({"title": title, "summary": desc or title, "url": link, "source": "dev.to", "topic": tag})
        except Exception:
            pass
    return results


def _fetch_medium(tags, max_per_tag=3):
    import xml.etree.ElementTree as _ET
    results = []
    seen = set()
    for tag in tags:
        url = f"https://medium.com/feed/tag/{urllib.parse.quote(tag)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AADP-Research/1.0)"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read()
            root = _ET.fromstring(raw)
            items = root.findall(".//item")
            count = 0
            for item in items:
                if count >= max_per_tag:
                    break
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if link and title and link not in seen:
                    seen.add(link)
                    results.append({"title": title, "summary": title, "url": link, "source": "Medium", "topic": tag})
                    count += 1
        except Exception:
            pass
    return results


def _fetch_github(queries, max_per_query=3):
    results = []
    seen = set()
    for query in queries:
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&order=desc&per_page={max_per_query}"
        req = urllib.request.Request(url, headers={"User-Agent": "AADP-Claudis/1.0", "Accept": "application/vnd.github.v3+json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = _json.loads(r.read())
            for repo in data.get("items", []):
                link = repo.get("html_url", "")
                name = repo.get("full_name", "")
                desc = repo.get("description", "") or ""
                stars = repo.get("stargazers_count", 0)
                if link and name and link not in seen:
                    seen.add(link)
                    results.append({"title": f"{name} ★{stars}", "summary": desc, "url": link, "source": "GitHub", "topic": query})
        except Exception:
            pass
    return results


def _fetch_lobsters(tags, max_per_tag=3):
    results = []
    seen = set()
    for tag in tags:
        url = f"https://lobste.rs/t/{urllib.parse.quote(tag)}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "AADP-Claudis/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = _json.loads(r.read())
            count = 0
            for story in data:
                if count >= max_per_tag:
                    break
                title = story.get("title", "")
                link = story.get("url", "") or story.get("short_id_url", "")
                if link and title and link not in seen:
                    seen.add(link)
                    results.append({"title": title, "summary": title, "url": link, "source": "lobste.rs", "topic": tag})
                    count += 1
        except Exception:
            pass
    return results


COMPANY_ENGINEERING_BLOGS = [
    ("openai", "https://openai.com/news/rss.xml"),
    ("deepmind", "https://deepmind.google/blog/rss.xml"),
    # Anthropic: no public RSS feed as of 2026-05-03 (lesson: anthropic_no_rss_2026-05-03)
]
_COMPANY_BLOG_CAP = 3  # posts per feed per run; raise this constant to tune


def _fetch_company_engineering_blogs(max_per_feed=None):
    """Freshness-driven fetcher for company engineering blogs via RSS.
    This source is freshness-driven, not query-driven; queries are ignored.
    Returns up to max_per_feed posts per feed from the last 30 days.
    One feed erroring does not block the others; errors logged to journald.
    """
    import xml.etree.ElementTree as _ET
    from email.utils import parsedate_to_datetime
    if max_per_feed is None:
        max_per_feed = _COMPANY_BLOG_CAP
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    results = []
    for org, feed_url in COMPANY_ENGINEERING_BLOGS:
        try:
            req = urllib.request.Request(
                feed_url,
                headers={"User-Agent": "AADP-Claudis/1.0 (research scout; contact via github.com/thompsmanlearn/claudis)"}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
            root = _ET.fromstring(raw)
            count = 0
            for item in root.findall(".//item"):
                if count >= max_per_feed:
                    break
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                desc = (item.findtext("description") or "").strip()
                pub_date_str = (item.findtext("pubDate") or "").strip()
                if not title or not link:
                    continue
                if pub_date_str:
                    try:
                        pub_dt = parsedate_to_datetime(pub_date_str)
                        if pub_dt.tzinfo is None:
                            pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                        if pub_dt < cutoff:
                            continue
                    except Exception:
                        pass
                results.append({
                    "title": title,
                    "url": link,
                    "source": org,
                    "summary": desc or title,
                })
                count += 1
        except Exception as e:
            try:
                subprocess.run(
                    ["systemd-cat", "-t", "aadp-stats", "-p", "err"],
                    input=f"_fetch_company_engineering_blogs: feed={org} url={feed_url} error={e}",
                    text=True, timeout=5
                )
            except Exception:
                pass
    return results


def _fetch_anthropic_signals(env, max_reddit=10, max_releases=5):
    """Fetch developer signals about Claude/Anthropic from Reddit r/ClaudeAI and Anthropic GitHub releases."""
    results = []

    # Reddit r/ClaudeAI — developer discussions, real use cases, problems
    try:
        req = urllib.request.Request(
            f"https://www.reddit.com/r/ClaudeAI/new.json?limit={max_reddit}",
            headers={"User-Agent": "AADP-Claudis/1.0 (research scout; github.com/thompsmanlearn/claudis)"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            data = _json.loads(r.read())
        for post in data.get("data", {}).get("children", []):
            p = post.get("data", {})
            title   = p.get("title", "")
            selftext = p.get("selftext", "")[:300]
            link    = f"https://reddit.com{p.get('permalink', '')}"
            results.append({"title": title, "summary": selftext or title, "url": link,
                            "source": "Reddit r/ClaudeAI", "topic": "anthropic_developer_signals"})
    except Exception:
        pass

    # Anthropic GitHub releases — SDK/API changes, new capabilities
    github_token = env.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "AADP-Claudis/1.0", "Accept": "application/vnd.github.v3+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    for repo in ["anthropics/anthropic-sdk-python", "anthropics/claude-code"]:
        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}/releases?per_page={max_releases}",
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                releases = _json.loads(r.read())
            for rel in releases[:max_releases]:
                title   = f"{repo} {rel.get('tag_name', '')} — {rel.get('name', '')}"
                body    = (rel.get("body") or "")[:300]
                link    = rel.get("html_url", "")
                results.append({"title": title, "summary": body or title, "url": link,
                                "source": "Anthropic GitHub", "topic": "anthropic_developer_signals"})
        except Exception:
            pass

    return results


def _send_telegram(message, env):
    """Send a message via Telegram Quick Send webhook (best effort)."""
    try:
        payload = _json.dumps({"chat_id": 8513796837, "message": message}).encode()
        req = urllib.request.Request(
            "http://localhost:5678/webhook/telegram-quick-send",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8):
            pass
    except Exception:
        pass


def _score_with_haiku(candidates, api_key):
    """Score candidates 1-10 for AADP relevance using Haiku. Returns list of {score, reason}."""
    if not candidates:
        return []
    items_txt = "\n".join(
        f"{i+1}. [{c['source']}] {c['title']}\n   Summary: {c['summary'][:200]}\n   Topic: {c['topic']}"
        for i, c in enumerate(candidates)
    )
    prompt = (
        "You are evaluating research items for relevance to AADP — an Autonomous Agent Developer Platform "
        "running on a Raspberry Pi 5. AADP builds, tests, and improves AI agents using n8n workflows, "
        "Supabase, ChromaDB, and Claude/Haiku via API. The operator is a solo developer focused on "
        "autonomous agent growth and self-improvement.\n\n"
        "Score each item 1-10 for relevance:\n"
        "9-10: Directly applicable — AADP could implement this immediately\n"
        "7-8: Clearly relevant — would inform design decisions\n"
        "5-6: Tangentially related\n"
        "1-4: Not relevant to AADP specifically\n\n"
        f"Items to score:\n{items_txt}\n\n"
        "Respond with a JSON array only — one object per item in order:\n"
        '[{"score": N, "reason": "one sentence"}, ...]'
    )
    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = _json.loads(r.read())
        text = resp["content"][0]["text"].strip()
        # Extract JSON array from response
        start = text.find("[")
        end   = text.rfind("]") + 1
        return _json.loads(text[start:end])
    except Exception as e:
        return [{"score": 0, "reason": f"scoring failed: {e}"}] * len(candidates)


def _chromadb_add(collection, doc_id, content, metadata):
    """Add a document to ChromaDB via MCP venv subprocess. Returns True on success."""
    script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
try:
    col = client.get_collection(args['collection'])
except Exception:
    col = client.create_collection(args['collection'])
col.upsert(ids=[args['id']], documents=[args['content']], metadatas=[args['metadata']])
print('ok')
"""
    import json as _j
    proc = subprocess.run(
        ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
         _j.dumps({"collection": collection, "id": doc_id,
                   "content": content, "metadata": metadata})],
        capture_output=True, text=True, timeout=30
    )
    return proc.returncode == 0


def _write_research_day(date_str, topics_used, entries):
    """Write/append today's research file and update INDEX.md. Single commit."""
    day_path  = f"{REPO}/experiments/research/{date_str}.md"
    idx_path  = f"{REPO}/experiments/research/INDEX.md"
    os.makedirs(f"{REPO}/experiments/research", exist_ok=True)

    topics_line = " · ".join(topics_used)

    # Build day file content
    header = f"# Research: {date_str}\n*Topics: {topics_line}*\n*Entries: {len(entries)}*\n\n---\n\n"
    entry_blocks = []
    for e in entries:
        block = (
            f"### [{e['source']}] {e['title']}\n"
            f"**Topic:** {e['topic']}\n"
            f"**Relevance:** {e['score']}/10\n"
            f"**Why it matters for AADP:** {e['reason']}\n"
            f"**Link:** {e['url']}\n"
            f"**Date:** {date_str}\n\n---\n\n"
        )
        entry_blocks.append(block)

    # Create or overwrite day file (idempotent for same day)
    with open(day_path, "w") as f:
        f.write(header + "".join(entry_blocks))

    # Update INDEX.md
    idx_header = "# Research Index\n\n| Date | Topics | Entries |\n|---|---|---|\n"
    new_row = f"| {date_str} | {topics_line} | {len(entries)} |\n"
    if not os.path.exists(idx_path):
        with open(idx_path, "w") as f:
            f.write(idx_header + new_row)
    else:
        with open(idx_path) as f:
            lines = f.readlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith(f"| {date_str} |"):
                new_lines.append(new_row)
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(new_row)
        with open(idx_path, "w") as f:
            f.writelines(new_lines)

    _git("add", day_path, idx_path)
    _git("commit", "-m", f"research: {date_str} — {len(entries)} entries ({topics_line})")
    return _push()


@app.post("/run_daily_research")
def run_daily_research(payload: dict = {}):
    """Daily research scout. Fetch arXiv+HN → Haiku scoring → write to experiments/research/.
    Idempotent: skips if today's file already contains entries.
    """
    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found in .env"}, status_code=500)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    day_path = f"{REPO}/experiments/research/{today}.md"

    # Idempotency check
    if os.path.exists(day_path) and not payload.get("force"):
        return JSONResponse({"status": "already_run", "date": today})

    # Get rotation index from Supabase
    try:
        rows = _sb_get(env, "system_config?key=eq.research_rotation_index&select=value")
        rotation_idx = int(rows[0]["value"]) if rows else 0
    except Exception:
        rotation_idx = 0

    # Pick today's 3 topics
    topics_today = [_RESEARCH_TOPICS[(rotation_idx + i) % len(_RESEARCH_TOPICS)] for i in range(3)]
    next_idx = (rotation_idx + 3) % len(_RESEARCH_TOPICS)

    # Fetch candidates (arXiv + HN per topic)
    candidates = []
    for topic in topics_today:
        candidates.extend(_fetch_arxiv(topic, max_results=3))
        candidates.extend(_fetch_hn(topic, max_results=3))

    if not candidates:
        return JSONResponse({"status": "no_candidates", "date": today, "topics": topics_today})

    # Score with Haiku
    scores = _score_with_haiku(candidates, api_key)

    # Merge scores, filter ≥7, cap at 3
    scored = []
    for i, c in enumerate(candidates):
        s = scores[i] if i < len(scores) else {"score": 0, "reason": "unscored"}
        if s.get("score", 0) >= 7:
            scored.append({**c, "score": s["score"], "reason": s.get("reason", "")})
    scored.sort(key=lambda x: x["score"], reverse=True)
    entries = scored[:3]

    # Write to GitHub
    pushed = _write_research_day(today, topics_today, entries)

    # Write to ChromaDB research_findings so lesson_injector can surface these
    chroma_ok = 0
    for entry in entries:
        topic_slug = entry.get("topic", "general").replace(" ", "_")[:40]
        doc_id = f"daily_research_{topic_slug}_{today}"
        content = (
            f"{entry.get('title', '')}\n"
            f"Topic: {entry.get('topic', '')}\n"
            f"Source: {entry.get('source', '')}\n"
            f"Relevance: {entry.get('score', '')}/10\n"
            f"Why it matters for AADP: {entry.get('reason', '')}\n"
            f"Link: {entry.get('url', '')}"
        )
        metadata = {
            "source": "daily_research_scout",
            "topic": entry.get("topic", ""),
            "date": today,
            "score": entry.get("score", 0),
            "link": entry.get("url", ""),
        }
        if _chromadb_add("research_findings", doc_id, content, metadata):
            chroma_ok += 1

    # Write to Supabase research_papers for structured temporal querying
    sb_ok = 0
    for entry in entries:
        try:
            _sb_upsert(env, "research_papers", {
                "title": entry.get("title", "")[:500],
                "abstract": entry.get("summary", "")[:800],
                "source": entry.get("source", ""),
                "source_id": entry.get("url", "")[:500],
                "url": entry.get("url", ""),
                "topic_tags": [entry.get("topic", "")],
                "relevance_score": round(entry.get("score", 0) / 10.0, 2),
                "status": "discovered",
                "discovered_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "notes": entry.get("reason", "")[:800],
            })
            sb_ok += 1
        except Exception:
            pass

    # Fetch and score Anthropic developer signals (Reddit r/ClaudeAI + GitHub releases)
    forum_posts = _fetch_anthropic_signals(env)
    forum_scored = []
    if forum_posts:
        forum_scores = _score_with_haiku(forum_posts, api_key)
        for i, post in enumerate(forum_posts):
            s = forum_scores[i] if i < len(forum_scores) else {"score": 0, "reason": "unscored"}
            score = s.get("score", 0)
            if score >= 7:
                forum_scored.append({**post, "score": score, "reason": s.get("reason", "")})

    forum_chroma = 0
    telegram_alerts = []
    for post in forum_scored:
        slug = post.get("title", "post").lower().replace(" ", "_")[:40]
        doc_id = f"anthropic_forum_{slug}_{today}"
        content = (
            f"{post.get('title', '')}\n"
            f"Source: Anthropic Developer Forum\n"
            f"Relevance: {post.get('score', '')}/10\n"
            f"Why it matters for AADP: {post.get('reason', '')}\n"
            f"Link: {post.get('url', '')}\n"
            f"Excerpt: {post.get('summary', '')}"
        )
        metadata = {
            "source": "anthropic_forum",
            "topic": "anthropic_developer_forum",
            "date": today,
            "score": post.get("score", 0),
            "link": post.get("url", ""),
        }
        if _chromadb_add("research_findings", doc_id, content, metadata):
            forum_chroma += 1
        if post.get("score", 0) >= 8:
            telegram_alerts.append(f"• [{post['score']}/10] {post['title']}\n  {post.get('url','')}")

    if telegram_alerts:
        msg = "📡 Anthropic Forum — high-relevance posts today:\n\n" + "\n\n".join(telegram_alerts)
        _send_telegram(msg, env)

    # Update rotation index
    try:
        _sb_upsert(env, "system_config", {"key": "research_rotation_index", "value": next_idx, "updated_at": "now()"})
    except Exception:
        pass

    return JSONResponse({
        "status": "complete",
        "date": today,
        "topics": topics_today,
        "candidates_fetched": len(candidates),
        "entries_written": len(entries),
        "pushed": pushed,
        "chroma_written": chroma_ok,
        "forum_posts_scored": len(forum_scored),
        "forum_chroma_written": forum_chroma,
    })


@app.post("/write_experiment")
def write_experiment(payload: dict):
    """Write a structured experiment artifact to experiments/sessions/ and commit to GitHub.
    Body: {filename: str, content: str}
    filename should be YYYY-MM-DD-HHMM.md
    """
    filename = payload.get("filename", "")
    content = payload.get("content", "")
    if not filename or not content:
        return JSONResponse({"error": "filename and content required"}, status_code=400)
    # Sanitize filename — alphanumeric, hyphens, underscores, dot only
    import re
    if not re.match(r'^[\w\-]+\.md$', filename):
        return JSONResponse({"error": "invalid filename"}, status_code=400)
    sessions_dir = f"{REPO}/experiments/sessions"
    os.makedirs(sessions_dir, exist_ok=True)
    fpath = f"{sessions_dir}/{filename}"
    try:
        with open(fpath, "w") as f:
            f.write(content)
        _git("add", fpath)
        _git("commit", "-m", f"session report: {filename}")
        pushed = _push()
        return JSONResponse({"status": "committed", "pushed": pushed, "path": fpath})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/lessons_applied")
def lessons_applied(payload: dict):
    """Increment times_applied for lessons_learned rows retrieved by lesson_injector.
    Matches by chromadb_id (primary) or content (fallback for legacy lessons).
    Body: {"ids": [str, ...], "contents": [str, ...]}
    Returns: {"status": "ok", "by_id": N, "by_content": N}
    """
    ids = payload.get("ids", [])
    contents = payload.get("contents", [])
    if not ids and not contents:
        return JSONResponse({"status": "ok", "by_id": 0, "by_content": 0, "skipped": "no ids or contents"})

    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase credentials not found in .env"}, status_code=500)

    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
    }

    by_id = 0
    by_content = 0

    # Primary: match by chromadb_id
    if ids:
        data = _json.dumps({"lesson_ids": ids}).encode()
        req = urllib.request.Request(
            f"{sb_url}/rest/v1/rpc/increment_lessons_applied_by_id",
            data=data, headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                r.read()
            by_id = len(ids)
        except Exception:
            pass

    # Fallback: match by content (for lessons without chromadb_id set)
    if contents:
        data = _json.dumps({"lesson_contents": contents}).encode()
        req = urllib.request.Request(
            f"{sb_url}/rest/v1/rpc/increment_lessons_applied",
            data=data, headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                r.read()
            by_content = len(contents)
        except Exception:
            pass

    return JSONResponse({"status": "ok", "by_id": by_id, "by_content": by_content})


@app.get("/lesson_stats")
def lesson_stats():
    """Lesson utilization summary (B-111, 2026-05-08).
    Returns total lessons, mean times_applied, never-applied count, top applied,
    and category breakdown. Used by Anvil get_lesson_stats() callable.
    """
    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase credentials not found"}, status_code=500)

    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
    }

    def _sb_get(path):
        req = urllib.request.Request(sb_url + path, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return _json.loads(r.read())

    try:
        # Summary stats via RPC
        rows = _sb_get(
            "/rest/v1/lessons_learned"
            "?select=times_applied,category"
            "&limit=1000"
        )
        total = len(rows)
        never_applied = sum(1 for r in rows if (r.get("times_applied") or 0) == 0)
        applied_counts = [r.get("times_applied") or 0 for r in rows]
        mean_applied = sum(applied_counts) / total if total else 0
        max_applied = max(applied_counts) if applied_counts else 0

        # Category distribution (top 10 by count)
        from collections import Counter
        cat_counts = Counter(r.get("category") or "uncategorized" for r in rows)
        top_categories = [{"category": c, "count": n} for c, n in cat_counts.most_common(10)]

        # Top 5 most applied (by times_applied desc)
        top_applied = _sb_get(
            "/rest/v1/lessons_learned"
            "?select=id,title,category,times_applied"
            "&order=times_applied.desc"
            "&limit=5"
        )

        return JSONResponse({
            "total": total,
            "never_applied": never_applied,
            "never_applied_pct": round(never_applied / total * 100, 1) if total else 0,
            "mean_times_applied": round(mean_applied, 2),
            "max_times_applied": max_applied,
            "top_categories": top_categories,
            "top_applied": top_applied,
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/get_outputs")
def get_outputs(agent_name: str, limit: int = 5, exclude_type: str = ""):
    """Fetch recent experimental_outputs for an agent from Supabase.
    Returns {outputs: [...], count: N} — always a single JSON object (never a raw array)
    so n8n HTTP Request nodes receive exactly 1 item (no array-unwrapping issue).
    Query params:
      agent_name (required)
      limit (default 5)
      exclude_type (optional): exclude rows with this output_type (e.g. '4pillars_evaluation')
    """
    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    if not sb_url or not sb_key:
        return JSONResponse({"outputs": [], "count": 0, "error": "Supabase credentials not found"})

    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
    }

    try:
        from urllib.parse import quote
        url = (
            f"{sb_url}/rest/v1/experimental_outputs"
            f"?agent_name=eq.{quote(agent_name)}"
            f"&order=created_at.desc"
            f"&limit={limit}"
        )
        if exclude_type:
            url += f"&output_type=neq.{quote(exclude_type)}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = _json.loads(r.read().decode())
        outputs = raw if isinstance(raw, list) else []
    except Exception as e:
        outputs = []

    return JSONResponse({"outputs": outputs, "count": len(outputs)})


@app.get("/get_audit")
def get_audit(agent_name: str, limit: int = 15):
    """Fetch recent audit_log entries for an agent from Supabase.
    Filters by actor=agent_name. Returns {entries: [...], count: N} — wrapped
    to avoid n8n array-unwrapping issue.
    Query params:
      agent_name (required): filter by actor field in audit_log
      limit (default 15)
    """
    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    if not sb_url or not sb_key:
        return JSONResponse({"entries": [], "count": 0, "error": "Supabase credentials not found"})

    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
    }

    try:
        from urllib.parse import quote
        url = (
            f"{sb_url}/rest/v1/audit_log"
            f"?actor=eq.{quote(agent_name)}"
            f"&order=timestamp.desc"
            f"&limit={limit}"
        )
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = _json.loads(r.read().decode())
        entries = raw if isinstance(raw, list) else []
    except Exception:
        entries = []

    return JSONResponse({"entries": entries, "count": len(entries)})


@app.post("/memory_query")
def memory_query(payload: dict):
    """Proxy ChromaDB semantic query using MCP server venv (chromadb 0.5.20).
    Body: {collection: str, query_text: str, n_results: int, distance_threshold: float}
    Returns: [{id, content, distance}, ...]  filtered by distance_threshold (default 1.4)
    """
    collection = payload.get("collection", "lessons_learned")
    query_text = payload.get("query_text", "")
    n_results = int(payload.get("n_results", 5))
    threshold = float(payload.get("distance_threshold", 1.4))

    if not query_text:
        return JSONResponse({"error": "query_text required"}, status_code=400)

    script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
results = col.query(query_texts=[args['query_text']], n_results=args['n_results'])
ids   = results.get('ids', [[]])[0]
docs  = results.get('documents', [[]])[0]
dists = results.get('distances', [[]])[0]
output = [{'id': ids[i], 'content': docs[i], 'distance': dists[i]} for i in range(len(ids))
          if dists[i] < args['threshold']]
print(json.dumps(output))
"""
    proc = subprocess.run(
        ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
         _json.dumps({"collection": collection, "query_text": query_text,
                      "n_results": n_results, "threshold": threshold})],
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        return JSONResponse({"error": proc.stderr[:500]}, status_code=500)
    try:
        results = _json.loads(proc.stdout)
        # Wrap in object so n8n HTTP Request node doesn't unwrap the array into multiple items
        return JSONResponse({"results": results, "count": len(results)})
    except Exception as e:
        return JSONResponse({"error": f"parse failed: {e}", "raw": proc.stdout[:200]}, status_code=500)


@app.post("/get_research_window")
def get_research_window(payload: dict = {}):
    """Return research_findings from ChromaDB within a date window.
    Body: {days_back: int (default 21), collection: str (default 'research_findings')}
    Returns: {entries: [{id, content, metadata}], count: int, date_range: {start, end}}
    """
    days_back  = int(payload.get("days_back", 21))
    collection = payload.get("collection", "research_findings")

    end_date   = datetime.utcnow()
    start_date = (end_date - timedelta(days=days_back)).strftime("%Y-%m-%d")
    end_str    = end_date.strftime("%Y-%m-%d")

    script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
results = col.get(include=["documents", "metadatas"])
ids   = results.get('ids', [])
docs  = results.get('documents', [])
metas = results.get('metadatas', [])
start = args['start_date']
entries = [
    {"id": ids[i], "content": docs[i], "metadata": metas[i]}
    for i in range(len(ids))
    if (metas[i] or {}).get("date", "") >= start
]
entries.sort(key=lambda x: x["metadata"].get("date", ""), reverse=True)
print(json.dumps(entries))
"""
    proc = subprocess.run(
        ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
         _json.dumps({"collection": collection, "start_date": start_date})],
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        return JSONResponse({"error": proc.stderr[:500]}, status_code=500)
    try:
        entries = _json.loads(proc.stdout)
        return JSONResponse({
            "entries": entries,
            "count": len(entries),
            "date_range": {"start": start_date, "end": end_str},
        })
    except Exception as e:
        return JSONResponse({"error": f"parse failed: {e}", "raw": proc.stdout[:200]}, status_code=500)


def _chroma_multi_query(collection, phrases, n_results_each=4, threshold=1.4):
    """Query ChromaDB with multiple phrases, return deduped results sorted by best distance."""
    if not phrases:
        return []
    script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
best = {}  # id -> {id, content, distance}
for phrase in args['phrases']:
    results = col.query(query_texts=[phrase], n_results=args['n_results'])
    ids   = results.get('ids', [[]])[0]
    docs  = results.get('documents', [[]])[0]
    dists = results.get('distances', [[]])[0]
    for i in range(len(ids)):
        if dists[i] < args['threshold']:
            doc_id = ids[i]
            if doc_id not in best or dists[i] < best[doc_id]['distance']:
                best[doc_id] = {'id': doc_id, 'content': docs[i], 'distance': dists[i]}
output = sorted(best.values(), key=lambda x: x['distance'])
print(json.dumps(output))
"""
    proc = subprocess.run(
        ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
         _json.dumps({"collection": collection, "phrases": phrases,
                      "n_results": n_results_each, "threshold": threshold})],
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        return []
    try:
        return _json.loads(proc.stdout)
    except Exception:
        return []


def _expand_intent_with_haiku(task_type, description, api_key):
    """Use Haiku to expand task_type+description into 3-4 specific technical search phrases.
    Returns list of phrases, or [] on failure (caller should fall back to v1 query)."""
    task_label = task_type or "general"
    task_desc = description or ""
    prompt = (
        "You help a retrieval system find the most useful lessons from a technical knowledge base. "
        "The knowledge base contains lessons about: n8n workflow gotchas, Supabase API patterns, "
        "ChromaDB query behavior, Claude API usage, agent evaluation, and AADP system operations.\n\n"
        f"Task type: {task_label}\n"
        f"Description: {task_desc if task_desc else '(none provided)'}\n\n"
        "Generate 3-4 specific technical search phrases that would retrieve the most useful lessons "
        "for someone about to work on this task. Be specific — name concrete technical patterns, "
        "failure modes, or API behaviors, not vague topic labels.\n\n"
        'Reply with a JSON array only. Example: ["n8n webhook trigger registration", '
        '"Supabase upsert conflict resolution", "ChromaDB distance threshold calibration"]'
    )
    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = _json.loads(r.read())
        text = resp["content"][0]["text"].strip()
        start = text.find("[")
        end   = text.rfind("]") + 1
        phrases = _json.loads(text[start:end])
        return [p for p in phrases if isinstance(p, str) and p.strip()][:4]
    except Exception:
        return []


@app.post("/inject_context_v3")
def inject_context_v3(payload: dict = {}):
    """Task-type-routed context injection with retrieval-vs-reasoning confidence signal (v3.0).
    Extends v2.1: per-task-type collection routing, confidence scoring, retrieve_recommendation.
    New response fields: routing_applied, confidence_tier, min_distance, retrieve_confidence,
    retrieve_recommendation (retrieve | reason_with_context | reason).
    """
    task_type   = payload.get("task_type", "general")
    task_id     = payload.get("task_id", "")
    description = payload.get("description", "")

    # When description is empty, use a rich default so Haiku generates specific queries
    # rather than generic phrases — broadens lesson retrieval coverage over time.
    if not description:
        description = _V3_DEFAULT_DESCRIPTIONS.get(task_type, "")

    # --- Routing: housekeeping tasks skip retrieval entirely ---
    HOUSEKEEPING_TYPES = {"housekeeping", "status_check", "heartbeat", "ping"}
    if task_type in HOUSEKEEPING_TYPES and len(description) < 50:
        return JSONResponse({
            "task_id": task_id, "task_type": task_type, "description": description,
            "context_block": "", "lesson_count": 0, "lesson_ids": [], "lesson_contents": [],
            "expansion_phrases": [], "token_estimate": 0,
            "routing_applied": "housekeeping_skip",
            "confidence_tier": "none", "min_distance": None,
            "retrieve_confidence": 0.0, "retrieve_recommendation": "reason",
            "queries": {"skipped": True, "reason": "housekeeping task type"},
        })

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")

    # --- Determine collection routing ---
    collections_to_query = _V3_TASK_ROUTING.get(task_type, _V3_DEFAULT_COLLECTIONS)
    routing_applied = task_type if task_type in _V3_TASK_ROUTING else "default"

    # --- Haiku intent expansion ---
    expansion_phrases = []
    if api_key:
        expansion_phrases = _expand_intent_with_haiku(task_type, description, api_key)
    if not expansion_phrases:
        fallback_q = f"{task_type} {description}".strip() or "general"
        expansion_phrases = [fallback_q]

    # --- Single-collection query helper (no metadata needed) ---
    def _single_query(collection, query_text, n_results=2, threshold=1.2):
        script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
results = col.query(query_texts=[args['query_text']], n_results=args['n_results'])
ids   = results.get('ids', [[]])[0]
docs  = results.get('documents', [[]])[0]
dists = results.get('distances', [[]])[0]
output = [{'id': ids[i], 'content': docs[i], 'distance': dists[i]}
          for i in range(len(ids)) if dists[i] < args['threshold']]
print(json.dumps(output))
"""
        proc = subprocess.run(
            ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
             _json.dumps({"collection": collection, "query_text": query_text,
                          "n_results": n_results, "threshold": threshold})],
            capture_output=True, text=True, timeout=15
        )
        if proc.returncode != 0:
            return []
        try:
            return _json.loads(proc.stdout)
        except Exception:
            return []

    # --- Shared multi-phrase query script for lessons_learned (with metadata) ---
    lessons_script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
best = {}
for phrase in args['phrases']:
    results = col.query(query_texts=[phrase], n_results=args['n_results'],
                        include=['documents', 'distances', 'metadatas'])
    ids   = results.get('ids', [[]])[0]
    docs  = results.get('documents', [[]])[0]
    dists = results.get('distances', [[]])[0]
    metas = results.get('metadatas', [[]])[0]
    for i in range(len(ids)):
        if dists[i] < args['threshold']:
            doc_id = ids[i]
            if doc_id not in best or dists[i] < best[doc_id]['distance']:
                meta = metas[i] if metas else {}
                best[doc_id] = {'id': doc_id, 'content': docs[i], 'distance': dists[i], 'metadata': meta}
output = sorted(best.values(), key=lambda x: x['distance'])
print(json.dumps(output))
"""

    def _multi_phrase_query(collection, phrases, n_results, threshold):
        proc = subprocess.run(
            ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", lessons_script,
             _json.dumps({"collection": collection, "phrases": phrases,
                          "n_results": n_results, "threshold": threshold})],
            capture_output=True, text=True, timeout=30
        )
        if proc.returncode != 0:
            return []
        try:
            return _json.loads(proc.stdout)
        except Exception:
            return []

    # --- Query each routed collection ---
    now = datetime.utcnow()
    seen_ids = set()
    all_results_by_collection = {}
    primary_query = f"{task_type} {description}".strip() or "general"

    for col_name in collections_to_query:
        params = _V3_COLLECTION_PARAMS.get(col_name, (3, 1.2))
        n_results, threshold = params

        if col_name == "lessons_learned":
            # Multi-phrase with staleness penalty
            raw = _multi_phrase_query(col_name, expansion_phrases, n_results, threshold)
            raw = raw[:5]
            for r in raw:
                meta = r.get("metadata") or {}
                if not meta.get("permanent", False):
                    date_str = meta.get("date", "")
                    if date_str:
                        try:
                            lesson_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                            age_weeks = (now - lesson_date).days / 7
                            if age_weeks > 4:
                                r["distance"] = r["distance"] + 0.05 * (age_weeks - 4)
                        except Exception:
                            pass
            raw = sorted(raw, key=lambda x: x["distance"])[:5]
        else:
            # Single-query for all other collections
            q = primary_query
            if col_name == "error_patterns":
                q = f"failure errors bugs {task_type}"
            elif col_name == "reference_material":
                q = f"AADP architecture patterns {task_type} workflow design"
            raw = [r for r in _single_query(col_name, q, n_results=n_results, threshold=threshold)
                   if r["id"] not in seen_ids]

        # Dedup
        deduped = []
        for r in raw:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                deduped.append(r)
        all_results_by_collection[col_name] = deduped

    # --- Compute confidence signal ---
    all_distances = [r["distance"] for results in all_results_by_collection.values() for r in results]
    if all_distances:
        min_dist = min(all_distances)
        if min_dist < 0.8:
            confidence_tier = "high"
            retrieve_confidence = 1.0
            retrieve_recommendation = "retrieve"
        elif min_dist < 1.1:
            confidence_tier = "medium"
            retrieve_confidence = round(1.0 - (min_dist - 0.8) / 0.6, 2)
            retrieve_recommendation = "retrieve"
        else:
            confidence_tier = "low"
            retrieve_confidence = round(max(0.0, 1.0 - (min_dist - 1.1) / 0.4), 2)
            retrieve_recommendation = "reason_with_context"
    else:
        min_dist = None
        confidence_tier = "none"
        retrieve_confidence = 0.0
        retrieve_recommendation = "reason"

    # --- Assemble context block ---
    lesson_ids = [r["id"] for r in all_results_by_collection.get("lessons_learned", [])]
    lesson_contents = [r["content"] for r in all_results_by_collection.get("lessons_learned", [])]
    total = sum(len(v) for v in all_results_by_collection.values())

    # --- Zero-applied wildcard: surface 2 uncirculated lessons per session ---
    # Lessons with times_applied=0 are invisible to semantic search because
    # their topics never recur. Random exposure ensures eventual coverage.
    zero_applied_wildcards = []
    sb_url_za = env.get("SUPABASE_URL", "")
    sb_key_za = env.get("SUPABASE_SERVICE_KEY", "")
    if sb_url_za and sb_key_za:
        try:
            headers_za = {"apikey": sb_key_za, "Authorization": f"Bearer {sb_key_za}"}
            # Fetch up to 50 candidates (>3 days old, never retrieved, with a chromadb_id)
            za_url = (f"{sb_url_za}/rest/v1/lessons_learned"
                      f"?times_applied=eq.0"
                      f"&created_at=lt.{(datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%dT%H:%M:%SZ')}"
                      f"&chromadb_id=not.is.null"
                      f"&select=chromadb_id,content"
                      f"&limit=50")
            req = urllib.request.Request(za_url, headers=headers_za)
            with urllib.request.urlopen(req, timeout=5) as r:
                za_candidates = _json.loads(r.read().decode())
            if za_candidates:
                import random as _random
                # Exclude lessons already surfaced by semantic search (avoid double-counting)
                existing_ids = set(lesson_ids)
                za_candidates = [c for c in za_candidates if c.get("chromadb_id") not in existing_ids]
                sample = _random.sample(za_candidates, min(2, len(za_candidates)))
                zero_applied_wildcards = [
                    {"id": c["chromadb_id"], "content": c["content"]}
                    for c in sample if c.get("chromadb_id")
                ]
                # Wildcards are surfaced for awareness only — not counted as applied.
                # Incrementing on random exposure conflates "surfaced" with "used"
                # and would drain the zero_applied pool without evidence of actual use.
        except Exception:
            pass

    confidence_line = f"*Routing: {routing_applied} | Confidence: {confidence_tier} (min_dist={f'{min_dist:.3f}' if min_dist else 'n/a'}) | Recommendation: {retrieve_recommendation}*"
    header = f"## PRE-LOADED CONTEXT\n*Injected by lesson_injector v3.1 — task_type: {task_type}, id: {task_id}*\n{confidence_line}\n\n"

    sections = []
    for col_name in collections_to_query:
        items = all_results_by_collection.get(col_name, [])
        if not items:
            continue
        label = _V3_SECTION_LABELS.get(col_name, f"### {col_name}")
        trunc = _V3_CONTENT_TRUNC.get(col_name, None)
        s = label + "\n"
        for r in items:
            content = r["content"][:trunc] if trunc else r["content"]
            s += f"**[{r['id']}]** dist:{r['distance']:.2f}\n{content}\n\n"
        sections.append(s)

    # Add zero_applied wildcards as a trailing section (trimmed first if budget tight)
    if zero_applied_wildcards:
        wc_section = "### Uncirculated Lessons (zero_applied — scan for relevance)\n"
        for w in zero_applied_wildcards:
            wc_section += f"**[{w['id']}]**\n{w['content'][:300]}\n\n"
        sections.append(wc_section)

    if not sections:
        sections = ["*No matching context found.*\n\n"]

    # --- Token budget: 2000-token cap, trim from bottom ---
    TOKEN_CAP = 2000
    trimmed = False
    while sections and len((header + "".join(sections) + "---\n")) // 4 > TOKEN_CAP:
        sections.pop()
        trimmed = True

    block = header + "".join(sections)
    if trimmed:
        block += "*[Context trimmed to 2000-token budget — lower-priority sections removed]*\n\n"
    block += "---\n"
    token_estimate = len(block) // 4

    # --- Track lessons_applied ---
    # Only increment for semantic search results (lesson_ids), not wildcards.
    # Content-match RPC (increment_lessons_applied) removed: redundant after B-062
    # chromadb_id backfill; firing both RPCs caused +2 per retrieval instead of +1.
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    if lesson_ids and sb_url and sb_key:
        headers = {"apikey": sb_key, "Authorization": f"Bearer {sb_key}", "Content-Type": "application/json"}
        try:
            req = urllib.request.Request(
                f"{sb_url}/rest/v1/rpc/increment_lessons_applied_by_id",
                data=_json.dumps({"lesson_ids": lesson_ids}).encode(), headers=headers
            )
            urllib.request.urlopen(req, timeout=8).read()
        except Exception:
            pass

    return JSONResponse({
        "task_id":                task_id,
        "task_type":              task_type,
        "description":            description,
        "context_block":          block,
        "lesson_count":           total,
        "lesson_ids":             lesson_ids,
        "lesson_contents":        lesson_contents,
        "expansion_phrases":      expansion_phrases,
        "token_estimate":         token_estimate,
        "trimmed":                trimmed,
        # v3 additions
        "routing_applied":        routing_applied,
        "confidence_tier":        confidence_tier,
        "min_distance":           min_dist,
        "retrieve_confidence":    retrieve_confidence,
        "retrieve_recommendation": retrieve_recommendation,
        "collections_queried":    collections_to_query,
        "queries": {
            "expanded":       expansion_phrases,
            "primary_query":  primary_query,
            "routing":        routing_applied,
        }
    })


_ARXIV_AADP_TOPICS = [
    "agent evaluation framework",
    "LLM memory retrieval",
    "tool use language model",
    "multi-agent coordination",
]

_COMPONENT_TAGS = [
    "lesson_injector", "evaluator", "session_handoff", "agent_builder",
    "scheduler", "memory_architecture", "stats_server", "research_pipeline", "none"
]
_ACTION_TYPES = ["implement", "defer", "already_addressed", "not_applicable", "investigate_further"]


def _score_with_haiku_aadp(candidates, api_key):
    """Score arXiv candidates for AADP design implications.
    Returns list of {score, reason, implication, component_tag, action_type}."""
    if not candidates:
        return []
    items_txt = "\n".join(
        f"{i+1}. {c['title']}\n   Abstract: {c['summary'][:300]}"
        for i, c in enumerate(candidates)
    )
    component_list = ", ".join(_COMPONENT_TAGS)
    action_list = ", ".join(_ACTION_TYPES)
    prompt = (
        "You are evaluating arXiv preprints for an autonomous agent platform called AADP. "
        "AADP runs on a Raspberry Pi 5, builds AI agents with n8n + Supabase + ChromaDB + Claude API. "
        "Its components: lesson_injector (retrieves context before sessions), evaluator (4-pillar Haiku judge), "
        "session_handoff (hot handoff notes between sessions), agent_builder (n8n workflow construction), "
        "scheduler (Sentinel cron + work queue), memory_architecture (ChromaDB collections + embeddings), "
        "stats_server (Python API layer), research_pipeline (arXiv/HN scout + synthesis).\n\n"
        "For each paper, score 1-10 and provide:\n"
        "9-10: Game-changing — AADP should change something based on this\n"
        "7-8: Worth tracking — informs a real design decision\n"
        "5-6: Tangentially useful\n"
        "1-4: Not applicable\n\n"
        f"component_tag: pick exactly one from [{component_list}] — the AADP component most implicated. Use 'none' if no specific component.\n"
        f"action_type: pick exactly one from [{action_list}].\n\n"
        f"Papers:\n{items_txt}\n\n"
        "Respond with JSON array only:\n"
        '[{"score": N, "reason": "one sentence", "implication": "one sentence on what AADP should do", '
        '"component_tag": "<tag>", "action_type": "<type>"}, ...]'
    )
    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = _json.loads(r.read())
        text = resp["content"][0]["text"].strip()
        start = text.find("[")
        end   = text.rfind("]") + 1
        return _json.loads(text[start:end])
    except Exception as e:
        return [{"score": 0, "reason": f"scoring failed: {e}", "implication": ""}] * len(candidates)


@app.post("/run_arxiv_aadp")
def run_arxiv_aadp(payload: dict = {}):
    """ArXiv-to-AADP pipeline. Fetches agent/memory/tool-use preprints, scores for design implications,
    writes to research_findings (ChromaDB) and research_papers (Supabase), sends Telegram digest.
    Idempotent: skips if already ran today unless force=true.
    """
    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Idempotency: check if we already ran today
    if not payload.get("force"):
        try:
            rows = _sb_get(env, f"research_papers?source=eq.arXiv&discovered_at=gte.{today}T00:00:00&source_id=like.*arxiv*&select=id&limit=1")
            # Also check by notes tag
            rows2 = _sb_get(env, f"system_config?key=eq.arxiv_aadp_last_run&select=value")
            if rows2 and rows2[0].get("value") == today:
                return JSONResponse({"status": "already_run", "date": today})
        except Exception:
            pass

    # Fetch arXiv candidates for all 4 topics
    candidates = []
    for topic in _ARXIV_AADP_TOPICS:
        candidates.extend(_fetch_arxiv(topic, max_results=4))

    if not candidates:
        return JSONResponse({"status": "no_candidates", "date": today})

    # Score with design-implications prompt
    scores = _score_with_haiku_aadp(candidates, api_key)

    # Filter ≥7, keep top 4
    scored = []
    for i, c in enumerate(candidates):
        s = scores[i] if i < len(scores) else {"score": 0, "reason": "", "implication": ""}
        if s.get("score", 0) >= 7:
            scored.append({**c, "score": s["score"], "reason": s.get("reason", ""), "implication": s.get("implication", "")})
    scored.sort(key=lambda x: x["score"], reverse=True)
    entries = scored[:4]

    # Write to ChromaDB research_findings
    chroma_ok = 0
    for entry in entries:
        topic_slug = entry.get("topic", "general").replace(" ", "_")[:40]
        doc_id = f"arxiv_aadp_{topic_slug}_{today}_{entry['title'][:30].replace(' ','_')}"
        content = (
            f"{entry.get('title', '')}\n"
            f"Topic: {entry.get('topic', '')}\n"
            f"Source: arXiv\n"
            f"Relevance: {entry.get('score', '')}/10\n"
            f"Why relevant: {entry.get('reason', '')}\n"
            f"AADP design implication: {entry.get('implication', '')}\n"
            f"Abstract: {entry.get('summary', '')}\n"
            f"Link: {entry.get('url', '')}"
        )
        metadata = {
            "source": "arxiv_aadp_pipeline",
            "topic": entry.get("topic", ""),
            "date": today,
            "score": entry.get("score", 0),
            "link": entry.get("url", ""),
        }
        if _chromadb_add("research_findings", doc_id, content, metadata):
            chroma_ok += 1

    # Write to Supabase research_papers
    sb_ok = 0
    for entry in entries:
        try:
            _sb_upsert(env, "research_papers", {
                "title": entry.get("title", "")[:500],
                "abstract": entry.get("summary", "")[:800],
                "source": "arXiv",
                "source_id": entry.get("url", "")[:500],
                "url": entry.get("url", ""),
                "topic_tags": [entry.get("topic", ""), "arxiv_aadp_pipeline"],
                "relevance_score": round(entry.get("score", 0) / 10.0, 2),
                "status": "discovered",
                "discovered_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
                "notes": f"Reason: {entry.get('reason','')} | Design implication: {entry.get('implication','')}",
                "component_tag": entry.get("component_tag", "none") if entry.get("component_tag") in _COMPONENT_TAGS else "none",
                "action_type": entry.get("action_type", "investigate_further") if entry.get("action_type") in _ACTION_TYPES else "investigate_further",
            })
            sb_ok += 1
        except Exception:
            pass

    # Mark as run today
    try:
        _sb_upsert(env, "system_config", {"key": "arxiv_aadp_last_run", "value": today, "updated_at": "now()"})
    except Exception:
        pass

    # Telegram digest
    if entries:
        lines = [f"📚 ArXiv → AADP — {today}\n"]
        for e in entries:
            lines.append(f"[{e['score']}/10] {e['title']}")
            lines.append(f"  ↳ {e.get('implication', e.get('reason', ''))}")
            lines.append(f"  {e.get('url', '')}\n")
        _send_telegram("\n".join(lines), env)

    # Write artifact to agent_artifacts
    try:
        artifact_content = {
            "date": today,
            "candidates_fetched": len(candidates),
            "papers_written": len(entries),
            "papers": [{"title": e["title"], "score": e["score"], "url": e["url"], "implication": e.get("implication", "")} for e in entries],
        }
        top_paper = entries[0]["title"][:80] if entries else "none"
        summary = f"{len(entries)} papers ingested on {today} (top: {top_paper})" if entries else f"No papers met threshold on {today}"
        _sb_upsert(env, "agent_artifacts", {
            "agent_name": "arxiv_aadp_pipeline",
            "artifact_type": "research_papers_supabase",
            "content": artifact_content,
            "summary": summary,
            "confidence": 0.9,
        })
    except Exception:
        pass

    return JSONResponse({
        "status": "complete",
        "date": today,
        "candidates_fetched": len(candidates),
        "entries_written": len(entries),
        "chroma_written": chroma_ok,
        "supabase_written": sb_ok,
    })


@app.post("/run_architecture_review")
def run_architecture_review(payload: dict = {}):
    """Biweekly research-to-architecture review.
    Queries research_papers for recent high-scored arxiv_aadp_pipeline findings,
    groups by component_tag, calls Sonnet to produce structured decision output,
    writes to experimental_outputs, sends Telegram digest, queues work_queue items for implement decisions.
    Idempotent: skips if already ran in the last 12 days unless force=true.
    """
    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Idempotency: skip if ran recently
    if not payload.get("force"):
        try:
            rows = _sb_get(env, "system_config?key=eq.arch_review_last_run&select=value")
            if rows:
                from datetime import date as _date
                last = _date.fromisoformat(rows[0]["value"])
                days_since = (datetime.utcnow().date() - last).days
                if days_since < 12:
                    return JSONResponse({"status": "skipped", "reason": f"ran {days_since}d ago, next run in {12-days_since}d"})
        except Exception:
            pass

    # Fetch recent high-scored papers from arxiv_aadp_pipeline
    window_days = payload.get("window_days", 14)
    cutoff = (datetime.utcnow() - timedelta(days=window_days)).strftime("%Y-%m-%d")
    try:
        rows = _sb_get(env,
            f"research_papers?topic_tags=cs.%7Barxiv_aadp_pipeline%7D"
            f"&relevance_score=gte.0.7"
            f"&discovered_at=gte.{cutoff}T00:00:00"
            f"&action_type=in.(implement,investigate_further,defer)"
            f"&already_addressed_since=is.null"
            f"&select=title,url,abstract,relevance_score,component_tag,action_type,notes,discovered_at"
            f"&order=relevance_score.desc&limit=20"
        )
    except Exception as e:
        rows = []

    if not rows:
        return JSONResponse({"status": "no_papers", "window_days": window_days, "cutoff": cutoff})

    # Read current implementation summary for context
    arch_context = ""
    try:
        arch_rows = _sb_get(env,
            "system_config?key=eq.arch_review_impl_context&select=value"
        )
        if arch_rows:
            arch_context = arch_rows[0].get("value", "")
    except Exception:
        pass

    if not arch_context:
        arch_context = (
            "lesson_injector: queries ChromaDB with Haiku-expanded intent phrases (v2, updated 2026-04-05). "
            "evaluator: 4-pillars Haiku-as-judge scoring 1-5 on behavior_consistency, output_quality, reliability, integration_fit. "
            "session_handoff: hot handoff notes written at session close, read by incoming session via bootstrap. "
            "agent_builder: n8n workflow creation via REST API, credentials from .env, webhookId must match path. "
            "scheduler: systemd timer every 8h, Sentinel runs claude -p with enriched prompt. "
            "memory_architecture: ChromaDB 384-dim embeddings, collections: lessons_learned(122), research_findings(99), error_patterns(15), reference_material(173). "
            "stats_server: FastAPI on port 9100, Python subprocesses for ChromaDB, Supabase REST. "
            "research_pipeline: daily_research_scout (arXiv+HN+Reddit daily), arxiv_aadp_pipeline (Mon/Wed/Fri, design implications), research_synthesis_agent (Sunday)."
        )

    # Group papers by component_tag
    by_component = {}
    for r in rows:
        tag = r.get("component_tag") or "none"
        by_component.setdefault(tag, []).append(r)

    papers_txt = ""
    for tag, papers in by_component.items():
        papers_txt += f"\n## Component: {tag}\n"
        for p in papers:
            score_pct = int(float(p.get("relevance_score", 0)) * 10)
            papers_txt += (
                f"- [{score_pct}/10] {p.get('title','')}\n"
                f"  Notes: {p.get('notes','')[:300]}\n"
                f"  URL: {p.get('url','')}\n"
            )

    review_date = today
    next_review = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d")

    prompt = (
        "You are Claudis, an AI agent developer running on AADP (Autonomous Agent Developer Platform). "
        "You are conducting a structured research-to-architecture review.\n\n"
        "Current AADP component implementations:\n"
        f"{arch_context}\n\n"
        "Recent high-scored arXiv findings grouped by component:\n"
        f"{papers_txt}\n\n"
        "For each paper, produce a structured finding. Be honest: measure the gap where you can, "
        "say 'not measured' where you cannot. Choose decisions from this enum exactly: "
        "implement, defer, already_addressed, not_applicable, investigate_further.\n\n"
        f"Output a JSON object matching this schema exactly:\n"
        "{\n"
        f'  "review_date": "{review_date}",\n'
        f'  "window_days": {window_days},\n'
        f'  "papers_reviewed": {len(rows)},\n'
        '  "findings": [\n'
        '    {\n'
        '      "paper_title": "",\n'
        '      "arxiv_url": "",\n'
        '      "component_tag": "",\n'
        '      "finding": "what the paper proposes",\n'
        '      "current_implementation": "what AADP does today",\n'
        '      "gap_measured": true/false,\n'
        '      "gap_evidence": "specific data if measured, null if not",\n'
        '      "decision": "implement|defer|already_addressed|not_applicable|investigate_further",\n'
        '      "proposed_action": "concrete change if implement, null otherwise",\n'
        '      "defer_reason": "why if defer, null otherwise"\n'
        '    }\n'
        '  ],\n'
        '  "actions_taken": [],\n'
        f'  "next_review_date": "{next_review}"\n'
        "}\n\n"
        "Reply with the JSON object only."
    )

    payload_api = _json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload_api,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = _json.loads(r.read())
        text = resp["content"][0]["text"].strip()
        start = text.find("{")
        end   = text.rfind("}") + 1
        review = _json.loads(text[start:end])
    except Exception as e:
        return JSONResponse({"error": f"Sonnet review failed: {e}"}, status_code=500)

    # Write to experimental_outputs
    try:
        _sb_upsert(env, "experimental_outputs", {
            "agent_name": "claude_code_master",
            "experiment_id": f"arch_review_{today}",
            "output_type": "architecture_review",
            "content": _json.dumps(review),
            "confidence": 0.8,
            "promoted": False,
            "reviewed_by_bill": False,
        })
    except Exception:
        pass

    # Queue work_queue items for implement decisions; backfill already_addressed_since on papers
    queued = 0
    findings = review.get("findings", [])
    for f in findings:
        if f.get("decision") == "implement" and f.get("proposed_action"):
            try:
                _sb_upsert(env, "work_queue", {
                    "task_type": "agent_build",
                    "status": "pending",
                    "priority": 2,
                    "input_data": {
                        "description": f"Architecture review action: {f.get('proposed_action','')}",
                        "source": "arch_review",
                        "paper": f.get("paper_title", ""),
                        "component": f.get("component_tag", ""),
                        "review_date": today,
                    },
                    "created_by": "arch_review_agent",
                })
                queued += 1
            except Exception:
                pass
            # Mark paper addressed so next review window doesn't re-queue it
            if f.get("arxiv_url"):
                try:
                    sb_url_env = env.get("SUPABASE_URL", "")
                    sb_key_env = env.get("SUPABASE_SERVICE_KEY", "")
                    patch = _json.dumps({
                        "already_addressed_since": today,
                        "addressed_by": f"arch_review_implement: {f.get('proposed_action','')[:300]}",
                        "action_type": "already_addressed",
                    }).encode()
                    req = urllib.request.Request(
                        f"{sb_url_env}/rest/v1/research_papers?url=eq.{urllib.parse.quote(f['arxiv_url'])}",
                        data=patch,
                        headers={
                            "apikey": sb_key_env,
                            "Authorization": f"Bearer {sb_key_env}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal",
                        },
                        method="PATCH"
                    )
                    urllib.request.urlopen(req, timeout=8).read()
                except Exception:
                    pass

        if f.get("decision") == "already_addressed" and f.get("arxiv_url"):
            # Mark the paper so future review cycles know when it was closed
            try:
                sb_url_env = env.get("SUPABASE_URL", "")
                sb_key_env = env.get("SUPABASE_SERVICE_KEY", "")
                addressed_note = f.get("proposed_action") or f.get("finding", "")[:200]
                patch = _json.dumps({
                    "already_addressed_since": today,
                    "addressed_by": addressed_note[:500],
                    "action_type": "already_addressed",
                }).encode()
                req = urllib.request.Request(
                    f"{sb_url_env}/rest/v1/research_papers?url=eq.{urllib.parse.quote(f['arxiv_url'])}",
                    data=patch,
                    headers={
                        "apikey": sb_key_env,
                        "Authorization": f"Bearer {sb_key_env}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    },
                    method="PATCH"
                )
                urllib.request.urlopen(req, timeout=8).read()
            except Exception:
                pass

    # Update last run
    try:
        _sb_upsert(env, "system_config", {"key": "arch_review_last_run", "value": today, "updated_at": "now()"})
    except Exception:
        pass

    # Telegram digest
    implement_count = sum(1 for f in findings if f.get("decision") == "implement")
    investigate_count = sum(1 for f in findings if f.get("decision") == "investigate_further")
    defer_count = sum(1 for f in findings if f.get("decision") == "defer")
    addressed_count = sum(1 for f in findings if f.get("decision") == "already_addressed")

    lines = [f"🔬 Architecture Review — {today}\n{len(rows)} papers | {len(findings)} findings\n"]
    lines.append(f"implement: {implement_count} | investigate: {investigate_count} | defer: {defer_count} | addressed: {addressed_count}")
    if implement_count > 0:
        lines.append("\nImplement:")
        for f in findings:
            if f.get("decision") == "implement":
                lines.append(f"  • [{f.get('component_tag','')}] {f.get('proposed_action','')[:120]}")
    if queued:
        lines.append(f"\n{queued} work_queue item(s) created.")
    _send_telegram("\n".join(lines), env)

    return JSONResponse({
        "status": "complete",
        "date": today,
        "papers_reviewed": len(rows),
        "findings": len(findings),
        "implement": implement_count,
        "investigate": investigate_count,
        "queued": queued,
        "next_review": next_review,
    })


# =============================================================================
# RESEARCH SYNTHESIS AGENT
# Weekly synthesis of research_findings from ChromaDB.
# Queries last 21 days, compares to prior synthesis, calls Sonnet for
# topic trajectory analysis. Modes: accumulation (runs 1-3) / synthesis (4+).
# Built: 2026-04-14
# =============================================================================

@app.post("/run_research_synthesis")
def run_research_synthesis(payload: dict = {}):
    """Weekly synthesis of research_findings from ChromaDB.
    Body: {force: bool (default false), days_back: int (default 21)}
    Returns: {status, experiment_id, mode, entry_count, synthesis_keys}
    """
    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    days_back = int(payload.get("days_back", 21))

    # Idempotency: skip if ran in last 5 days unless force=true
    if not payload.get("force"):
        try:
            rows = _sb_get(env,
                "experimental_outputs"
                "?agent_name=eq.research_synthesis_agent"
                "&output_type=eq.research_synthesis"
                "&order=created_at.desc&limit=1&select=created_at"
            )
            if rows:
                import datetime as _dt
                last_str = rows[0]["created_at"].replace("Z", "+00:00")
                last_dt = _dt.datetime.fromisoformat(last_str)
                now_utc = _dt.datetime.now(tz=_dt.timezone.utc)
                days_since = (now_utc - last_dt).days
                if days_since < 5:
                    return JSONResponse({
                        "status": "skipped",
                        "reason": f"ran {days_since}d ago — use force=true to override"
                    })
        except Exception:
            pass

    # Step 1: Fetch research window from ChromaDB via subprocess
    script = """
import chromadb, json, sys
from datetime import datetime, timedelta
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
results = col.get(include=["documents", "metadatas"])
ids   = results.get('ids', [])
docs  = results.get('documents', [])
metas = results.get('metadatas', [])
start = args['start_date']
entries = [
    {"id": ids[i], "content": docs[i], "metadata": metas[i]}
    for i in range(len(ids))
    if (metas[i] or {}).get("date", "") >= start
]
entries.sort(key=lambda x: x["metadata"].get("date", ""), reverse=True)
print(json.dumps(entries))
"""
    from datetime import timedelta as _td
    start_date = (datetime.utcnow() - _td(days=days_back)).strftime("%Y-%m-%d")
    proc = subprocess.run(
        ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
         _json.dumps({"collection": "research_findings", "start_date": start_date})],
        capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0:
        return JSONResponse({"error": f"ChromaDB query failed: {proc.stderr[:300]}"}, status_code=500)
    try:
        entries = _json.loads(proc.stdout)
    except Exception as e:
        return JSONResponse({"error": f"ChromaDB parse failed: {e}"}, status_code=500)

    if not entries:
        return JSONResponse({"status": "no_entries", "days_back": days_back, "start_date": start_date})

    # Step 2: Get prior synthesis for comparison mode
    prior_synthesis = None
    prior_date = None
    run_count = 0
    try:
        rows = _sb_get(env,
            "experimental_outputs"
            "?agent_name=eq.research_synthesis_agent"
            "&output_type=eq.research_synthesis"
            "&order=created_at.desc&limit=1&select=content,created_at"
        )
        if rows:
            prior_synthesis = rows[0]["content"]
            prior_date = rows[0]["created_at"][:10]
    except Exception:
        pass
    try:
        count_rows = _sb_get(env,
            "experimental_outputs"
            "?agent_name=eq.research_synthesis_agent"
            "&output_type=eq.research_synthesis"
            "&select=id"
        )
        run_count = len(count_rows)
    except Exception:
        pass

    mode = "accumulation" if run_count < 3 else "synthesis"

    # Step 3: Condense entries for Sonnet (cap at 80, truncate content)
    capped = entries[:80]
    entries_txt = ""
    for e in capped:
        src = (e.get("metadata") or {}).get("source", "?")
        date = (e.get("metadata") or {}).get("date", "?")
        content_short = (e.get("content") or "")[:250].replace("\n", " ")
        entries_txt += f"[{date}][{src}] {content_short}\n"

    # Step 4: Build Sonnet prompt
    schema_synthesis = (
        '{\n'
        '  "mode": "synthesis",\n'
        f'  "period": "{today}",\n'
        f'  "prior_period": "{prior_date}",\n'
        f'  "entry_count": {len(entries)},\n'
        '  "topic_trajectories": [{"topic": "", "trajectory": ""}],\n'
        '  "top_signals": ["signal1", "signal2", "signal3"],\n'
        '  "shifts": ["what changed since prior synthesis"],\n'
        '  "coverage_gaps": ["gap1", "gap2"],\n'
        '  "narrative": "2-3 sentence synthesis of what the past 21 days means for AADP"\n'
        '}'
    )
    schema_accum = (
        '{\n'
        '  "mode": "accumulation",\n'
        f'  "period": "{today}",\n'
        f'  "entry_count": {len(entries)},\n'
        '  "topic_trajectories": [{"topic": "", "trajectory": ""}],\n'
        '  "top_signals": ["signal1", "signal2", "signal3"],\n'
        '  "coverage_gaps": ["gap1", "gap2"],\n'
        '  "narrative": "2-3 sentence synthesis of what the past 21 days means for AADP"\n'
        '}'
    )

    if mode == "synthesis" and prior_synthesis and isinstance(prior_synthesis, dict):
        prior_signals = prior_synthesis.get("top_signals", [])
        prior_traj = prior_synthesis.get("topic_trajectories", [])
        prior_narrative = prior_synthesis.get("narrative", "")[:300]
        prior_block = (
            f"PRIOR SYNTHESIS ({prior_date}):\n"
            f"Narrative: {prior_narrative}\n"
            f"Top signals: {prior_signals}\n"
            f"Trajectories: {[t.get('topic','') + ': ' + t.get('trajectory','')[:100] for t in prior_traj[:5]]}\n"
        )
        prompt = (
            "You are Claudis, an AI agent developer on AADP (Autonomous Agent Developer Platform).\n"
            "Synthesize the past 21 days of AI research findings to identify what is changing.\n\n"
            f"{prior_block}\n"
            f"CURRENT PERIOD ({today}): {len(entries)} entries from {start_date} to {today}.\n\n"
            "ENTRIES (most recent first, 250 chars each):\n"
            f"{entries_txt}\n"
            "Compare to the prior synthesis. Identify topic trajectories, top signals, shifts, and coverage gaps.\n"
            f"Output only this JSON object:\n{schema_synthesis}\n"
            "Reply with the JSON object only."
        )
    else:
        prompt = (
            "You are Claudis, an AI agent developer on AADP (Autonomous Agent Developer Platform).\n"
            "Build a baseline synthesis of the past 21 days of AI research findings.\n\n"
            f"CURRENT PERIOD ({today}): {len(entries)} entries from {start_date} to {today}.\n\n"
            "ENTRIES (most recent first, 250 chars each):\n"
            f"{entries_txt}\n"
            "Identify topic trajectories, top signals, and coverage gaps.\n"
            f"Output only this JSON object:\n{schema_accum}\n"
            "Reply with the JSON object only."
        )

    # Step 5: Call Sonnet
    api_payload = _json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=api_payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            resp = _json.loads(r.read())
        text = resp["content"][0]["text"].strip()
        start_brace = text.find("{")
        end_brace = text.rfind("}") + 1
        synthesis = _json.loads(text[start_brace:end_brace])
    except Exception as e:
        return JSONResponse({"error": f"Sonnet call failed: {e}"}, status_code=500)

    # Step 6: Write to experimental_outputs
    experiment_id = f"synthesis_{today}"
    try:
        _sb_upsert(env, "experimental_outputs", {
            "agent_name": "research_synthesis_agent",
            "experiment_id": experiment_id,
            "output_type": "research_synthesis",
            "content": synthesis,
            "confidence": 0.85,
            "promoted": False,
            "reviewed_by_bill": False,
        })
    except Exception as e:
        return JSONResponse({
            "error": f"Supabase write failed: {e}",
            "synthesis": synthesis
        }, status_code=500)

    # Step 7: Telegram digest (750 char max)
    top_signals = synthesis.get("top_signals", [])
    narrative = synthesis.get("narrative", "")[:280]
    trajectories = synthesis.get("topic_trajectories", [])[:3]
    traj_lines = "\n".join(
        f"• {t.get('topic','')[:30]}: {t.get('trajectory','')[:70]}"
        for t in trajectories
    )
    signals_lines = "\n".join(f"• {str(s)[:100]}" for s in top_signals[:3])
    msg = (
        f"🔬 Research Synthesis — {today} ({mode})\n\n"
        f"{narrative}\n\n"
        f"Top signals:\n{signals_lines}\n\n"
        f"Trajectories:\n{traj_lines}"
    )
    if len(msg) > 750:
        msg = msg[:747] + "..."
    _send_telegram(msg, env)

    return JSONResponse({
        "status": "ok",
        "experiment_id": experiment_id,
        "mode": mode,
        "entry_count": len(entries),
        "synthesis_keys": list(synthesis.keys()),
    })


# =============================================================================
# BEHAVIORAL TEST RUNNER
# Triggers an agent via webhook, observes state changes, runs assertions.
# Design: /docs/evaluator_behavioral_test_design_2026-04-06.md
# =============================================================================

def _bt_sb_get(url, sb_key, timeout=10):
    """GET from Supabase, return parsed JSON or []."""
    try:
        req = urllib.request.Request(url, headers={
            "apikey": sb_key, "Authorization": f"Bearer {sb_key}"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return _json.loads(r.read().decode())
    except Exception:
        return []


def _bt_fetch_agent(agent_name, sb_url, sb_key):
    """Fetch a single agent_registry row by agent_name."""
    from urllib.parse import quote
    rows = _bt_sb_get(
        f"{sb_url}/rest/v1/agent_registry?agent_name=eq.{quote(agent_name)}&limit=1",
        sb_key
    )
    return rows[0] if rows else None


def _bt_fetch_test_config(agent_name, sb_url, sb_key):
    """Fetch behavioral_test config from agent_config.metadata for this agent.
    Returns dict with keys: webhook_url, webhook_method, cooldown_hours, assertions.
    """
    from urllib.parse import quote
    rows = _bt_sb_get(
        f"{sb_url}/rest/v1/agent_config?agent_name=eq.{quote(agent_name)}&limit=1",
        sb_key
    )
    if not rows:
        return {}
    meta = rows[0].get("metadata") or {}
    return meta.get("behavioral_test", {})


def _bt_get_last_execution(workflow_id, n8n_key):
    """Return most recent n8n execution dict for workflow_id, or None."""
    if not workflow_id or not n8n_key:
        return None
    try:
        url = f"http://localhost:5678/api/v1/executions?workflowId={workflow_id}&limit=1"
        req = urllib.request.Request(url, headers={"X-N8N-API-KEY": n8n_key})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read().decode())
        execs = data.get("data", [])
        return execs[0] if execs else None
    except Exception:
        return None


def _bt_snapshot(agent_name, workflow_id, assertions_spec, sb_url, sb_key, n8n_key):
    """Record pre/post observable state for assertion evaluation."""
    from urllib.parse import quote

    # Audit log count for this agent
    audit_rows = _bt_sb_get(
        f"{sb_url}/rest/v1/audit_log?actor=eq.{quote(agent_name)}&select=id",
        sb_key
    )
    audit_count = len(audit_rows) if isinstance(audit_rows, list) else 0

    # Latest experimental_output timestamps per output_type (for output_produced checks)
    output_type_filter = next(
        (a.get("expected") for a in assertions_spec if a.get("type") == "output_type_match"),
        None
    )
    latest_output_ts = None
    if output_type_filter:
        from urllib.parse import quote as q
        rows = _bt_sb_get(
            f"{sb_url}/rest/v1/experimental_outputs"
            f"?output_type=eq.{q(output_type_filter)}"
            f"&order=created_at.desc&limit=1&select=created_at",
            sb_key
        )
        if rows and isinstance(rows, list) and rows[0].get("created_at"):
            latest_output_ts = rows[0]["created_at"]

    # Most recent execution
    last_exec = _bt_get_last_execution(workflow_id, n8n_key)
    last_exec_id = last_exec.get("id") if last_exec else None

    return {
        "audit_count": audit_count,
        "latest_output_ts": latest_output_ts,
        "output_type_tracked": output_type_filter,
        "last_exec_id": last_exec_id,
    }


def _bt_parse_ts(ts_str):
    """Parse ISO timestamp string to UTC datetime, tolerating Z or +00:00 suffix."""
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _bt_poll_execution(workflow_id, trigger_ts, timeout_s, n8n_key):
    """Poll n8n execution API until a new finished execution appears or timeout.
    Returns execution dict or None on timeout.
    trigger_ts is ISO string — we look for executions with startedAt >= trigger_ts
    using datetime comparison (not string comparison, which fails on milliseconds).
    """
    if not workflow_id or not n8n_key:
        return None
    import time
    trigger_dt = _bt_parse_ts(trigger_ts)
    if trigger_dt is None:
        return None
    deadline = time.time() + timeout_s
    poll_interval = 5
    while time.time() < deadline:
        try:
            url = f"http://localhost:5678/api/v1/executions?workflowId={workflow_id}&limit=5"
            req = urllib.request.Request(url, headers={"X-N8N-API-KEY": n8n_key})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = _json.loads(r.read().decode())
            for exec_ in data.get("data", []):
                started_dt = _bt_parse_ts(exec_.get("startedAt", ""))
                terminal = exec_.get("finished") or exec_.get("status") in ("success", "error", "crashed")
                if started_dt and started_dt >= trigger_dt and terminal:
                    return exec_
        except Exception:
            pass
        time.sleep(poll_interval)
    return None


def _bt_run_assertions(assertions_spec, pre, post, execution, duration_s, trigger_ts):
    """Evaluate each assertion against pre/post state and execution data.
    Returns list of assertion result dicts.
    """
    results = []
    for spec in assertions_spec:
        atype = spec.get("type", "")
        name = spec.get("name", atype)

        if atype == "execution_succeeded":
            if execution is None:
                passed = False
                actual = "no_execution_found"
                notes = "No n8n execution found after trigger — timeout or workflow not reachable."
            else:
                actual = execution.get("status", "unknown")
                passed = actual == "success"
                notes = "" if passed else f"execution status={actual}"
            results.append({"name": name, "type": atype, "expected": "success",
                            "actual": actual, "passed": passed, "notes": notes})

        elif atype == "output_produced":
            output_type = pre.get("output_type_tracked") or spec.get("expected_type")
            pre_ts = pre.get("latest_output_ts")
            post_ts = post.get("latest_output_ts")
            if output_type is None:
                passed = None
                notes = "No output_type_match assertion configured — cannot determine expected output_type."
            elif post_ts is None:
                passed = False
                notes = f"No output of type '{output_type}' found after execution."
            elif pre_ts is None or post_ts > pre_ts:
                passed = True
                notes = f"New {output_type} output appeared after trigger."
            else:
                passed = False
                notes = f"Latest {output_type} output unchanged (pre={pre_ts}, post={post_ts})."
            results.append({"name": name, "type": atype,
                            "expected": f"new row with type={output_type}",
                            "actual": post_ts, "passed": passed, "notes": notes})

        elif atype == "audit_written":
            pre_c = pre.get("audit_count", 0)
            post_c = post.get("audit_count", 0)
            passed = post_c > pre_c
            results.append({"name": name, "type": atype,
                            "expected": f">{pre_c}", "actual": post_c,
                            "passed": passed,
                            "notes": "" if passed else f"audit_count unchanged at {pre_c}"})

        elif atype == "output_type_match":
            expected = spec.get("expected", "")
            post_ts = post.get("latest_output_ts")
            pre_ts = pre.get("latest_output_ts")
            tracked = post.get("output_type_tracked") or pre.get("output_type_tracked")
            if post_ts and (pre_ts is None or post_ts > pre_ts):
                passed = tracked == expected
                actual = tracked
                notes = "" if passed else f"tracked type='{tracked}' != expected='{expected}'"
            else:
                passed = False
                actual = "no_new_output"
                notes = f"No new output of type '{expected}' found."
            results.append({"name": name, "type": atype, "expected": expected,
                            "actual": actual, "passed": passed, "notes": notes})

        elif atype == "execution_duration":
            max_s = spec.get("max_seconds", 120)
            # Prefer execution's own timestamps over wall-clock duration
            actual_s = duration_s
            if execution and execution.get("startedAt") and execution.get("stoppedAt"):
                start_dt = _bt_parse_ts(execution["startedAt"])
                stop_dt  = _bt_parse_ts(execution["stoppedAt"])
                if start_dt and stop_dt:
                    actual_s = round((stop_dt - start_dt).total_seconds(), 1)
            passed = actual_s <= max_s
            results.append({"name": name, "type": atype,
                            "expected": f"<={max_s}s", "actual": f"{actual_s:.1f}s",
                            "passed": passed,
                            "notes": "" if passed else f"{actual_s:.1f}s exceeded {max_s}s limit"})

        else:
            results.append({"name": name, "type": atype, "expected": "?",
                            "actual": "?", "passed": None,
                            "notes": f"Unknown assertion type: {atype}"})

    return results


@app.post("/run_behavioral_test")
def run_behavioral_test(payload: dict = {}):
    """Behavioral test runner. Triggers an agent via webhook, observes state
    changes, runs configured assertions, writes result to experimental_outputs.
    Input: {agent_name, timeout_seconds?}
    """
    agent_name = payload.get("agent_name", "")
    timeout_s = int(payload.get("timeout_seconds", 120))

    if not agent_name:
        return JSONResponse({"error": "agent_name required"}, status_code=400)

    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    n8n_key = env.get("N8N_API_KEY", "")

    # 1. Load agent registry entry
    agent = _bt_fetch_agent(agent_name, sb_url, sb_key)
    if not agent:
        return JSONResponse({"error": f"agent not found: {agent_name}"}, status_code=404)
    workflow_id = agent.get("workflow_id")

    # 2. Load behavioral test config
    test_config = _bt_fetch_test_config(agent_name, sb_url, sb_key)
    webhook_url   = test_config.get("webhook_url", "")
    webhook_method = test_config.get("webhook_method", "GET").upper()
    cooldown_hours = test_config.get("cooldown_hours")
    assertions_spec = test_config.get("assertions", [{"type": "execution_succeeded"}])

    if not webhook_url:
        return JSONResponse({"error": f"no webhook_url in behavioral_test config for {agent_name}"},
                            status_code=400)

    # 3. Cooldown check
    if cooldown_hours:
        last_exec = _bt_get_last_execution(workflow_id, n8n_key)
        if last_exec and last_exec.get("startedAt"):
            try:
                last_dt = datetime.fromisoformat(last_exec["startedAt"].replace("Z", "+00:00"))
                age_h = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                if age_h < cooldown_hours:
                    return JSONResponse({
                        "agent_name": agent_name,
                        "test_result": "test_skipped",
                        "reason": f"cooldown active — last run {age_h:.1f}h ago (cooldown={cooldown_hours}h)",
                        "test_passed": None,
                    })
            except Exception:
                pass

    # 4. Pre-state snapshot
    trigger_time = datetime.now(timezone.utc)
    trigger_ts = trigger_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    pre_state = _bt_snapshot(agent_name, workflow_id, assertions_spec, sb_url, sb_key, n8n_key)

    # 5. Trigger agent
    trigger_error = None
    try:
        req = urllib.request.Request(webhook_url)
        if webhook_method == "POST":
            req.method = "POST"
            req.add_header("Content-Type", "application/json")
            req.data = b"{}"
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        return JSONResponse({
            "agent_name": agent_name,
            "test_result": "trigger_failed",
            "error": str(e)[:200],
            "test_passed": False,
        })

    # 6. Poll for execution completion
    execution = _bt_poll_execution(workflow_id, trigger_ts, timeout_s, n8n_key)
    completed_time = datetime.now(timezone.utc)
    duration_s = round((completed_time - trigger_time).total_seconds(), 1)

    # 7. Post-state snapshot
    post_state = _bt_snapshot(agent_name, workflow_id, assertions_spec, sb_url, sb_key, n8n_key)

    # 8. Run assertions
    assertion_results = _bt_run_assertions(
        assertions_spec, pre_state, post_state, execution, duration_s, trigger_ts
    )
    n_passed  = sum(1 for a in assertion_results if a["passed"] is True)
    n_failed  = sum(1 for a in assertion_results if a["passed"] is False)
    n_unknown = sum(1 for a in assertion_results if a["passed"] is None)
    test_passed = (n_failed == 0 and n_passed > 0)

    failure_summary = None
    if n_failed:
        failure_summary = "; ".join(
            f"{a['name']}: {a['notes']}" for a in assertion_results if a["passed"] is False
        )

    record = {
        "agent_name":       agent_name,
        "triggered_at":     trigger_ts,
        "completed_at":     completed_time.isoformat(),
        "duration_seconds": duration_s,
        "execution_id":     execution.get("id") if execution else None,
        "execution_status": (execution.get("status", "unknown") if execution
                             else ("timeout" if duration_s >= timeout_s else "unknown")),
        "pre_state":        pre_state,
        "post_state":       post_state,
        "assertions":       assertion_results,
        "assertions_passed": n_passed,
        "assertions_failed": n_failed,
        "assertions_unknown": n_unknown,
        "test_passed":      test_passed,
        "failure_summary":  failure_summary,
    }

    # 9. Write to experimental_outputs
    today = trigger_time.strftime("%Y-%m-%d")
    exp_record = {
        "agent_name":     agent_name,
        "experiment_id":  f"behavioral_test_{agent_name}_{today}",
        "output_type":    "behavioral_test",
        "content":        record,
        "confidence":     1.0 if test_passed else 0.0,
        "promoted":       False,
        "reviewed_by_bill": False,
    }
    try:
        sb_headers = {
            "apikey": sb_key, "Authorization": f"Bearer {sb_key}",
            "Content-Type": "application/json", "Prefer": "return=minimal"
        }
        req = urllib.request.Request(
            f"{sb_url}/rest/v1/experimental_outputs",
            data=_json.dumps(exp_record).encode(),
            headers=sb_headers,
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10).read()
    except Exception:
        pass  # write failure is non-fatal — result is still returned

    return JSONResponse(record)


@app.post("/score_reddit_resources")
def score_reddit_resources(payload: dict = {}):
    """Batch-score Reddit posts for Capability Amplifier interest relevance using Haiku.
    Input: { posts: [{i, url, title, source_name, thread_id}], interests: "...", thread_id: "..." }
    Output: { scores: [{i, score, assessment}], total: N }
    """
    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not in .env"}, status_code=500)

    posts = payload.get("posts", [])
    interests = payload.get("interests", "")
    if not posts:
        return JSONResponse({"scores": [], "total": 0})

    posts_for_prompt = [
        {"i": p["i"], "title": p["title"], "src": p.get("source_name", ""), "desc": p.get("selftext", "")[:150]}
        for p in posts
    ]

    prompt = (
        f"You are a relevance scout for a learning-focused research system.\n\n"
        f"ACTIVE INTERESTS:\n{interests}\n\n"
        f"Score each resource 1-5 for relevance to the active interests above.\n"
        f"5: Directly matches — practical AI tool, workflow, or new release for Blender/UE5\n"
        f"4: Clearly relevant to AI-assisted game dev interests\n"
        f"3: Tangentially relevant — some connection to interests\n"
        f"2: Weak connection\n"
        f"1: Not relevant at all\n\n"
        f"RESOURCES TO SCORE:\n{_json.dumps(posts_for_prompt)}\n\n"
        f"Respond ONLY with a compact JSON array (no markdown, no extra text):\n"
        f'[{{"i":0,"score":N,"assessment":"one-line description"}},...]\n'
        f"Score every resource. Array length must equal {len(posts)}."
    )

    req_payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=req_payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST"
    )
    try:
        resp_raw = urllib.request.urlopen(req, timeout=90).read()
        resp_data = _json.loads(resp_raw)
        haiku_text = (resp_data.get("content") or [{}])[0].get("text", "")
    except Exception as e:
        return JSONResponse({"error": f"Haiku call failed: {e}"}, status_code=500)

    scores = []
    try:
        import re
        match = re.search(r'\[[\s\S]*\]', haiku_text)
        if match:
            scores = _json.loads(match.group(0))
    except Exception:
        return JSONResponse({"error": "JSON parse failed", "raw": haiku_text[:500]}, status_code=500)

    return JSONResponse({"scores": scores, "total": len(scores)})


@app.post("/fetch_youtube_videos")
def fetch_youtube_videos(payload: dict = {}):
    """Fetch YouTube videos for fixed game-dev AI queries.
    Input: { existing_urls: ["https://..."] }
    Output: { videos: [{i, title, url, source_name, selftext, duration}], total: N }
    """
    env = _read_env_simple()
    yt_key = env.get("YOUTUBE_API_KEY", "")
    if not yt_key:
        return JSONResponse({"error": "YOUTUBE_API_KEY not in .env"}, status_code=500)

    existing_urls = set(payload.get("existing_urls", []))

    queries = [
        "AI Blender workflow",
        "AI generated 3D models UE5",
        "Meshy Blender Unreal",
        "AI game dev tools 2026",
    ]

    import urllib.parse as _urlparse

    seen_ids = set()
    videos = []

    for query in queries:
        params = _urlparse.urlencode({
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 10,
            "order": "relevance",
            "key": yt_key,
        })
        req = urllib.request.Request(
            f"https://www.googleapis.com/youtube/v3/search?{params}",
            headers={"User-Agent": "AADP-Scout/1.0"},
        )
        try:
            resp = _json.loads(urllib.request.urlopen(req, timeout=15).read())
        except Exception as e:
            continue

        for item in resp.get("items", []):
            vid_id = (item.get("id") or {}).get("videoId", "")
            if not vid_id or vid_id in seen_ids:
                continue
            url = f"https://www.youtube.com/watch?v={vid_id}"
            if url in existing_urls:
                continue
            seen_ids.add(vid_id)
            snippet = item.get("snippet", {})
            videos.append({
                "i": len(videos),
                "title": snippet.get("title", ""),
                "url": url,
                "source_name": "youtube",
                "selftext": snippet.get("description", "")[:150],
                "duration": "",
                "channel": snippet.get("channelTitle", ""),
            })

    return JSONResponse({"videos": videos, "total": len(videos)})


def _parse_processed_md(content: str, filename: str) -> dict:
    """Parse a processed/ markdown file into structured fields."""
    import re
    result = {"filename": filename}

    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if not title_match:
        return {}
    result["title"] = title_match.group(1).strip()

    source_match = re.search(r'^Source:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
    result["url"] = source_match.group(1).strip() if source_match else None

    thread_match = re.search(r'^Thread:\s*(.+)$', content, re.MULTILINE | re.IGNORECASE)
    result["thread"] = thread_match.group(1).strip() if thread_match else None

    def extract_section(heading):
        pattern = rf'^##\s+{re.escape(heading)}\s*\n([\s\S]*?)(?=\n##\s|\Z)'
        m = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    result["summary"] = extract_section("Summary") or None
    result["key_takeaways"] = extract_section("Key Takeaways") or None
    result["new_questions"] = extract_section("New Questions") or None
    return result


def _match_thread(thread_ref: str, threads: list) -> str:
    """Match a thread reference string to an inquiry_threads.id."""
    if not thread_ref or not threads:
        return None
    ref = thread_ref.lower().strip()
    for t in threads:
        if t["domain_name"].lower() == ref:
            return t["id"]
    for t in threads:
        if ref in t["domain_name"].lower() or t["domain_name"].lower() in ref:
            return t["id"]
    for t in threads:
        if ref in t["description"].lower():
            return t["id"]
    if len(threads) == 1:
        return threads[0]["id"]
    return None


@app.post("/run_processed_content_agent")
def run_processed_content_agent(payload: dict = {}):
    """
    Checks processed/ in claudis repo for new markdown files, parses them,
    and upserts to resources table with status='processed'.
    Returns new_questions list for Telegram notification.
    """
    env = _read_env_simple()
    github_token = env.get("GITHUB_TOKEN", "")

    # 1. Fetch GitHub directory listing for processed/
    gh_url = "https://api.github.com/repos/thompsmanlearn/claudis/contents/processed"
    req = urllib.request.Request(gh_url, headers={
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "AADP-Claudis/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            gh_files = _json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return JSONResponse({"processed": 0, "new_questions": [], "errors": [],
                                 "message": "processed/ directory not found or empty"})
        return JSONResponse({"error": f"GitHub listing failed: {e}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": f"GitHub listing failed: {e}"}, status_code=500)

    md_files = [f for f in gh_files if isinstance(f, dict) and f.get("name", "").endswith(".md")]
    if not md_files:
        return JSONResponse({"processed": 0, "new_questions": [], "errors": [],
                             "message": "No markdown files in processed/"})

    # 2. Fetch existing processed resources to deduplicate by filename and URL
    try:
        existing = _sb_get(env, "resources?status=eq.processed&select=url,source_name")
    except Exception as e:
        return JSONResponse({"error": f"Supabase fetch failed: {e}"}, status_code=500)

    existing_filenames = {r["source_name"] for r in existing if r.get("source_name")}
    existing_urls = {r["url"] for r in existing if r.get("url")}

    new_files = [f for f in md_files if f["name"] not in existing_filenames]
    if not new_files:
        return JSONResponse({"processed": 0, "new_questions": [], "errors": [],
                             "message": "All files already processed"})

    # 3. Fetch active inquiry threads for matching
    try:
        threads = _sb_get(env, "inquiry_threads?status=eq.active&select=id,domain_name,description")
    except Exception as e:
        return JSONResponse({"error": f"Failed to fetch threads: {e}"}, status_code=500)

    # 4. Process each new file
    processed_count = 0
    all_new_questions = []
    errors = []

    for file_meta in new_files:
        try:
            file_req = urllib.request.Request(file_meta["download_url"], headers={
                "Authorization": f"token {github_token}",
                "User-Agent": "AADP-Claudis/1.0",
            })
            with urllib.request.urlopen(file_req, timeout=15) as r:
                content = r.read().decode("utf-8")

            parsed = _parse_processed_md(content, file_meta["name"])
            if not parsed.get("title"):
                errors.append(f"Parse failed (no title): {file_meta['name']}")
                continue

            if parsed.get("url") and parsed["url"] in existing_urls:
                continue  # URL-based dedup for manually inserted resources

            thread_id = _match_thread(parsed.get("thread"), threads)
            if not thread_id:
                errors.append(f"No thread match for {file_meta['name']} (ref: {parsed.get('thread', 'none')})")
                continue

            record = {
                "thread_id": thread_id,
                "url": parsed.get("url"),
                "title": parsed["title"],
                "source_name": file_meta["name"],
                "status": "processed",
                "summary": parsed.get("summary"),
                "key_takeaways": parsed.get("key_takeaways"),
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }
            _sb_upsert(env, "resources", record)
            processed_count += 1

            if parsed.get("new_questions"):
                all_new_questions.append({
                    "file": file_meta["name"],
                    "title": parsed["title"],
                    "questions": parsed["new_questions"],
                })

        except Exception as e:
            errors.append(f"{file_meta['name']}: {e}")

    return JSONResponse({
        "processed": processed_count,
        "new_questions": all_new_questions,
        "errors": errors,
    })


@app.api_route("/trigger_lean", methods=["GET", "POST"])
def trigger_lean():
    """Spawn a non-interactive lean Claude Code session via lean_runner.sh.
    Checks /tmp/oslean.lock — rejects if a session is already running.
    Returns immediately; lean_runner.sh reports completion via Telegram.
    """
    lock_file = "/tmp/oslean.lock"
    stale_secs = 7200

    if os.path.exists(lock_file):
        age = int(datetime.now(timezone.utc).timestamp()) - int(os.path.getmtime(lock_file))
        if age < stale_secs:
            mins = age // 60
            secs = age % 60
            return JSONResponse({
                "status": "blocked",
                "message": f"\u26a0\ufe0f Session already in progress ({mins}m {secs}s elapsed). Try again when it's done."
            })
        # Stale lock — kill orphan and remove
        subprocess.run(
            ["pkill", "-f", "claude.*dangerously-skip-permissions"],
            capture_output=True
        )
        try:
            os.remove(lock_file)
        except FileNotFoundError:
            pass

    runner = "/home/thompsman/aadp/sentinel/lean_runner.sh"
    log_dir = "/home/thompsman/aadp/logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"lean_spawn_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    with open(log_path, "w") as lf:
        subprocess.Popen(
            ["/bin/bash", runner],
            stdout=lf, stderr=lf,
            start_new_session=True
        )

    return JSONResponse({
        "status": "started",
        "message": "\u2699\ufe0f Session starting \u2014 running directive from DIRECTIVES.md."
    })


@app.post("/scout_youtube")
def scout_youtube(payload: dict = {}):
    """Search YouTube for AI game dev content, score with Haiku, return qualified results.
    Input: { interests: "...", thread_id: "...", existing_urls: [...] }
    Output: { results: [{url, title, source_name, thread_id, score, assessment, channel}], total: N, skipped?: "no_key" }
    """
    import re as _re
    env = _read_env_simple()
    yt_key = env.get("YOUTUBE_API_KEY", "")
    anthropic_key = env.get("ANTHROPIC_API_KEY", "")

    if not yt_key:
        return JSONResponse({"results": [], "total": 0, "skipped": "no_key"})

    interests = payload.get("interests", "")
    thread_id = payload.get("thread_id", "")
    existing_urls = set(payload.get("existing_urls", []))

    queries = [
        "AI Blender workflow 2026",
        "AI generated 3D models UE5",
        "Meshy Blender Unreal",
        "AI game dev tools 2026",
    ]

    seen_ids = set()
    videos = []

    for query in queries:
        yt_url = (
            "https://www.googleapis.com/youtube/v3/search"
            f"?part=snippet&q={urllib.parse.quote(query)}"
            f"&type=video&maxResults=10&key={yt_key}&order=date"
        )
        try:
            req = urllib.request.Request(yt_url, headers={"Accept": "application/json"})
            resp = _json.loads(urllib.request.urlopen(req, timeout=15).read())
            for item in resp.get("items", []):
                vid_id = (item.get("id") or {}).get("videoId")
                if not vid_id or vid_id in seen_ids:
                    continue
                video_url = f"https://www.youtube.com/watch?v={vid_id}"
                if video_url in existing_urls:
                    continue
                seen_ids.add(vid_id)
                snippet = item.get("snippet") or {}
                videos.append({
                    "i": len(videos),
                    "url": video_url,
                    "title": snippet.get("title", ""),
                    "selftext": (snippet.get("description", "") or "")[:150],
                    "source_name": "youtube",
                    "thread_id": thread_id,
                    "channel": snippet.get("channelTitle", ""),
                })
        except Exception:
            pass

    if not videos:
        return JSONResponse({"results": [], "total": 0})

    posts_for_prompt = [
        {
            "i": v["i"],
            "title": v["title"],
            "src": f"youtube/{v.get('channel', '')}",
            "desc": v["selftext"],
        }
        for v in videos
    ]

    prompt = (
        "You are a relevance scout for a learning-focused research system.\n\n"
        f"ACTIVE INTERESTS:\n{interests}\n\n"
        "Score each resource 1-5 for relevance to the active interests above.\n"
        "5: Directly matches — practical AI tool, workflow, or new release for Blender/UE5\n"
        "4: Clearly relevant to AI-assisted game dev interests\n"
        "3: Tangentially relevant — some connection to interests\n"
        "2: Weak connection\n"
        "1: Not relevant at all\n\n"
        f"RESOURCES TO SCORE:\n{_json.dumps(posts_for_prompt)}\n\n"
        "Respond ONLY with a compact JSON array (no markdown, no extra text):\n"
        '[{"i":0,"score":N,"assessment":"one-line description"},...]\n'
        f"Score every resource. Array length must equal {len(videos)}."
    )

    req_payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=req_payload,
        headers={
            "x-api-key": anthropic_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        resp_raw = urllib.request.urlopen(req, timeout=90).read()
        resp_data = _json.loads(resp_raw)
        haiku_text = (resp_data.get("content") or [{}])[0].get("text", "")
    except Exception as e:
        return JSONResponse({"error": f"Haiku call failed: {e}"}, status_code=500)

    scores = []
    try:
        match = _re.search(r'\[[\s\S]*\]', haiku_text)
        if match:
            scores = _json.loads(match.group(0))
    except Exception:
        return JSONResponse({"error": "JSON parse failed", "raw": haiku_text[:500]}, status_code=500)

    score_map = {s["i"]: s for s in scores}

    results = []
    for v in videos:
        s = score_map.get(v["i"], {})
        score = s.get("score", 0)
        if score >= 3:
            results.append({
                "url": v["url"],
                "title": v["title"],
                "source_name": "youtube",
                "thread_id": v["thread_id"],
                "score": score,
                "assessment": s.get("assessment", ""),
                "channel": v.get("channel", ""),
            })

    return JSONResponse({"results": results, "total": len(results)})


def _fetch_page_text(url, max_chars=2000):
    """Fetch a URL and return stripped plain text (best effort)."""
    import re
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AADP-Research/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            ct = r.headers.get("Content-Type", "")
            if "html" not in ct and "text" not in ct:
                return ""
            raw = r.read(20000).decode("utf-8", errors="ignore")
        raw = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', '', raw, flags=re.DOTALL | re.IGNORECASE)
        raw = re.sub(r'<[^>]+>', ' ', raw)
        raw = re.sub(r'\s+', ' ', raw).strip()
        return raw[:max_chars]
    except Exception:
        return ""


def _summarize_article_haiku(title, url, raw_content, api_key):
    """Generate a 2-3 paragraph summary of an article using Haiku."""
    if not api_key:
        return ""
    prompt = (
        f"Article title: {title}\n"
        f"URL: {url}\n"
        f"Content:\n{raw_content[:1500]}\n\n"
        "Your job is to summarize this article for a general reader unfamiliar with the article's "
        "domain. The relevance judgment happens downstream.\n\n"
        "Write a 2-3 paragraph summary (~150 words):\n"
        "1. What the article says — its central claim or finding, stated neutrally\n"
        "2. The key technique, pattern, or argument the article rests on\n"
        "3. (Optional) What is notable, surprising, or contested about the claim — only if the "
        "article genuinely has such an angle. Omit this paragraph if the article is "
        "straightforward.\n"
        "No bullet points. Do not mention Reflexion, AADP, ChromaDB, memory architecture, or "
        "agent-system implications unless the article itself is about those subjects. "
        "Do not refer to 'the reader,' 'this system,' 'a typical implementation,' or any other "
        "implied use case. The summary is about the article, not about how anyone might apply it."
    )
    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = _json.loads(r.read())
        return resp["content"][0]["text"].strip()
    except Exception:
        return ""


def _log_research_error(env, node_name, error_message):
    """Write a row to error_logs for a research agent fetch/insert failure."""
    try:
        url = f"{env['SUPABASE_URL']}/rest/v1/error_logs"
        data = _json.dumps({
            # workflow deleted B-106 2026-05-08; workflow_id left null, name kept for log traceability
            "workflow_id": None,
            "workflow_name": "context_engineering_research",
            "node_name": (node_name or "unknown")[:255],
            "error_type": "fetch_error",
            "error_message": error_message,
        }).encode()
        req = urllib.request.Request(url, data=data, headers={
            "apikey": env["SUPABASE_SERVICE_KEY"],
            "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }, method="POST")
        with urllib.request.urlopen(req, timeout=8):
            pass
    except Exception:
        pass


# ── Research orchestrator (B-096) ────────────────────────────────────────────
_ORCHESTRATOR_COST_CAP_USD = 0.50
_MAX_FETCHES_PER_CYCLE = 8
_ORCHESTRATOR_MODEL = "claude-sonnet-4-6"

_CHARTER_SECTIONS = [
    "Question", "Scope", "Success Criteria", "Disqualifying Criteria",
    "Initial Sub-Questions", "Source Preferences", "Time Bounds", "Memory Check"
]


def _parse_charter(content: str) -> dict:
    """Parse charter markdown into section dict."""
    import re
    sections = {}
    pattern = r"##\s+(" + "|".join(re.escape(s) for s in _CHARTER_SECTIONS) + r")\s*\n(.*?)(?=\n##\s|\Z)"
    for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
        key = match.group(1).strip().lower().replace(" ", "_")
        sections[key] = match.group(2).strip()
    return sections


def _get_thread_charter(thread_id: str, env) -> dict:
    """Fetch most recent charter entry for thread. Returns parsed sections."""
    rows = _sb_query(env, "thread_entries",
                     {"thread_id": f"eq.{thread_id}", "entry_type": "eq.charter",
                      "select": "id,content,created_at", "order": "created_at.desc", "limit": "1"})
    if not rows:
        return {}
    return {"entry_id": rows[0]["id"], "content": rows[0]["content"],
            **_parse_charter(rows[0]["content"])}


def _get_thread_entries_for_cycle(thread_id: str, env) -> list:
    """Fetch all non-state_change entries for memory pass."""
    rows = _sb_query(env, "thread_entries",
                     {"thread_id": f"eq.{thread_id}",
                      "select": "id,entry_type,content,created_at",
                      "order": "created_at.desc", "limit": "50"})
    return [r for r in rows if r.get("entry_type") != "state_change"]


def _memory_pass(charter: dict, thread_entries: list, env) -> dict:
    """Query ChromaDB + Supabase for prior coverage. Returns summary."""
    question = charter.get("question", "")[:300]
    if not question:
        return {"summary": "No question in charter.", "results": []}

    results = []

    # ChromaDB collections
    chroma_url = f"http://localhost:8000"
    for collection in ["research_findings", "lessons_learned", "reference_material"]:
        try:
            coll_r = requests.get(f"{chroma_url}/api/v1/collections/{collection}", timeout=5)
            if coll_r.status_code != 200:
                continue
            coll_id = coll_r.json().get("id")
            query_r = requests.post(f"{chroma_url}/api/v1/collections/{coll_id}/query",
                                    json={"query_texts": [question], "n_results": 3,
                                          "include": ["documents", "distances", "metadatas"]},
                                    timeout=10)
            if query_r.status_code == 200:
                qdata = query_r.json()
                docs = (qdata.get("documents") or [[]])[0]
                dists = (qdata.get("distances") or [[]])[0]
                for doc, dist in zip(docs, dists):
                    if dist < 1.2:
                        results.append({"source": collection, "distance": round(dist, 3),
                                        "content": doc[:300]})
        except Exception:
            pass

    # research_articles: semantic search via ChromaDB research_findings (B-103)
    # Uses subprocess chromadb client (same pattern as _chroma_multi_query) with where filter.
    _article_script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
results = col.query(
    query_texts=[args['question']],
    n_results=args['n_results'],
    where={'type': {'$eq': 'research_article'}},
)
ids   = results.get('ids', [[]])[0]
docs  = results.get('documents', [[]])[0]
dists = results.get('distances', [[]])[0]
output = [{'id': i, 'content': d, 'distance': dist}
          for i, d, dist in zip(ids, docs, dists) if dist < args['threshold']]
print(json.dumps(output))
"""
    try:
        proc = subprocess.run(
            ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c",
             _article_script,
             _json.dumps({"collection": "research_findings", "question": question,
                          "n_results": 5, "threshold": 1.4})],
            capture_output=True, text=True, timeout=20
        )
        if proc.returncode == 0 and proc.stdout.strip():
            for item in _json.loads(proc.stdout):
                results.append({"source": "research_articles_semantic",
                                 "distance": round(item["distance"], 3),
                                 "content": item["content"][:300]})
        else:
            raise Exception(proc.stderr[:100] if proc.stderr else "empty output")
    except Exception:
        # Fallback: keyword ilike
        try:
            kw = [w for w in question.split() if len(w) > 4][:2]
            if kw:
                art_rows = _sb_query(env, "research_articles",
                                     {"select": "title,url,summary", "limit": "5",
                                      "title": f"ilike.%{kw[0]}%"})
                for art in art_rows:
                    results.append({"source": "research_articles_keyword", "distance": 0.5,
                                    "content": f"{art.get('title','')} — {art.get('summary','')[:200]}"})
        except Exception:
            pass

    # Prior thread entries
    for e in thread_entries[:10]:
        if e.get("entry_type") in ("analysis", "summary", "conclusion") and e.get("content"):
            results.append({"source": f"thread_entry:{e['entry_type']}",
                             "distance": 0.3, "content": e["content"][:300]})

    high_relevance = [r for r in results if r["distance"] < 0.8]
    summary = (f"Found {len(results)} relevant items across memory ({len(high_relevance)} high-relevance). "
               f"Sources: {', '.join(set(r['source'] for r in results[:5]))}")
    return {"summary": summary, "results": results[:10], "high_relevance_count": len(high_relevance)}


def _plan_searches(charter: dict, memory_results: list, api_key: str) -> list:
    """Use Haiku to plan 3-7 searches based on charter + memory."""
    question = charter.get("question", "")
    sub_qs = charter.get("initial_sub-questions", charter.get("initial_sub_questions", ""))
    prior = "\n".join(r["content"][:100] for r in memory_results[:3]) if memory_results else "None"
    src_prefs = charter.get("source_preferences", "")
    time_bounds = charter.get("time_bounds", "")

    prompt = (
        f"Plan web searches for a research question.\n\n"
        f"QUESTION: {question}\n"
        f"SUB-QUESTIONS: {sub_qs}\n"
        f"SOURCE PREFERENCES: {src_prefs}\n"
        f"TIME BOUNDS: {time_bounds}\n"
        f"ALREADY KNOWN (skip these): {prior}\n\n"
        f"Produce 3-7 specific search queries. Each should target a different angle.\n"
        f"Respond with JSON only:\n"
        f'{{"searches": [{{"query": "...", "rationale": "...", "source_type": "paper|blog|doc|news|forum"}}]}}'
    )
    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = _json.loads(r.read())
    text = resp["content"][0]["text"].strip()
    start, end = text.find("{"), text.rfind("}") + 1
    return _json.loads(text[start:end]).get("searches", [])


def _execute_searches(searches: list, charter: dict, api_key: str, env) -> list:
    """Run each search via /web_search, apply source preferences filter."""
    disqualify_text = charter.get("disqualifying_criteria", "").lower()
    time_bounds = charter.get("time_bounds", "")
    freshness = None
    if "past year" in time_bounds.lower() or "12 month" in time_bounds.lower():
        freshness = "py"
    elif "past month" in time_bounds.lower():
        freshness = "pm"

    all_results = []
    seen_urls = set()
    for s in searches[:7]:
        try:
            _ws_data = _json.dumps({"query": s["query"], "max_results": 5, "freshness_window": freshness}).encode()
            _ws_req = urllib.request.Request("http://localhost:9100/web_search", data=_ws_data,
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(_ws_req, timeout=20) as _ws_r:
                _ws_resp = _json.loads(_ws_r.read())
            if True:
                for item in _ws_resp.get("results", []):
                    url = item.get("url", "")
                    if url in seen_urls:
                        continue
                    # Apply disqualifying filter (simple keyword check)
                    snippet_lower = (item.get("snippet", "") + item.get("title", "")).lower()
                    if disqualify_text and any(kw in snippet_lower for kw in disqualify_text.split("\n")[:3] if len(kw) > 5):
                        continue
                    seen_urls.add(url)
                    item["search_query"] = s["query"]
                    item["source_type"] = s.get("source_type", "")
                    all_results.append(item)
        except Exception:
            pass
    return all_results


def _fetch_promising_urls(search_results: list, charter: dict, api_key: str, env) -> list:
    """Select and fetch the most promising URLs (cap _MAX_FETCHES_PER_CYCLE)."""
    # Score by source_type preference alignment
    preferred_text = charter.get("source_preferences", "").lower()
    def _score(item):
        st = item.get("source_type", "")
        if "paper" in preferred_text and st == "paper":
            return 3
        if "doc" in preferred_text and st == "doc":
            return 2
        return 1

    scored = sorted(search_results, key=_score, reverse=True)[:_MAX_FETCHES_PER_CYCLE]

    fetched = []
    for item in scored:
        try:
            _wf_data = _json.dumps({"url": item["url"], "max_chars": 3000}).encode()
            _wf_req = urllib.request.Request("http://localhost:9100/web_fetch", data=_wf_data,
                                             headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(_wf_req, timeout=25) as _wf_r:
                item["fetched_content"] = _json.loads(_wf_r.read()).get("content", "")
            fetched.append(item)
        except Exception:
            item["fetched_content"] = ""
            fetched.append(item)
    return fetched


def _synthesize(charter: dict, fetched: list, memory: dict, api_key: str) -> dict:
    """Call Sonnet to synthesize findings against the charter."""
    question = charter.get("question", "")
    success_criteria = charter.get("success_criteria", "")
    disqualify = charter.get("disqualifying_criteria", "")

    sources_text = ""
    for i, item in enumerate(fetched[:8]):
        content = item.get("fetched_content") or item.get("snippet", "")
        sources_text += f"\n--- SOURCE {i+1}: {item.get('title','?')} ({item.get('url','?')}) ---\n{content[:1500]}\n"

    memory_summary = memory.get("summary", "")
    prior_text = "\n".join(r["content"][:200] for r in memory.get("results", [])[:3])

    prompt = (
        f"Synthesize research findings for this question.\n\n"
        f"QUESTION: {question}\n\n"
        f"SUCCESS CRITERIA:\n{success_criteria}\n\n"
        f"DISQUALIFYING CRITERIA:\n{disqualify}\n\n"
        f"PRIOR KNOWLEDGE FROM MEMORY:\n{memory_summary}\n{prior_text}\n\n"
        f"NEW SOURCES THIS CYCLE:{sources_text}\n\n"
        f"Produce:\n"
        f"1. A synthesis paragraph (what the sources say, agreements, disagreements, gaps)\n"
        f"2. Criteria assessment: for each success criterion, is it met, partially met, or unmet?\n"
        f"3. Sub-questions to pursue next (0-3, only if genuinely unanswered)\n"
        f"4. A one-sentence summary if conclusions can be drawn\n"
        f"5. Self-assessment: does this cycle advance the charter? (yes/partial/no)\n\n"
        f"Respond with JSON only:\n"
        f'{{"synthesis": "...", '
        f'"criteria_assessment": [{{"criterion": "...", "status": "met|partial|unmet", "evidence": "..."}}], '
        f'"sub_questions": ["...", "..."], '
        f'"summary": "...", '
        f'"charter_advancement": "yes|partial|no", '
        f'"memory_contribution": "..."}}'
    )

    payload = _json.dumps({
        "model": _ORCHESTRATOR_MODEL,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = _json.loads(r.read())
    text = resp["content"][0]["text"].strip()
    start, end = text.find("{"), text.rfind("}") + 1
    return _json.loads(text[start:end])


def _sb_post_entry(env, payload: dict) -> str:
    """POST a thread_entry row. Returns row id or ''."""
    url = f"{env['SUPABASE_URL']}/rest/v1/thread_entries"
    data = _json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        rows = _json.loads(r.read())
    return rows[0].get("id", "") if rows else ""


def _write_cycle_entries(thread_id: str, cycle_n: int, search_results: list,
                          fetched: list, synthesis: dict, env) -> dict:
    """Write gather, analysis, summary, sub_question_candidates, cycle_metadata entries."""
    entry_ids = {}

    # Gather entry
    gather_lines = [f"- [{item.get('title','?')}]({item.get('url','?')}) — {item.get('snippet','')[:120]}"
                    for item in search_results[:20]]
    gather_content = f"Cycle {cycle_n} gather — {len(search_results)} results, {len(fetched)} fetched\n\n" + "\n".join(gather_lines)
    entry_ids["gather"] = _sb_post_entry(env, {
        "thread_id": thread_id, "entry_type": "gather",
        "content": gather_content, "source": "orchestrator"
    })

    # Analysis entry
    analysis_content = (
        f"## Cycle {cycle_n} Analysis\n\n"
        f"{synthesis.get('synthesis', '')}\n\n"
        f"**Memory contribution:** {synthesis.get('memory_contribution', 'None noted')}\n\n"
        f"**Charter advancement:** {synthesis.get('charter_advancement', '?')}"
    )
    entry_ids["analysis"] = _sb_post_entry(env, {
        "thread_id": thread_id, "entry_type": "analysis",
        "content": analysis_content, "source": "orchestrator"
    })

    # Summary entry (if conclusions available)
    summary_text = synthesis.get("summary", "").strip()
    if summary_text:
        entry_ids["summary"] = _sb_post_entry(env, {
            "thread_id": thread_id, "entry_type": "summary",
            "content": summary_text, "source": "orchestrator"
        })

    # Sub-question candidates
    for sq in synthesis.get("sub_questions", [])[:3]:
        if sq.strip():
            _sb_post_entry(env, {
                "thread_id": thread_id, "entry_type": "sub_question_candidate",
                "content": sq, "source": "orchestrator"
            })

    # Cycle metadata
    meta_obj = {
        "cycle_number": cycle_n,
        "searches_run": len(search_results),
        "urls_fetched": len(fetched),
        "charter_advancement": synthesis.get("charter_advancement", "?"),
        "outcome": "complete" if synthesis.get("charter_advancement") == "yes" else "partial",
        "grader_verdict": "",  # filled in by B-097
    }
    entry_ids["cycle_metadata"] = _sb_post_entry(env, {
        "thread_id": thread_id, "entry_type": "cycle_metadata",
        "content": f"Cycle {cycle_n}: {len(search_results)} results, {len(fetched)} fetched",
        "metadata": _json.dumps(meta_obj), "source": "orchestrator"
    })

    return entry_ids


def _get_cycle_number(thread_id: str, env) -> int:
    """Count existing cycle_metadata entries to determine next cycle number."""
    try:
        rows = _sb_query(env, "thread_entries",
                         {"thread_id": f"eq.{thread_id}", "entry_type": "eq.cycle_metadata", "select": "id"})
        return len(rows) + 1
    except Exception:
        return 1


@app.post("/run_research_cycle")
def run_research_cycle(payload: dict = {}):
    """Run one research cycle against a thread's charter."""
    thread_id = payload.get("thread_id", "").strip()
    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    brave_key = env.get("BRAVE_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)
    if not brave_key:
        return JSONResponse({"error": "BRAVE_API_KEY not found"}, status_code=500)

    # Step 1: Read charter
    charter = _get_thread_charter(thread_id, env)
    if not charter or not charter.get("question"):
        return JSONResponse({"error": "No charter found for thread. Add a charter first."}, status_code=404)

    cycle_n = _get_cycle_number(thread_id, env)

    # Step 2: Memory pass
    thread_entries = _get_thread_entries_for_cycle(thread_id, env)
    memory = _memory_pass(charter, thread_entries, env)

    # Step 3: Plan searches (Haiku)
    try:
        searches = _plan_searches(charter, memory.get("results", []), api_key)
    except Exception as e:
        return JSONResponse({"error": f"search planning failed: {e}"}, status_code=500)

    if not searches:
        return JSONResponse({"error": "Planner returned no searches"}, status_code=500)

    # Step 4: Execute searches
    search_results = _execute_searches(searches, charter, api_key, env)

    # Step 5: Fetch promising URLs
    fetched = _fetch_promising_urls(search_results, charter, api_key, env)

    # Step 6: Synthesize (Sonnet)
    try:
        synthesis = _synthesize(charter, fetched, memory, api_key)
    except Exception as e:
        return JSONResponse({"error": f"synthesis failed: {e}"}, status_code=500)

    # Step 7: Write entries
    try:
        entry_ids = _write_cycle_entries(thread_id, cycle_n, search_results, fetched, synthesis, env)
    except Exception as e:
        return JSONResponse({"error": f"entry write failed: {e}"}, status_code=500)

    # Step 8: Call grader (B-097 will complete this path)
    try:
        grade_data = _json.dumps({"thread_id": thread_id, "cycle_number": cycle_n}).encode()
        grade_req = urllib.request.Request(
            "http://localhost:9100/grade_research_cycle", data=grade_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(grade_req, timeout=90) as gr:
            grader_verdict = _json.loads(gr.read()).get("verdict", "continue")
    except Exception:
        grader_verdict = "continue"

    return JSONResponse({
        "cycle_number": cycle_n,
        "searches_run": len(searches),
        "results_found": len(search_results),
        "urls_fetched": len(fetched),
        "charter_advancement": synthesis.get("charter_advancement"),
        "grader_verdict": grader_verdict,
        "entry_ids": entry_ids,
    })


# ── Thread research agent (B-117) ────────────────────────────────────────────

_HAIKU_INPUT_COST_PER_TOK = 0.00000025   # $0.25 / 1M tokens
_HAIKU_OUTPUT_COST_PER_TOK = 0.00000125  # $1.25 / 1M tokens

_THREAD_RESEARCH_SCREEN_SYSTEM = (
    "You are a research screener. Given a web search result and research criteria, "
    "decide if it qualifies as a relevant finding.\n"
    "Respond with valid JSON only: "
    "{\"qualifies\": true/false, \"relevance_note\": \"one concise sentence\"}"
)

_FRESHNESS_MAP = {
    "day": "pd", "24h": "pd",
    "week": "pw", "7 day": "pw",
    "month": "pm", "30 day": "pm",
    "year": "py", "12 month": "py",
}


def _charter_freshness(recency: str) -> str | None:
    rl = recency.lower()
    for kw, code in _FRESHNESS_MAP.items():
        if kw in rl:
            return code
    return None


def _screen_result_haiku(item: dict, question: str, success_criteria: str,
                          disqualifying_criteria: str, api_key: str) -> tuple[bool, str, float]:
    """Screen one search result with Haiku. Returns (qualifies, relevance_note, cost_usd)."""
    prompt = (
        f"Research question: {question[:300]}\n\n"
        f"Success criteria:\n{success_criteria[:400]}\n\n"
        f"Disqualifying criteria:\n{disqualifying_criteria[:300]}\n\n"
        f"Result:\nTitle: {item.get('title', '')}\n"
        f"URL: {item.get('url', '')}\n"
        f"Snippet: {item.get('snippet', '')[:400]}\n\n"
        f"Does this qualify? JSON only."
    )
    data = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 120,
        "messages": [{"role": "user", "content": prompt}],
        "system": _THREAD_RESEARCH_SCREEN_SYSTEM,
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=data,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = _json.loads(r.read())
    usage = resp.get("usage", {})
    cost = (usage.get("input_tokens", 0) * _HAIKU_INPUT_COST_PER_TOK +
            usage.get("output_tokens", 0) * _HAIKU_OUTPUT_COST_PER_TOK)
    raw = resp["content"][0]["text"].strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    verdict = _json.loads(raw[start:end])
    return verdict.get("qualifies", False), verdict.get("relevance_note", ""), cost


@app.post("/run_thread_research")
def run_thread_research(payload: dict = {}):
    """B-117: Thread-native research agent. Reads charter JSONB, searches Brave, screens with
    Haiku, writes finding + cycle_summary entries to thread_entries."""
    thread_id = (payload.get("thread_id") or "").strip()
    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)
    if not env.get("BRAVE_API_KEY"):
        return JSONResponse({"error": "BRAVE_API_KEY not found"}, status_code=500)

    # Read charter JSONB from threads table
    thread_rows = _sb_query(env, "threads",
                            {"id": f"eq.{thread_id}", "select": "id,title,charter"})
    if not thread_rows:
        return JSONResponse({"error": f"Thread {thread_id} not found"}, status_code=404)
    charter = thread_rows[0].get("charter") or {}
    if not charter.get("question", "").strip():
        return JSONResponse({"error": "No charter found for thread. Add a charter first."},
                            status_code=404)

    question = charter["question"].strip()
    sub_questions = [q.strip() for q in (charter.get("sub_questions") or []) if q.strip()]
    success_criteria = charter.get("success_criteria", "").strip()
    disqualifying_criteria = charter.get("disqualifying_criteria", "").strip()
    freshness = _charter_freshness(charter.get("recency_requirement", ""))

    # One query per sub-question (up to 5); fall back to main question
    queries = sub_questions[:5] or [question]

    cost_usd = 0.0
    all_results = []
    seen_urls: set = set()
    queries_run = []

    # Search Brave for each query
    for query in queries:
        if cost_usd >= _ORCHESTRATOR_COST_CAP_USD:
            break
        try:
            ws_data = _json.dumps({"query": query, "max_results": 5,
                                   "freshness_window": freshness}).encode()
            ws_req = urllib.request.Request(
                "http://localhost:9100/web_search", data=ws_data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(ws_req, timeout=20) as ws_r:
                ws_resp = _json.loads(ws_r.read())
            queries_run.append(query)
            for item in ws_resp.get("results", []):
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    item["search_query"] = query
                    all_results.append(item)
        except Exception:
            pass

    # Screen each result via Haiku against charter criteria
    qualifying = []
    screened_count = 0
    for item in all_results:
        if cost_usd >= _ORCHESTRATOR_COST_CAP_USD:
            break
        screened_count += 1
        try:
            qualifies, note, call_cost = _screen_result_haiku(
                item, question, success_criteria, disqualifying_criteria, api_key
            )
            cost_usd += call_cost
            if qualifies:
                item["relevance_note"] = note
                qualifying.append(item)
        except Exception:
            pass

    # Fetch URLs already written as findings for this thread to prevent cross-cycle duplicates
    existing_finding_urls: set = set()
    try:
        existing_rows = _sb_query(env, "thread_entries",
                                  {"thread_id": f"eq.{thread_id}", "entry_type": "eq.finding",
                                   "select": "source", "limit": "200"})
        for row in existing_rows:
            src = (row.get("source") or "").strip()
            if src:
                existing_finding_urls.add(src)
    except Exception:
        pass

    # Write qualifying results as finding entries
    finding_ids = []
    skipped_duplicates = 0
    for item in qualifying:
        content = (
            f"**{item.get('title', 'Untitled')}**\n"
            f"URL: {item.get('url', '')}\n"
            f"Query: {item.get('search_query', '')}\n\n"
            f"{item.get('snippet', '')}\n\n"
            f"Relevance: {item.get('relevance_note', '')}"
        )
        url = item.get("url", "")
        if url and url in existing_finding_urls:
            skipped_duplicates += 1
            continue
        eid = _sb_post_entry(env, {
            "thread_id": thread_id,
            "entry_type": "finding",
            "content": content,
            "source": url,
            "metadata": _json.dumps({
                "url": url,
                "title": item.get("title", ""),
                "source_domain": item.get("source_domain", ""),
                "search_query": item.get("search_query", ""),
                "relevance_note": item.get("relevance_note", ""),
            }),
        })
        if eid:
            finding_ids.append(eid)
            existing_finding_urls.add(url)

    # Write cycle_summary entry
    dup_note = f"\n**Skipped duplicates:** {skipped_duplicates}" if skipped_duplicates else ""
    summary_content = (
        f"## Research Cycle Summary\n\n"
        f"**Queries run:** {len(queries_run)}\n"
        f"**Results screened:** {screened_count}\n"
        f"**Qualifying findings:** {len(finding_ids)}"
        f"{dup_note}\n"
        f"**Estimated cost:** ${cost_usd:.4f}\n\n"
        f"Queries: {', '.join(queries_run[:5])}"
    )
    cycle_id = _sb_post_entry(env, {
        "thread_id": thread_id,
        "entry_type": "cycle_summary",
        "content": summary_content,
        "source": "thread_research_agent",
        "metadata": _json.dumps({
            "queries_run": len(queries_run),
            "results_screened": screened_count,
            "findings_written": len(finding_ids),
            "cost_usd": round(cost_usd, 4),
        }),
    })

    return JSONResponse({
        "thread_id": thread_id,
        "queries_run": len(queries_run),
        "results_screened": screened_count,
        "findings_written": len(finding_ids),
        "skipped_duplicates": skipped_duplicates,
        "cost_usd": round(cost_usd, 4),
        "finding_ids": finding_ids,
        "cycle_summary_id": cycle_id,
    })


# ── Semantic article indexing (B-103) ────────────────────────────────────────
_CHROMA_URL = "http://localhost:8000"


def _get_chroma_collection_id(name: str) -> str:
    """Get ChromaDB collection UUID by name."""
    req = urllib.request.Request(f"{_CHROMA_URL}/api/v1/collections/{name}")
    with urllib.request.urlopen(req, timeout=8) as r:
        return _json.loads(r.read())["id"]


def _chroma_add_documents_via_client(collection_name: str, doc_ids: list, documents: list, metadatas: list):
    """Add documents via Python client subprocess so embeddings are generated automatically."""
    script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
# Add in one batch
col.add(ids=args['ids'], documents=args['documents'], metadatas=args['metadatas'])
print(json.dumps({'added': len(args['ids'])}))
"""
    proc = subprocess.run(
        ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
         _json.dumps({"collection": collection_name, "ids": doc_ids,
                      "documents": documents, "metadatas": metadatas})],
        capture_output=True, text=True, timeout=60
    )
    if proc.returncode != 0:
        raise Exception(f"chroma add failed: {proc.stderr[:200]}")
    return _json.loads(proc.stdout)


def _chroma_query(collection_id: str, query_text: str, n_results: int = 5) -> list:
    """Semantic query against a ChromaDB collection. Returns [{content, distance, metadata}]."""
    payload = _json.dumps({
        "query_texts": [query_text],
        "n_results": n_results,
        "include": ["documents", "distances", "metadatas"],
    }).encode()
    req = urllib.request.Request(
        f"{_CHROMA_URL}/api/v1/collections/{collection_id}/query",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        data = _json.loads(r.read())
    docs = (data.get("documents") or [[]])[0]
    dists = (data.get("distances") or [[]])[0]
    metas = (data.get("metadatas") or [[]])[0]
    return [{"content": d, "distance": dist, "metadata": m}
            for d, dist, m in zip(docs, dists, metas)]


def _embed_single_article(article: dict, collection_name: str, env) -> str:
    """Embed one research_article via Python client (generates embeddings). Returns chromadb_id."""
    title = article.get("title", "")
    summary = (article.get("summary") or "")[:2000]
    url = article.get("url", "")
    source = article.get("source", "")
    article_id = str(article.get("id", ""))
    import re as _re
    slug = _re.sub(r'[^a-z0-9_]', '', title.lower()[:30].replace(" ", "_"))
    doc_id = f"article_{article_id[:8]}_{slug}"[:80]
    document = f"{title}\n{url}\nSource: {source}\n\n{summary}"
    metadata = {
        "title": title[:200],
        "url": url[:300],
        "source": source[:100],
        "supabase_id": article_id,
        "type": "research_article",
    }
    _chroma_add_documents_via_client(collection_name, [doc_id], [document], [metadata])
    # Update chromadb_id in Supabase
    patch_url = f"{env['SUPABASE_URL']}/rest/v1/research_articles?id=eq.{article_id}"
    data = _json.dumps({"chromadb_id": doc_id}).encode()
    req = urllib.request.Request(patch_url, data=data, method="PATCH", headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    })
    with urllib.request.urlopen(req, timeout=8):
        pass
    return doc_id


@app.post("/backfill_articles_to_chromadb")
def backfill_articles_to_chromadb(payload: dict = {}):
    """Batch backfill: embed research_articles into research_findings via Python client."""
    env = _read_env_simple()
    batch_size = int(payload.get("batch_size", 20))

    rows = _sb_query(env, "research_articles",
                     {"chromadb_id": "is.null",
                      "select": "id,title,url,source,summary",
                      "limit": str(batch_size)})

    # Filter rows with usable content
    import re as _re
    to_embed = [r for r in rows if r.get("title") and (r.get("summary") or "").strip()[:10]]

    if not to_embed:
        remaining = _sb_query(env, "research_articles",
                              {"chromadb_id": "is.null", "select": "id", "limit": "1"})
        return JSONResponse({"embedded": 0, "errors": [], "has_more": len(remaining) > 0, "call_again": False})

    # Build batch data
    ids, docs, metas, article_ids = [], [], [], []
    for art in to_embed:
        article_id = str(art.get("id", ""))
        title = art.get("title", "")
        summary = (art.get("summary") or "")[:2000]
        url = art.get("url", "")
        source = art.get("source", "")
        slug = _re.sub(r'[^a-z0-9_]', '', title.lower()[:25].replace(" ", "_"))
        doc_id = f"article_{article_id[:8]}_{slug}"[:80]
        ids.append(doc_id)
        docs.append(f"{title}\n{url}\nSource: {source}\n\n{summary}")
        metas.append({"title": title[:200], "url": url[:300], "source": source[:100],
                      "supabase_id": article_id, "type": "research_article"})
        article_ids.append((article_id, doc_id))

    # Batch embed via Python client subprocess
    script = """
import chromadb, json, sys
args = json.loads(sys.argv[1])
client = chromadb.HttpClient(host='localhost', port=8000)
col = client.get_collection(args['collection'])
col.add(ids=args['ids'], documents=args['documents'], metadatas=args['metadatas'])
print(json.dumps({'added': len(args['ids'])}))
"""
    try:
        proc = subprocess.run(
            ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", script,
             _json.dumps({"collection": "research_findings", "ids": ids,
                          "documents": docs, "metadatas": metas})],
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return JSONResponse({"error": f"batch embed failed: {proc.stderr[:300]}"}, status_code=500)
    except subprocess.TimeoutExpired:
        return JSONResponse({"error": "batch embed timed out — try smaller batch_size"}, status_code=500)

    # Update chromadb_ids in Supabase
    embedded = 0
    errors = []
    for article_id, doc_id in article_ids:
        try:
            patch_url = f"{env['SUPABASE_URL']}/rest/v1/research_articles?id=eq.{article_id}"
            data = _json.dumps({"chromadb_id": doc_id}).encode()
            req = urllib.request.Request(patch_url, data=data, method="PATCH", headers={
                "apikey": env["SUPABASE_SERVICE_KEY"],
                "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            })
            with urllib.request.urlopen(req, timeout=8):
                pass
            embedded += 1
        except Exception as e:
            errors.append(f"{article_id[:8]}: {e}")

    remaining = _sb_query(env, "research_articles",
                          {"chromadb_id": "is.null", "select": "id", "limit": "1"})
    return JSONResponse({
        "embedded": embedded,
        "errors": errors[:3],
        "has_more": len(remaining) > 0,
        "call_again": len(remaining) > 0,
    })


@app.post("/embed_article")
def embed_article(payload: dict = {}):
    """Embed a single research_article by id into research_findings."""
    article_id = payload.get("article_id", "").strip()
    if not article_id:
        return JSONResponse({"error": "article_id required"}, status_code=400)

    env = _read_env_simple()
    rows = _sb_query(env, "research_articles",
                     {"id": f"eq.{article_id}", "select": "id,title,url,source,summary"})
    if not rows:
        return JSONResponse({"error": "article not found"}, status_code=404)

    try:
        collection_id = _get_chroma_collection_id("research_findings")
        doc_id = _embed_single_article(rows[0], collection_id, env)
        return JSONResponse({"doc_id": doc_id, "embedded": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Memory consultation (B-099) ──────────────────────────────────────────────

@app.post("/consult_memory")
def consult_memory(payload: dict = {}):
    """Query memory stores for prior coverage of a question. Writes memory_consultation entry if thread_id provided."""
    question = payload.get("question", "").strip()
    charter_summary = payload.get("charter_summary", "").strip()
    thread_id = payload.get("thread_id", "").strip()

    if not question and not charter_summary:
        return JSONResponse({"error": "question or charter_summary required"}, status_code=400)

    env = _read_env_simple()

    # When thread_id is provided, fetch the charter question directly from the threads table.
    # This is the authoritative source — callers may pass stale or incorrect question text.
    if thread_id:
        try:
            charter_rows = _sb_query(env, "threads",
                                     {"id": f"eq.{thread_id}", "select": "charter"})
            if charter_rows:
                charter_q = ((charter_rows[0].get("charter") or {}).get("question") or "").strip()
                if charter_q:
                    question = charter_q
        except Exception:
            pass  # fall through to caller-provided question

    query_text = question or charter_summary

    # Build consultation results from the same 4 sources as the orchestrator memory pass
    mock_charter = {"question": query_text}
    memory = _memory_pass(mock_charter, [], env)

    results = memory.get("results", [])
    high_count = memory.get("high_relevance_count", 0)

    # Format output as readable content
    lines = [f"## Memory Consultation", f"Query: {query_text[:200]}", ""]
    if not results:
        lines.append("No prior coverage found in memory stores.")
    else:
        lines.append(f"Found {len(results)} relevant items ({high_count} high-relevance, distance < 0.8):")
        lines.append("")
        for i, r in enumerate(results[:8]):
            src = r.get("source", "?")
            dist = r.get("distance", 0)
            content_preview = r.get("content", "")[:200].replace("\n", " ")
            confidence = "high" if dist < 0.8 else ("medium" if dist < 1.2 else "low")
            lines.append(f"**[{i+1}]** ({src}, {confidence}) {content_preview}")

    consultation_content = "\n".join(lines)

    # Write memory_consultation entry to thread if thread_id provided
    if thread_id:
        try:
            _sb_post_entry(env, {
                "thread_id": thread_id,
                "entry_type": "memory_consultation",
                "content": consultation_content,
                "source": "system",
            })
        except Exception as e:
            pass  # non-fatal

    return JSONResponse({
        "result_count": len(results),
        "high_relevance_count": high_count,
        "summary": memory.get("summary", ""),
        "content": consultation_content,
    })


# ── Watch state (B-098) ──────────────────────────────────────────────────────
_WATCH_INTERVALS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
}


def _get_existing_thread_urls(thread_id: str, env) -> set:
    """Collect all URLs already referenced in thread gather entries."""
    rows = _sb_query(env, "thread_entries",
                     {"thread_id": f"eq.{thread_id}", "entry_type": "eq.gather",
                      "select": "content", "limit": "20"})
    import re
    urls = set()
    for r in rows:
        for url in re.findall(r'https?://[^\s\)]+', r.get("content", "")):
            urls.add(url.rstrip("."),)
    return urls


def _update_watch_timestamps(thread_id: str, interval: str, env):
    """Update last_watch_cycle_at and next_watch_due_at on the thread."""
    now = datetime.now(timezone.utc)
    delta = _WATCH_INTERVALS.get(interval, timedelta(weeks=1))
    next_due = (now + delta).isoformat()
    url = f"{env['SUPABASE_URL']}/rest/v1/threads?id=eq.{thread_id}"
    data = _json.dumps({"last_watch_cycle_at": now.isoformat(), "next_watch_due_at": next_due}).encode()
    req = urllib.request.Request(url, data=data, method="PATCH", headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    })
    with urllib.request.urlopen(req, timeout=8):
        pass


@app.post("/run_watch_cycle")
def run_watch_cycle(payload: dict = {}):
    """Run a lighter recency-focused cycle for a watch-enabled thread."""
    thread_id = payload.get("thread_id", "").strip()
    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    # Read charter and thread watch settings
    charter = _get_thread_charter(thread_id, env)
    if not charter:
        return JSONResponse({"error": "No charter for thread"}, status_code=404)

    thread_rows = _sb_query(env, "threads",
                            {"id": f"eq.{thread_id}", "select": "watch_interval,watch_enabled"})
    thread_meta = thread_rows[0] if thread_rows else {}
    interval = thread_meta.get("watch_interval", "weekly")

    # Existing URLs — novelty baseline
    existing_urls = _get_existing_thread_urls(thread_id, env)

    # Run 2-3 searches focused on recent content
    question = charter.get("question", "")
    searches = [
        {"query": f"{question} recent 2025", "rationale": "recency scan", "source_type": "news"},
        {"query": f"{question} new developments", "rationale": "new developments", "source_type": "blog"},
    ]

    search_results = _execute_searches(searches, charter, api_key, env)

    # Novelty filter: keep only URLs not already in thread
    novel = [r for r in search_results if r.get("url", "") not in existing_urls]
    overlap_pct = 1.0 - (len(novel) / max(len(search_results), 1))

    if overlap_pct > 0.8 or not novel:
        # No change — write only cycle_metadata
        cycle_n = _get_cycle_number(thread_id, env)
        _sb_post_entry(env, {
            "thread_id": thread_id,
            "entry_type": "cycle_metadata",
            "content": f"Watch cycle {cycle_n}: no new content found",
            "metadata": _json.dumps({"cycle_number": cycle_n, "outcome": "no_change",
                                     "is_watch_cycle": True, "overlap_pct": round(overlap_pct, 2)}),
            "source": "watch",
        })
        _update_watch_timestamps(thread_id, interval, env)
        return JSONResponse({"outcome": "no_change", "novel_count": 0,
                             "overlap_pct": round(overlap_pct, 2)})

    # Novel content found — run normal cycle logic on novel results only
    fetched = _fetch_promising_urls(novel[:4], charter, api_key, env)
    try:
        synthesis = _synthesize(charter, fetched, {"summary": "", "results": []}, api_key)
    except Exception as e:
        _update_watch_timestamps(thread_id, interval, env)
        return JSONResponse({"error": f"synthesis failed: {e}"}, status_code=500)

    cycle_n = _get_cycle_number(thread_id, env)
    entry_ids = _write_cycle_entries(thread_id, cycle_n, novel, fetched, synthesis, env)

    # Tag as watch cycle in metadata
    _sb_post_entry(env, {
        "thread_id": thread_id, "entry_type": "cycle_metadata",
        "content": f"Watch cycle {cycle_n}: {len(novel)} novel results",
        "metadata": _json.dumps({"cycle_number": cycle_n, "outcome": "new_content",
                                  "is_watch_cycle": True, "novel_count": len(novel)}),
        "source": "watch",
    })

    # Grade the watch cycle
    try:
        grade_data = _json.dumps({"thread_id": thread_id, "cycle_number": cycle_n}).encode()
        grade_req = urllib.request.Request(
            "http://localhost:9100/grade_research_cycle", data=grade_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(grade_req, timeout=90) as gr:
            grade_result = _json.loads(gr.read())
        grader_verdict = grade_result.get("verdict", "continue")
    except Exception:
        grader_verdict = "continue"

    # If significant (complete verdict), re-open thread to active
    if grader_verdict == "complete":
        url = f"{env['SUPABASE_URL']}/rest/v1/threads?id=eq.{thread_id}"
        data = _json.dumps({"state": "active"}).encode()
        req = urllib.request.Request(url, data=data, method="PATCH", headers={
            "apikey": env["SUPABASE_SERVICE_KEY"],
            "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
            "Content-Type": "application/json", "Prefer": "return=minimal",
        })
        with urllib.request.urlopen(req, timeout=8):
            pass
        # Telegram notification would go here via stats_server _send_telegram if wired

    _update_watch_timestamps(thread_id, interval, env)
    return JSONResponse({"outcome": "new_content", "novel_count": len(novel),
                         "cycle_number": cycle_n, "grader_verdict": grader_verdict,
                         "entry_ids": entry_ids})


@app.get("/check_watch_threads")
def check_watch_threads():
    """Hourly job endpoint: run watch cycles for all due threads."""
    env = _read_env_simple()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        due_threads = _sb_query(env, "threads",
                                {"watch_enabled": "eq.true",
                                 "next_watch_due_at": f"lte.{now_iso}",
                                 "select": "id,title,watch_interval"})
    except Exception as e:
        return JSONResponse({"error": f"query failed: {e}"}, status_code=500)

    results = []
    for t in due_threads:
        try:
            data = _json.dumps({"thread_id": t["id"]}).encode()
            req = urllib.request.Request(
                "http://localhost:9100/run_watch_cycle", data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=150) as r:
                outcome = _json.loads(r.read()).get("outcome", "error")
            results.append({"thread_id": t["id"], "title": t["title"][:40], "outcome": outcome})
        except Exception as ex:
            results.append({"thread_id": t["id"], "outcome": f"error: {ex}"})

    return JSONResponse({"checked": len(due_threads), "results": results})


# ── Research cycle grader (B-097) ────────────────────────────────────────────
_CYCLE_GRADER_SYSTEM = """You are grading a research cycle against a charter. You have no context
from the team that ran the cycle — judge from artifacts only. Do not ask for clarification.
Cite specific evidence from the cycle entries for each criterion assessment.
Research cycle verdicts: continue | complete | pause | fail
- continue: cycle made progress; more cycles warranted
- complete: success criteria are met; thread can close
- pause: cycle drifted, hit ambiguity, or surfaced something Bill should see
- fail: no usable output (search failures, all disqualified, no content)"""


def _get_cycle_entries(thread_id: str, cycle_n: int, env) -> list:
    """Fetch entries written by the specified cycle (most recent N entries of each type)."""
    rows = _sb_query(env, "thread_entries",
                     {"thread_id": f"eq.{thread_id}",
                      "select": "id,entry_type,content,created_at,metadata",
                      "order": "created_at.desc", "limit": "20"})
    # The most recent cycle's entries are the newest rows
    # Return the first occurrence of each key type
    seen_types = set()
    cycle_entries = []
    for r in rows:
        et = r.get("entry_type", "")
        if et in ("charter", "state_change"):
            continue
        if et not in seen_types or et == "sub_question_candidate":
            seen_types.add(et)
            cycle_entries.append(r)
    return cycle_entries


def _call_sonnet_cycle_grader(charter: dict, cycle_entries: list, api_key: str) -> dict:
    """Call Sonnet to grade the research cycle."""
    success_criteria = charter.get("success_criteria", "No criteria specified")
    disqualify = charter.get("disqualifying_criteria", "")
    question = charter.get("question", "")

    entries_text = ""
    for e in cycle_entries:
        entries_text += f"\n[{e.get('entry_type','?')}]\n{(e.get('content') or '')[:1000]}\n"

    prompt = (
        f"Grade this research cycle.\n\n"
        f"RESEARCH QUESTION: {question}\n\n"
        f"SUCCESS CRITERIA:\n{success_criteria}\n\n"
        f"DISQUALIFYING CRITERIA:\n{disqualify}\n\n"
        f"CYCLE ENTRIES:\n{entries_text[:5000]}\n\n"
        f"For each success criterion, assess: met | partial | unmet. Cite evidence.\n"
        f"Then give an overall verdict: continue | complete | pause | fail\n\n"
        f"Respond with JSON only:\n"
        f'{{"verdict": "continue|complete|pause|fail", '
        f'"rationale": "2-3 sentences", '
        f'"criteria_results": [{{"criterion": "...", "met": true|false, "evidence": "..."}}]}}'
    )

    payload = _json.dumps({
        "model": _ORCHESTRATOR_MODEL,
        "max_tokens": 1024,
        "system": _CYCLE_GRADER_SYSTEM,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload, headers={
        "x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = _json.loads(r.read())
    text = resp["content"][0]["text"].strip()
    start, end = text.find("{"), text.rfind("}") + 1
    return _json.loads(text[start:end])


def _persist_cycle_grader_review(thread_id, cycle_n, verdict, rationale, criteria_results, env) -> str:
    """Write grader_reviews row for a research cycle."""
    url = f"{env['SUPABASE_URL']}/rest/v1/grader_reviews"
    payload = {
        "card_id": f"cycle:{thread_id}:{cycle_n}",
        "target_id": thread_id,
        "review_type": "research_cycle",
        "verdict": verdict,
        "rationale": rationale,
        "criteria_results": criteria_results,
        "input_snapshot": {"thread_id": thread_id, "cycle_number": cycle_n},
    }
    data = _json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        rows = _json.loads(r.read())
    return rows[0].get("id", "") if rows else ""


def _handle_cycle_verdict(thread_id, cycle_n, verdict, rationale, env):
    """Act on grader verdict: update thread state or file annotation."""
    if verdict == "complete":
        # Close the thread
        url = f"{env['SUPABASE_URL']}/rest/v1/threads?id=eq.{thread_id}"
        data = _json.dumps({"state": "closed"}).encode()
        req = urllib.request.Request(url, data=data, method="PATCH", headers={
            "apikey": env["SUPABASE_SERVICE_KEY"],
            "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        })
        with urllib.request.urlopen(req, timeout=8):
            pass
    elif verdict in ("pause", "fail"):
        # File annotation
        intent = "question" if verdict == "pause" else "correction"
        note = f"Grader verdict: {verdict} (cycle {cycle_n}). {rationale}"
        _sb_post_entry(env, {
            "thread_id": thread_id,
            "entry_type": "annotation",
            "content": note,
            "source": "grader",
        })
        # Also write to agent_feedback
        url = f"{env['SUPABASE_URL']}/rest/v1/agent_feedback"
        fb_payload = {
            "target_type": "thread",
            "target_id": thread_id,
            "content": note,
            "action_session": f"cycle_grader_{cycle_n}",
            "metadata": _json.dumps({"intent_type": intent, "cycle_number": cycle_n}),
        }
        data = _json.dumps(fb_payload).encode()
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "apikey": env["SUPABASE_SERVICE_KEY"],
            "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        })
        with urllib.request.urlopen(req, timeout=8):
            pass


@app.post("/grade_research_cycle")
def grade_research_cycle(payload: dict = {}):
    """Grade a research cycle against its charter. Called by /run_research_cycle."""
    thread_id = payload.get("thread_id", "").strip()
    cycle_n = int(payload.get("cycle_number", 1))

    if not thread_id:
        return JSONResponse({"error": "thread_id required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    charter = _get_thread_charter(thread_id, env)
    if not charter:
        return JSONResponse({"error": "No charter found for thread"}, status_code=404)

    cycle_entries = _get_cycle_entries(thread_id, cycle_n, env)
    if not cycle_entries:
        return JSONResponse({"verdict": "fail", "rationale": "No cycle entries found."})

    try:
        result = _call_sonnet_cycle_grader(charter, cycle_entries, api_key)
    except Exception as e:
        return JSONResponse({"error": f"grader call failed: {e}"}, status_code=500)

    verdict = result.get("verdict", "pause")
    rationale = result.get("rationale", "")
    criteria_results = result.get("criteria_results", [])

    try:
        review_id = _persist_cycle_grader_review(thread_id, cycle_n, verdict, rationale, criteria_results, env)
    except Exception as e:
        review_id = ""

    try:
        _handle_cycle_verdict(thread_id, cycle_n, verdict, rationale, env)
    except Exception:
        pass

    return JSONResponse({
        "review_id": review_id,
        "thread_id": thread_id,
        "cycle_number": cycle_n,
        "verdict": verdict,
        "rationale": rationale,
        "criteria_results": criteria_results,
    })


# ── Web search + fetch (B-094) ───────────────────────────────────────────────
_BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
_USER_AGENT = "AADP-Research/1.0 (+https://github.com/thompsmanlearn/claudis)"


def _log_external_api_usage(env, provider, endpoint, query, result_count, response_ms):
    """Log external API call to external_api_usage table."""
    try:
        url = f"{env['SUPABASE_URL']}/rest/v1/external_api_usage"
        data = _json.dumps({
            "provider": provider,
            "endpoint": endpoint,
            "query": (query or "")[:500],
            "result_count": result_count,
            "response_ms": response_ms,
        }).encode()
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "apikey": env["SUPABASE_SERVICE_KEY"],
            "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        })
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass  # non-fatal


def _brave_search(query: str, max_results: int, freshness: str, api_key: str) -> list:
    """Call Brave Search API. Returns list of {url, title, snippet, source_domain, published_date}."""
    params = {
        "q": query,
        "count": str(min(max_results, 20)),
        "safesearch": "moderate",
        "text_decorations": "false",
    }
    if freshness:
        params["freshness"] = freshness  # pd (past day), pw (past week), pm (past month), py (past year)
    url = _BRAVE_SEARCH_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
        # Brave may gzip even without explicit Accept-Encoding handling
        try:
            import gzip as _gzip
            data = _json.loads(_gzip.decompress(raw))
        except Exception:
            data = _json.loads(raw)
    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "url": item.get("url", ""),
            "title": item.get("title", ""),
            "snippet": item.get("description", ""),
            "source_domain": item.get("meta_url", {}).get("hostname", ""),
            "published_date": item.get("page_age", ""),
        })
    return results


@app.post("/web_search")
def web_search(payload: dict = {}):
    """Search the web via Brave Search API."""
    query = payload.get("query", "").strip()
    max_results = int(payload.get("max_results", 10))
    freshness_window = payload.get("freshness_window")  # None, 'pd', 'pw', 'pm', 'py'

    if not query:
        return JSONResponse({"error": "query required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("BRAVE_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "BRAVE_API_KEY not found in .env"}, status_code=500)

    t0 = datetime.now(timezone.utc)
    try:
        results = _brave_search(query, max_results, freshness_window, api_key)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return JSONResponse({"error": "Brave rate limit hit", "retry_after": e.headers.get("Retry-After", "60")}, status_code=429)
        return JSONResponse({"error": f"Brave HTTP {e.code}: {e.reason}"}, status_code=502)
    except Exception as e:
        return JSONResponse({"error": f"search failed: {e}"}, status_code=500)

    elapsed_ms = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)
    _log_external_api_usage(env, "brave", "/web_search", query, len(results), elapsed_ms)

    return JSONResponse({"results": results, "query": query, "count": len(results)})


def _check_robots(url: str) -> bool:
    """Return True if fetching url is allowed by robots.txt (best effort)."""
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        req = urllib.request.Request(robots_url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=5) as r:
            robots_text = r.read().decode("utf-8", errors="ignore")
        # Simple check: if "Disallow: /" for our user agent or "*"
        lines = robots_text.splitlines()
        applies = False
        for line in lines:
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                applies = agent == "*" or "AADP" in agent
            elif applies and line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path == "/" or (path and parsed.path.startswith(path)):
                    return False
        return True
    except Exception:
        return True  # if robots.txt unreachable, allow (best effort)


def _html_to_text(html: str, max_chars: int = 8000) -> str:
    """Strip HTML tags and clean up whitespace."""
    import re
    # Remove script/style blocks
    html = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


@app.post("/web_fetch")
def web_fetch(payload: dict = {}):
    """Fetch a URL and return its text content. Respects robots.txt."""
    url = payload.get("url", "").strip()
    max_chars = int(payload.get("max_chars", 8000))

    if not url:
        return JSONResponse({"error": "url required"}, status_code=400)
    if not url.startswith(("http://", "https://")):
        return JSONResponse({"error": "url must be http(s)"}, status_code=400)

    env = _read_env_simple()

    if not _check_robots(url):
        return JSONResponse({"error": "robots.txt disallows fetching this URL", "url": url}, status_code=403)

    t0 = datetime.now(timezone.utc)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            content_type = r.headers.get("Content-Type", "")
            raw = r.read(200_000)  # read up to 200KB; trim to max_chars after HTML stripping
    except urllib.error.HTTPError as e:
        return JSONResponse({"error": f"HTTP {e.code}: {e.reason}", "url": url}, status_code=502)
    except Exception as e:
        return JSONResponse({"error": f"fetch failed: {e}", "url": url}, status_code=500)

    elapsed_ms = int((datetime.now(timezone.utc) - t0).total_seconds() * 1000)

    if "html" in content_type.lower():
        text = _html_to_text(raw.decode("utf-8", errors="ignore"), max_chars)
    else:
        text = raw.decode("utf-8", errors="ignore")[:max_chars]

    _log_external_api_usage(env, "web", "/web_fetch", url, len(text), elapsed_ms)

    return JSONResponse({"url": url, "content": text, "content_type": content_type, "length": len(text)})


# ── Carry documents (B-091) ──────────────────────────────────────────────────
_CARRY_DIR = REPO  # CARRY_*.md files live at repo root


def _sb_query(env, path, params=None):
    """GET from Supabase REST API with optional query params."""
    url = f"{env['SUPABASE_URL']}/rest/v1/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        return _json.loads(r.read())


def _generate_carry_questions(env) -> str:
    lines = ["# CARRY_QUESTIONS.md",
             "# Auto-generated. Read at desktop session start.",
             f"# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
             ""]

    questions = []

    # 1. Thread sub_question_candidates
    try:
        rows = _sb_query(env, "thread_entries",
                         {"entry_type": "eq.sub_question_candidate",
                          "select": "id,content,thread_id,created_at",
                          "order": "created_at.desc", "limit": "20"})
        for r in rows:
            questions.append(f"- **Thread question** [{r.get('thread_id','?')[:8]}]: {r.get('content','')[:200]}")
    except Exception as e:
        questions.append(f"- [thread sub_questions unavailable: {e}]")

    # 2. Grader pause/fail verdicts not yet reviewed by Bill
    try:
        rows = _sb_query(env, "grader_reviews",
                         {"verdict": "in.(pause,fail)", "reviewed_by_bill": "eq.false",
                          "select": "card_id,verdict,rationale,created_at",
                          "order": "created_at.desc", "limit": "10"})
        for r in rows:
            questions.append(f"- **Grader {r.get('verdict','?').upper()}** [{r.get('card_id','?')}]: {(r.get('rationale') or '')[:200]}")
    except Exception as e:
        questions.append(f"- [grader verdicts unavailable: {e}]")

    # 3. Unanswered question annotations
    try:
        rows = _sb_query(env, "agent_feedback",
                         {"or": "(processed.is.null,processed.eq.false)",
                          "select": "target_type,target_id,content,created_at",
                          "order": "created_at.desc", "limit": "20"})
        # Filter for question intent (metadata jsonb)
        for r in rows:
            meta = r.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = _json.loads(meta)
                except Exception:
                    meta = {}
            if meta.get("intent_type") == "question":
                questions.append(f"- **Annotation question** [{r.get('target_type','?')}:{r.get('target_id','?')[:20]}]: {r.get('content','')[:200]}")
    except Exception as e:
        questions.append(f"- [annotation questions unavailable: {e}]")

    if questions:
        lines.extend(questions)
    else:
        lines.append("*No questions pending.*")

    return "\n".join(lines)


def _generate_carry_proposals(env) -> str:
    lines = ["# CARRY_PROPOSALS.md",
             "# Auto-generated. Read at desktop session start.",
             f"# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
             ""]

    proposals = []

    # Look for direction-intent annotations (multiple against the same target)
    try:
        rows = _sb_query(env, "agent_feedback",
                         {"or": "(processed.is.null,processed.eq.false)",
                          "select": "target_type,target_id,content,created_at",
                          "order": "target_type.asc,target_id.asc",
                          "limit": "50"})
        # Group by target
        from collections import Counter
        target_counts = Counter((r.get("target_type"), r.get("target_id")) for r in rows)
        for (tt, tid), count in target_counts.most_common():
            if count >= 2:
                proposals.append(f"- **{count} annotations** on {tt}:{tid[:40]} — may warrant a card")
    except Exception as e:
        proposals.append(f"- [proposal scan unavailable: {e}]")

    if proposals:
        lines.extend(proposals)
    else:
        lines.append("*No proposals pending.*")

    return "\n".join(lines)


def _generate_carry_health(env) -> str:
    lines = ["# CARRY_HEALTH.md",
             "# Auto-generated. Read at desktop session start.",
             f"# Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
             ""]

    # Lesson store health
    try:
        rows = _sb_query(env, "lessons_learned",
                         {"select": "id", "chromadb_id": "is.null"})
        broken = len(rows)
        total_rows = _sb_query(env, "lessons_learned", {"select": "id"})
        total = len(total_rows)
        lines.append(f"**Lesson store:** {total} lessons, {broken} missing chromadb_id {'⚠️' if broken > 0 else '✅'}")
    except Exception as e:
        lines.append(f"**Lesson store:** unavailable ({e})")

    # Agent fleet
    try:
        rows = _sb_query(env, "agent_registry",
                         {"status": "eq.active", "select": "agent_name,workflow_id"})
        no_workflow = [r["agent_name"] for r in rows if not r.get("workflow_id")]
        lines.append(f"**Agent fleet:** {len(rows)} active, {len(no_workflow)} without workflow_id {'⚠️' if no_workflow else '✅'}")
        if no_workflow:
            lines.append(f"  No workflow: {', '.join(no_workflow)}")
    except Exception as e:
        lines.append(f"**Agent fleet:** unavailable ({e})")

    # Unresolved errors
    try:
        rows = _sb_query(env, "error_logs",
                         {"resolved": "eq.false", "select": "id"})
        count = len(rows)
        lines.append(f"**Unresolved errors:** {count} {'⚠️' if count > 5 else '✅'}")
    except Exception as e:
        lines.append(f"**Unresolved errors:** unavailable ({e})")

    # Recent grader reviews
    try:
        rows = _sb_query(env, "grader_reviews",
                         {"select": "verdict,created_at", "order": "created_at.desc", "limit": "5"})
        if rows:
            summary = ", ".join(f"{r['verdict']}" for r in rows)
            lines.append(f"**Recent grader verdicts (last 5):** {summary}")
        else:
            lines.append("**Recent grader verdicts:** none yet")
    except Exception as e:
        lines.append(f"**Grader reviews:** unavailable ({e})")

    return "\n".join(lines)


@app.post("/generate_carry_documents")
def generate_carry_documents(payload: dict = {}):
    """Generate CARRY_QUESTIONS.md, CARRY_PROPOSALS.md, CARRY_HEALTH.md at repo root."""
    env = _read_env_simple()
    results = {}

    for fname, generator in [
        ("CARRY_QUESTIONS.md", _generate_carry_questions),
        ("CARRY_PROPOSALS.md", _generate_carry_proposals),
        ("CARRY_HEALTH.md", _generate_carry_health),
    ]:
        try:
            content = generator(env)
            path = os.path.join(_CARRY_DIR, fname)
            with open(path, "w") as f:
                f.write(content)
            results[fname] = "ok"
        except Exception as e:
            results[fname] = f"error: {e}"

    return JSONResponse({"generated": results})


# ── Skill resolver (B-090) ───────────────────────────────────────────────────
_SKILL_CONFIDENCE_THRESHOLD = 0.6


def _get_skills_registry(env):
    """Fetch all active skills from skills_registry."""
    url = (f"{env['SUPABASE_URL']}/rest/v1/skills_registry"
           f"?status=eq.active&select=name,applies_when,also_triggers_when,provides")
    req = urllib.request.Request(url, headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
    })
    with urllib.request.urlopen(req, timeout=8) as r:
        return _json.loads(r.read())


def _resolve_skills_haiku(directive_text: str, skills: list, api_key: str) -> list:
    """Use Haiku to match directive against skills. Returns [{name, confidence, reasoning}]."""
    skills_desc = "\n".join(
        f"- {s['name']}: applies_when={s.get('applies_when','')[:200]} | "
        f"also_triggers={s.get('also_triggers_when','')[:100]}"
        for s in skills
    )
    prompt = (
        f"Match this directive against the available skills.\n\n"
        f"DIRECTIVE: {directive_text[:500]}\n\n"
        f"AVAILABLE SKILLS:\n{skills_desc}\n\n"
        f"For each skill that applies to this directive, return it with a confidence score.\n"
        f"Only include skills with genuine relevance. Confidence: 1.0=certain, 0.7=likely, 0.5=possible.\n"
        f"Respond with JSON only:\n"
        f'{{"matches": [{{"name": "<skill_name>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}}]}}'
    )
    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = _json.loads(r.read())
    text = resp["content"][0]["text"].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    result = _json.loads(text[start:end])
    return result.get("matches", [])


def _increment_skill_times_used(names: list, env):
    """Increment times_used for loaded skills in skills_registry."""
    for name in names:
        try:
            url = f"{env['SUPABASE_URL']}/rest/v1/skills_registry?name=eq.{urllib.parse.quote(name)}"
            # Read current times_used
            req = urllib.request.Request(url + "&select=times_used,times_loaded", headers={
                "apikey": env["SUPABASE_SERVICE_KEY"],
                "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
            })
            with urllib.request.urlopen(req, timeout=5) as r:
                rows = _json.loads(r.read())
            if not rows:
                continue
            current = rows[0].get("times_used", 0) or 0
            now_iso = datetime.now(timezone.utc).isoformat()
            data = _json.dumps({"times_used": current + 1, "last_used": now_iso}).encode()
            patch_req = urllib.request.Request(url, data=data, method="PATCH", headers={
                "apikey": env["SUPABASE_SERVICE_KEY"],
                "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            })
            with urllib.request.urlopen(patch_req, timeout=5):
                pass
        except Exception:
            pass  # non-fatal


@app.post("/resolve_skills")
def resolve_skills(payload: dict = {}):
    """Match directive text against skills_registry. Returns skills to load."""
    directive_text = payload.get("directive_text", "").strip()
    increment = payload.get("increment_on_load", False)

    if not directive_text:
        return JSONResponse({"error": "directive_text required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    try:
        skills = _get_skills_registry(env)
    except Exception as e:
        return JSONResponse({"error": f"skills_registry fetch failed: {e}"}, status_code=500)

    if not skills:
        return JSONResponse({"skills": [], "confidence_threshold": _SKILL_CONFIDENCE_THRESHOLD})

    try:
        matches = _resolve_skills_haiku(directive_text, skills, api_key)
    except Exception as e:
        return JSONResponse({"error": f"haiku resolution failed: {e}"}, status_code=500)

    # Filter by threshold
    confident = [m for m in matches if m.get("confidence", 0) >= _SKILL_CONFIDENCE_THRESHOLD]

    if increment and confident:
        _increment_skill_times_used([m["name"] for m in confident], env)

    return JSONResponse({
        "skills": confident,
        "confidence_threshold": _SKILL_CONFIDENCE_THRESHOLD,
        "all_matches": matches,
    })


# ── Grader (B-087) ───────────────────────────────────────────────────────────
_BACKLOG_PATH = os.path.join(REPO, "BACKLOG.md")
_SESSIONS_PATH = os.path.join(REPO, "sessions", "lean")
_GRADER_SYSTEM = """You are a grader evaluating whether a completed task meets its specification.
You have no context from the session that produced this work — you judge from artifacts only.
Do not ask for clarification. Every criterion must be evaluated with evidence cited from the artifact.
Be specific: quote or reference concrete lines/sections. A criterion is met only if there is positive
evidence in the artifact; absence of evidence is not a pass."""


def _parse_card_from_backlog(card_id: str) -> dict:
    """Extract card spec from BACKLOG.md. Returns {title, done_when, full_text} or raises."""
    try:
        text = open(_BACKLOG_PATH).read()
    except FileNotFoundError:
        raise ValueError(f"BACKLOG.md not found at {_BACKLOG_PATH}")
    # Find card section header: "B-NNN: title" or "## B-NNN: title"
    import re
    pattern = rf"(?:^##\s+)?{re.escape(card_id)}:\s+(.+?)$"
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"Card {card_id} not found in BACKLOG.md")
    title = match.group(1).strip()
    # Extract from match position to next card or end
    start = match.start()
    next_card = re.search(r"^(?:##\s+)?B-\d+:", text[start + 1:], re.MULTILINE)
    end = (start + 1 + next_card.start()) if next_card else len(text)
    card_text = text[start:end].strip()
    # Extract Done when section — handles ##, ###, or no-hash variants (B-105 fix)
    done_match = re.search(
        r"(?:^|\n)#{0,4}\s*Done when\s*\n(.*?)(?=\n#{1,4}\s|\Z)",
        card_text, re.DOTALL
    )
    done_when = done_match.group(1).strip() if done_match else ""
    data_only = bool(re.search(r"(?:^|\n)data_only:\s*true\b", card_text, re.IGNORECASE))
    return {"title": title, "card_id": card_id, "done_when": done_when, "full_text": card_text, "data_only": data_only}


def _read_session_artifact(artifact_path: str) -> str:
    """Read session artifact. artifact_path may be filename or full path."""
    if os.path.isabs(artifact_path) and os.path.exists(artifact_path):
        return open(artifact_path).read()
    # Try as filename under sessions/lean/
    candidate = os.path.join(_SESSIONS_PATH, os.path.basename(artifact_path))
    if os.path.exists(candidate):
        return open(candidate).read()
    raise FileNotFoundError(f"Session artifact not found: {artifact_path}")


def _get_git_diff_for_card(commit_sha: str = "") -> str:
    """Get diff context for a card. Uses explicit SHA when provided, else HEAD~3."""
    if commit_sha:
        # Show the specific commit and one parent commit for context
        log_out, _ = _git("log", "-1", "--oneline", commit_sha)
        diff_out, _ = _git("diff", f"{commit_sha}^", commit_sha, "--stat")
        return f"Card commit: {commit_sha}\n{log_out}\n\nChanged files in that commit:\n{diff_out}"
    else:
        log_out, _ = _git("log", "-3", "--oneline")
        diff_out, _ = _git("diff", "HEAD~3", "HEAD", "--stat")
        return f"Recent commits (HEAD~3..HEAD — no commit_sha provided):\n{log_out}\n\nChanged files:\n{diff_out}"


def _call_sonnet_grader(card: dict, artifact_text: str, git_diff: str, api_key: str) -> dict:
    """Call Sonnet to grade the artifact against the card's done-when criteria."""
    done_when_lines = [l.strip("- ").strip() for l in card["done_when"].splitlines() if l.strip()]
    criteria_json = _json.dumps(done_when_lines)

    prompt = (
        f"Grade this completed work against its specification.\n\n"
        f"CARD: {card['card_id']} — {card['title']}\n\n"
        f"DONE-WHEN CRITERIA (grade each one):\n{card['done_when']}\n\n"
        f"SESSION ARTIFACT:\n{artifact_text[:6000]}\n\n"
        f"RECENT GIT CHANGES:\n{git_diff[:2000]}\n\n"
        f"For each criterion, determine: met or not_met. Cite specific evidence from the artifact.\n"
        f"Then give an overall verdict: pass (all met), pause (most met but issues to review), "
        f"or fail (significant criteria not met).\n\n"
        f"Respond with JSON only:\n"
        f'{{\n'
        f'  "verdict": "pass|pause|fail",\n'
        f'  "rationale": "1-3 sentence overall assessment",\n'
        f'  "criteria_results": [\n'
        f'    {{"criterion": "...", "met": true|false, "evidence": "specific quote or observation"}},\n'
        f'    ...\n'
        f'  ]\n'
        f'}}'
    )

    payload = _json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2048,
        "system": _GRADER_SYSTEM,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = _json.loads(r.read())
    text = resp["content"][0]["text"].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    return _json.loads(text[start:end])


def _persist_grader_review(card_id, artifact_path, verdict, rationale, criteria_results,
                            input_snapshot, env) -> str:
    """INSERT grader review into Supabase. Returns the new row id."""
    url = f"{env['SUPABASE_URL']}/rest/v1/grader_reviews"
    payload = {
        "card_id": card_id,
        "session_artifact_path": artifact_path,
        "verdict": verdict,
        "rationale": rationale,
        "criteria_results": criteria_results,
        "input_snapshot": input_snapshot,
    }
    data = _json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        rows = _json.loads(r.read())
    return rows[0]["id"] if rows else ""


@app.post("/grade_card")
def grade_card(payload: dict = {}):
    """Grade a completed card against its done-when criteria. Returns structured verdict."""
    card_id = payload.get("card_id", "").strip()
    artifact_path = payload.get("session_artifact_path", "").strip()
    commit_sha = payload.get("commit_sha", "").strip()  # B-104: explicit SHA

    if not card_id:
        return JSONResponse({"error": "card_id required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    # Parse card
    try:
        card = _parse_card_from_backlog(card_id)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=404)

    # B-105: guard against empty done_when — refuse to grade without a rubric
    if not card.get("done_when", "").strip():
        return JSONResponse({
            "error": "cannot_grade",
            "verdict": "cannot_grade",
            "rationale": (f"Card {card_id} has no parseable Done when section in BACKLOG.md. "
                          f"Cannot grade without a rubric. "
                          f"Check that the card uses '## Done when', '### Done when', or 'Done when' as a section header."),
        }, status_code=400)

    # Read artifact
    artifact_text = ""
    if artifact_path:
        try:
            artifact_text = _read_session_artifact(artifact_path)
        except FileNotFoundError as e:
            return JSONResponse({"error": str(e)}, status_code=404)

    # Git diff — skip for data_only cards; use explicit SHA if provided (B-104), else HEAD~3 fallback
    data_only = card.get("data_only", False)
    if data_only:
        git_diff = ("data_only: true — no file changes expected for this card. "
                    "Evaluate done-when criteria against the session artifact and any "
                    "Supabase query output recorded in it. Do not penalize the absence of a git diff.")
    else:
        git_diff = _get_git_diff_for_card(commit_sha)

    # Build input snapshot (what the grader saw)
    input_snapshot = {
        "card_id": card_id,
        "card_title": card["title"],
        "done_when": card["done_when"],
        "artifact_path": artifact_path,
        "artifact_length": len(artifact_text),
        "commit_sha": commit_sha or "HEAD~3 fallback",
        "git_diff_summary": git_diff[:500],
        "data_only": data_only,
        "graded_at": datetime.now(timezone.utc).isoformat(),
    }

    # Call grader
    try:
        result = _call_sonnet_grader(card, artifact_text, git_diff, api_key)
    except Exception as e:
        return JSONResponse({"error": f"grader call failed: {e}"}, status_code=500)

    verdict = result.get("verdict", "pause")
    rationale = result.get("rationale", "")
    criteria_results = result.get("criteria_results", [])

    # Persist
    try:
        review_id = _persist_grader_review(
            card_id, artifact_path, verdict, rationale, criteria_results, input_snapshot, env
        )
    except Exception as e:
        review_id = ""
        rationale += f" [persist error: {e}]"

    return JSONResponse({
        "review_id": review_id,
        "card_id": card_id,
        "verdict": verdict,
        "rationale": rationale,
        "criteria_results": criteria_results,
        "high_confidence": verdict == "pass",
    })


# ── Annotation classifier (B-086) ────────────────────────────────────────────
# Intent types for the annotation classification system.
_ANNOTATION_INTENT_TYPES = [
    "direction",   # Bill steering the system (refine charter, change priority, add/remove scope)
    "correction",  # something is wrong with the target (incorrect lesson, broken skill)
    "gap",         # target is missing something (source gap, capability gap, knowledge gap)
    "question",    # Bill asking a question that may need research or clarification
    "screening",   # agreement or override of an automatic decision
    "note",        # observation worth keeping but no action required
    "noise",       # not actionable, likely filed in error
]
_ANNOTATION_HIGH_CONFIDENCE = 0.8


def _classify_annotation_haiku(target_type, target_id, target_summary, content, api_key):
    """Call Haiku to classify annotation intent. Returns (intent_type, confidence, reasoning)."""
    intent_list = "\n".join(f"- {t}" for t in _ANNOTATION_INTENT_TYPES)
    prompt = (
        f"You are classifying an annotation filed against a system target.\n\n"
        f"Target type: {target_type}\n"
        f"Target ID: {target_id}\n"
        f"Target summary: {target_summary or '(not provided)'}\n"
        f"Annotation content: {content}\n\n"
        f"Classify the annotation intent. Choose exactly one:\n{intent_list}\n\n"
        f"Respond with JSON only:\n"
        f'{{"intent_type": "<one of the above>", "confidence": <0.0-1.0>, "reasoning": "<one sentence>"}}'
    )
    payload = _json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 256,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        resp = _json.loads(r.read())
    text = resp["content"][0]["text"].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    result = _json.loads(text[start:end])
    intent = result.get("intent_type", "uncertain")
    confidence = float(result.get("confidence", 0.0))
    reasoning = result.get("reasoning", "")
    if intent not in _ANNOTATION_INTENT_TYPES or confidence < _ANNOTATION_HIGH_CONFIDENCE:
        intent = "uncertain"
    return intent, confidence, reasoning


def _write_annotation_classification(feedback_id, intent_type, confidence, reasoning, env):
    """Write classifier output back to agent_feedback.metadata."""
    classified_at = datetime.now(timezone.utc).isoformat()
    metadata = _json.dumps({
        "intent_type": intent_type,
        "confidence": confidence,
        "reasoning": reasoning,
        "classified_at": classified_at,
    })
    url = f"{env['SUPABASE_URL']}/rest/v1/agent_feedback?id=eq.{feedback_id}"
    data = _json.dumps({"metadata": metadata}).encode()
    req = urllib.request.Request(url, data=data, method="PATCH", headers={
        "apikey": env["SUPABASE_SERVICE_KEY"],
        "Authorization": f"Bearer {env['SUPABASE_SERVICE_KEY']}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    })
    with urllib.request.urlopen(req, timeout=8):
        pass


@app.post("/classify_annotation")
def classify_annotation(payload: dict = {}):
    """Classify the intent of an annotation. Called by annotate() uplink callable after write."""
    feedback_id = payload.get("feedback_id", "")
    target_type = payload.get("target_type", "")
    target_id = payload.get("target_id", "")
    target_summary = payload.get("target_summary", "")
    content = payload.get("content", "")

    if not content:
        return JSONResponse({"error": "content required"}, status_code=400)

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    try:
        intent_type, confidence, reasoning = _classify_annotation_haiku(
            target_type, target_id, target_summary, content, api_key
        )
    except Exception as e:
        return JSONResponse({"error": f"classification failed: {e}"}, status_code=500)

    if feedback_id:
        try:
            _write_annotation_classification(feedback_id, intent_type, confidence, reasoning, env)
        except Exception as e:
            return JSONResponse({
                "intent_type": intent_type,
                "confidence": confidence,
                "reasoning": reasoning,
                "write_error": str(e),
            })

    return JSONResponse({
        "intent_type": intent_type,
        "confidence": confidence,
        "reasoning": reasoning,
        "high_confidence": confidence >= _ANNOTATION_HIGH_CONFIDENCE,
    })


@app.post("/run_capability_curation_scan")
def run_capability_curation_scan(payload: dict = {}):
    """Capability curation pass (B-109, 2026-05-08).
    Scans agent_registry and skills_registry for retirement/review candidates.
    Writes each candidate as an agent_feedback annotation (Tier 2, intent_type=question).
    Returns candidate list and annotation IDs.
    """
    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    if not sb_url or not sb_key:
        return JSONResponse({"error": "Supabase credentials not found"}, status_code=500)

    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    def _sb_get(path):
        req = urllib.request.Request(sb_url + path, headers={k: v for k, v in headers.items() if k != "Prefer"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return _json.loads(r.read())

    def _write_annotation(target_type, target_id, content, recommended_action):
        data = _json.dumps({
            "target_type": target_type,
            "target_id": target_id,
            "content": content,
            "action_session": "capability_curator",
            "metadata": {
                "intent_type": "question",
                "recommended_action": recommended_action,
                "source": "run_capability_curation_scan",
                "scan_date": "2026-05-08",
            },
        }).encode()
        req = urllib.request.Request(
            sb_url + "/rest/v1/agent_feedback",
            data=data,
            headers={**headers, "Prefer": "return=representation"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return _json.loads(r.read())[0]["id"]

    candidates = []

    # Signal 1: Paused agents with no workflow_id (never built or workflow deleted)
    agents = _sb_get(
        "/rest/v1/agent_registry"
        "?status=eq.paused"
        "&workflow_id=is.null"
        "&select=agent_name,status,updated_at,description"
    )
    for agent in agents:
        name = agent["agent_name"]
        if name == "autonomous_growth_scheduler":
            continue  # Intentionally paused by Bill, memory: never reactivate autonomously
        ann_id = _write_annotation(
            "agent", name,
            f"Curation flag: '{name}' is paused with no workflow_id — never built or workflow deleted. "
            f"Paused since {str(agent.get('updated_at','?'))[:10]}. "
            f"Recommended action: retire (no workflow exists to restore) or build missing workflow.",
            "retire",
        )
        candidates.append({"type": "agent", "name": name, "signal": "paused_no_workflow", "annotation_id": ann_id})

    # Signal 2: Skills with times_used = 0
    skills = _sb_get(
        "/rest/v1/skills_registry"
        "?times_used=eq.0"
        "&status=eq.active"
        "&select=name,applies_when,created_at"
    )
    for skill in skills:
        name = skill["name"]
        ann_id = _write_annotation(
            "skill", name,
            f"Curation flag: skill '{name}' has times_used=0 since registration "
            f"({str(skill.get('created_at','?'))[:10]}). "
            f"Applies when: {str(skill.get('applies_when','?'))[:200]}. "
            "Recommended action: monitor (plausible but untriggered) or revise applies_when.",
            "monitor",
        )
        candidates.append({"type": "skill", "name": name, "signal": "never_used", "annotation_id": ann_id})

    return JSONResponse({
        "status": "ok",
        "candidates": candidates,
        "agent_retire_candidates": sum(1 for c in candidates if c["type"] == "agent"),
        "skill_monitor_candidates": sum(1 for c in candidates if c["type"] == "skill"),
    })


def _next_card_number():
    """Determine next B-NNN by scanning sessions/lean/ and BACKLOG.md."""
    import re as _re, os as _os
    seen = set()
    sessions_dir = "/home/thompsman/aadp/claudis/sessions/lean"
    if _os.path.isdir(sessions_dir):
        for fname in _os.listdir(sessions_dir):
            for m in _re.findall(r"b(\d+)", fname, _re.I):
                seen.add(int(m))
    backlog = "/home/thompsman/aadp/claudis/BACKLOG.md"
    if _os.path.isfile(backlog):
        with open(backlog) as f:
            for m in _re.findall(r"## B-(\d+):", f.read()):
                seen.add(int(m))
    return max(seen, default=114) + 1


@app.post("/generate_card_from_comment")
def generate_card_from_comment(payload: dict = {}):
    """Generate a backlog card from a classified annotation (B-114).
    Called by annotate() when intent_type in (correction, gap), confidence>=0.8,
    target_type in (agent, skill, capability).
    Body: {feedback_id: str}
    Returns: {card_id, card_text}
    """
    feedback_id = payload.get("feedback_id", "").strip()
    if not feedback_id:
        return JSONResponse({"error": "feedback_id required"}, status_code=400)

    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    api_key = env.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JSONResponse({"error": "ANTHROPIC_API_KEY not found"}, status_code=500)

    sb_headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
    }

    def _sb_get(path):
        req = urllib.request.Request(sb_url + path, headers={k: v for k, v in sb_headers.items() if k != "Content-Type"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return _json.loads(r.read())

    # Read the feedback row
    rows = _sb_get(f"/rest/v1/agent_feedback?id=eq.{feedback_id}&select=*")
    if not rows:
        return JSONResponse({"error": "feedback_id not found"}, status_code=404)
    fb = rows[0]
    target_type = fb.get("target_type", "")
    target_id = fb.get("target_id", "")
    content = fb.get("content", "")
    metadata = fb.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = _json.loads(metadata)
        except Exception:
            metadata = {}
    intent_type = metadata.get("intent_type", "unknown")
    confidence = float(metadata.get("confidence", 0.0))

    # Fetch target context
    target_context = ""
    if target_type == "agent":
        agents = _sb_get(f"/rest/v1/agent_registry?agent_name=eq.{target_id}&select=description,status,schedule")
        if agents:
            a = agents[0]
            target_context = f"Agent: {target_id}\nDescription: {a.get('description','')}\nStatus: {a.get('status','')}\nSchedule: {a.get('schedule','')}"
    elif target_type == "skill":
        skills = _sb_get(f"/rest/v1/skills_registry?name=eq.{target_id}&select=description,applies_when,provides")
        if skills:
            s = skills[0]
            target_context = f"Skill: {target_id}\nApplies when: {s.get('applies_when','')}\nProvides: {s.get('provides','')}"
    elif target_type == "capability":
        caps = _sb_get(f"/rest/v1/capabilities?name=eq.{target_id}&select=description,category")
        if caps:
            c = caps[0]
            target_context = f"Capability: {target_id}\nDescription: {c.get('description','')}"

    card_num = _next_card_number()
    card_id = f"B-{card_num}-cmt"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Generate card via Sonnet
    _SCHEMA_SUMMARY = (
        "SUPABASE TABLES (use exact names when referencing tables in the Scope section):\n"
        "- agent_registry: agent_name, status, schedule, webhook_url, description, protected\n"
        "- capabilities: name, description, category, confidence_score\n"
        "- agent_feedback: target_type, target_id, content, processed, metadata\n"
        "- work_queue: task_type, status, priority, payload\n"
        "- error_logs: resolved, workflow_id, node_name\n"
        "- thread_entries: thread_id, entry_type, content, source, created_at\n"
        "- grader_reviews: card_id, verdict, rationale, criteria_results\n"
        "- lessons_learned: id, content, metadata (also in ChromaDB)\n"
        "Common files touched in this project:\n"
        "- ~/aadp/claudis/stats-server/stats_server.py\n"
        "- ~/aadp/claudis/anvil/uplink_server.py\n"
        "- ~/aadp/claude-dashboard/client_code/Form1/__init__.py\n"
        "- ~/aadp/claudis/BACKLOG.md\n"
    )
    prompt = (
        f"You are generating a backlog card for a system called AADP (an AI agent development platform).\n\n"
        f"A comment was filed against a system target and classified as '{intent_type}' (confidence {confidence:.2f}).\n\n"
        f"Original comment:\n{content}\n\n"
        f"Target context:\n{target_context or '(none available)'}\n\n"
        f"{_SCHEMA_SUMMARY}\n"
        f"Generate a backlog card in this exact format:\n\n"
        f"## {card_id}: [short descriptive title — what to fix]\n"
        f"Status: ready Depends on: none\n"
        f"Goal\n[One paragraph: what to accomplish and why. Reference the original comment.]\n"
        f"Context\n[What Claude Code needs to know: current state, the gap, what not to touch.]\n"
        f"Done when\n[3-5 specific verifiable criteria. No 'works correctly' — use checkable facts.]\n"
        f"Scope\nTouch: [specific files or tables]\nDo not touch: [explicit exclusions]\n\n"
        f"Rules:\n"
        f"- Goal: what and why, not how\n"
        f"- Done when: every item checkable by curl, SQL, or file check\n"
        f"- Scope: name exact files — no directories\n"
        f"- Two-hour ceiling: if too large, scope it down\n"
        f"- Output the card text only, no preamble"
    )

    api_payload = _json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=api_payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = _json.loads(r.read())
        card_text = resp["content"][0]["text"].strip()
    except Exception as e:
        return JSONResponse({"error": f"card generation failed: {e}"}, status_code=500)

    # Append to BACKLOG.md with origin marker
    backlog_path = "/home/thompsman/aadp/claudis/BACKLOG.md"
    marker = f"\n> Generated from agent_feedback {feedback_id} on {today} (intent={intent_type}, confidence={confidence:.2f})\n"
    with open(str(backlog_path), "a") as f:
        f.write(f"\n{card_text}\n{marker}")

    # Update agent_feedback metadata with generated card_id
    new_meta = {**metadata, "generated_card_id": card_id, "card_generated_at": today}
    patch_data = _json.dumps({"metadata": _json.dumps(new_meta)}).encode()
    patch_req = urllib.request.Request(
        f"{sb_url}/rest/v1/agent_feedback?id=eq.{feedback_id}",
        data=patch_data,
        method="PATCH",
        headers={**sb_headers, "Prefer": "return=minimal"},
    )
    try:
        with urllib.request.urlopen(patch_req, timeout=8):
            pass
    except Exception:
        pass  # non-fatal

    return JSONResponse({"card_id": card_id, "card_text": card_text})


@app.post("/export_comment_driven_results")
def export_comment_driven_results(payload: dict = {}):
    """Bundle comment-driven card results for desktop review (B-114).
    Body: {since_date: 'YYYY-MM-DD' (optional), agent_name: str (optional)}
    Returns: {markdown: str, count: int}
    """
    since_date = payload.get("since_date", "")
    agent_name = payload.get("agent_name", "")

    env = _read_env_simple()
    sb_url = env.get("SUPABASE_URL", "")
    sb_key = env.get("SUPABASE_SERVICE_KEY", "")
    sb_headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
    }

    def _sb_get(path):
        req = urllib.request.Request(sb_url + path, headers=sb_headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return _json.loads(r.read())

    # Fetch agent_feedback rows with generated_card_id in metadata
    params = "select=id,target_type,target_id,content,created_at,metadata"
    if agent_name:
        params += f"&target_id=eq.{agent_name}"
    if since_date:
        params += f"&created_at=gte.{since_date}"
    params += "&order=created_at.desc&limit=50"

    all_rows = _sb_get(f"/rest/v1/agent_feedback?{params}")
    driven = []
    for row in all_rows:
        meta = row.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = _json.loads(meta)
            except Exception:
                meta = {}
        if meta.get("generated_card_id"):
            row["_meta"] = meta
            driven.append(row)

    if not driven:
        return JSONResponse({"markdown": "No comment-driven results found.", "count": 0})

    # Fetch grader_reviews for generated card IDs
    card_ids = [r["_meta"]["generated_card_id"] for r in driven]
    verdicts = {}
    for cid in card_ids:
        reviews = _sb_get(f"/rest/v1/grader_reviews?card_id=eq.{cid}&select=verdict,rationale,created_at&order=created_at.desc&limit=1")
        if reviews:
            verdicts[cid] = reviews[0]

    # Read BACKLOG.md for card text
    import os as _os2
    _backlog_path = "/home/thompsman/aadp/claudis/BACKLOG.md"
    backlog_text = open(_backlog_path).read() if _os2.path.isfile(_backlog_path) else ""

    sections = []
    for row in driven:
        meta = row["_meta"]
        card_id = meta.get("generated_card_id", "?")
        created = (row.get("created_at") or "")[:10]
        verdict_info = verdicts.get(card_id)
        verdict_str = f"{verdict_info['verdict']} — {verdict_info['rationale'][:200]}" if verdict_info else "not yet graded"

        # Extract card text from BACKLOG.md
        import re as _re2
        m = _re2.search(rf"(## {_re2.escape(card_id)}:.*?)(?=\n## B-|\Z)", backlog_text, _re2.S)
        card_excerpt = m.group(1)[:800] + "..." if m else "(card text not found in BACKLOG.md)"

        sections.append(
            f"---\n"
            f"**Comment** ({created}) on `{row['target_type']}:{row['target_id']}`:\n"
            f"> {row['content'][:300]}\n\n"
            f"**Generated card:** {card_id}\n"
            f"```\n{card_excerpt}\n```\n\n"
            f"**Grader verdict:** {verdict_str}\n"
        )

    header = f"# Comment-Driven Work Export — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n{len(driven)} item(s)\n\n"
    return JSONResponse({"markdown": header + "\n".join(sections), "count": len(driven)})


_CONSUMER_MANIFEST_PATH = os.path.join(REPO, "architecture", "consumer_manifest.json")

_SEVERITY_ORDER = {"orphaned": 0, "consumer_unknown": 1, "partial": 2, "wired": 3}


def _n8n_workflow_status(workflow_id: str, n8n_key: str) -> dict:
    """Return {active, recent_executions} for a workflow, or None on error."""
    if not workflow_id or not n8n_key:
        return None
    try:
        # Check active state
        url = f"http://localhost:5678/api/v1/workflows/{workflow_id}"
        req = urllib.request.Request(url, headers={"X-N8N-API-KEY": n8n_key})
        with urllib.request.urlopen(req, timeout=5) as r:
            wf = _json.loads(r.read().decode())
        active = bool(wf.get("active", False))

        # Count executions in last 14 days
        cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
        url2 = f"http://localhost:5678/api/v1/executions?workflowId={workflow_id}&limit=50"
        req2 = urllib.request.Request(url2, headers={"X-N8N-API-KEY": n8n_key})
        with urllib.request.urlopen(req2, timeout=5) as r2:
            exec_data = _json.loads(r2.read().decode())
        recent = sum(
            1 for e in exec_data.get("data", [])
            if (e.get("startedAt") or "") >= cutoff
        )
        return {"active": active, "recent_executions": recent}
    except Exception:
        return None


def _build_finding(resource: dict, rtype: str, live_override: str = None, live_note: str = None) -> dict:
    """Build a single audit finding dict."""
    classification = live_override or resource.get("classification", "consumer_unknown")
    return {
        "resource": resource.get("path") or resource.get("name") or resource.get("agent_name"),
        "type": rtype,
        "classification": classification,
        "manifest_classification": resource.get("classification"),
        "notes": resource.get("notes", ""),
        "live_note": live_note or "",
    }


@app.post("/consumer_audit")
def consumer_audit(payload: dict = {}):
    """
    Reads consumer_manifest.json, augments endpoint/agent entries with live n8n
    workflow state, and returns all findings sorted by severity (orphaned first).
    """
    # Load manifest
    try:
        with open(_CONSUMER_MANIFEST_PATH) as f:
            manifest = _json.load(f)
    except Exception as e:
        return JSONResponse({"error": f"Could not load manifest: {e}"}, status_code=500)

    env = _read_env_simple()
    n8n_key = env.get("N8N_API_KEY", "")

    findings = []

    # --- Endpoints ---
    for ep in manifest.get("endpoints", []):
        caller_type = ep.get("caller_type")
        caller_ids = ep.get("caller_ids", [])
        manifest_class = ep.get("classification")
        live_override = None
        live_note = None

        if caller_type == "n8n_workflow" and caller_ids:
            statuses = []
            for wf_id in caller_ids:
                s = _n8n_workflow_status(wf_id, n8n_key)
                if s:
                    statuses.append(s)

            if statuses:
                all_active = all(s["active"] for s in statuses)
                total_recent = sum(s["recent_executions"] for s in statuses)
                if not all_active:
                    live_override = "partial"
                    live_note = f"Caller workflow(s) inactive in n8n. Recent executions (14d): {total_recent}."
                elif total_recent == 0:
                    live_override = "partial"
                    live_note = f"Caller workflow active but 0 executions in last 14 days."
                else:
                    live_note = f"Caller workflow active. Recent executions (14d): {total_recent}."
            else:
                live_note = "n8n status check failed or N8N_API_KEY missing."

        findings.append(_build_finding(ep, "endpoint", live_override, live_note))

    # --- Tables ---
    for tbl in manifest.get("tables", []):
        findings.append(_build_finding(tbl, "table"))

    # --- Agents ---
    for agent in manifest.get("agents", []):
        manifest_class = agent.get("classification")
        live_override = None
        live_note = None

        # Check agent's n8n workflow if it has one
        # Agent status comes from manifest (already reflects agent_registry)
        wf_id = None  # agents don't store workflow_id in manifest — skip live n8n check
        # Instead surface status from manifest notes
        if agent.get("status") == "paused":
            live_note = "Agent is paused in agent_registry."
        elif agent.get("status") == "active":
            # Check consumer_automated flag
            if not agent.get("consumer_automated", False):
                live_note = "Consumer is manual (Bill). Loop does not close automatically."
            else:
                live_note = "Consumer is automated."

        findings.append(_build_finding(agent, "agent", live_override, live_note))

    # Sort by severity: orphaned → consumer_unknown → partial → wired
    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f["classification"], 99))

    # Summary counts
    counts = {"wired": 0, "partial": 0, "orphaned": 0, "consumer_unknown": 0}
    for f in findings:
        c = f["classification"]
        counts[c] = counts.get(c, 0) + 1

    return JSONResponse({
        "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest_path": _CONSUMER_MANIFEST_PATH,
        "summary": counts,
        "total": len(findings),
        "findings": findings,
    })


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9100, log_level="warning", access_log=False)
