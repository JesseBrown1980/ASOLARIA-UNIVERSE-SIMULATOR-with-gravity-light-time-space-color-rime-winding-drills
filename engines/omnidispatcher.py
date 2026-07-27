#!/usr/bin/env python3
"""OMNIDISPATCHER (container port) — the ROUTER, node [1] of the spine.
Faithful E=0 port of omni-dispatcher/{validator.mjs, omnidispatcher.mjs,
emitter/pid-chain-revolver.mjs}. Validates FEDENV-v1 envelopes, mints PIDs on the
7-lane revolver, routes to a 1000-slot PID table. No real ports, no worker spawn,
no fire — this measures routing behavior only. process_launch=0, dispatch=0.

MEASURED-in-container: validation gates, deterministic revolver, slot routing.
OPERATOR-CANON (NOT measured here): ~5,000,000 PID/s single-thread, ~1.16T agents/s
multi-emitter — those are throughput claims of the live acer fabric, not this port."""
import hashlib, json, os

# ---- glyph alphabet (clean) for PID rendering ----
_HERE = os.path.dirname(os.path.abspath(__file__))
def _alphabet():
    a = json.load(open(os.path.join(_HERE, 'alphabet.json')))
    for k in ('symbols','glyphs','alphabet','table'):
        if isinstance(a.get(k), list) and len(a[k]) == 256: return a[k]
    if 'blocks' in a:
        out=[]
        for b in a['blocks']: out += b.get('glyphs', b.get('symbols', []))
        if len(out)==256: return out
    return [format(i,'02x') for i in range(256)]
ALPHABET = _alphabet()

# ---- FEDENV-v1 validator (ported 1:1 from validator.mjs) ----
COSIGN_WINDOW   = 'QUINTUPLE-DELEGATED-2WEEK-2026-05-22-to-2026-06-05'
COSIGN_WINDOW_V3= 'FOUNDATION-V3-LAW-EXTENDED-4MO'
ADMIN_OVERRIDE  = 'ADMIN-OVERRIDE-OP-JESSE'
REQUIRED = ['caller_pid','target','verb','payload','back_address','cube_47d',
            'glyph_5','cosign_token','ttl_seconds','antecedents','row_hash']
TARGET_PREFIXES = ['google:','cli:','citizen:','antigravity:','daemon:','meta:','pid:H']
MAX_PAYLOAD = 64*1024
import re
def validate(env):
    if not isinstance(env, dict):
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-MALFORMED','detail':'not object'}
    for f in REQUIRED:
        if env.get(f) in (None,'',):
            return {'ok':False,'reason':'EVT-FEDENV-REJECTED-MALFORMED','detail':f'missing field: {f}'}
    tgt = str(env['target'])
    if not any(tgt.startswith(p) for p in TARGET_PREFIXES):
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-UNRESOLVABLE-TARGET','detail':tgt}
    if len(str(env['payload']).encode('utf8')) > MAX_PAYLOAD:
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-PAYLOAD-TOO-LARGE','detail':'>64KB'}
    cube = str(env['cube_47d']).split('-')
    if len(cube)!=6 or any(not re.fullmatch('[0-7]',n) for n in cube):
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-MALFORMED','detail':'cube_47d = six 0-7 ints'}
    if len(list(str(env['glyph_5']))) < 5:
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-MALFORMED','detail':'glyph_5 >=5 glyphs'}
    ttl = env['ttl_seconds']
    try: ttl = float(ttl)
    except: ttl = -1
    if not (0 < ttl <= 86400):
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-MALFORMED','detail':'ttl out of range'}
    if not re.fullmatch('[0-9a-f]{16}', str(env['row_hash'])):
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-MALFORMED','detail':'row_hash 16-hex'}
    if not re.fullmatch('[0-9a-f]{16}', str(env['antecedents'])):
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-MALFORMED','detail':'antecedents 16-hex'}
    tok = str(env['cosign_token'])
    if not (COSIGN_WINDOW in tok or COSIGN_WINDOW_V3 in tok or ADMIN_OVERRIDE in tok):
        return {'ok':False,'reason':'EVT-FEDENV-REJECTED-COSIGN','detail':'no active cosign window'}
    return {'ok':True}

# ---- revolver PID emitter (ported from pid-chain-revolver.mjs) ----
LANE_CYCLE = ['nervous','circulatory','skeletal','muscular','immune','memory','lymphatic']
def _prime_at(i):
    n=2; c=0
    while True:
        p=True
        for d in range(2,int(n**0.5)+1):
            if n%d==0: p=False; break
        if p:
            if c==i: return n
            c+=1
        n+=1
def _mint(actor, device, lane, prime, alphabet=256):
    seed = f"{device}|{lane}|{prime}|{actor}|{alphabet}"
    h = hashlib.sha256(seed.encode()).digest()
    v = int.from_bytes(h[:8],'big'); out=[]
    for _ in range(8): out.append(ALPHABET[v%256]); v//=256
    return {'pid':''.join(out), 'sha16':h[:8].hex(), 'lane':lane, 'prime':prime, 'actor':actor}

class Revolver:
    def __init__(self, anchor, alphabet=256):
        if not isinstance(anchor,str) or not anchor: raise TypeError('anchor required')
        self.anchor=anchor; self.counter=0; self.alphabet=alphabet
    def next(self):
        i=self.counter
        pid=_mint(i%self.alphabet, self.anchor, LANE_CYCLE[i%7], _prime_at(i%1000), self.alphabet)
        self.counter+=1; return pid

# ---- 1000-slot dispatcher (in-memory, E=0) ----
class OmniDispatcher:
    SLOTS=1000
    def __init__(self):
        self.table=[None]*self.SLOTS; self.accepted=0; self.rejected=0; self.rejects={}
    def dispatch(self, env):
        v=validate(env)
        if not v['ok']:
            self.rejected+=1; self.rejects[v['reason']]=self.rejects.get(v['reason'],0)+1
            return v
        slot=int(str(env['row_hash']),16)%self.SLOTS   # content-addressed slot
        self.table[slot]={'caller':env['caller_pid'],'verb':env['verb'],'target':env['target']}
        self.accepted+=1
        return {'ok':True,'slot':slot,'process_launch':0,'fire':0}

if __name__=='__main__':
    d=OmniDispatcher(); rev=Revolver('AGT-CONTAINER-EVIDENCE-FABLE5')
    good=dict(caller_pid='asolaria',target='cli:build',verb='evaluate',payload='hi',
        back_address='pid:H12',cube_47d='1-2-3-4-5-6',glyph_5='ΠχC⊥μ',
        cosign_token=ADMIN_OVERRIDE,ttl_seconds=60,antecedents='0'*16,row_hash='a09993369d31ca73')
    print('good ->', d.dispatch(good))
    for bad in [dict(good,target='evil:x'), dict(good,cube_47d='9-9-9-9-9-9'),
                {k:v for k,v in good.items() if k!='verb'}, dict(good,cosign_token='none')]:
        print('bad  ->', d.dispatch(bad)['reason'])
    print('revolver:', [rev.next()['pid'] for _ in range(3)])
    print(f"accepted={d.accepted} rejected={d.rejected} rejects={d.rejects}")
