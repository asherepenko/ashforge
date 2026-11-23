#!/usr/bin/env python3
"""resolve-doc.py — map a Material component/topic name to its raw docs URL.

The catalog below is the single source for which doc file backs which name;
SKILL.md no longer carries a copy that could drift from it.

Usage:  resolve-doc.py [<component-or-topic> ...]
  Words are joined; case, spaces, hyphens and underscores are ignored.
  No argument → print the catalog (category<TAB>name<TAB>file).
Output (match): URL=<raw url>  LABEL=<source label>  NAME=  CATEGORY=  FILE=
Exit:   0 resolved (or catalog printed) · 3 ambiguous (candidates on stdout,
        one `CANDIDATE=<name>` per line) · 4 unknown topic
"""
import re
import sys

BASE = "https://raw.githubusercontent.com/material-components/material-components-android/master/docs/"

# category | name | file | aliases (comma-separated, already normalized; the
# name is always a key, so list the file stem here when it differs)
CATALOG = """\
components|BadgeDrawable|BadgeDrawable.md|badge
components|Banner|Banner.md|
components|BottomAppBar|BottomAppBar.md|
components|BottomNavigation|BottomNavigation.md|bottomnav
components|BottomSheet|BottomSheet.md|
components|Buttons (overview)|Button.md|buttonindex
components|ButtonGroup|ButtonGroup.md|
components|Card|Card.md|cards
components|Carousel|Carousel.md|
components|Checkbox|Checkbox.md|
components|Chip|Chip.md|chips
components|Common Buttons|CommonButton.md|button,buttons,commonbutton
components|DataTable|DataTable.md|
components|DatePicker|DatePicker.md|
components|Dialog|Dialog.md|dialogs
components|Divider|Divider.md|
components|DockedFloatingToolbars|DockedFloatingToolbars.md|
components|DockedToolbar|DockedToolbar.md|
components|Extended FAB|ExtendedFloatingActionButton.md|extendedfloatingactionbutton
components|FAB|FloatingActionButton.md|floatingactionbutton
components|FAB Menu|FloatingActionButtonMenu.md|floatingactionbuttonmenu
components|FloatingToolbar|FloatingToolbar.md|
components|IconButton|IconButton.md|
components|ImageList|ImageList.md|
components|List|List.md|lists
components|LoadingIndicator|LoadingIndicator.md|
components|MaterialTextView|MaterialTextView.md|
components|Menu|Menu.md|menus
components|NavigationDrawer|NavigationDrawer.md|drawer
components|NavigationRail|NavigationRail.md|rail
components|OverflowLinearLayout|OverflowLinearLayout.md|
components|ProgressIndicator|ProgressIndicator.md|
components|RadioButton|RadioButton.md|
components|Search|Search.md|
components|SideSheet|SideSheet.md|
components|Slider|Slider.md|
components|Snackbar|Snackbar.md|
components|SplitButton|SplitButton.md|
components|Switch|Switch.md|
components|Tabs|Tabs.md|tab
components|TextField|TextField.md|
components|TimePicker|TimePicker.md|
components|ToggleButtonGroup|ToggleButtonGroup.md|
components|Tooltip|Tooltip.md|
components|TopAppBar|TopAppBar.md|
theming|Color|Color.md|colour
theming|Dark Theme|Dark.md|dark
theming|Motion|Motion.md|
theming|Shape|Shape.md|
theming|Typography|Typography.md|type
foundations|Predictive Back|PredictiveBack.md|
adaptive|Canonical Layouts|CanonicalLayouts.md|
top|Getting Started|getting-started.md|
"""


def norm(s):
    return re.sub(r"[ _-]", "", s.lower())


def rows():
    for line in CATALOG.splitlines():
        cat, name, file, aliases = line.split("|")
        yield cat, name, file, [a for a in aliases.split(",") if a]


def resolve(words):
    """Returns (exit_code, stdout_lines, stderr_line)."""
    q = norm(" ".join(words))
    if not q:
        return 4, [], "empty topic"
    exact, partial = [], []
    for cat, name, file, aliases in rows():
        # File stems are not keys: Button.md's stem would tie with the `button` alias.
        keys = [norm(name)] + aliases
        if q in keys:
            exact.append((cat, name, file))
        elif any(q in k for k in keys):
            partial.append((cat, name, file))
    pick = exact or partial
    topic = " ".join(words)
    if not pick:
        return 4, [], f"unknown topic: {topic}"
    if len(pick) > 1:
        return 3, [f"CANDIDATE={n}" for _, n, _ in pick], f"ambiguous topic: {topic} ({len(pick)} matches)"
    cat, name, file = pick[0]
    stem = file[:-3] if file.endswith(".md") else file
    if cat == "top":
        url, label = BASE + file, f"material-{stem}"
    elif cat == "components":
        url, label = f"{BASE}{cat}/{file}", f"material-{stem}"
    else:
        url, label = f"{BASE}{cat}/{file}", f"material-{cat}-{stem}"
    return 0, [f"URL={url}", f"LABEL={label}", f"NAME={name}", f"CATEGORY={cat}", f"FILE={file}"], ""


def main(argv):
    if not argv:
        for cat, name, file, _ in rows():
            print(f"{cat}\t{name}\t{file}")
        return 0
    code, out, err = resolve(argv)
    for line in out:
        print(line)
    if err:
        print(err, file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
