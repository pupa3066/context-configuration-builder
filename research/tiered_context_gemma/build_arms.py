#!/usr/bin/env python3
"""Build the monolithic (whole file in the prompt) and tiered (index in the prompt, sections on demand) arms for each repository from one generated context file.

Monolithic arm: the whole file in the system prompt. Tiered arm: the file split; the always-on part (header, tests, documentation
examples, and an index of the layout sections) is in the system prompt, and each layout section is a skill loaded
on demand. Same-text control: always-on part plus all sections reassemble exactly into the monolithic file, and the index
is the only added text. Both arms start from the no-context baseline (submission_v81_noskill) and add one context block.

Usage: python build_arms.py <repos_dir> <commits.txt> <out_dir>
"""
import json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_context as mc

HERE = os.path.dirname(os.path.abspath(__file__))
GA = os.path.join(HERE, "..", "..", "benchmark", "gemma_agent")
NO_CONTEXT_BASELINE = os.path.join(GA, "submission_v81_noskill")


def split(root, name, commit):
    """Return (full_text, always_on_prefix, [(skill_name, description, section_text)])."""
    full = mc.render(root, name, commit, 10**6)
    marker = "## Package layout\n\n"
    assert full.count(marker) == 1, "layout section must appear once"
    pre, layout = full.split(marker)
    groups, order = {}, []
    for line in layout.splitlines(keepends=True):
        m = re.match(r"- `([^`]+)`", line)
        key = os.path.dirname(m.group(1)) if m else (order[-1] if order else "")
        if key not in groups:
            groups[key] = []; order.append(key)
        groups[key].append(line)
    repo = name.split("/")[-1].lower()
    sections = []
    for key in order:
        slug = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-") or "root"
        skill = f"ctx-{repo}-{slug}"
        n = sum(1 for l in groups[key] if l.startswith("- `"))
        sections.append((skill, f"Package layout of {key or 'the repository root'} in {name}, {n} modules", "".join(groups[key])))
    assert pre + marker + "".join(s[2] for s in sections) == full, "same-text control failed"
    return full, pre + marker, sections


def write_arm(dst, prompt, skills):
    shutil.rmtree(dst, ignore_errors=True); shutil.copytree(NO_CONTEXT_BASELINE, dst)
    open(os.path.join(dst, "prompts", "system.md"), "w").write(prompt)
    y = os.path.join(dst, "agent.yaml"); a = open(y).read()
    arm = "cck_" + "_".join(dst.rstrip("/").split(os.sep)[-2:])
    a = re.sub(r"^name: .*$", "name: " + arm, a, flags=re.M)
    if skills:
        a = a.rstrip() + "\nskills:\n" + "".join(f"  - skills/{s}\n" for s, _, _ in skills)
        for s, desc, text in skills:
            d = os.path.join(dst, "skills", s); os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "SKILL.md"), "w").write(
                f"---\nname: {s}\ndescription: {json.dumps(desc)}\n---\n\n" + text)
    open(y, "w").write(a)


if __name__ == "__main__":
    repos_dir, commits, out = sys.argv[1:4]
    base = open(os.path.join(NO_CONTEXT_BASELINE, "prompts", "system.md")).read().rstrip() + "\n"
    lead = "\n## Repository context\n\nThe repository context follows."
    for line in open(commits):
        short, slug, sha = line.split()
        full, always_on, sections = split(os.path.join(repos_dir, short), slug, sha)
        write_arm(os.path.join(out, "monolithic", short), base + lead + "\n\n" + full, [])
        index = "".join(f"- `{s}`: {d}.\n" for s, d, _ in sections)
        c2 = (base + lead + " Its package layout is split into sections listed below; load a section with `load_skill`"
              " when you need it.\n\n" + always_on + index)
        write_arm(os.path.join(out, "tiered", short), c2, sections)
        print(f"{short}: monolithic prompt {len((base + lead + full).split())} words | tiered prompt {len(c2.split())} words | "
              f"{len(sections)} on-demand sections | same-text control passed")
