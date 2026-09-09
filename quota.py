"""
Quota introspection for the agy (Google Antigravity CLI) backend.

Data sources (all verified against public docs / reverse-engineering write-ups):

1. Local Connect RPC (real-time, zero LLM-token cost):
   A running `agy` process (or Antigravity IDE) hosts an HTTPS server on
   127.0.0.1. POST to /exa.language_server_pb.LanguageServerService/GetUserStatus
   returns real-time quota fractions and reset timestamps for the 5-hour
   bucket. The weekly bucket is NOT exposed through this RPC.
   Refs: github.com/skainguyen1412/antigravity-usage,
         dev.to "Preventing Quota Crashes via Antigravity CLI Agent Hooks".

2. Statusline dump (optional, provides the WEEKLY bucket):
   The official statusline feature pipes a JSON payload to a script on every
   agent-state change. The payload contains quota buckets keyed
   "gemini-5h" / "gemini-weekly" / "3p-5h" / "3p-weekly", each with
   remaining_fraction, reset_time, reset_in_seconds.
   Refs: https://antigravity.google/docs/cli/statusline/
   Install statusline_quota_dump.sh (this repo) to keep a fresh dump on disk.

3. Cache file: last successful snapshot, so /status works even when no agy
   process is alive right now (shows data age instead of failing).
"""

import asyncio
import json
import os
import re
import shutil
import ssl
import subprocess
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# 5h bucket aliases to look for in statusline payloads
FIVE_H_KEYS = ("gemini-5h", "3p-5h")
WEEKLY_KEYS = ("gemini-weekly", "3p-weekly")

# Default locations (override dump path at runtime via QUOTA_STATUSLINE_DUMP env)
STATUSLINE_DUMP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".statusline_quota.json"
)
CACHE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".quota_cache.json"
)


def _statusline_dump_candidates() -> List[str]:
    """Dump file candidates: module dir (explicit env) + the standard statusline location."""
    cands = [os.environ.get("QUOTA_STATUSLINE_DUMP", STATUSLINE_DUMP_PATH)]
    cands.append(os.path.expanduser("~/.gemini/antigravity-cli/.statusline_quota.json"))
    seen, out = set(), []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out

_BUYS = None  # reserved for future injection


# ---------------------------------------------------------------- ss parsing

def _list_agy_ports() -> List[int]:
    """Find 127.0.0.1 ports owned by an 'agy' process via ss (root recommended)."""
    ss = shutil.which("ss")
    if not ss:
        return []
    try:
        out = subprocess.run(
            [ss, "-tlnp"], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:
        return []
    ports = set()
    for line in out.splitlines():
        if "agy" not in line:
            continue
        m = re.search(r"127\.0\.0\.1:(\d+)\s", line)
        if m:
            ports.add(int(m.group(1)))
    return sorted(ports)


# ---------------------------------------------------------------- RPC probe

_TLS = ssl._create_unverified_context()


def _post_user_status(port: int, timeout: float = 4.0) -> Optional[Dict[str, Any]]:
    """POST GetUserStatus to one local port. Returns parsed JSON or None."""
    import urllib.request

    url = (
        f"https://127.0.0.1:{port}/exa.language_server_pb."
        "LanguageServerService/GetUserStatus"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(
            {
                "metadata": {
                    "ideName": "antigravity",
                    "extensionName": "antigravity",
                    "locale": "en",
                }
            }
        ).encode(),
        headers={
            "Content-Type": "application/json",
            "Connect-Protocol-Version": "1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout, context=_TLS) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    if "userStatus" in data or _find_key(data, "userStatus") is not None:
        return data
    return None


def probe_local_rpc(timeout: float = 4.0) -> Optional[Dict[str, Any]]:
    """
    Probe the local agy Connect RPC for a userStatus snapshot.
    Returns the parsed JSON dict containing 'userStatus', or None.
    Never raises.
    """
    for port in _list_agy_ports():
        try:
            data = _post_user_status(port, timeout=timeout)
            if data:
                return data
        except Exception:
            continue
    return None


def capture_during_call(duration: float = 60.0, interval: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Run inside a worker thread DURING an agy call. The agy process hosts its
    local RPC only while alive (headless `-p` runs included — verified live:
    quota refreshes on every doRefreshQuota), so we poll for the port inside
    that window and grab a userStatus snapshot. Saves cache on success.
    Fire-and-forget safe: never raises, bounded by `duration`.
    """
    deadline = time.time() + max(5.0, duration)
    while time.time() < deadline:
        for port in _list_agy_ports():
            try:
                data = _post_user_status(port, timeout=3.0)
            except Exception:
                continue
            if data:
                save_cache(data)
                return data
        time.sleep(interval)
    return None


async def probe_and_cache(timeout: float = 15.0) -> Optional[Dict[str, Any]]:
    """Async wrapper: probe in a worker thread and persist a snapshot on success."""
    try:
        data = await asyncio.get_running_loop().run_in_executor(
            None, lambda: probe_local_rpc(timeout=timeout)
        )
    except Exception:
        data = None
    if data:
        save_cache(data)
    return data


async def async_capture_during_call(duration: float = 60.0, interval: float = 2.0) -> Optional[Dict[str, Any]]:
    """Async wrapper around capture_during_call for use inside the bot loop."""
    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: capture_during_call(duration=duration, interval=interval)
        )
    except asyncio.CancelledError:
        return None
    except Exception:
        return None


# ------------------------------------------------------------- extraction

def _find_key(obj: Any, name: str) -> Any:
    """Recursively find the first dict under key `name`."""
    if isinstance(obj, dict):
        if name in obj:
            return obj[name]
        for v in obj.values():
            hit = _find_key(v, name)
            if hit is not None:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = _find_key(v, name)
            if hit is not None:
                return hit
    return None


# Generic path segments that carry no identity info
_GENERIC_NAMES = {
    "userStatus", "cascadeModelConfigData", "clientModelConfigs",
    "quotaInfo", "quotaStatus", "quota", "buckets", "planStatus",
}


def _walk_nodes(obj: Any) -> List[Dict[str, Any]]:
    """Collect every dict that carries quota-ish fields, with identity hints.

    For Antigravity's GetUserStatus payload, quota blocks live inside
    clientModelConfigs[].quotaInfo — the model identity is a SIBLING key
    (modelOrAlias / modelId) of the config dict, so we inherit it as a hint.
    """
    nodes: List[Dict[str, Any]] = []

    def visit(o: Any, names: List[str], hint: Optional[str] = None) -> None:
        if isinstance(o, dict):
            keys = set(o.keys())
            if keys & {
                "remainingFraction",
                "remaining_fraction",
                "resetTime",
                "reset_time",
                "reset_in_seconds",
                "resetInSeconds",
            }:
                nm = list(names)
                if hint:
                    nm.append(hint)
                nodes.append({"names": nm, "node": o})
            # Identity priority: modelId > modelOrAlias > model > displayName.
            # NOTE (verified live): modelOrAlias can be an OBJECT
            # ({"model": "MODEL_PLACEHOLDER_M73"}) while modelId holds the
            # canonical model string — so modelId must be checked first.
            mhint = None
            for k in ("modelId", "modelOrAlias", "model", "displayName", "label"):
                v = o.get(k)
                if isinstance(v, dict):
                    v = v.get("model") or v.get("id") or v.get("name") or v.get("display_name")
                if isinstance(v, str) and v.strip():
                    mhint = v.strip()
                    break
            for k, v in o.items():
                visit(v, names + [str(k)], str(mhint) if mhint else None)
        elif isinstance(o, list):
            for v in o:
                visit(v, names, hint)

    visit(obj, [])
    return nodes


def extract_entries(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize a raw userStatus payload into a flat list:
      {name, remaining (0-100 float or None), reset_time (ISO str or None),
       reset_in_seconds (int or None)}
    Tolerant to camelCase/snake_case and unknown nesting.
    """
    entries: List[Dict[str, Any]] = []
    for item in _walk_nodes(raw):
        node = item["node"]
        names = [n for n in item["names"] if n not in ("quota", "quotaStatus", "buckets")]
        frac = node.get("remainingFraction", node.get("remaining_fraction"))
        used = node.get("usedFraction", node.get("used_fraction"))
        if frac is None and used is not None:
            try:
                frac = 1.0 - float(used)
            except Exception:
                frac = None
        remaining = None
        if frac is not None:
            try:
                f = float(frac)
                if f <= 1.0:
                    f *= 100.0
                remaining = round(f, 1)
            except Exception:
                pass
        reset_time = node.get("resetTime", node.get("reset_time"))
        reset_sec = node.get("reset_in_seconds", node.get("resetInSeconds"))
        if reset_sec is None and reset_time:
            try:
                dt = _parse_iso(reset_time)
                if dt:
                    reset_sec = int((dt - datetime.now(timezone.utc)).total_seconds())
            except Exception:
                pass
        entries.append(
            {
                "name": "/".join(
                    n for n in item["names"]
                    if n not in _GENERIC_NAMES and not re.fullmatch(r"\d+", n)
                ) or "quota",
                "remaining": remaining,
                "reset_time": reset_time,
                "reset_in_seconds": int(reset_sec) if reset_sec is not None else None,
            }
        )
    # dedupe by (name, remaining, reset_time)
    seen = set()
    uniq = []
    for e in entries:
        k = (e["name"], e["remaining"], e["reset_time"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    return uniq


def _parse_iso(s: str) -> Optional[datetime]:
    try:
        s2 = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


# ------------------------------------------------------------- statusline dump

def read_statusline_quota() -> List[Dict[str, Any]]:
    """
    Read the optional statusline dump and return normalized bucket entries
    for the 5h and weekly Gemini buckets (known official schema).
    """
    payload = None
    mtime = None
    for cand in _statusline_dump_candidates():
        try:
            with open(cand, "r", encoding="utf-8") as f:
                payload = json.load(f)
            mtime = os.path.getmtime(cand)
            break
        except Exception:
            continue
    if payload is None:
        return []
    quota = payload.get("quota") or {}
    out = []
    for bucket in list(FIVE_H_KEYS) + list(WEEKLY_KEYS):
        b = quota.get(bucket)
        if not isinstance(b, dict):
            continue
        remaining = None
        if b.get("remaining_fraction") is not None:
            try:
                remaining = round(float(b["remaining_fraction"]) * 100, 1)
            except Exception:
                pass
        out.append(
            {
                "name": bucket,
                "remaining": remaining,
                "reset_time": b.get("reset_time"),
                "reset_in_seconds": b.get("reset_in_seconds"),
                "mtime": mtime,
            }
        )
    return out


# ---------------------------------------------------------------- cache

def save_cache(raw: Dict[str, Any]) -> None:
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "raw": raw}, f)
    except Exception:
        pass


def load_cache() -> Optional[Dict[str, Any]]:
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        if "ts" in d and "raw" in d:
            return d
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- public API

def get_quota(live: bool = True, probe_timeout: float = 4.0) -> Dict[str, Any]:
    """
    Returns:
      {
        "live": bool,            # fresh RPC probe succeeded
        "age_seconds": int|None, # age of the data shown
        "entries": [...],        # 5h-bucket entries (RPC or statusline)
        "weekly": [...],         # weekly buckets (statusline only)
        "reason": str|None,      # why empty (for UI hint)
      }
    """
    now = time.time()
    raw = probe_local_rpc(timeout=probe_timeout) if live else None
    if raw:
        save_cache(raw)
        entries = extract_entries(raw)
        weekly = [e for e in read_statusline_quota() if e["name"] in WEEKLY_KEYS]
        return {"live": True, "age_seconds": 0, "entries": entries, "weekly": weekly, "reason": None}

    # no live agy: fall back to statusline dump (if fresh enough) then cache
    sl = read_statusline_quota()
    five_h_sl = [e for e in sl if e["name"] in FIVE_H_KEYS]
    weekly = [e for e in sl if e["name"] in WEEKLY_KEYS]
    if five_h_sl or weekly:
        age = int(now - max(e["mtime"] for e in sl))
        five = [
            {k: v for k, v in e.items() if k != "mtime"} for e in five_h_sl
        ]
        return {"live": False, "age_seconds": age, "entries": five, "weekly": weekly, "reason": None}

    cached = load_cache()
    if cached:
        entries = extract_entries(cached["raw"])
        weekly = [e for e in read_statusline_quota() if e["name"] in WEEKLY_KEYS]
        return {
            "live": False,
            "age_seconds": int(now - cached["ts"]),
            "entries": entries,
            "weekly": weekly,
            "reason": None,
        }

    return {
        "live": False,
        "age_seconds": None,
        "entries": [],
        "weekly": [],
        "reason": "没有运行中的 agy / Antigravity IDE，且尚无缓存快照",
    }


# ---------------------------------------------------------------- formatting

def _humanize_seconds(sec: Optional[int]) -> str:
    if sec is None or sec <= 0:
        return ""
    h, m = sec // 3600, (sec % 3600) // 60
    if h >= 24:
        return f"{h // 24}d{h % 24}h" if h % 24 else f"{h // 24}d"
    if h > 0:
        return f"{h}h{m:02d}m"
    return f"{m}m"


def _fmt_reset(e: Dict[str, Any]) -> str:
    parts = []
    rt = e.get("reset_time")
    dt = _parse_iso(rt) if rt else None
    if dt:
        local = dt.astimezone()
        parts.append("重置 " + local.strftime("%m-%d %H:%M"))
    rs = e.get("reset_in_seconds")
    if isinstance(rs, int) and rs > 0:
        parts.append(f"{_humanize_seconds(rs)}后")
    return " ".join(parts)


def format_markdown(data: Dict[str, Any]) -> str:
    """Render the quota section for /status (plain text, safe for Telegram)."""
    if data.get("reason"):
        return f"📊 Gemini 额度: 不可用（{data['reason']}）"

    entries = data.get("entries") or []
    weekly = data.get("weekly") or []
    lines = []

    if entries:
        # Group by (remaining, reset_time): Antigravity shares one bucket
        # across the whole Gemini Flash/Pro family — show it as one line.
        groups: Dict[Any, Dict[str, Any]] = {}
        for e in entries:
            key = (e.get("remaining"), e.get("reset_time"))
            g = groups.setdefault(key, {"members": [], "e": e})
            g["members"].append(e["name"])
        lines.append("📊 *模型额度（实测自本机 agy）*")
        for g in groups.values():
            e = g["e"]
            rem = e.get("remaining")
            rem_str = f"{rem:g}%" if isinstance(rem, (int, float)) else "未知"
            tail = _fmt_reset(e)
            m = g["members"]
            label = " / ".join(m[:2]) + (f" 等{len(m)}个模型" if len(m) > 2 else "")
            lines.append(f"• {label}: 剩余 {rem_str}" + (f"（{tail}）" if tail else ""))
    if weekly:
        lines.append("📊 *周窗口额度*")
        for e in weekly[:2]:
            rem = e.get("remaining")
            rem_str = f"{rem:g}%" if isinstance(rem, (int, float)) else "未知"
            tail = _fmt_reset(e)
            lines.append(f"• {e['name']}: 剩余 {rem_str}" + (f"（{tail}）" if tail else ""))

    if not entries and not weekly:
        return "📊 Gemini 额度: 暂无数据"

    if data.get("live"):
        lines.append("（实时读取自本机 agy RPC）")
    else:
        age = data.get("age_seconds")
        age_str = _humanize_seconds(age) + "前" if age else ""
        lines.append(f"（缓存快照{age_str}，下次对话后自动刷新）")
    return "\n".join(lines)


# ---------------------------------------------------------------- self-test

if __name__ == "__main__":
    # Synthetic userStatus payload (structure per GDE write-up)
    fake = {
        "userStatus": {
            "quotaStatus": {
                "buckets": {
                    "gemini": {
                        "remainingFraction": 0.712,
                        "resetTime": "2026-09-09T03:12:00Z",
                    },
                    "claude": {
                        "usedFraction": 0.1,
                        "resetTime": "2026-09-09T01:00:00Z",
                    },
                }
            },
            "email": "test@example.com",
        }
    }
    ent = extract_entries(fake)
    assert ent, "extraction failed"
    names = {e["name"] for e in ent}
    assert any("gemini" in n for n in names), names
    g = next(e for e in ent if "gemini" in e["name"])
    assert abs(g["remaining"] - 71.2) < 0.2, g
    c = next(e for e in ent if "claude" in e["name"])
    assert abs(c["remaining"] - 90.0) < 0.2, c

    # Real GetUserStatus shape: identity is a SIBLING key of quotaInfo
    real = {
        "userStatus": {
            "cascadeModelConfigData": {
                "clientModelConfigs": [
                    {"modelOrAlias": "claude-sonnet-4-6",
                     "quotaInfo": {"remainingFraction": 1, "resetTime": "2026-09-09T05:33:07Z"}},
                    {"modelOrAlias": "gemini-3.8-flash-high",
                     "quotaInfo": {"remainingFraction": 0.8865693, "resetTime": "2026-09-09T03:51:08Z"}},
                    {"modelOrAlias": "gemini-3.7-flash-high",
                     "quotaInfo": {"remainingFraction": 0.8865693, "resetTime": "2026-09-09T03:51:08Z"}},
                ]
            }
        }
    }
    ent2 = extract_entries(real)
    names2 = {e["name"] for e in ent2}
    assert "claude-sonnet-4-6" in names2, names2
    assert "gemini-3.8-flash-high" in names2, names2
    gem = next(e for e in ent2 if e["name"] == "gemini-3.8-flash-high")
    assert abs(gem["remaining"] - 88.7) < 0.2, gem
    print("extract_entries OK:", json.dumps(ent2, ensure_ascii=False))

    data = get_quota(live=False)
    print("no-live path:", json.dumps({k: v for k, v in data.items() if k != "raw"}, ensure_ascii=False))
    print(format_markdown(data))

    # statusline dump path
    os.environ["QUOTA_STATUSLINE_DUMP"] = "/tmp/_sl_test.json"
    with open("/tmp/_sl_test.json", "w") as f:
        json.dump(
            {
                "quota": {
                    "gemini-5h": {"remaining_fraction": 0.5, "reset_time": "2026-09-09T04:00:00Z", "reset_in_seconds": 3600},
                    "gemini-weekly": {"remaining_fraction": 0.9378, "reset_time": "2026-09-12T07:50:32Z", "reset_in_seconds": 300000},
                }
            },
            f,
        )
    data2 = get_quota(live=False)
    assert data2["entries"], "statusline 5h missing"
    assert data2["weekly"], "statusline weekly missing"
    print(format_markdown(data2))
    print("ALL SELF-TESTS PASSED")
