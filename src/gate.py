     1|"""
     2|TRCM Gate v4.2 — 纯拦截 + 度量日志 + 提醒措辞。
     3|
     4|pass_gate(text, station=None) → GateResult
     5|- 信号检查: 编码行？面板？
     6|- 轨道检查: 输出字段匹配当前站台 schema？
     7|- 拦截日志: 拦截日志写入配置目录（默认 ~/.agent-governance/logs/）
     8|- 提醒措辞: "提醒"取代"惩罚"——拦截消息是给Agent下轮的上下文注入
     9|
    10|get_interception_stats() → {total, by_reason, by_station, recent}
    11|"""
    12|import re
    13|import os
    14|from dataclasses import dataclass, field
    15|from typing import Any, Dict, Optional, List
    16|
    17|# ── 从 rules.yaml 加载 R0 规则 ──
    18|_FALLBACK_PATTERN = r'###\s*任务编码[：:].*→?\s*M(?P<m>\d)'
    19|_FALLBACK_FIX = "### 任务编码：R?-C? → M? | tag:<标签> | gate:Y/N"
    20|
    21|def _normalize_r0_pattern(p: str) -> str:
    22|    if "?P<m>" in p:
    23|        return p
    24|    p2 = re.sub(r'M\\d', r'M(?P<m>\\d)', p, count=1)
    25|    if "?P<m>" not in p2:
    26|        raise ValueError("R0 pattern must contain M\\d or (?P<m>...)")
    27|    return p2
    28|
    29|def _load_r0_rule():
    30|    rules_path = os.environ.get("AG_RULES_PATH", os.path.expanduser("~/.agent-governance/rules.yaml"))
    31|    try:
    32|        import yaml
    33|        with open(rules_path, 'r', encoding='utf-8') as f:
    34|            data = yaml.safe_load(f)
    35|        r0 = (data or {}).get("rules", {}).get("R0", {})
    36|        pattern = _normalize_r0_pattern(r0.get("pattern", _FALLBACK_PATTERN))
    37|        re.compile(pattern)
    38|        return pattern
    39|    except Exception:
    40|        return _FALLBACK_PATTERN
    41|
    42|_R0_PATTERN = _load_r0_rule()
    43|M_RE = re.compile(_R0_PATTERN, re.UNICODE)
    44|
    45|# ── 站台 schema 缓存 ──
    46|_SCHEMAS_CACHE: Optional[Dict] = None
    47|
    48|def _load_schemas():
    49|    global _SCHEMAS_CACHE
    50|    if _SCHEMAS_CACHE is not None:
    51|        return _SCHEMAS_CACHE
    52|    import yaml
    53|    schemas_path = os.environ.get("AG_SCHEMAS_PATH", os.path.expanduser("~/.agent-governance/station-schemas.yaml"))
    54|    with open(schemas_path, 'r', encoding='utf-8') as f:
    55|        _SCHEMAS_CACHE = yaml.safe_load(f)
    56|    return _SCHEMAS_CACHE
    57|
    58|
    59|# ── 信号层：编码行 + 面板 ──
    60|
    61|def has_panel(text: str) -> bool:
    62|    lines = text.split('\n')
    63|    has_top = has_bottom = has_content = False
    64|    for line in lines:
    65|        if '┌' in line and '┐' in line:
    66|            has_top = True
    67|        elif '└' in line and '┘' in line:
    68|            has_bottom = True
    69|        elif '│' in line and line.strip().startswith('│'):
    70|            has_content = True
    71|    return has_top and has_bottom and has_content
    72|
    73|
    74|def extract_m(text: str) -> int | None:
    75|    first_line = text.strip().split('\n')[0]
    76|    m = M_RE.search(first_line)
    77|    if m:
    78|        try:
    79|            return int(m.group("m"))
    80|        except (IndexError, ValueError):
    81|            return None
    82|    return None
    83|
    84|
    85|def has_encoding(text: str) -> bool:
    86|    return extract_m(text) is not None
    87|
    88|
    89|# ── 轨道层：站台 schema 检查 ──
    90|
    91|def check_track(station: str, text: str) -> Dict[str, Any]:
    92|    """
    93|    检查输出是否在当前站台轨道上。
    94|    返回 {"ok": bool, "station": str, "missing": [...], "violations": [...]}
    95|    """
    96|    schemas = _load_schemas()
    97|    st = schemas.get("stations", {}).get(station)
    98|
    99|    if not st:
   100|        return {"ok": False, "station": station, "error": f"未知站台: {station}",
   101|                "missing": [], "violations": []}
   102|
   103|    missing: List[str] = []
   104|    violations: List[str] = []
   105|
   106|    for item in st.get("required_fields", []):
   107|        if item["field"] not in text:
   108|            missing.append(item["field"])
   109|
   110|    for item in st.get("required_patterns", []):
   111|        if not re.search(item["pattern"], text):
   112|            missing.append(item["pattern"])
   113|
   114|    for item in st.get("forbidden_patterns", []):
   115|        if re.search(item["pattern"], text):
   116|            violations.append(item["pattern"])
   117|
   118|    return {
   119|        "ok": len(missing) == 0 and len(violations) == 0,
   120|        "station": station,
   121|        "state": st.get("state", "?"),
   122|        "missing": missing,
   123|        "violations": violations,
   124|    }
   125|
   126|
   127|# ── 拦截消息 ──
   128|
   129|def gate_message(reason: str) -> str:
   130|    """生成拦截消息。v4.2：提醒语气取代惩罚语气。"""
   131|    messages = {
   132|        "missing-code":   '[信] 格式提醒 — 你的回复缺少编码行。每条回复的第一行需要是：### 任务编码：R?-C? → M? | tag:xxx | 信:Y/N',
   133|        "bad-format":     "[信] 格式提醒 — 编码格式有误，请检查。",
   134|        "missing-panel":  "[信] 格式提醒 — M1+ 任务需要在编码行后紧跟派发面板。",
   135|        "empty-output":   "[信] 格式提醒 — 回复为空，请重新生成。",
   136|    }
   137|    if reason.startswith("track:"):
   138|        return f"[信] 内容提醒 — 输出缺少当前站台需要的字段（{reason[6:]}）"
   139|    return messages.get(reason, f"[信] 提醒 — {reason}")
   140|
   141|
   142|# ── 拦截日志（度量体系） ──
   143|
   144|import json as _json
   145|import time as _time
   146|from datetime import datetime as _dt
   147|
   148|_LOG_DIR = os.environ.get("AG_LOG_DIR", os.path.expanduser("~/.agent-governance/logs"))
   149|_LOG_FILE = os.path.join(_LOG_DIR, "gate-interceptions.jsonl")
   150|
   151|def _log_interception(reason: str, station: Optional[str], text_snippet: str):
   152|    """记录每次拦截。一行JSON。"""
   153|    os.makedirs(_LOG_DIR, exist_ok=True)
   154|    entry = {
   155|        "ts": _dt.now().isoformat(),
   156|        "reason": reason,
   157|        "station": station or "free",
   158|        "snippet": text_snippet[:100],
   159|    }
   160|    try:
   161|        with open(_LOG_FILE, "a", encoding="utf-8") as f:
   162|            f.write(_json.dumps(entry, ensure_ascii=False) + "\n")
   163|    except Exception:
   164|        pass  # 日志写失败不阻塞拦截
   165|
   166|
   167|def get_interception_stats() -> Dict[str, Any]:
   168|    """读取拦截统计。返回 {total, by_reason, by_station, recent}"""
   169|    if not os.path.exists(_LOG_FILE):
   170|        return {"total": 0, "by_reason": {}, "by_station": {}, "recent": []}
   171|
   172|    by_reason: Dict[str, int] = {}
   173|    by_station: Dict[str, int] = {}
   174|    recent: List[Dict] = []
   175|    total = 0
   176|
   177|    try:
   178|        with open(_LOG_FILE, "r", encoding="utf-8") as f:
   179|            for line in f:
   180|                line = line.strip()
   181|                if not line:
   182|                    continue
   183|                try:
   184|                    e = _json.loads(line)
   185|                except Exception:
   186|                    continue
   187|                total += 1
   188|                r = e.get("reason", "?")
   189|                s = e.get("station", "?")
   190|                by_reason[r] = by_reason.get(r, 0) + 1
   191|                by_station[s] = by_station.get(s, 0) + 1
   192|                recent.append(e)
   193|    except Exception:
   194|        pass
   195|
   196|    return {
   197|        "total": total,
   198|        "by_reason": dict(sorted(by_reason.items(), key=lambda x: -x[1])),
   199|        "by_station": dict(sorted(by_station.items(), key=lambda x: -x[1])),
   200|        "recent": recent[-10:],
   201|    }
   202|
   203|
   204|# ═══════════════════════════════════════════
   205|# GateResult + pass_gate v4.1 — 信号+轨道双检
   206|# ═══════════════════════════════════════════
   207|
   208|@dataclass
   209|class GateResult:
   210|    """门检查结果。兼容 bool() 和 tuple 解包。"""
   211|    ok: bool
   212|    reason: str = "ok"
   213|    text: str = ""
   214|    meta: Dict[str, Any] = field(default_factory=dict)
   215|    # v4 兼容字段 — 始终为 False
   216|    repaired: bool = False
   217|    auto_trigger: bool = False
   218|    forced: bool = False
   219|    trigger_reason: str = ""
   220|
   221|    def __bool__(self):
   222|        return self.ok
   223|
   224|    def __iter__(self):
   225|        return iter((self.ok, self.reason))
   226|
   227|
   228|def pass_gate(text: str, auto_trigger_count: int = 0, station: Optional[str] = None):
   229|    """
   230|    TRCM Gate v4.1 — 信号+轨道双检，零容忍。
   231|
   232|    参数:
   233|      text: Agent 回复内容
   234|      auto_trigger_count: 保留以兼容旧 patch（实际不使用）
   235|      station: 流水线站台名（describer/rc-definer/designers/pipeline-reviewer/executor）
   236|               为 None 时只检查信号，不检查轨道（自由模式）
   237|
   238|    返回 GateResult:
   239|      ok=True:  信号合规 + 轨道合规（如有）
   240|      ok=False: 信号或轨道任一违规 → 拦截
   241|    """
   242|    # ── 信号层 ──
   243|    if not text or not text.strip():
   244|        _log_interception("empty-output", station, "")
   245|        return GateResult(ok=False, reason="empty-output", text="")
   246|
   247|    m = extract_m(text)
   248|
   249|    if m is None:
   250|        _log_interception("missing-code", station, text[:100])
   251|        return GateResult(ok=False, reason="missing-code", text=text[:200])
   252|
   253|    if m == 0:
   254|        signal_ok = True
   255|    elif has_panel(text):
   256|        signal_ok = True
   257|    else:
   258|        _log_interception("missing-panel", station, text[:100])
   259|        return GateResult(ok=False, reason="missing-panel", text=text[:200], meta={"m": m})
   260|
   261|    # ── 轨道层（仅当 station 指定时） ──
   262|    if station:
   263|        track = check_track(station, text)
   264|        if not track["ok"]:
   265|            parts = []
   266|            if track.get("missing"):
   267|                parts.append(f"缺失={track['missing']}")
   268|            if track.get("violations"):
   269|                parts.append(f"违规={track['violations']}")
   270|            reason = "track:" + " + ".join(parts)
   271|            _log_interception(reason[:80], station, text[:100])
   272|            return GateResult(
   273|                ok=False, reason=reason[:200], text=text[:200],
   274|                meta={**track, "m": m}
   275|            )
   276|
   277|    return GateResult(ok=True, reason="ok-m0" if m == 0 else "ok",
   278|                      text=text, meta={"m": m})
   279|
   280|
   281|# ── 自测 ──
   282|if __name__ == "__main__":
   283|    import sys
   284|
   285|    print("=== 信号测试 ===")
   286|    for label, t in [
   287|        ("缺编码", "好的我来处理。"),
   288|        ("M0通过", "### 任务编码：R0-C0 → M0 | tag:t | 信:N\n好的。"),
   289|        ("M1缺面板", "### 任务编码：R1-C2 → M1 | tag:t | 信:N\n无面板..."),
   290|        ("M1有面板", "### 任务编码：R1-C2 → M1 | tag:t | 信:N\n┌──┐\n│ p │\n└──┘\n正文"),
   291|    ]:
   292|        r = pass_gate(t)
   293|        print(f"  {label}: ok={r.ok}, reason={r.reason}")
   294|
   295|    print("\n=== 轨道测试（station=describer）===")
   296|    desc_ok = "### 任务编码：R1-C1 → M1 | tag:t | 信:N\n┌──┐\n│ p │\n└──┘\n🚂 区间1: DESCRIBED\nuser_verbatim: test\n核心意图: test\n验收标准: test"
   297|    desc_bad = "### 任务编码：R1-C1 → M1 | tag:t | 信:N\n┌──┐\n│ p │\n└──┘\n只是一段随便的文字没有任何站台标记..."
   298|    print(f"  合规: ok={pass_gate(desc_ok, station='describer').ok}")
   299|    r = pass_gate(desc_bad, station='describer')
   300|    print(f"  偏离: ok={r.ok}, reason={r.reason}")
   301|
   302|    print("\n=== 自由模式（station=None）===")
   303|    r = pass_gate(desc_bad, station=None)
   304|    print(f"  无轨道检查: ok={r.ok} (只查信号)")
   305|