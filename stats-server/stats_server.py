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


@app.post("/inject_context_v2")
def inject_context_v2(payload: dict = {}):
    """Intent-expanded context injection with tiered memory architecture (v2.1).
    Tiers: episodic (session_memory), semantic (lessons_learned, error_patterns,
    reference_material, research_findings). Housekeeping tasks skip retrieval.
    Staleness penalty on lessons (exempt if metadata.permanent=true). 2000-token cap.
    """
    task_type   = payload.get("task_type", "general")
    task_id     = payload.get("task_id", "")
    description = payload.get("description", "")

    # --- Routing: housekeeping tasks skip retrieval entirely ---
    HOUSEKEEPING_TYPES = {"housekeeping", "status_check", "heartbeat", "ping"}
    if task_type in HOUSEKEEPING_TYPES and len(description) < 50:
        return JSONResponse({
            "task_id": task_id, "task_type": task_type, "description": description,
            "context_block": "", "lesson_count": 0, "lesson_ids": [], "lesson_contents": [],
            "expansion_phrases": [], "token_estimate": 0,
            "queries": {"skipped": True, "reason": "housekeeping task type"},
        })

    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    sb_url  = env.get("SUPABASE_URL", "")
    sb_key  = env.get("SUPABASE_SERVICE_KEY", "")

    # --- Haiku intent expansion ---
    expansion_phrases = []
    if api_key:
        expansion_phrases = _expand_intent_with_haiku(task_type, description, api_key)
    if not expansion_phrases:
        fallback_q = f"{task_type} {description}".strip() or "general"
        expansion_phrases = [fallback_q]

    # --- Query lessons_learned with metadata (for staleness penalty) ---
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
    proc = subprocess.run(
        ["/home/thompsman/aadp/mcp-server/venv/bin/python", "-c", lessons_script,
         _json.dumps({"collection": "lessons_learned", "phrases": expansion_phrases,
                      "n_results": 4, "threshold": 1.4})],
        capture_output=True, text=True, timeout=30
    )
    lessons = []
    if proc.returncode == 0:
        try:
            lessons = _json.loads(proc.stdout)
        except Exception:
            pass
    lessons = lessons[:5]

    # Apply staleness penalty: +0.05/week beyond 4 weeks; skip if permanent=true in metadata
    now = datetime.utcnow()
    for r in lessons:
        meta = r.get("metadata") or {}
        if meta.get("permanent", False):
            continue
        date_str = meta.get("date", "")
        if date_str:
            try:
                lesson_date = datetime.strptime(date_str[:10], "%Y-%m-%d")
                age_weeks = (now - lesson_date).days / 7
                if age_weeks > 4:
                    r["distance"] = r["distance"] + 0.05 * (age_weeks - 4)
            except Exception:
                pass
    lessons = sorted(lessons, key=lambda x: x["distance"])[:5]

    # --- Single query helper (no metadata needed for other collections) ---
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

    q_errors    = f"failure errors bugs {task_type}"
    q_patterns  = f"AADP architecture patterns {task_type} workflow design"
    q_session   = f"{task_type} {description}".strip() or "general"
    q_research  = f"{task_type} {description}".strip() or "general"

    errors   = _single_query("error_patterns",    q_errors,   n_results=2, threshold=1.2)
    patterns = _single_query("reference_material", q_patterns, n_results=2, threshold=1.2)
    episodic = _single_query("session_memory",     q_session,  n_results=2, threshold=1.3)
    research = _single_query("research_findings",  q_research, n_results=2, threshold=1.1)

    # --- Dedup across all five collections ---
    seen = set()
    def _dedup(items):
        out = []
        for r in items:
            if r["id"] not in seen:
                seen.add(r["id"])
                out.append(r)
        return out

    all_lessons  = _dedup(lessons)
    all_errors   = _dedup(errors)
    all_patterns = _dedup(patterns)
    all_episodic = _dedup(episodic)
    all_research = _dedup(research)
    total = len(all_lessons) + len(all_errors) + len(all_patterns) + len(all_episodic) + len(all_research)

    # --- Assemble sections (lessons → errors → patterns → episodic → research) ---
    # Research is last so it's trimmed first if budget is exceeded.
    header = f"## PRE-LOADED CONTEXT\n*Injected by lesson_injector v2.1 — task_type: {task_type}, id: {task_id}*\n\n"
    sections = []
    if all_lessons:
        s = "### Relevant Lessons\n"
        for r in all_lessons:
            s += f"**[{r['id']}]** dist:{r['distance']:.2f}\n{r['content']}\n\n"
        sections.append(s)
    if all_errors:
        s = "### Known Failure Modes\n"
        for r in all_errors:
            s += f"**[{r['id']}]** dist:{r['distance']:.2f}\n{r['content']}\n\n"
        sections.append(s)
    if all_patterns:
        s = "### Architecture Patterns\n"
        for r in all_patterns:
            s += f"**[{r['id']}]** dist:{r['distance']:.2f}\n{r['content']}\n\n"
        sections.append(s)
    if all_episodic:
        s = "### Prior Session Context\n"
        for r in all_episodic:
            s += f"**[{r['id']}]** dist:{r['distance']:.2f}\n{r['content'][:400]}\n\n"
        sections.append(s)
    if all_research:
        s = "### Relevant Research\n"
        for r in all_research:
            s += f"**[{r['id']}]** dist:{r['distance']:.2f}\n{r['content'][:300]}\n\n"
        sections.append(s)
    if not sections:
        sections = ["*No matching context found.*\n\n"]

    # --- Token budget: soft cap at 2000 tokens (approx chars//4), trim sections from bottom ---
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

    lesson_ids      = [r["id"] for r in all_lessons]
    lesson_contents = [r["content"] for r in all_lessons]

    # --- Track lessons_applied (same RPC as v1) ---
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
        if lesson_contents:
            try:
                req = urllib.request.Request(
                    f"{sb_url}/rest/v1/rpc/increment_lessons_applied",
                    data=_json.dumps({"lesson_contents": lesson_contents}).encode(), headers=headers
                )
                urllib.request.urlopen(req, timeout=8).read()
            except Exception:
                pass

    return JSONResponse({
        "task_id":           task_id,
        "task_type":         task_type,
        "description":       description,
        "context_block":     block,
        "lesson_count":      total,
        "lesson_ids":        lesson_ids,
        "lesson_contents":   lesson_contents,
        "expansion_phrases": expansion_phrases,
        "token_estimate":    token_estimate,
        "trimmed":           trimmed,
        "queries": {
            "expanded":    expansion_phrases,
            "q_errors":    q_errors,
            "q_patterns":  q_patterns,
            "q_session":   q_session,
            "q_research":  q_research,
        }
    })


# ---------------------------------------------------------------------------
# inject_context_v3 — task-type routing + retrieval-vs-reasoning signal
# ---------------------------------------------------------------------------

# Which collections to query per task type (ordered by priority)
_V3_TASK_ROUTING = {
    "agent_build":      ["lessons_learned", "error_patterns", "reference_material", "session_memory", "research_findings"],
    "research_cycle":   ["research_findings", "lessons_learned", "reference_material", "session_memory"],
    "explore":          ["lessons_learned", "session_memory", "research_findings"],
    "self_diagnostic":  ["self_diagnostics", "error_patterns", "lessons_learned"],
    "directive":        ["lessons_learned", "error_patterns", "reference_material", "session_memory"],
    "gh_weekly_search": ["research_findings"],
    "gh_report":        ["session_memory", "lessons_learned"],
    "gh_task":          ["lessons_learned", "reference_material"],
    "agent_control":    ["lessons_learned", "error_patterns"],
    "agent_test":       ["lessons_learned", "error_patterns", "reference_material"],
}
_V3_DEFAULT_COLLECTIONS = ["lessons_learned", "error_patterns", "reference_material", "session_memory", "research_findings"]

# Fallback descriptions when task has no description — widens Haiku query expansion
# beyond generic phrases so more of the 155-lesson corpus gets retrieved over time.
_V3_DEFAULT_DESCRIPTIONS = {
    "explore":         "investigate debug diagnose system health n8n workflow memory stores agent evaluation session close architecture decisions",
    "agent_build":     "build n8n workflow webhook trigger agent evaluate promote sandbox architecture n8n gotchas error handling",
    "research_cycle":  "research academic papers ChromaDB findings lessons knowledge gap memory architecture agent design",
    "self_diagnostic": "diagnose health probe stuck tasks memory sync lesson utilization zero_applied ChromaDB Supabase",
    "directive":       "implement task n8n workflow Supabase agent build debug fix architecture",
    "agent_test":      "test agent execution n8n workflow sandbox evaluate promote output experimental",
    "agent_control":   "activate deactivate pause n8n workflow agent status registry",
}

# Per-collection query params: (n_results, threshold)
_V3_COLLECTION_PARAMS = {
    "lessons_learned":    (8, 1.4),   # Increased from 5: wider retrieval = more zero_applied lessons surfaced
    "error_patterns":     (2, 1.2),
    "reference_material": (2, 1.2),
    "session_memory":     (2, 1.3),
    "research_findings":  (2, 1.1),
    "self_diagnostics":   (3, 1.2),
}

# Section header labels per collection
_V3_SECTION_LABELS = {
    "lessons_learned":    "### Relevant Lessons",
    "error_patterns":     "### Known Failure Modes",
    "reference_material": "### Architecture Patterns",
    "session_memory":     "### Prior Session Context",
    "research_findings":  "### Relevant Research",
    "self_diagnostics":   "### Diagnostic Procedures",
}

# Content truncation per collection (chars)
_V3_CONTENT_TRUNC = {
    "session_memory":     400,
    "research_findings":  300,
    "self_diagnostics":   500,
}


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
        "Write a 2-3 paragraph summary (~150 words) covering:\n"
        "1. What the article is about and its main claim\n"
        "2. The key pattern or technique it describes\n"
        "3. Why it might matter for a Reflexion-style agentic system with ChromaDB memory\n"
        "No bullet points. Be concise."
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
            "workflow_id": "gzCSocUFNxTGIzSD",
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


@app.post("/run_context_research")
def run_context_research(payload: dict = {}):
    """Context engineering research agent. Runs hardcoded searches, summarizes with Haiku,
    writes results to research_articles. Called by n8n webhook trigger."""
    import uuid as _uuid
    env = _read_env_simple()
    api_key = env.get("ANTHROPIC_API_KEY", "")
    PER_RUN_CAP = 20

    # HN + arXiv queries
    QUERIES = [
        "autonomous agent platform persistent memory",
        "agent dashboard human in the loop",
        "lessons-learned vector memory architecture",
        "n8n LLM agent orchestration",
        "Reflexion ExpeL agent system production",
    ]
    # Per-source configs — tags chosen to match agent/memory/orchestration content specifically
    DEVTO_TAGS    = ["agents", "n8n", "llmops", "rag", "claude"]
    MEDIUM_TAGS   = ["ai", "machine-learning", "agents", "llm"]
    LOBSTERS_TAGS = ["ai", "ml", "programming"]
    GITHUB_QUERIES = [
        "autonomous agent memory llm",
        "llm orchestration dashboard",
        "agent evaluation framework",
        "human in the loop llm agent",
    ]
    # Sources that carry rich content and don't need a page fetch
    SKIP_FETCH_SOURCES = {"arXiv", "GitHub"}
    # Max candidates from any single source before global cap — prevents one source dominating
    PER_SOURCE_CAP = 5

    agent_run_id = str(_uuid.uuid4())

    # Phase 1: collect candidates from all sources
    seen_in_batch = set()
    candidates = []  # list of (item, query)

    for query in QUERIES:
        for item in _fetch_hn(query, max_results=5) + _fetch_arxiv(query, max_results=5):
            url = item.get("url", "")
            title = item.get("title", "")
            if url and title and url not in seen_in_batch:
                seen_in_batch.add(url)
                candidates.append((item, query))

    for item in _fetch_devto(DEVTO_TAGS, max_per_tag=3):
        url = item.get("url", "")
        title = item.get("title", "")
        if url and title and url not in seen_in_batch:
            seen_in_batch.add(url)
            candidates.append((item, item.get("topic", "devto")))

    for item in _fetch_medium(MEDIUM_TAGS, max_per_tag=3):
        url = item.get("url", "")
        title = item.get("title", "")
        if url and title and url not in seen_in_batch:
            seen_in_batch.add(url)
            candidates.append((item, item.get("topic", "medium")))

    for item in _fetch_github(GITHUB_QUERIES, max_per_query=3):
        url = item.get("url", "")
        title = item.get("title", "")
        if url and title and url not in seen_in_batch:
            seen_in_batch.add(url)
            candidates.append((item, item.get("topic", "github")))

    for item in _fetch_lobsters(LOBSTERS_TAGS, max_per_tag=3):
        url = item.get("url", "")
        title = item.get("title", "")
        if url and title and url not in seen_in_batch:
            seen_in_batch.add(url)
            candidates.append((item, item.get("topic", "lobsters")))

    # Phase 2: batch dedup against existing research_articles
    try:
        existing_rows = _sb_get(env, "research_articles?select=url&limit=2000")
        existing_urls = {row["url"] for row in existing_rows}
    except Exception:
        existing_urls = set()

    fresh = [(item, q) for item, q in candidates if item.get("url") not in existing_urls]
    skipped_dupe = len(candidates) - len(fresh)

    # Rebalance: limit each source to PER_SOURCE_CAP before applying global cap
    _src_counts: dict = {}
    rebalanced = []
    for item, q in fresh:
        src = item.get("source", "unknown")
        if _src_counts.get(src, 0) < PER_SOURCE_CAP:
            rebalanced.append((item, q))
            _src_counts[src] = _src_counts.get(src, 0) + 1
    fresh = rebalanced

    capped = max(0, len(fresh) - PER_RUN_CAP)

    # Phase 3: summarize and insert up to cap
    inserted = 0
    errors_logged = 0

    for item, query in fresh[:PER_RUN_CAP]:
        url = item.get("url", "")
        title = item.get("title", "")

        raw_content = item.get("summary", title)
        if item.get("source") not in SKIP_FETCH_SOURCES:
            page_text = _fetch_page_text(url)
            if page_text:
                raw_content = page_text
            else:
                _log_research_error(env, url, "page fetch returned empty — skipped")
                errors_logged += 1
                continue

        summary = _summarize_article_haiku(title, url, raw_content, api_key)
        if not summary:
            summary = raw_content[:500]

        source = item.get("source", "")
        try:
            source = urllib.parse.urlparse(url).netloc.replace("www.", "") or source
        except Exception:
            pass

        try:
            _sb_upsert(env, "research_articles", {
                "agent_run_id": agent_run_id,
                "title": title,
                "url": url,
                "source": source,
                "summary": summary,
                "query_used": query,
                "provenance": "context_engineering_research_agent",
            })
            inserted += 1
        except Exception as e:
            _log_research_error(env, url, str(e))
            errors_logged += 1

    return JSONResponse({
        "agent_run_id": agent_run_id,
        "inserted": inserted,
        "skipped_dupe": skipped_dupe,
        "capped": capped,
        "errors_logged": errors_logged,
    })


@app.post("/test_research_error_path")
def test_research_error_path(payload: dict = {}):
    """Verify error logging path works: tries to fetch an unreachable URL, logs the failure."""
    env = _read_env_simple()
    bad_url = payload.get("url", "http://definitely-does-not-exist.invalid/test-article")
    page_text = _fetch_page_text(bad_url)
    if not page_text:
        _log_research_error(env, bad_url, "page fetch returned empty — test error injection")
        return JSONResponse({"logged": True, "url": bad_url})
    return JSONResponse({"logged": False, "note": "page fetch unexpectedly succeeded"})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9100, log_level="warning", access_log=False)
