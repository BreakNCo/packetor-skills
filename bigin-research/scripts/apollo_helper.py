#!/usr/bin/env python3
"""Apollo helper for the bigin-research skill. The API key is never printed.

Key lookup order: APOLLO_API_KEY env var, ~/.env, then the repo-root .env (two levels above this script).

  apollo_helper.py org <domain>                 -> org profile (search + free enrich), JSON
  apollo_helper.py people <org_id> [--global]   -> tiered candidate list (India-first unless --global), JSON
  apollo_helper.py reveal <person_id>           -> people/match with phone reveal via the ngrok webhook;
                                                   returns full identity (name/title/email) -- no separate identity check needed
  apollo_helper.py poll <id> [<id> ...] [--timeout 300]  -> poll the webhook for phone results, JSON
  apollo_helper.py credits                      -> remaining Apollo credits, JSON

Costs: org/people search and org enrich are free; a reveal is ~9 credits when a phone is found (1 email + ~8 direct dial).
Requires ~/.apollo_webhook_url (ngrok URL of apollo_webhook_server.py) for reveal/poll.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

BASE = "https://api.apollo.io/api/v1"


def key():
    if os.environ.get("APOLLO_API_KEY"):
        return os.environ["APOLLO_API_KEY"].strip()
    repo_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
    for path in (os.path.expanduser("~/.env"), repo_env):
        if not os.path.exists(path):
            continue
        for line in open(path):
            m = re.match(r'^(?:export )?APOLLO_API_KEY=(.*)$', line.strip())
            if m:
                return m.group(1).strip().strip('"').strip("'")
    sys.exit("APOLLO_API_KEY not found (env var, ~/.env, or repo .env)")


def call(method, path, body=None, params=None, timeout=60):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": key()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return {"_http_error": e.code, "_body": e.read().decode()[:300]}


def webhook():
    return open(os.path.expanduser("~/.apollo_webhook_url")).read().strip().rstrip("/")


def out(o):
    print(json.dumps(o, indent=1, ensure_ascii=False))


ORG_FIELDS = ["id", "name", "website_url", "primary_domain", "linkedin_url", "twitter_url", "facebook_url",
              "phone", "estimated_num_employees", "industry", "founded_year", "city", "state", "country",
              "short_description", "technology_names", "total_funding_printed", "latest_funding_stage"]


def cmd_org(domain):
    s = call("POST", "/mixed_companies/search", {"q_organization_domains": domain, "per_page": 1})
    orgs = s.get("organizations") or []
    if not orgs:
        return out({"found": False, "domain": domain})
    base = orgs[0]
    e = call("GET", "/organizations/enrich", params={"domain": domain}).get("organization") or {}
    merged = {k: (e.get(k) if e.get(k) not in (None, "", []) else base.get(k)) for k in ORG_FIELDS}
    merged["found"] = True
    out(merged)


TIER_RULES = [
    (1, r"company secretary|secretar|office manager|general enquir|receptionist|administrator"),
    (3, r"ciso|chief information security|information security|security|compliance|grc|iso |risk|data protection|dpo|privacy|chief information officer|\bcio\b|general counsel|legal|audit|governance"),
    (4, r"engineer|architect|technology|\bcto\b|chief technology|\bit\b|infrastructure"),
    (2, r"\bceo\b|chief executive|managing director|\bmd\b|chairman|founder|owner|president|general manager|\bcoo\b|chief operating|\bcfo\b|chief financial|\bdirector\b"),
]


def tier(title):
    t = (title or "").lower()
    for n, rx in TIER_RULES:
        if re.search(rx, t):
            return n
    return 5


SEARCHES = [
    ["Company Secretary", "Chief Compliance Officer", "Head of Compliance", "Compliance Manager", "Chief Information Security Officer",
     "CISO", "Information Security Manager", "Chief Information Officer", "CIO", "Head of IT", "General Counsel", "Head of Legal", "Risk Manager",
     "Data Protection Officer", "Head of Internal Audit"],
    ["Chief Executive Officer", "CEO", "Managing Director", "Chief Financial Officer", "CFO", "Chief Operating Officer", "Chief Technology Officer", "Founder", "Chairman", "General Manager"],
]


def cmd_people(org_id, global_only=False):
    cands = {}
    for scope in ([None] if global_only else ["India", None]):
        for titles in SEARCHES:
            body = {"organization_ids": [org_id], "person_titles": titles, "include_similar_titles": True, "per_page": 15}
            if scope:
                body["person_locations"] = [scope]
            r = call("POST", "/mixed_people/api_search", body)
            for p in r.get("people") or []:
                cands.setdefault(p["id"], {"id": p["id"], "first_name": p.get("first_name"), "title": p.get("title"),
                                           "tier": tier(p.get("title")), "scope": scope or "global"})
        if len(cands) >= 3:
            break
    ranked = sorted(cands.values(), key=lambda c: (c["tier"], c["scope"] != "India"))
    out(ranked[:12])


PERSON_FIELDS = ["id", "name", "first_name", "last_name", "title", "email", "email_status", "linkedin_url", "twitter_url", "facebook_url",
                 "city", "state", "country", "seniority", "departments", "headline", "phone_numbers", "personal_emails"]


def person_view(r):
    p = r.get("person") or {}
    o = p.get("organization") or {}
    v = {k: p.get(k) for k in PERSON_FIELDS}
    v["organization"] = {k: o.get(k) for k in ("name", "website_url", "linkedin_url", "primary_phone")}
    v["waterfall"] = r.get("waterfall")
    if r.get("_http_error"):
        v["_error"] = r
    return v


def cmd_match(pid):
    out(person_view(call("POST", "/people/match", {"id": pid})))


def cmd_reveal(pid):
    out(person_view(call("POST", "/people/match", {"id": pid}, params={
        "reveal_phone_number": "true", "run_waterfall_phone": "true", "webhook_url": webhook()})))


def cmd_poll(ids, timeout):
    base = webhook()
    pending, got, t0 = set(ids), {}, time.time()
    while pending and time.time() - t0 < timeout:
        for i in list(pending):
            try:
                req = urllib.request.Request(f"{base}/result/{i}", headers={"ngrok-skip-browser-warning": "1"})
                r = json.loads(urllib.request.urlopen(req, timeout=15).read())
            except Exception:
                continue
            if r.get("ready"):
                d = r.get("data", {})
                p = d.get("person", d)
                nums = p.get("phone_numbers") or []
                got[i] = {"phones": [{"n": n.get("sanitized_number"), "type": n.get("type")} for n in nums],
                          "email": p.get("email")}
                pending.discard(i)
        if pending:
            time.sleep(5)
    out({"results": got, "timed_out": sorted(pending), "elapsed_s": int(time.time() - t0)})


def cmd_credits():
    p = call("GET", "/users/api_profile", params={"include_credit_usage": "true"})
    out({k: p.get(k) for k in ("num_credits_remaining", "num_lead_credits_used", "num_direct_dial_credits_used", "total_unified_credits_used")})


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    c = a[0]
    if c == "org": cmd_org(a[1])
    elif c == "people": cmd_people(a[1], "--global" in a)
    elif c == "match": cmd_match(a[1])
    elif c == "reveal": cmd_reveal(a[1])
    elif c == "poll":
        t = int(a[a.index("--timeout") + 1]) if "--timeout" in a else 300
        ids = [x for x in a[1:] if not x.startswith("--") and x != str(t)]
        cmd_poll(ids, t)
    elif c == "credits": cmd_credits()
    else: sys.exit(__doc__)
