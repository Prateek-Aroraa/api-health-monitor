import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from checker import EndpointChecker, EndpointConfig, ProbeResult

def cfg(**kw):
    d = {"name":"Test","url":"https://jsonplaceholder.typicode.com/posts/1","expected_status":200,"sla_ms":1000}
    d.update(kw); return EndpointConfig.from_dict(d)

def eval_(status=200, ms=200, expected=200, sla=1000, error=None):
    return EndpointChecker()._evaluate(cfg(expected_status=expected, sla_ms=sla), status, ms, error)

def test_healthy():       assert eval_().health == "HEALTHY"
def test_sla_breach():    r = eval_(ms=1500); assert r.health=="DEGRADED" and r.sla_breach
def test_wrong_status():  assert eval_(status=404).health == "ERROR"
def test_down():          assert eval_(status=None, error="connection refused").health == "DOWN"
def test_to_dict():
    d = eval_().to_dict()
    for k in ("name","url","health","status_code","response_ms","sla_ms","sla_breach"): assert k in d
def test_is_healthy():    assert eval_().is_healthy
def test_not_healthy():   assert not eval_(status=500).is_healthy
def test_defaults():
    c = EndpointConfig.from_dict({"name":"X","url":"http://x.com"})
    assert c.method=="GET" and c.expected_status==200 and c.sla_ms==1000.0