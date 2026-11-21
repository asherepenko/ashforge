#!/usr/bin/env python3
"""Sweep patterns must not count words from other frameworks, comments or substrings."""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT = PROJECT_ROOT / "skills" / "ios-conventions" / "scripts" / "detect-patterns.py"

# (category, sweep id, source, counts) - a file counts once when the pattern matches code.
CASES = [
    # @Reducer
    ("architecture", "tca", "@Reducer\nstruct F {}\n", 1),
    ("architecture", "tca", "@Reducer(state: .equatable)\nenum D {}\n", 1),
    ("architecture", "tca", "// @Reducer struct Old {}\n", 0),
    ("architecture", "tca", "/* @Reducer\n struct Old {} */\n", 0),
    ("architecture", "tca", '/// Uses `@Reducer` macros\nlet s = "@Reducer"\n', 0),
    ("architecture", "tca", "func f(@ReducerBuilder<S, A> body: () -> R) {}\n", 0),
    # @Observable
    ("architecture", "mvvm_observable", "@Observable final class M {}\n", 1),
    ("architecture", "mvvm_observable", "@MainActor @Observable\nclass M {}\n", 1),
    ("architecture", "mvvm_observable", "@ObservableState struct S {}\n", 0),
    ("architecture", "mvvm_observable", "// @Observable class Old {}\n", 0),
    ("architecture", "mvvm_observable", "let x = Observable<Int>.just(1)\n", 0),
    # ObservableObject
    ("architecture", "mvvm_object", "final class VM: ObservableObject {}\n", 1),
    ("architecture", "mvvm_object", "final class VM<T: Equatable>: Base, ObservableObject {\n}\n", 1),
    ("architecture", "mvvm_object", "// final class VM: ObservableObject {}\n", 0),
    ("architecture", "mvvm_object", "final class Box<T: ObservableObject>: NSObject {}\n", 0),
    ("architecture", "mvvm_object", "class func make(x: ObservableObject) {}\n", 0),
    ("architecture", "mvvm_object", "final class A: Base where P == ObservableObjectPublisher {}\n", 0),
    # UIViewController
    ("architecture", "uikit", "final class H: UIViewController {}\n", 1),
    ("architecture", "uikit", "final class H: UITableViewController {}\n", 1),
    ("architecture", "uikit", "// class H: UIViewController {}\n", 0),
    ("architecture", "uikit", "final class A: UIViewControllerTransitioningDelegate {}\n", 0),
    ("architecture", "uikit", "final class A: UIViewControllerRepresentable {}\n", 0),
    # DI
    ("di", "tca_dependency", "@Dependency(\\.date) var date\n", 1),
    ("di", "tca_dependency", "enum K: DependencyKey {}\n", 1),
    ("di", "tca_dependency", "// @Dependency(\\.date) var date\n", 0),
    ("di", "tca_dependency", "@DependencyClient struct C {}\n", 0),
    ("di", "tca_dependency", "struct K: MyDependencyKeyed {}\n", 0),
    ("di", "singleton", "static let shared = Foo()\n", 1),
    ("di", "singleton", "static let sharedInstance = 1\n", 0),
    ("di", "singleton", "// static let shared = Foo()\n", 0),
    ("di", "factory", "let f = ViewFactory()\n", 1),
    ("di", "factory", "func makeFeedViewModel() -> FeedViewModel {}\n", 1),
    ("di", "factory", "import Factory\n", 1),
    ("di", "factory", "func makeUIView(context: Context) -> V {}\n", 0),
    ("di", "factory", "func makeUIViewController(context: Context) -> V {}\n", 0),
    ("di", "factory", "func makeCoordinator() -> Coordinator {}\n", 0),
    ("di", "factory", "func makeBody(configuration: Configuration) -> some View {}\n", 0),
    ("di", "factory", "func makeIterator() -> Iter {}\n", 0),
    ("di", "factory", 'let s = "Factory"\n// ViewFactory\n', 0),
    ("di", "factory", "let manufactory = 1\n", 0),
    # testing
    ("testing", "swift_testing", "import Testing\n", 1),
    ("testing", "swift_testing", "@testable import Testing\n", 1),
    ("testing", "swift_testing", "import TestingSupport\n", 0),
    ("testing", "swift_testing", "// import Testing\n", 0),
    ("testing", "xctest", "final class T: XCTestCase {}\n", 1),
    ("testing", "xctest", "import XCTest\nimport Testing\n@Suite struct S {}\n", 0),
    ("testing", "xctest", "// XCTestCase is gone\nlet x = XCTestCaseEntry.self\n", 0),
    # persistence
    ("persistence", "swiftdata", "@Model final class Item {}\n", 1),
    ("persistence", "swiftdata", "@ModelActor actor Store {}\n", 0),
    ("persistence", "swiftdata", "// @Model\n", 0),
    ("persistence", "core_data", "final class E: NSManagedObject {}\n", 1),
    ("persistence", "core_data", "// NSManagedObject subclass\n", 0),
    # navigation
    ("navigation", "navigation_stack", "NavigationStack { Text(\"\") }\n", 1),
    ("navigation", "navigation_stack", ".navigationDestination(for: Int.self) { _ in }\n", 1),
    ("navigation", "navigation_stack", "var navigationDestination: Route?\n", 0),
    ("navigation", "navigation_stack", "struct AppNavigationStackWrapper {}\n", 0),
    ("navigation", "navigation_stack", "// NavigationStack\n", 0),
    ("navigation", "coordinator", "final class AppCoordinator: Coordinator {}\n", 1),
    ("navigation", "coordinator", "protocol Coordinator: AnyObject {}\n", 1),
    ("navigation", "coordinator", "let nav = UINavigationController()\n", 1),
    ("navigation", "coordinator", "final class Coordinator: NSObject {}\n", 0),
    ("navigation", "coordinator", "func makeCoordinator() -> Coordinator { Coordinator() }\n", 0),
    ("navigation", "coordinator", "let c = NSPersistentStoreCoordinator(model: m)\n", 0),
    ("navigation", "coordinator", "class C: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {}\n", 0),
    ("navigation", "coordinator", "// AppCoordinator\n", 0),
    ("concurrency", "main_actor", "@MainActor final class A {}\n", 1),
    ("concurrency", "main_actor", "// @MainActor\n", 0),
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


@pytest.mark.parametrize("category,ident,source,expected", CASES, ids=[f"{i}-{c[1]}" for i, c in enumerate(CASES)])
def test_sweep_counts_code_only(tmp_path, category, ident, source, expected):
    (tmp_path / "Sources").mkdir()
    folder = "Tests" if category == "testing" else "Sources"
    (tmp_path / folder).mkdir(exist_ok=True)
    (tmp_path / folder / "Sample.swift").write_text(source, encoding="utf-8")
    assert counts(tmp_path, category)[ident] == expected


def test_package_manifest_comment_is_not_a_language_mode_setting(tmp_path):
    (tmp_path / "Package.swift").write_text("// swiftLanguageModes: [.v6]\n", encoding="utf-8")
    assert counts(tmp_path, "concurrency")["language_mode_settings"] == 0
    (tmp_path / "Package.swift").write_text("let p = Package(swiftLanguageModes: [.v6])\n", encoding="utf-8")
    assert counts(tmp_path, "concurrency")["language_mode_settings"] == 1


def test_version_facts_ignore_a_commented_language_mode(tmp_path):
    (tmp_path / "Package.swift").write_text("// swiftLanguageModes: [.v5]\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path), "version"], capture_output=True, text=True, check=True
    )
    assert "swift_language_modes=none" in result.stdout


def test_block_comment_and_string_state_do_not_leak_across_lines(tmp_path):
    (tmp_path / "Sources").mkdir()
    source = '/* open\n@Reducer\n*/\nlet a = """\n@Reducer\n"""\n@Reducer struct Real {}\n'
    (tmp_path / "Sources/Sample.swift").write_text(source, encoding="utf-8")
    assert counts(tmp_path, "architecture")["tca"] == 1
    (tmp_path / "Sources/Sample.swift").write_text('/* open\n@Reducer\n*/\nlet a = """\n@Reducer\n"""\n', encoding="utf-8")
    assert counts(tmp_path, "architecture")["tca"] == 0
