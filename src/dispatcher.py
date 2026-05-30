import os
     1|#!/usr/bin/env python3
     2|"""
     3|TRCM Dispatcher — 全自动覆盖引擎
     4|消费4个cronjob的输出,按规则自动编码/建议圆桌/告警/写日志。
     5|不靠Agent自觉。不靠用户手动触发。
     6|"""
     7|
     8|import json, os, sys
     9|from datetime import datetime
    10|from pathlib import Path
    11|
    12|RULES_FILE = Path(os.environ.get("AG_RULES_FILE", Path.home() / ".agent-governance/rules.yaml"))
    13|EVENTS_LOG = Path(os.environ.get("AG_EVENTS_LOG", Path.home() / ".agent-governance/logs/events.jsonl"))
    14|CRON_OUTPUTS = {
    15|    "compliance_scan": Path(os.environ.get("AG_COMPLIANCE_SCAN", Path.home() / ".agent-governance/logs/compliance_scan_latest.json")),
    16|    "config_hash": Path(os.environ.get("AG_CONFIG_HASH", Path.home() / ".agent-governance/logs/config_hash_latest.json")),
    17|    "trcm_audit": Path(os.environ.get("AG_TRCM_AUDIT", Path.home() / ".agent-governance/logs/trcm_audit_latest.json")),
    18|    "friend_log": Path(os.environ.get("AG_FRIEND_LOG", Path.home() / ".agent-governance/logs/friend_log_latest.json")),
    19|}
    20|
    21|def load_json(path):
    22|    if path.exists():
    23|        try:
    24|            return json.loads(path.read_text())
    25|        except: pass
    26|    return {}
    27|
    28|def check_conditions(data):
    29|    actions = []
    30|    cs = data.get("compliance_scan", {})
    31|    ch = data.get("config_hash", {})
    32|    ta = data.get("trcm_audit", {})
    33|    fl = data.get("friend_log", {})
    34|
    35|    enc_rate = cs.get("encoding_rate", 100)
    36|    enc_dropped = cs.get("encoding_rate_dropped_3_days", False)
    37|    new_p0 = cs.get("new_p0_failures", [])
    38|    config_changed = ch.get("changed", False)
    39|    config_authorized = ch.get("authorized", True)
    40|    anomaly_count = ta.get("anomaly_count", 0)
    41|    friend_enc = fl.get("encoding_rate", 100)
    42|    block_rate = cs.get("approvals_block_rate", 0)
    43|
    44|    # 自动编码触发
    45|    if enc_rate < 20:
    46|        actions.append({"type":"encode","target":"recent_sessions","reason":f"编码率{enc_rate}%<20%","priority":"P1"})
    47|    if friend_enc == 0:
    48|        actions.append({"type":"encode","target":"friend_sessions","reason":"Friend网关编码率0%","priority":"P0"})
    49|
    50|    # 自动建议圆桌
    51|    if enc_dropped:
    52|        actions.append({"type":"suggest_roundtable","topic":"编码率连续3天下降原因分析","priority":"P1"})
    53|    if config_changed and not config_authorized:
    54|        actions.append({"type":"suggest_roundtable","topic":"配置漂移审查","priority":"P0"})
    55|    if new_p0:
    56|        actions.append({"type":"suggest_roundtable","topic":f"新P0违规:{new_p0[0] if new_p0 else '未知'}","priority":"P0"})
    57|    if anomaly_count > 3:
    58|        actions.append({"type":"suggest_roundtable","topic":"TRCM异常聚类分析","priority":"P1"})
    59|
    60|    # 告警
    61|    if config_changed and not config_authorized:
    62|        actions.append({"type":"alert","level":"P0","msg":"配置文件被修改但无授权记录"})
    63|    if block_rate > 20:
    64|        actions.append({"type":"alert","level":"P1","msg":f"审批拦截率异常:{block_rate}%"})
    65|
    66|    return actions
    67|
    68|def main():
    69|    data = {}
    70|    for name, path in CRON_OUTPUTS.items():
    71|        data[name] = load_json(path)
    72|
    73|    actions = check_conditions(data)
    74|    if not actions:
    75|        print("TRCM Dispatcher: 无待处理项。系统正常。")
    76|        return
    77|
    78|    event = {
    79|        "timestamp": datetime.now().isoformat(),
    80|        "triggers": [k for k,v in data.items() if v],
    81|        "actions": actions,
    82|        "user_decision_required": any(a["type"] in ("suggest_roundtable","alert") for a in actions)
    83|    }
    84|
    85|    EVENTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    86|    with open(EVENTS_LOG, "a") as f:
    87|        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    88|
    89|    print(json.dumps(event, ensure_ascii=False, indent=2))
    90|    if event["user_decision_required"]:
    91|        print("\n⚠️ 需要用户决策。请查看上述建议。")
    92|
    93|if __name__ == "__main__":
    94|    main()
    95|