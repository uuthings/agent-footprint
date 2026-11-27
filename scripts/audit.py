#!/usr/bin/env python3
"""Read-only report of what coding-agent work left on this Mac.

Lists simulators, Xcode derived data, project build output and test result
bundles, temporary-folder leftovers, agent data, and shared caches with sizes
and last use. It never deletes, moves, or changes anything and does not follow
symbolic links. Sizes come from `du` (allocated blocks); clones and hard links
can make them larger than what removal would free.
"""
import argparse
import datetime as dt
import json
import os
import plistlib
import subprocess
import time
from pathlib import Path

HOME = Path.home()
NOW = time.time()
DAY = 86400.0
RELEASE_MARKERS = (".xcarchive", ".dmg", ".pkg", ".ipa", "releasearchives", "releases")
SKIP_DIRS = {".git", "node_modules", "pods", ".venv", "venv", "__pycache__", ".gradle", ".swiftpm", "deriveddata", ".build"}
BUNDLE_SUFFIXES = (".app", ".xcarchive", ".framework", ".xcframework", ".bundle", ".xcresult", ".appex")


def run(args, timeout=300):
    """stdout of a command, or None. A non-zero exit still returns output (du reports unreadable files that way)."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout


def sizes_kb(paths, chunk=100):
    """Allocated size per path in KB. Paths are measured in batches; `du` counts a
    hard-linked file once per batch, so a later path in the batch can read smaller."""
    found = {}
    paths = [str(p) for p in paths]
    for start in range(0, len(paths), chunk):
        batch = paths[start:start + chunk]
        out = run(["du", "-sk", "--"] + batch, timeout=1800) or ""
        for line in out.splitlines():
            size, _, name = line.partition("\t")
            try:
                found[name] = int(size)
            except ValueError:
                continue
    return {p: found.get(p) for p in paths}


def size_kb(path):
    return sizes_kb([path]).get(str(path))


def human(kb):
    if kb is None:
        return "?"
    value = kb * 1024.0
    for unit, factor in (("TB", 1e12), ("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if value >= factor:
            return "%.1f %s" % (value / factor, unit)
    return "%d B" % value


def ago(timestamp):
    if timestamp is None:
        return "never"
    days = int((NOW - timestamp) // DAY)
    return "today" if days <= 0 else "%d d ago" % days


def mtime(path):
    try:
        return os.lstat(path).st_mtime
    except OSError:
        return None


def birth(path):
    try:
        info = os.lstat(path)
    except OSError:
        return None
    return getattr(info, "st_birthtime", info.st_mtime)


def short(path):
    text = str(path)
    home = str(HOME)
    return "~" + text[len(home):] if text.startswith(home) else text


def table(headers, rows, limit=None):
    shown = rows if limit is None else rows[:limit]
    if not shown:
        print("  (none)")
        return
    widths = [max(len(str(h)), *(len(str(r[i])) for r in shown)) for i, h in enumerate(headers)]
    print("  " + "  ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    for row in shown:
        print("  " + "  ".join(str(c).ljust(w) for c, w in zip(row, widths)))
    if limit is not None and len(rows) > limit:
        print("  ... %d more" % (len(rows) - limit))


def section(title):
    print("\n## " + title)


def has_release_material(path):
    try:
        names = [n.lower() for n in os.listdir(path)]
    except OSError:
        return False
    return any(n.endswith(RELEASE_MARKERS[:4]) or n in RELEASE_MARKERS[4:] for n in names)


def latest_activity(path, depth=2):
    """Newest modification time among a folder and its first levels (cheap estimate)."""
    newest = mtime(path)
    frontier = [Path(path)]
    for _ in range(depth):
        nxt = []
        for folder in frontier:
            try:
                entries = list(os.scandir(folder))
            except OSError:
                continue
            for entry in entries[:500]:
                try:
                    stamp = entry.stat(follow_symlinks=False).st_mtime
                except OSError:
                    continue
                newest = max(newest or 0, stamp)
                if entry.is_dir(follow_symlinks=False):
                    nxt.append(Path(entry.path))
        frontier = nxt[:200]
    return newest


# ---------------------------------------------------------------- simulators

def simctl_path():
    developer = (run(["xcode-select", "-p"], timeout=20) or "").strip()
    for folder in (developer, "/Applications/Xcode.app/Contents/Developer"):
        if folder:
            tool = Path(folder) / "usr/bin/simctl"
            if os.access(str(tool), os.X_OK):
                return str(tool)
    return None


def runtime_title(identifier):
    last = identifier.split(".")[-1]
    parts = last.split("-")
    if len(parts) >= 2 and parts[0] and all(p.isdigit() for p in parts[1:]):
        name = "visionOS" if parts[0] == "xrOS" else parts[0]
        return name + " " + ".".join(parts[1:])
    return last


def parse_iso(value):
    if not value:
        return None
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()
    except ValueError:
        return None


def record_last_use(data_path):
    if not data_path:
        return None
    plist = Path(data_path).parent / "device.plist"
    try:
        with open(plist, "rb") as handle:
            record = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException, ValueError):
        return None
    value = record.get("lastUsedAt") or record.get("lastBootedAt")
    return value.timestamp() if isinstance(value, dt.datetime) else None


def report_simulators(tool, days, top):
    section("Simulators")
    if not tool:
        print("  Xcode's simctl was not found; simulators are not listed.")
        return 0
    out = run([tool, "list", "-j", "devices"], timeout=120)
    try:
        devices = json.loads(out)["devices"] if out else {}
    except ValueError:
        devices = {}
    rows, total, stale = [], 0, 0
    for runtime, entries in devices.items():
        for device in entries:
            used = parse_iso(device.get("lastUsedAt")) or record_last_use(device.get("dataPath"))
            folder = Path(device["dataPath"]).parent if device.get("dataPath") else None
            data_bytes = device.get("dataPathSize")
            kb = int(data_bytes) // 1024 if isinstance(data_bytes, (int, float)) else (size_kb(folder) if folder else None)
            total += kb or 0
            state = device.get("state", "?")
            notes = []
            if state != "Shutdown":
                notes.append("in use")
            if device.get("isAvailable") is False:
                notes.append("runtime missing")
            reference = used if used is not None else (birth(folder) if folder else None)
            if state == "Shutdown" and reference is not None and NOW - reference >= days * DAY:
                notes.append("unused %d+ days" % days)
                stale += kb or 0
            rows.append((kb or 0, device.get("name", "?"), runtime_title(runtime), state, ago(used),
                         human(kb), ", ".join(notes), device.get("udid", "")))
    rows.sort(key=lambda r: r[0], reverse=True)
    table(("name", "system", "state", "last used", "size", "note", "udid"), [r[1:] for r in rows], top)
    print("  %d devices, %s; unused %d+ days: %s." % (len(rows), human(total), days, human(stale)))
    print("  Delete only with `xcrun simctl delete <udid>` (irreversible). Remove devices whose runtime is gone with `xcrun simctl delete unavailable`.")

    runtimes_out = run([tool, "runtime", "list", "-j"], timeout=120)
    try:
        runtimes = json.loads(runtimes_out) if runtimes_out else {}
    except ValueError:
        runtimes = {}
    if runtimes:
        print("\n  Runtimes (shared system images; keep unless the user drops that OS version):")
        rrows = sorted(((v.get("platformIdentifier", "").split(".")[-1], v.get("version", "?"),
                         human((v.get("sizeBytes") or 0) // 1024), v.get("state", "?")) for v in runtimes.values()),
                       key=lambda r: r[1])
        table(("platform", "version", "size", "state"), rrows)

    other = [HOME / "Library/Developer/XCTestDevices", HOME / "Library/Developer/Xcode/UserData/Previews/Simulator Devices"]
    extra = [(short(p), human(size_kb(p))) for p in other if p.is_dir()]
    if extra:
        print("\n  Other device sets (parallel testing, SwiftUI previews):")
        table(("folder", "size"), extra)
    return total


# ---------------------------------------------------------------- Xcode and projects

def report_derived_data(days, top):
    section("Xcode derived data (default location)")
    root = HOME / "Library/Developer/Xcode/DerivedData"
    if not root.is_dir():
        print("  (none)")
        return 0
    children = [p for p in root.iterdir() if p.is_dir() and not p.is_symlink()]
    measured = sizes_kb(children)
    rows = []
    for child in children:
        kb = measured.get(str(child))
        active = latest_activity(child)
        note = "used within %d days" % days if active and NOW - active < days * DAY else ""
        rows.append((kb or 0, child.name, ago(active), human(kb), note))
    rows.sort(key=lambda r: r[0], reverse=True)
    table(("project folder", "last change", "size", "note"), [r[1:] for r in rows], top)
    total = sum(r[0] for r in rows)
    print("  Total %s. Rebuilt locally by the next build; keep folders of projects in active use." % human(total))
    return total


def find_project_items(roots, max_depth):
    found = {"xcresult": [], "deriveddata": [], "swiftpm": [], "node_modules": [], "worktrees": []}
    for root in roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        for current, folders, _ in os.walk(str(root), followlinks=False):
            depth = len(Path(current).relative_to(root).parts)
            keep = []
            for name in folders:
                path = Path(current) / name
                lower = name.lower()
                if path.is_symlink():
                    continue
                if lower.endswith(".xcresult"):
                    found["xcresult"].append(path)
                elif name == "node_modules":
                    found["node_modules"].append(path)
                elif name == ".build" and (Path(current) / "Package.swift").is_file():
                    found["swiftpm"].append(path)
                elif lower.endswith("deriveddata"):
                    found["deriveddata"].append(path)
                elif name == "worktrees" and Path(current).name == ".claude":
                    found["worktrees"].append(path)
                elif lower in SKIP_DIRS or lower.endswith(BUNDLE_SUFFIXES) or depth >= max_depth:
                    continue
                else:
                    keep.append(name)
            folders[:] = keep
    return found


def project_of(path, roots):
    for root in roots:
        root = Path(root).expanduser()
        try:
            parts = Path(path).relative_to(root).parts
        except ValueError:
            continue
        return str(root / parts[0]) if parts else str(root)
    return str(Path(path).parent)


def last_commit(folder, cache):
    current = Path(folder)
    while current != current.parent and current != HOME:
        if (current / ".git").exists():
            key = str(current)
            if key not in cache:
                out = run(["git", "-C", key, "log", "-1", "--format=%ct"], timeout=30)
                try:
                    cache[key] = float(out.strip()) if out and out.strip() else None
                except ValueError:
                    cache[key] = None
            return cache[key]
        current = current.parent
    return None


def report_projects(roots, days, stale_days, top):
    section("Project build output (" + ", ".join(short(Path(r).expanduser()) for r in roots) + ")")
    started = time.time()
    found = find_project_items(roots, max_depth=8)
    totals = 0

    bundles = found["xcresult"]
    measured = sizes_kb(bundles)
    groups = {}
    for bundle in bundles:
        groups.setdefault(project_of(bundle, roots), []).append(bundle)
    rows = []
    for project, items in groups.items():
        items.sort(key=lambda p: mtime(p) or 0, reverse=True)
        sizes = [measured.get(str(p)) or 0 for p in items]
        older = [s for p, s in zip(items[1:], sizes[1:]) if (mtime(p) or NOW) < NOW - days * DAY]
        rows.append((sum(sizes), short(project), len(items), ago(mtime(items[0])), human(sum(sizes)),
                     "%d older than %d days: %s" % (len(older), days, human(sum(older)))))
        totals += sum(sizes)
    rows.sort(key=lambda r: r[0], reverse=True)
    print("\nTest result bundles (.xcresult), keep the newest unless a comparison is needed:")
    table(("project", "bundles", "newest", "size", "removable"), [r[1:] for r in rows], top)

    candidates = found["deriveddata"] + found["swiftpm"]
    measured = sizes_kb(candidates)
    rows = []
    for item in candidates:
        kb = measured.get(str(item))
        active = latest_activity(item)
        notes = []
        if active and NOW - active < days * DAY:
            notes.append("used within %d days" % days)
        if has_release_material(item):
            notes.append("contains release files, inspect first")
        kind = "SwiftPM .build" if item.name == ".build" else "derived data"
        rows.append((kb or 0, short(item), kind, ago(active), human(kb), ", ".join(notes)))
        totals += kb or 0
    rows.sort(key=lambda r: r[0], reverse=True)
    print("\nBuild folders (derived data, SwiftPM):")
    table(("folder", "kind", "last change", "size", "note"), [r[1:] for r in rows], top)

    cache = {}
    stale = []
    for item in found["node_modules"]:
        commit = last_commit(item.parent, cache)
        reference = commit if commit is not None else mtime(item.parent / "package.json")
        if reference is not None and NOW - reference >= stale_days * DAY:
            stale.append((item, reference))
    measured = sizes_kb([p for p, _ in stale])
    rows = sorted(((measured.get(str(p)) or 0, short(p), ago(ref), human(measured.get(str(p))))
                   for p, ref in stale), reverse=True)
    print("\nDependencies of projects without commits for %d+ days (reinstall downloads them again):" % stale_days)
    table(("folder", "last commit", "size"), [r[1:] for r in rows], top)
    totals += sum(r[0] for r in rows)

    measured = sizes_kb(found["worktrees"])
    rows = [(short(p), len([c for c in p.iterdir() if c.is_dir()]), human(measured.get(str(p)))) for p in found["worktrees"]]
    print("\nAgent worktrees inside projects (remove merged or abandoned ones with `git worktree remove`):")
    table(("folder", "worktrees", "size"), rows)
    print("  Project scan took %.0f s." % (time.time() - started))
    return totals


# ---------------------------------------------------------------- temporary, agent data, caches

def report_temporary(top):
    section("Temporary folder leftovers")
    # The per-user folder macOS assigns; agents may point TMPDIR at their own scratch area.
    folder = Path((run(["getconf", "DARWIN_USER_TEMP_DIR"], timeout=10) or "").strip() or os.environ.get("TMPDIR") or "/tmp")
    try:
        entries = [p for p in folder.iterdir() if not p.is_symlink()]
    except OSError:
        print("  The temporary folder could not be read.")
        return 0
    measured = sizes_kb(entries)
    rows, old_total = [], 0
    for entry in entries:
        kb = measured.get(str(entry)) or 0
        created = birth(entry)
        old = created is not None and NOW - created >= DAY
        if old:
            old_total += kb
        rows.append((kb, entry.name, ago(created), human(kb), "older than 24 h" if old else "recent"))
    rows.sort(key=lambda r: r[0], reverse=True)
    table(("item", "created", "size", "note"), [r[1:] for r in rows], top)
    print("  %s in items created more than 24 h ago; remove only items no running program uses." % human(old_total))
    return old_total


def month_sizes(folder):
    rows = []
    if folder.is_dir():
        for year in sorted(p for p in folder.iterdir() if p.is_dir() and p.name.isdigit()):
            months = sorted(p for p in year.iterdir() if p.is_dir() and p.name.isdigit())
            measured = sizes_kb(months)
            rows += [(year.name + "-" + m.name, human(measured.get(str(m))), ago(latest_activity(m, depth=2))) for m in months]
    return rows


def report_agent_data():
    section("Agent data (history, not caches; archive rather than delete, and only with consent)")
    codex = HOME / ".codex"
    if codex.is_dir():
        print("Codex:")
        for label, sub in (("sessions", "sessions"), ("screenshots and prototypes", "visualizations")):
            rows = month_sizes(codex / sub)
            if rows:
                print("  %s by month:" % label)
                table(("month", "size", "last change"), rows)
        for sub in ("archived_sessions", "worktrees"):
            path = codex / sub
            if path.is_dir():
                print("  %s: %s" % (short(path), human(size_kb(path))))
    claude = HOME / ".claude"
    if claude.is_dir():
        print("Claude Code:")
        projects = claude / "projects"
        transcripts = list(projects.glob("*/*.jsonl")) if projects.is_dir() else []
        oldest = min((mtime(p) or NOW for p in transcripts), default=None)
        print("  transcripts: %d files, %s, oldest %s" % (len(transcripts), human(size_kb(projects)) if projects.is_dir() else "0", ago(oldest)))
        for path in (claude / "file-history", Path("/private/tmp") / ("claude-%d" % os.getuid()),
                     HOME / "Library/Application Support/Claude/vm_bundles"):
            if path.is_dir():
                print("  %s: %s" % (short(path), human(size_kb(path))))


def report_caches(measure):
    section("Shared caches (clean only when the user asks, with the tool's own command)")
    known = [
        ("npm", HOME / ".npm/_cacache"), ("pnpm store", HOME / "Library/pnpm/store"),
        ("Yarn", HOME / "Library/Caches/Yarn"), ("uv", HOME / ".cache/uv"), ("pip", HOME / "Library/Caches/pip"),
        ("Homebrew", HOME / "Library/Caches/Homebrew"), ("SwiftPM", HOME / "Library/Caches/org.swift.swiftpm"),
        ("CocoaPods", HOME / "Library/Caches/CocoaPods"), ("Gradle", HOME / ".gradle/caches"),
        ("Cargo registry", HOME / ".cargo/registry"), ("Go build", HOME / "Library/Caches/go-build"),
        ("Playwright browsers", HOME / "Library/Caches/ms-playwright"), ("Puppeteer browsers", HOME / ".cache/puppeteer"),
    ]
    present = [(name, path) for name, path in known if path.is_dir()]
    # Caches hold many small files; measuring them takes much longer than everything else.
    measured = sizes_kb([p for _, p in present]) if measure else {}
    rows = [(name, short(p), human(measured.get(str(p))) if measure else "not measured", ago(latest_activity(p, depth=1)))
            for name, p in present]
    table(("cache", "folder", "size", "last change"), rows)
    if not measure:
        print("  Run with --caches to measure their sizes (slow).")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--roots", nargs="+", default=["~/Developer"], help="project folders to scan (default ~/Developer)")
    parser.add_argument("--days", type=int, default=7, help="activity window for devices and build output (default 7)")
    parser.add_argument("--stale-days", type=int, default=180, help="projects without commits this long count as inactive (default 180)")
    parser.add_argument("--top", type=int, default=15, help="rows per table (default 15)")
    parser.add_argument("--quick", action="store_true", help="skip the project scan")
    parser.add_argument("--caches", action="store_true", help="also measure shared cache sizes (slow)")
    args = parser.parse_args()

    print("# Agent footprint audit — %s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("Read-only: nothing was deleted, moved, or changed.")
    out = run(["df", "-k", str(HOME)], timeout=20)
    if out and len(out.splitlines()) > 1:
        fields = out.splitlines()[1].split()
        print("Free space on the home volume: %s of %s" % (human(int(fields[3])), human(int(fields[1]))))
    report_simulators(simctl_path(), args.days, args.top)
    report_derived_data(args.days, args.top)
    if not args.quick:
        report_projects(args.roots, args.days, args.stale_days, args.top)
    report_temporary(args.top)
    report_agent_data()
    report_caches(args.caches)
    print("\nSizes are allocated blocks from du. Clones and hard links can make them larger than what removal frees.")


if __name__ == "__main__":
    main()
