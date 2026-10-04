"""Uji asap terhadap server yang SEDANG berjalan (setelah .\\run.ps1): python scripts/smoke.py [password]
Login per peran, memanggil endpoint utama lewat proxy web, dan memastikan halaman web ada. Keluar 1 bila ada yang gagal."""
import http.cookiejar
import json
import sys
import urllib.error
import urllib.request

PW = sys.argv[1] if len(sys.argv) > 1 else "dev-password"
BASE = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:3000").rstrip("/")
PAGES = ["/", "/login", "/news", "/events", "/map", "/globe", "/watchlist", "/portfolio", "/supply/NICKEL", "/copilot",
         "/companies/ANTM", "/sectors/ENERGY"]
API = {  # path -> (peran minimum yang boleh 200, kunci yang harus ada di JSON)
    "/market/overview": ("INVESTOR", None), "/market/sectors": ("INVESTOR", None), "/dashboard": ("INVESTOR", "priorities"),
    "/companies/ANTM": ("INVESTOR", "price"), "/companies/ANTM/brief": ("INVESTOR", "facts"), "/sectors/ENERGY": ("INVESTOR", "companies"),
    "/news": ("INVESTOR", None), "/events": ("INVESTOR", None), "/map/assets": ("INVESTOR", "features"),
    "/portfolio": ("INVESTOR", "positions"), "/watchlist": ("INVESTOR", None), "/alerts": ("INVESTOR", None),
    "/supply-chain/NICKEL": ("INVESTOR", "stages"), "/clients/radar": ("RM", None),
}
RANK = {"INVESTOR": 0, "RM": 1, "ADMIN": 3}
fails = []


def call(op, url, body=None):
    req = urllib.request.Request(BASE + url, data=json.dumps(body).encode() if body else None, headers={"Content-Type": "application/json"})
    try:
        with op.open(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


for role, email in [("INVESTOR", "investor@imvest.local"), ("RM", "rm@imvest.local"), ("ADMIN", "admin@imvest.local")]:
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    code, _ = call(op, "/api/v1/auth/login", {"email": email, "password": PW})
    check(code == 200, f"[{role}] login")
    if code != 200:
        continue
    for path, (min_role, key) in API.items():
        code, body = call(op, "/api/v1" + path)
        want = 200 if RANK[role] >= RANK[min_role] else 403
        ok = code == want
        if ok and want == 200 and key:
            ok = key in json.loads(body)
        check(ok, f"[{role}] {path} -> {code} (harap {want})")
    if role == "INVESTOR":
        for page in PAGES:
            code, _ = call(op, page)
            check(code == 200, f"[web] {page} -> {code}")

code, _ = call(urllib.request.build_opener(), "/api/v1/dashboard")
check(code == 401, f"tanpa login -> {code} (harap 401)")
print(f"\n{'GAGAL: ' + str(len(fails)) if fails else 'SEMUA LULUS'}")
sys.exit(1 if fails else 0)
