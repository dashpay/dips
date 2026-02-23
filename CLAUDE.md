# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is the **Dash Improvement Proposals (DIPs)** repository — a collection of technical specification documents for the Dash cryptocurrency protocol. Similar to Bitcoin's BIPs, each DIP describes a new feature, protocol change, or informational specification unique to Dash. This is a documentation-only repo with no application code.

## Repository Structure

- Each DIP is a markdown file at the root: `dip-NNNN.md` (zero-padded 4-digit number)
- Some DIPs have companion directories `dip-NNNN/` containing images, JSON schemas, supplementary documents, or scripts
- `README.md` contains the master table of all DIPs with their number, layer, title, owner, type, and status
- Gaps in numbering are intentional (e.g., no DIP 17-19)

## DIP Document Format

Every DIP begins with a metadata header in `<pre>` tags:

```
<pre>
  DIP: NNNN
  Title: ...
  Author(s): ...
  Comments-Summary: ...
  Status: Proposed | Final | Withdrawn
  Type: Standard | Informational
  Created: YYYY-MM-DD
  License: MIT License
</pre>
```

Some DIPs include additional fields like `Chain`, `Special-Thanks`, or `Requires`. The body follows BIP 2 style conventions with sections like Abstract, Motivation, Specification, and Copyright.

## Linting

Markdown linting runs on PRs via GitHub Actions (`.github/workflows/markdownlint.yml`). Only changed `.md` files are linted.

```bash
# Run locally (requires markdownlint-cli2)
npx markdownlint-cli2 "dip-0031.md" --config .markdownlint.json
```

### Markdownlint Configuration (`.markdownlint.json`)

Key rule overrides:
- **MD004**: List style must use asterisks (`*`), not dashes
- **MD013**: Line length limit is **disabled** (long lines are allowed)
- **MD033**: Inline HTML is **allowed** (needed for `<pre>` headers and images)
- **MD041**: First-line-heading rule is **disabled** (DIPs start with `<pre>` block)

## Editing Guidelines

- When adding a new DIP, also add its entry to the summary table in `README.md`
- DIP numbers are assigned by editors — drafts should use an alias name, not a self-assigned number
- Place supporting assets (images, JSON, scripts) in a `dip-NNNN/` directory matching the DIP number
- Use asterisks for unordered lists, not dashes (enforced by MD004)
