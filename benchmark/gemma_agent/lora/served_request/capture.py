"""Capture the exact first request the scorer's agent sends (messages + tools), offline, no model.
Compiles the arm with adk_submission, swaps in a capturing LLM, runs one turn with the harness's prompt builder."""
import asyncio, json, sys, types
from pathlib import Path
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.models import lite_llm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as gt
from adk_submission import compile_submission
from adk_submission.registry import ModelRegistry
from swegemma.tools import create_tools
from swegemma.harness.agent_runner import build_agent_prompt, _extract_declared_tools
from swegemma.config import EvalConfig
ARM = Path(sys.argv[1]); OUT = sys.argv[2]
CAP = {}
class Cap(BaseLlm):
    model: str = 'openai/gemma-4-e4b-it-qat-w4a16-ct'
    async def generate_content_async(self, llm_request, stream=False):
        msgs, tools, rf, gen = await lite_llm._get_completion_inputs(llm_request, self.model)
        CAP['messages'] = [m if isinstance(m, dict) else m.model_dump(exclude_none=True) for m in msgs]
        CAP['tools'] = tools; CAP['gen'] = gen
        yield LlmResponse(content=gt.Content(role='model', parts=[gt.Part(text='done')]))
ctx = types.SimpleNamespace()
models = ModelRegistry(); models.register('gemma-4-e4b-it-qat-w4a16-ct', 'openai/gemma-4-e4b-it-qat-w4a16-ct')
agent = compile_submission(submission_dir=ARM, tool_registry=create_tools(ctx), model_registry=models)
agent.model = Cap()
import yaml
ev = yaml.safe_load(open(ARM / 'eval_config.yaml'))['evaluation']
cfg = EvalConfig(tasks_path=Path('x'), snapshots_dir=Path('x'), results_dir=Path('x'), submission_dir=ARM, models=models, timeout_seconds=ev['timeout_seconds'], max_time_minutes=ev['max_time_minutes'], max_tool_calls=ev['max_tool_calls'], max_turns=ev['max_turns'], graph_dir='/nonexistent', embeddings_dir='/nonexistent')
task = types.SimpleNamespace(repo='OWNER/REPO', problem_statement='PROBLEM_STATEMENT', hints_text='', base_commit=None)
prompt = build_agent_prompt(task, cfg, workspace_tree='WORKSPACE_TREE', declared_tools=_extract_declared_tools(agent))
async def main():
    ss = InMemorySessionService(); s = await ss.create_session(app_name='a', user_id='u')
    r = Runner(agent=agent, app_name='a', session_service=ss)
    async for _ in r.run_async(user_id='u', session_id=s.id, new_message=gt.Content(role='user', parts=[gt.Part(text=prompt)])): pass
asyncio.run(main())
json.dump(CAP, open(OUT, 'w'), indent=1, default=str)
print('roles', [m['role'] for m in CAP['messages']], '| tools', [t['function']['name'] for t in CAP['tools']])
print('system head:', CAP['messages'][0]['content'][:200].replace('\n', ' '))
print('system tail:', CAP['messages'][0]['content'][-300:].replace('\n', ' '))
print('user:', str(CAP['messages'][1]['content'])[:1500])
