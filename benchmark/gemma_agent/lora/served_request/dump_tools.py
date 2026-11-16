# Exact tool declarations the scorer's agent sends, via ADK 1.36.1 + swegemma 0.2.11 (no model call).
import json, types
from swegemma.tools import create_tools
from google.adk.tools.function_tool import FunctionTool
from google.adk.models.lite_llm import _function_declaration_to_tool_param
ctx = types.SimpleNamespace()
tools = create_tools(ctx)
order = ["run_command","read_file","edit_file","write_file","get_status","submit_patch","get_code_neighbors","search_similar_code","get_code_subgraph"]
out = []
for n in order:
    ft = FunctionTool(tools[n]); d = ft._get_declaration()
    out.append(_function_declaration_to_tool_param(d))
json.dump(out, open('/tmp/lora2/tools_exact.json','w'), indent=1)
for t in out: print(t['function']['name'], '|', t['function'].get('description','')[:90].replace('\n',' '), '|', list(t['function'].get('parameters',{}).get('properties',{}).keys()))
