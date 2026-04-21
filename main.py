#!/usr/bin/env python3
"""
API Health Monitor CLI
Usage:
  python main.py
  python main.py --config config/endpoints.json
  python main.py --watch --interval 30
  python main.py --json-out report.json
"""
import sys, time, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, str(Path(__file__).parent))
from checker import EndpointChecker
from dashboard import CliDashboard, JsonReporter, CsvReporter
import config_loader

def probe_all(endpoints, checker, workers=5):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(checker.probe, ep): ep for ep in endpoints}
        for fut in as_completed(futures): results.append(fut.result())
    order = {ep.name: i for i, ep in enumerate(endpoints)}
    return sorted(results, key=lambda r: order.get(r.endpoint.name, 999))

def run_once(endpoints, checker, dashboard, json_out, csv_out, run_number):
    results = probe_all(endpoints, checker)
    dashboard.render(results, run_number=run_number)
    if json_out:
        Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        JsonReporter().write(results, json_out, run=run_number)
    if csv_out:
        Path(csv_out).parent.mkdir(parents=True, exist_ok=True)
        CsvReporter().write(results, csv_out)
    return 2 if any(r.health in ("ERROR","DOWN") for r in results) else (3 if any(r.sla_breach for r in results) else 0)

def main():
    p = argparse.ArgumentParser(description="API Health Monitor")
    p.add_argument("--config",   metavar="PATH")
    p.add_argument("--json-out", metavar="PATH")
    p.add_argument("--csv-out",  metavar="PATH")
    p.add_argument("--watch",    action="store_true")
    p.add_argument("--interval", type=int, default=60)
    p.add_argument("--workers",  type=int, default=5)
    p.add_argument("--timeout",  type=float, default=5.0)
    args = p.parse_args()
    endpoints = config_loader.load(args.config) if args.config else config_loader.demo_endpoints()
    checker   = EndpointChecker(); dashboard = CliDashboard()
    if args.watch:
        run = 1
        try:
            while True:
                run_once(endpoints, checker, dashboard, args.json_out, args.csv_out, run); run += 1
                print(f"  ⏳  Next check in {args.interval}s…"); time.sleep(args.interval)
        except KeyboardInterrupt: print("\n  Monitoring stopped.")
        return 0
    return run_once(endpoints, checker, dashboard, args.json_out, args.csv_out, 1)

if __name__ == "__main__": sys.exit(main())