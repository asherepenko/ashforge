# Changelog

All notable changes to the iOS Expert Toolkit plugin.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html): major for removed or renamed skills and agents, minor for new ones, patch for docs and reference fixes.

## [1.0.0] - 2026-11-03

### Added

- Plugin scaffold: Claude and Codex manifests, the Xcode MCP (`xcrun mcpbridge`), and maintainer docs.
- Claude manifest lists skill groups: `./skills/`, `./skills/community/`, `./skills/xcode/`. Codex scans `./skills/` recursively.
