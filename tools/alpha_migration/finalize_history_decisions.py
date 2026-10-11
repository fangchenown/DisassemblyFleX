"""Close every historical family only after real candidate decisions exist."""
from common import *
links={
'alpha0.2-submission':['A002-01','A002-02'],
'alpha0.3-C03':['A003-01'],
'alpha0.6-LTCG':['A006-03'],
'alpha0.6-hazard':['A006-04'],
'alpha0.6-resource-cache':['A006-02'],
'alpha2.0-prefix':['A003-01'],
'alpha2.1-W06':['A003-01'],
'alpha2.1-W21':['A021-01'],
'alpha2.3-W6':['A003-01'],
'alpha2.4-W33':['A024-01'],
'alpha3.7-distance-first':['A037-01'],
'alpha3.7-bounded-tail':['A037-02'],
'alpha3.9-unused-stream':['A039-01'],
'alpha4.2-spring-rsqrt':['A042-01'],
'alpha7.3-packing':['A042-01'],
'alpha8.2-radix':['A082-01']}
opts=read(LEDGER/'optimizations.json');by_id={r['id']:r for r in opts};rows=read(LEDGER/'history_decisions.json')
assert all(r['status'].startswith(('accepted','rejected')) for r in opts),'Resolve every actual candidate before closing history'
for row in rows:
    if row['id'] in links:
        ids=links[row['id']];row.update(disposition='experimented-and-closed',candidate_ids=ids,outcomes={i:by_id[i]['status'] for i in ids},closed=now())
        if row['id']=='alpha4.2-spring-rsqrt':row['closure_scope']='Only exact-bit metadata packing was tested. The rsqrt/sqrt-div substitution was excluded because it changes original floating-point arithmetic.'
        if row['id']=='alpha7.3-packing':row['closure_scope']='Twelve-byte packing was implemented/tested as A042. Eight-byte index/stiffness-palette encoding was not ported: OF alpha7.4 itself found no reliable DX11 RTX gain, while DF lacks the donor host canonical palette/generation proof; no claim that DF eight-byte packing was benchmarked.'
assert not [r['id'] for r in rows if 'candidate' in r.get('disposition','')],'Unresolved historical families remain'
versions=read(LEDGER/'versions.json')
for v in versions:
    ids=[r['id'] for r in rows if r['version']==v['version']]
    candidate_ids=[r['id'] for r in opts if r['version']==v['version']]
    assert ids or candidate_ids,('Missing version disposition',v['version'])
    v.update(status='review-complete',review_ids=ids,candidate_ids=candidate_ids,closed=now())
write(LEDGER/'history_decisions.json',rows);write(LEDGER/'versions.json',versions)
tasks=read(LEDGER/'tasks.json')
for t in tasks:
    if t['id'] in ['M1','M2']:t['status']='complete'
write(LEDGER/'tasks.json',tasks);event('history-and-candidates-closed',versions=len(versions),history_ideas=len(rows),experiments=len(opts));print(len(versions),'versions;',len(rows),'historical ideas;',len(opts),'candidate decisions closed.')
