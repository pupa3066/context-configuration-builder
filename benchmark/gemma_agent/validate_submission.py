"""Local pre-upload check for an Agent Track submission directory.

Mirrors the rules stated in the competition's HARNESS_README (sections 2 and 6): one root config,
sandboxed !include (relative to the including file, no absolute paths, no '..', no symlinks), allowed
file extensions, total size < 3 GiB, the single base model, the 9 harness tools, agent_tool config
paths, skills as directories with a SKILL.md whose frontmatter has a name, and generation-config
bounds. It does not run the official compiler (adk-submission); it catches format errors before a
submission slot is spent.

Usage: python validate_submission.py <submission_dir> [--zip out.zip]
Needs: PyYAML.
"""
import os
import re
import sys
import zipfile

import yaml

MODEL = "gemma-4-31b-it-qat-w4a16-ct"
TOOLS = {"run_command", "submit_patch", "get_status", "read_file", "edit_file", "write_file",
         "get_code_neighbors", "search_similar_code", "get_code_subgraph"}
ROOTS = ("agent.yaml", "agent.yml", "root_agent.yaml", "root_agent.yml")
EXTS = {".yaml", ".yml", ".md", ".txt", ".py", ".json", ".safetensors"}
GEN_FORBIDDEN = {"tools", "system_instruction", "http_options", "safety_settings", "response_schema"}
MAX_BYTES = 3 * 1024 ** 3
errors = []


def err(msg):
    errors.append(msg)


def loader_for(root, base_dir, depth):
    class L(yaml.SafeLoader):
        pass

    def include(ld, node):
        rel = ld.construct_scalar(node)
        if os.path.isabs(rel) or ".." in rel.replace("\\", "/").split("/") or "\x00" in rel:
            err(f"!include {rel!r}: absolute paths and '..' are blocked")
            return ""
        p = os.path.join(base_dir, rel)
        if os.path.islink(p) or not os.path.realpath(p).startswith(os.path.realpath(root) + os.sep):
            err(f"!include {rel!r}: symlink or outside the submission root")
            return ""
        if not os.path.isfile(p):
            err(f"!include {rel!r}: file not found (resolved from {os.path.relpath(base_dir, root) or '.'})")
            return ""
        if p.endswith((".md", ".txt")):
            return open(p, encoding="utf-8").read()
        return load_yaml(root, p, depth + 1)

    L.add_constructor("!include", include)
    return L


def load_yaml(root, path, depth=0):
    if depth > 10:
        err(f"{path}: include depth > 10")
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.load(f, Loader=loader_for(root, os.path.dirname(path), depth))


def check_gen(cfg, where):
    if not cfg:
        return
    if not isinstance(cfg, dict):
        err(f"{where}: generate_content_config must be a mapping")
        return
    bad = GEN_FORBIDDEN & set(cfg)
    if bad:
        err(f"{where}: forbidden generate_content_config fields {sorted(bad)}")
    mot = cfg.get("max_output_tokens")
    if mot is not None and not 1 <= mot <= 32768:
        err(f"{where}: max_output_tokens {mot} outside 1..32768")
    tb = (cfg.get("thinking_config") or {}).get("thinking_budget")
    if tb is not None and not 1 <= tb <= 32768:
        err(f"{where}: thinking_budget {tb} outside 1..32768")
    if cfg.get("temperature", 0) < 0:
        err(f"{where}: temperature must be >= 0")


def check_agent(root, cfg, where, seen):
    if not isinstance(cfg, dict):
        err(f"{where}: agent config must be a mapping")
        return
    cls = cfg.get("agent_class", "LlmAgent")
    if not cfg.get("name"):
        err(f"{where}: missing name")
    if cls == "LlmAgent":
        if cfg.get("model") != MODEL:
            err(f"{where}: model must be {MODEL} (got {cfg.get('model')!r})")
        for t in cfg.get("tools") or []:
            if isinstance(t, str):
                if t not in TOOLS:
                    err(f"{where}: unknown tool {t!r}")
            elif isinstance(t, dict) and "agent_tool" in t:
                check_ref(root, t["agent_tool"].get("config_path"), where, seen)
            elif not isinstance(t, dict):
                err(f"{where}: bad tool entry {t!r}")
        for s in cfg.get("skills") or []:
            sk = os.path.join(root, s, "SKILL.md")
            if not os.path.isfile(sk):
                err(f"{where}: skill {s!r} has no SKILL.md")
                continue
            txt = open(sk, encoding="utf-8").read()
            fm = txt.split("---")[1] if txt.startswith("---") and txt.count("---") >= 2 else ""
            if "name:" not in fm:
                err(f"{s}/SKILL.md: YAML frontmatter with name: is required")
            else:
                # The harness (google.adk skills Frontmatter) rejects any name that is not lowercase
                # kebab-case; one underscore makes every task fail to compile (measured 2026-11-12).
                nm = next((l.split(":", 1)[1].strip().strip("'\"") for l in fm.splitlines() if l.strip().startswith("name:")), "")
                if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nm):
                    err(f"{s}/SKILL.md: skill name {nm!r} must be lowercase kebab-case (a-z, 0-9, single hyphens)")
        adapter = cfg.get("adapter")
        if adapter and not os.path.isfile(os.path.join(root, "adapters", adapter, "adapter_model.safetensors")):
            err(f"{where}: adapter {adapter!r} not found under adapters/")
        check_gen(cfg.get("generate_content_config"), where)
    for sa in cfg.get("sub_agents") or []:
        if isinstance(sa, dict) and "config_path" in sa:
            check_ref(root, sa["config_path"], where, seen)
        else:
            check_agent(root, sa, f"{where} > inline sub-agent", seen)


def check_ref(root, rel, where, seen):
    if not rel:
        err(f"{where}: agent reference without config_path")
        return
    p = os.path.join(root, rel)
    if not os.path.isfile(p):
        err(f"{where}: config_path {rel!r} not found")
        return
    if p in seen:
        return
    seen.add(p)
    check_agent(root, load_yaml(root, p), rel, seen)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    root = os.path.abspath(sys.argv[1])
    roots = [r for r in ROOTS if os.path.isfile(os.path.join(root, r))]
    if len(roots) != 1:
        err(f"need exactly one root config, found {roots or 'none'}")
    total = 0
    for dp, dns, fns in os.walk(root):
        for n in dns + fns:
            p = os.path.join(dp, n)
            if os.path.islink(p):
                err(f"symlink not allowed: {os.path.relpath(p, root)}")
        for n in fns:
            p = os.path.join(dp, n)
            total += os.path.getsize(p)
            if os.path.splitext(n)[1] not in EXTS:
                err(f"file type not allowed: {os.path.relpath(p, root)}")
    if total >= MAX_BYTES:
        err(f"total size {total} bytes >= 3 GiB")
    if len(roots) == 1:
        rp = os.path.join(root, roots[0])
        check_agent(root, load_yaml(root, rp), roots[0], {rp})
    if errors:
        print("INVALID:")
        for e in errors:
            print("  - " + e)
        return 1
    print(f"VALID: {roots[0]} at root, {total} bytes")
    if "--zip" in sys.argv:
        out = os.path.abspath(sys.argv[sys.argv.index("--zip") + 1])
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for dp, _, fns in os.walk(root):
                for n in sorted(fns):
                    p = os.path.join(dp, n)
                    z.write(p, os.path.relpath(p, root))
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
