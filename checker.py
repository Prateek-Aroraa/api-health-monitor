import time, urllib.request, urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class EndpointConfig:
    name: str; url: str; method: str = "GET"; expected_status: int = 200
    sla_ms: float = 1000.0; timeout_s: float = 5.0
    headers: dict = field(default_factory=dict)
    tags: list    = field(default_factory=list)
    body: Optional[str] = None

    @classmethod
    def from_dict(cls, d):
        return cls(name=d["name"], url=d["url"], method=d.get("method","GET").upper(),
                   expected_status=d.get("expected_status",200), sla_ms=float(d.get("sla_ms",1000)),
                   timeout_s=float(d.get("timeout_s",5)), headers=d.get("headers",{}),
                   tags=d.get("tags",[]), body=d.get("body"))

@dataclass
class ProbeResult:
    endpoint: EndpointConfig; status_code: Optional[int]; response_ms: float
    health: str; sla_breach: bool; error_message: Optional[str]
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_healthy(self): return self.health == "HEALTHY"

    def to_dict(self):
        return {"name": self.endpoint.name, "url": self.endpoint.url, "health": self.health,
                "status_code": self.status_code, "expected": self.endpoint.expected_status,
                "response_ms": round(self.response_ms,1), "sla_ms": self.endpoint.sla_ms,
                "sla_breach": self.sla_breach, "error": self.error_message,
                "tags": self.endpoint.tags, "checked_at": self.checked_at}

class EndpointChecker:
    USER_AGENT = "APIHealthMonitor/2.0 (github.com/Prateek-Aroraa)"

    def probe(self, cfg):
        start = time.perf_counter(); status_code = None; error_message = None
        try:
            data = cfg.body.encode() if cfg.body else None
            req  = urllib.request.Request(cfg.url, data=data, method=cfg.method)
            req.add_header("User-Agent", self.USER_AGENT)
            for k, v in cfg.headers.items(): req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=cfg.timeout_s) as resp:
                status_code = resp.status; resp.read()
        except urllib.error.HTTPError as e: status_code = e.code; error_message = str(e.reason)
        except urllib.error.URLError  as e: error_message = f"URLError: {e.reason}"
        except TimeoutError:               error_message = f"Timed out after {cfg.timeout_s}s"
        except Exception as e:             error_message = f"{type(e).__name__}: {e}"
        return self._evaluate(cfg, status_code, (time.perf_counter()-start)*1000, error_message)

    def _evaluate(self, cfg, status_code, elapsed_ms, error_message):
        sla_breach = elapsed_ms > cfg.sla_ms
        status_ok  = (status_code == cfg.expected_status) if status_code is not None else False
        if error_message and status_code is None: health = "DOWN"
        elif not status_ok:                       health = "ERROR"
        elif sla_breach:                          health = "DEGRADED"
        else:                                     health = "HEALTHY"
        return ProbeResult(cfg, status_code, elapsed_ms, health, sla_breach, error_message)