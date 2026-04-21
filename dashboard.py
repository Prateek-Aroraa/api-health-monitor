import json, csv
from datetime import datetime
from typing import List
from checker import ProbeResult

R="[91m"; Y="[93m"; G="[92m"; B="[94m"; W="[97m"; DIM="[2m"; RST="[0m"
HEALTH_COLOR={"HEALTHY":G,"DEGRADED":Y,"ERROR":R,"DOWN":R}
HEALTH_ICON ={"HEALTHY":"✅","DEGRADED":"🟡","ERROR":"🔴","DOWN":"⛔"}

class CliDashboard:
    def render(self, results, run_number=1):
        healthy = sum(1 for r in results if r.health=="HEALTHY")
        uptime  = f"{healthy/len(results)*100:.1f}%" if results else "—"
        print(f"\n{B}{'═'*70}{RST}")
        print(f"{W}  🩺  API HEALTH MONITOR  {DIM}run #{run_number}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RST}")
        print(f"{DIM}  Endpoints: {len(results)}  |  Uptime: {uptime}  |  Healthy: {healthy}/{len(results)}{RST}")
        print(f"{B}{'═'*70}{RST}\n  {DIM}{'ENDPOINT':<44}  {'HEALTH':<12}  {'RESP':>7}  SLA{RST}\n  {'─'*66}")
        for r in results:
            sla_flag = f"{Y}⚠ SLA{RST}" if r.sla_breach else f"{G}OK{RST}"
            http     = str(r.status_code) if r.status_code else "—"
            print(f"  {HEALTH_ICON[r.health]} {r.endpoint.name[:42]:<44}  {HEALTH_COLOR[r.health]}{r.health:<12}{RST}  {r.response_ms:>6.0f}ms  {sla_flag}  HTTP {http}")
            if r.error_message: print(f"     {DIM}└─ {r.error_message[:72]}{RST}")
        breaches  = [r for r in results if r.sla_breach]
        incidents = [r for r in results if r.health in ("ERROR","DOWN")]
        if breaches:
            print(f"\n{Y}  ⚠  SLA BREACHES ({len(breaches)}){RST}\n  {'─'*50}")
            for r in breaches: print(f"  • {r.endpoint.name}  →  {r.response_ms:.0f}ms  (limit {r.endpoint.sla_ms:.0f}ms)")
        if incidents:
            print(f"\n{R}  🚨  INCIDENTS ({len(incidents)}){RST}\n  {'─'*50}")
            for r in incidents:
                reason = r.error_message or f"HTTP {r.status_code} (expected {r.endpoint.expected_status})"
                print(f"  • {r.endpoint.name}  →  {reason[:65]}")
        from collections import Counter
        counts = Counter(r.health for r in results)
        resp   = [r.response_ms for r in results]
        avg    = sum(resp)/len(resp) if resp else 0
        overall = "✅ ALL SYSTEMS OPERATIONAL" if counts.get("HEALTHY",0)==len(results) else ("⚠  DEGRADED" if not counts.get("DOWN",0) and not counts.get("ERROR",0) else "🚨 INCIDENTS DETECTED")
        print(f"\n{'─'*70}\n  {W}{overall}{RST}  {DIM}avg {avg:.0f}ms{RST}\n  {G}✅ {counts.get('HEALTHY',0)}{RST}  {Y}🟡 {counts.get('DEGRADED',0)}{RST}  {R}🔴 {counts.get('ERROR',0)}{RST}  {R}⛔ {counts.get('DOWN',0)}{RST}\n{'─'*70}\n")

class JsonReporter:
    def write(self, results, path, run=1):
        from collections import Counter
        counts = Counter(r.health for r in results); resp = [r.response_ms for r in results]
        payload = {"meta": {"checked_at": datetime.now().isoformat(), "run_number": run, "total_endpoints": len(results)},
                   "summary": {"healthy": counts.get("HEALTHY",0), "degraded": counts.get("DEGRADED",0),
                                "error": counts.get("ERROR",0), "down": counts.get("DOWN",0),
                                "sla_breaches": sum(1 for r in results if r.sla_breach),
                                "avg_ms": round(sum(resp)/len(resp),1) if resp else 0,
                                "uptime_pct": round(counts.get("HEALTHY",0)/len(results)*100,1) if results else 0},
                   "endpoints": [r.to_dict() for r in results],
                   "sla_breaches": [r.to_dict() for r in results if r.sla_breach],
                   "incidents": [r.to_dict() for r in results if r.health in ("ERROR","DOWN")]}
        with open(path,"w") as fh: json.dump(payload, fh, indent=2)
        print(f"  💾  JSON report → {path}")

class CsvReporter:
    def write(self, results, path):
        with open(path,"w",newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["name","url","health","status_code","response_ms","sla_ms","sla_breach","error","checked_at"])
            for r in results:
                w.writerow([r.endpoint.name,r.endpoint.url,r.health,r.status_code,round(r.response_ms,1),r.endpoint.sla_ms,r.sla_breach,r.error_message or "",r.checked_at])
        print(f"  📊  CSV report  → {path}")