#!/usr/bin/env python3
"""Sweep patterns must count code only: comments and string literals are blanked, except where the sweep targets strings."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "skills" / "android-conventions" / "scripts" / "detect-patterns.py"
KEY = "A" * 40

# (category, sweep id, file name, source, counts) - a file counts once when the pattern matches code.
CASES = [
    ("di", "hilt", "A.kt", "@HiltViewModel\nclass A\n", 1),
    ("di", "hilt", "A.kt", "// @HiltViewModel\nclass A\n", 0),
    ("di", "hilt", "A.kt", "/** Annotated with @HiltViewModel */\nclass A\n", 0),
    ("di", "hilt", "A.java", "// @InstallIn(Foo.class)\nclass A {}\n", 0),
    ("di", "hilt", "A.java", "@InstallIn(Foo.class)\nclass A {}\n", 1),
    ("di", "dagger", "A.kt", "/* @Component */\nclass A\n", 0),
    ("di", "dagger", "A.kt", "/* /* @Component */ */\nclass A\n", 0),
    ("di", "dagger", "A.kt", "/* /* inner */ @Component */\nclass A\n", 0),
    ("di", "dagger", "A.kt", "/* a */\n@Component\ninterface C\n", 1),
    ("di", "dagger", "A.java", "/* /* @Component */\n@Component\ninterface C {}\n", 0),
    ("di", "dagger", "A.kt", 'val s = "@Component"\n', 0),
    ("di", "koin", "A.kt", 'val s = "startKoin"\n// koinViewModel\n', 0),
    ("di", "koin", "A.kt", "startKoin { }\n", 1),
    ("testing", "mockk", "A.kt", 'val s = "every { }"\n', 0),
    ("testing", "mockk", "A.kt", "/** Use @MockK here */\nclass A\n", 0),
    ("testing", "mockk", "A.kt", "@MockK lateinit var x: X\n", 1),
    ("testing", "mockk", "A.kt", "every { x.y() } returns 1\n", 1),
    ("testing", "mockk", "A.kt", "val a = 'x'\nevery { x.y() } returns 1\n", 1),
    ("testing", "mockk", "A.kt", "val q = '\"'\nevery { x.y() } returns 1\n", 1),
    ("testing", "mockito", "A.java", '// verify(x)\nString s = "mock(";\n', 0),
    ("testing", "mockito", "A.java", "verify(x).y();\n", 1),
    ("architecture", "compose", "A.kt", 'val s = """@Composable"""\n', 0),
    ("architecture", "compose", "A.kt", 'val s = """\n@Composable\n"""\n', 0),
    ("architecture", "compose", "A.kt", '// @Composable\nval s = "@Composable"\n', 0),
    ("architecture", "compose", "A.kt", "@Composable\nfun F() {}\n", 1),
    ("architecture", "viewmodel", "A.java", 'String s = """\n  extends ViewModel\n  """;\n', 0),
    ("architecture", "viewmodel", "A.java", "class A extends ViewModel {}\n", 1),
    ("architecture", "presenter", "A.kt", "// Presenter\n", 0),
    ("state", "stateflow", "A.kt", "// val x: StateFlow<Int>\n", 0),
    ("state", "stateflow", "A.kt", "val x: StateFlow<Int>\n", 1),
    ("state", "livedata", "A.java", "/* LiveData<Foo> */\n", 0),
    ("performance", "global_scope", "A.kt", "// GlobalScope.launch\n", 0),
    ("performance", "global_scope", "A.kt", "GlobalScope.launch {}\n", 1),
    ("accessibility", "clickable", "A.kt", "// Modifier.clickable\n", 0),
    ("accessibility", "icon_without_content_description", "A.kt", 'val s = "Icon("\n', 0),
    ("accessibility", "icon_without_content_description", "A.kt", "Icon(x)\n", 1),
    ("accessibility", "icon_without_content_description", "A.kt", 'Icon(x, contentDescription = "a")\n', 0),
    # string-targeting sweep keeps raw text
    ("security", "hardcoded_secrets", "A.kt", f'val key = "{KEY}"\n', 1),
    ("security", "hardcoded_secrets", "A.kt", 'val key = "short"\n', 0),
    ("security", "certificate_pinning", "A.kt", "// CertificatePinner\n", 0),
    ("security", "certificate_pinning", "A.kt", "CertificatePinner.Builder()\n", 1),
    ("security", "encrypted_storage", "A.kt", 'val s = "MasterKey"\n', 0),
]


def counts(project: Path, category: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(project), category], capture_output=True, text=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stderr
    found = {}
    for line in result.stdout.splitlines():
        words = line.split()
        if words[:1] == ["count"]:
            found[words[1]] = int(words[2].split("=")[1])
        elif len(words) == 3 and words[1].startswith("files=") and words[2].startswith("share="):
            found[words[0]] = int(words[1].split("=")[1])
    return found


@pytest.mark.parametrize("category,ident,name,source,expected", CASES, ids=[f"{i}-{c[1]}" for i, c in enumerate(CASES)])
def test_sweep_counts_code_only(tmp_path, category, ident, name, source, expected):
    folder = tmp_path / "app" / "src" / "main"
    folder.mkdir(parents=True)
    (folder / name).write_text(source, encoding="utf-8")
    assert counts(tmp_path, category)[ident] == expected


def test_block_comment_and_raw_string_state_do_not_leak_across_lines(tmp_path):
    folder = tmp_path / "app" / "src" / "main"
    folder.mkdir(parents=True)
    head = '/* open\n@Component\n*/\nval a = """\n@Component\n"""\n'
    (folder / "A.kt").write_text(head + "@Component\ninterface Real\n", encoding="utf-8")
    assert counts(tmp_path, "di")["dagger"] == 1
    (folder / "A.kt").write_text(head, encoding="utf-8")
    assert counts(tmp_path, "di")["dagger"] == 0


def test_xml_is_not_stripped(tmp_path):
    folder = tmp_path / "app" / "src" / "main" / "res" / "xml"
    folder.mkdir(parents=True)
    (folder / "net.xml").write_text('<a android:usesCleartextTraffic="true"/>\n', encoding="utf-8")
    assert counts(tmp_path, "security")["cleartext_traffic"] == 1


def load_script():
    spec = importlib.util.spec_from_file_location("detect_patterns", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STRIP = [
    ("a // c\nb", "a \nb"),
    ("a /* c\nd */ b", "a \n b"),
    ("/* a /* b\n*/ c */ d", "\n d"),
    ('x "a\\"b" y', 'x "" y'),
    ('x """a\n"b\\""" y', 'x """\n""" y'),
    ('"a${ f("}") + {1} }b" y', '"" y'),
    ("x 'a' y '\\u0041' z", "x '' y '' z"),
    ("x '\"' y '\\'' z", "x '' y '' z"),
    ('"a${"b"}c" d', '"" d'),
    ('"unterminated\nnext', '""\nnext'),
]


@pytest.mark.parametrize("source,expected", STRIP)
def test_strip_code(source, expected):
    out = load_script().strip_code(source)
    assert out == expected
    assert out.count("\n") == source.count("\n")
