# Third-party notices

The vendored skills below are copied unmodified, except swiftui-pro (a fork), by `scripts/sync-ios-skills.sh`.
Pinned commits and the Xcode build are recorded in `ios-skills.lock`. The rest of
this plugin is MIT (see `LICENSE`).

## Community skills

Each skill keeps its upstream `LICENSE` file next to its `SKILL.md`.

### swift-concurrency

- Repo: [AvdLee/Swift-Concurrency-Agent-Skill](https://github.com/AvdLee/Swift-Concurrency-Agent-Skill)
- Commit: `d5770817d2622e1585b1f7eaebc791a9cb0959c8`
- Copyright (c) 2026 Antoine van der Lee. MIT License.

### swift-testing-expert

- Repo: [AvdLee/Swift-Testing-Agent-Skill](https://github.com/AvdLee/Swift-Testing-Agent-Skill)
- Commit: `798e9b1a2bcac164d4f0c781908199e754f0bab6`
- Copyright (c) 2026 Antoine van der Lee. MIT License.

### swiftdata-pro

- Repo: [twostraws/SwiftData-Agent-Skill](https://github.com/twostraws/SwiftData-Agent-Skill)
- Commit: `8051f177a0076e7fd45bdf4ee687b070ba58fdc6`
- Copyright (c) 2026 Paul Hudson. MIT License.

### swiftui-pro

A modified fork, not a copy: `SKILL.md` and `references/views.md` are changed and
three upstream references are removed (see `skills/swiftui-pro/FORK.md`). The other
references are byte-identical to upstream; their sha256 are in `ios-skills.lock`.

- Repo: [twostraws/SwiftUI-Agent-Skill](https://github.com/twostraws/SwiftUI-Agent-Skill)
- Commit: `f9800713b24580bc444931949aad4519128605e8` (tag `2.0.0`)
- Copyright (c) 2026 Paul Hudson. MIT License. Upstream `LICENSE` is kept in `skills/swiftui-pro/`.

## Xcode skills (Apple Inc.)

Each skill below is © Apple Inc., exported from Xcode 27.2 (27B52) with
`xcrun agent skills export`. Apple states no licence for these files.

- `swiftui-specialist`
- `swiftui-whats-new-27`
- `app-intents-specialist`
- `app-intents-whats-new-27`
- `xctrace`
- `modernize-tests`
- `audit-xcode-security-settings`
- `app-resizability`
- `device-interaction`
