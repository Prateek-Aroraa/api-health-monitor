import json
from pathlib import Path
from typing import List
from checker import EndpointConfig

DEMO_ENDPOINTS = [
    {"name":"JSONPlaceholder — Posts","url":"https://jsonplaceholder.typicode.com/posts/1","method":"GET","expected_status":200,"sla_ms":800,"tags":["demo"]},
    {"name":"JSONPlaceholder — Users","url":"https://jsonplaceholder.typicode.com/users/1","method":"GET","expected_status":200,"sla_ms":800,"tags":["demo"]},
    {"name":"HTTPBin — OK",           "url":"https://httpbin.org/status/200",               "method":"GET","expected_status":200,"sla_ms":1500,"tags":["health-check"]},
    {"name":"HTTPBin — Delayed 1s (SLA breach demo)","url":"https://httpbin.org/delay/1",   "method":"GET","expected_status":200,"sla_ms":800,"tags":["sla-demo"]},
    {"name":"HTTPBin — 404 (error demo)",             "url":"https://httpbin.org/status/404","method":"GET","expected_status":200,"sla_ms":1000,"tags":["error-demo"]},
]

def load(path):
    p = Path(path)
    if not p.exists(): raise FileNotFoundError(f"Config not found: {path}")
    if p.suffix == ".json":
        with open(p) as fh: data = json.load(fh)
    elif p.suffix in (".yml",".yaml"):
        try: import yaml
        except ImportError: raise ImportError("Install PyYAML: pip install pyyaml")
        with open(p) as fh: data = yaml.safe_load(fh)
    else: raise ValueError(f"Unsupported format: {p.suffix}")
    raw = data if isinstance(data, list) else data.get("endpoints", data)
    return [EndpointConfig.from_dict(ep) for ep in raw]

def demo_endpoints():
    return [EndpointConfig.from_dict(ep) for ep in DEMO_ENDPOINTS]