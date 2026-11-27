#!/usr/bin/env python3
"""Check this package's working files. Does not audit Git history or all secrets."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    '.gitignore', 'AGENTS.md', 'CONTRIBUTING.md', 'LICENSE',
    'README.md', 'README.zh-CN.md', 'SKILL.md', 'agents/openai.yaml',
    'assets/AGENTS.block.md', 'assets/AGENTS.block.zh-CN.md',
    'references/apple.md', 'references/packages.md',
    'references/agent-data.md', 'references/measuring.md',
    'prompts/install.md', 'prompts/install.zh-CN.md',
    'prompts/audit.md', 'prompts/audit.zh-CN.md',
    'scripts/audit.py', 'scripts/check_public.py',
}
PATTERNS = {
    'personal home path': re.compile(r'(?:/Users/|/home/)[A-Za-z0-9_.-]+|[A-Za-z]:\\Users\\[^\s\\]+'),
    'device or session identifier': re.compile(r'\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b'),
    'private key header': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
    'token-shaped value': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{32,})\b'),
    'email address': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
}
LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')


def main():
    errors = []
    found = set()
    texts = {}
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == '.git' or '__pycache__' in rel.parts or rel.name == '.DS_Store':
            continue
        if path.is_symlink():
            errors.append(f'{rel}: symlinks are not part of the public package')
            continue
        if not path.is_file():
            continue
        name = rel.as_posix()
        found.add(name)
        if name not in ALLOWED:
            errors.append(f'{name}: outside public file allowlist')
            continue
        raw = path.read_bytes()
        if len(raw) > 256_000:
            errors.append(f'{name}: unexpectedly large file')
        try:
            content = raw.decode('utf-8')
        except UnicodeDecodeError:
            errors.append(f'{name}: expected UTF-8 text')
            continue
        texts[name] = content
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                line = content.count('\n', 0, match.start()) + 1
                errors.append(f'{name}:{line}: {label} (value redacted)')
        if path.suffix == '.md':
            for link in LINK.findall(content):
                if '://' in link or link.startswith(('#', 'mailto:')):
                    continue
                target = link.split('#', 1)[0]
                resolved = (path.parent / target).resolve()
                if ROOT not in resolved.parents and resolved != ROOT or not resolved.is_file():
                    errors.append(f'{name}: missing or external local link: {target}')
    for name in sorted(ALLOWED - found):
        errors.append(f'{name}: required public file missing')
    skill = texts.get('SKILL.md', '')
    if not skill.startswith('---\nname: agent-footprint\ndescription: ') or '\n---\n' not in skill[4:]:
        errors.append('SKILL.md: missing expected skill frontmatter')
    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1
    print(f'PASS: {len(found)} allowed text files; local links and basic metadata resolve.')
    print('Scope: working files only; no full secret scan, Git history audit, or platform execution.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
