# Repository maintenance

This repository is the reusable Agent Footprint skill, not a record of any user's machine.

- Keep the content general: no personal paths, account names, device UDIDs, private project names, or machine-specific settings. Examples use placeholders or generic names.
- Keep SKILL.md short and put platform detail in references/. Keep the English instructions consistent with the Chinese README, prompts, and rule block.
- scripts/audit.py stays read-only: it must not delete, move, or write anything except its report on standard output, must not follow symbolic links, and must not read privacy-protected folders by default.
- Tool facts (locations, retention behavior, commands) change between versions. State observations with their context and verify them before relying on them.
- Run `python3 scripts/check_public.py` for package changes. Review staged content and outgoing history separately before publishing; the script is not a full secret scanner.
- Upstream changes are maintainer-only. Do not add PR invitations or publish, push, change repository settings, or create a release without task authorization.
