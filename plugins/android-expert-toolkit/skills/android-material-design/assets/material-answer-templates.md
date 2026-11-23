# Material answer templates

Pick the shape that matches the question. Fill only what the fetched doc supports; leave a row out rather than guess a default.

## "How do I implement X"

```markdown
## Material Design: {Component}

**Toolkit**: {Compose or Views} · **Source**: {page url} · **M3 spec**: {m3.material.io link} · **API**: {developer.android.com reference link}

### When to use
{the variant whose documented purpose fits, from the doc's purpose table}

### Implementation
{Compose or XML example from the doc}

### Key parameters or attributes
| Parameter / attribute | Description | Default |
|-----------------------|-------------|---------|

### Styles or variants
| Style / composable | Description |
|--------------------|-------------|

### Notes
- {M3 Expressive styles, sizes, shapes — when the doc covers them}
- {Deprecated variants and their replacements}
- {Theming and accessibility notes}
```

## Theming question

```markdown
## Material Design: {Topic}

**Toolkit**: {Compose or Views} · **Source**: {page url}

### Setup
{theme configuration steps}

### Attributes
{relevant theme attributes table}

### Code example
{Compose, XML or programmatic example}
```

## "Which component should I use"

- Recommend from the toolkit's page list: the Compose components table in material-compose, or the Views catalog (`resolve-doc.py` with no argument).
- When comparing, fetch each candidate's page (Views: its `--toc`) and contrast the sections that differ.
- Link the M3 guidelines page for each.
