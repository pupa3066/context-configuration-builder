"""Convert resolved 31B arm-G trajectories into chat-format SFT records (train: fastapi + requests; rich held out)."""
import json, glob, ast, csv, sys, collections
T=lambda n,d,p,req: {"type":"function","function":{"name":n,"description":d,"parameters":{"type":"object","properties":p,"required":req}}}
S=lambda t,d="": {"type":t,"description":d}
TOOLS=[T("run_command","Run a shell command in /workspace.",{"command":S("string")},["command"]),
 T("submit_patch","Submit the current diff as the patch.",{},[]),
 T("get_status","Return budget use and patch status.",{},[]),
 T("read_file","Read a file, optionally a line range.",{"filepath":S("string"),"start_line":S("integer"),"end_line":S("integer")},["filepath"]),
 T("edit_file","Replace an exact string in a file.",{"filepath":S("string"),"old_string":S("string"),"new_string":S("string"),"allow_multiple":S("boolean")},["filepath","old_string","new_string"]),
 T("write_file","Write a whole file.",{"filepath":S("string"),"content":S("string")},["filepath","content"]),
 T("get_code_neighbors","Graph neighbors of a code node.",{"node":S("string"),"edge_type":S("string"),"max_neighbors":S("integer")},["node"]),
 T("search_similar_code","Search code nodes by name and embedding.",{"query":S("string"),"k":S("integer")},["query"]),
 T("get_code_subgraph","Subgraph over code nodes.",{"nodes":{"type":"array","items":{"type":"string"}}},["nodes"])]
def parse(x):
    if x is None or isinstance(x,(list,dict)): return x
    try: return ast.literal_eval(x)
    except Exception: return None
def obs_text(o):
    o=parse(o)
    if isinstance(o,dict) and 'content' in o: return str(o['content'])
    return str(o) if o is not None else ""
recs=[]; stats=collections.Counter()
for run in ("cck-all129-grep","cck-fa67-grep"):
    resolved={r['task'] for r in csv.DictReader(open(f"/tmp/kout/{run}/diag_summary.csv")) if r['resolved']=='True'}
    for f in sorted(glob.glob(f"/tmp/kout/{run}/**/trace_*.json",recursive=True)):
        task=f.split("trace_")[-1][:-5]
        if task not in resolved: continue
        split="heldout" if task.startswith("rich_") else ("train" if task.split('_')[0] in ("fastapi","requests") else "other")
        msgs=[]; ok=True
        for s in json.load(open(f))["steps"]:
            src=s.get("source")
            if src=="system": msgs.append({"role":"system","content":s["message"]})
            elif src=="user": msgs.append({"role":"user","content":s["message"]})
            elif src=="agent":
                tcs=parse(s.get("tool_calls")) or []
                m={"role":"assistant","content":s.get("message") or ""}
                if tcs:
                    m["tool_calls"]=[{"id":tc.get("tool_call_id",f"call_{i}"),"type":"function","function":{"name":tc["function_name"],"arguments":tc.get("arguments") or {}}} for i,tc in enumerate(tcs)]
                msgs.append(m)
                for tc in tcs: msgs.append({"role":"tool","tool_call_id":tc.get("tool_call_id"),"name":tc["function_name"],"content":obs_text(s.get("observation"))[:12000]})
        if not msgs or msgs[0]["role"]!="system": ok=False
        stats[(split,ok)]+=1
        if ok: recs.append({"run":run,"task":task,"split":split,"messages":msgs})
json.dump(TOOLS,open("/tmp/lora/tools.json","w"),indent=1)
for sp in ("train","heldout"):
    with open(f"/tmp/lora/sft_{sp}.jsonl","w") as fh:
        for r in recs:
            if r["split"]==sp: fh.write(json.dumps(r)+"\n")
print(dict(stats)); print({sp:sum(r['split']==sp for r in recs) for sp in ("train","heldout")}, "| unique train tasks", len({r['task'] for r in recs if r['split']=='train'}))
print("assistant turns per train record, median:", sorted(sum(m['role']=='assistant' for m in r['messages']) for r in recs if r['split']=='train')[len([1 for r in recs if r['split']=='train'])//2])
