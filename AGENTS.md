# AGENTS.md

## Cautious Coding

---
description: Guidelines to reduce common LLM coding mistakes - biases toward less
  code and caution over speed
alwaysApply: true
---

Behavioural guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward less code and caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## CHANGELOG.md

---
description: Guidelines for maintaining CHANGELOG.md with proper categorization and
  versioning
alwaysApply: false
---

If there is a CHANGELOG.md file, update it with any notable features or bug fixes once these have been successfully implemented.
- When updating the `CHANGELOG.md`, add notable features and fixes, with the following categories:
  - `Added` for new features.
  - `Changed` for changes in existing functionality.
  - `Deprecated` for soon-to-be removed features.
  - `Removed` for now removed features.
  - `Fixed` for any bug fixes.
  - `Security` in case of vulnerabilities.
- For `[Unreleased]`, we don't need to maintain a history of every intermediate change if a change was reverted or overrides a previous unreleased change (eg 'changed to use packageX version 1, then changed to use packageX version 2') - just document the changes relative to the last versioned release to the current state. You may update or remove text from the `[Unreleased]` section as required - you don't always need to append only.

Keep dot points concise - list the change but don't elaborate on implementation detail.

## Code style

---
description: Code style guidelines including comments, emojis, language preferences,
  and naming conventions
alwaysApply: false
---

- Don't use too many comments.
- Don't overuse emojis - if in doubt, use a non-emoji alternative.
- Don't remove TODO comments unless they become out of date since you have added that feature or fix.
- Use comments sparingly, don't add comments about idiomatic code. Only add comments to explain WHY something uncommon or unconventional is being done, not what typical code is doing.
- Use Australian English in comments (colour not color). But use `color` in variable names etc.
- DO NOT hard code API keys, passwords and secrets into scripts - these should be loaded from environment variables, `.env` or configuration files.
- Follow the existing code style for capitalisation and punctuation for variable, function, class and method names
- If you need clarification on any part of a task, ask for more information before proceeding with the implemention.

## Config files

---
description: Preferences for implementing configuration file support in apps
alwaysApply: false
---

- By default, prefer using TOML as a config file format
- Support config auto-detected in the current working directory, and standard system paths like ~/.config/{app_name}/config.toml
- For determining default config file paths, use the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/). Use the `platformdirs` package to achive this in Python.
- Support -c / --config commandline options to specify a config file path explicity.
- Ideally, every config file variable can be overriden by a corresponding environment variable and a commandline variable, eg for the variable 'foo.bar', the env var $APPNAME_FOO_BAR, or the --foo-bar commandline option would override.
- Config precedence should be:
  1. Commandline arguments
  2. Environment variables (typically UPPERCASE and prefixed with APPNAME_)
  3. Config file in current working directory
  4. User config file
  5. System config file
  6. Default values
- Allow environment variables to be used in config files, eg `${MY_VAR}`.

## Docker

---
description: Docker and docker compose best practices including Dockerfile optimizations
  and package management
alwaysApply: false
---

- Use `docker compose` not `docker-compose`. 
- Don't include a "version" at the top of docker-compose files. 
- If using apt-get in a Dockerfile, include ENV `DEBIAN_FRONTEND=noninteractive`, and use best-practises to clean `/var/lib/apt/lists/`
- When using `pip install`, include `--no-cache-dir` and the environment variable `ENV PIP_BREAK_SYSTEM_PACKAGES=1`

## .env files (12 factor app)

---
description: Guidelines for managing environment variables and .env files following
  12 factor app principles
alwaysApply: false
---

This applies to web services in particular.

- Use a .env file for web services and provide a .env.example
- When new environment variables are added to the codebase, ensure they are also added to .env.example
- Ensure .env is added to .gitignore
- NEVER delete the existing .env file, even if you cannot see it

## FastAPI and SQLAlchemy

---
description: FastAPI and SQLAlchemy best practices including async patterns, migrations,
  and schema management
alwaysApply: false
---

- Use async where possible
- Use alembic for migrations when using Postgres
- When modifying models, also ensure to update any associated Pydantic schema and the alembic migrations
- Modifying alembic migrations may involve providing the request alembic command to run. In early non-production development we may instead modify the initial migrations and provide SQL to update the dev database (to prevent unnessecary bloat of migration versions). Ask what would be preferred.

## Git and version control

---
description: Git commit message guidelines and version control best practices
alwaysApply: false
---

- DO NOT include attribution to Claude or any other AI tool in the commit message or co-author attribution. NEVER include "Generated by Claude" or any co-author information.
- DO NOT include emojis in the commit message (unless the message specifically relates to a Unicode emoji)
- The first line of the commit message should be short, concise and to the point. Further detail can be added after a blank line - use dot points.

## Nextflow .nf files

---
description: Nextflow workflow language guidelines including variable escaping, channel
  types, and operator usage
alwaysApply: false
---

- Nextflow is a domain specific language based on Groovy
  - Nextflow docs: https://www.nextflow.io/docs/latest/overview.html
- Inside `script:` sections, ensure $ is correctly escaped - use \${BASH_VARIABLE} or \$(basename x) for shell variables or subshells, and no escaping for ${nextflow_variables}
- Files passed between processes via channels should be or type `path()` or `file()` - passing files as a `val()` is almost always incorrect
- Be aware that Nextflow channels do not behave like regular lists - consult the documentation (https://www.nextflow.io/docs/latest/reference/operator.html) to understand the methods ("operators") available on channels

## PR checklist

---
description: Pre-pull request checklist for updating documentation and configuration
  files
alwaysApply: false
---

- Update `README.md` where required
- Update `.env.example` when env vars change
- Update `CHANGELOG.md` condensing and summarizing `[Unreleased]` changes where required.

## Python

---
description: Python coding standards including type hints, dependency management,
  imports, and tooling preferences
alwaysApply: false
---

- When writing Python code, include type hints where practical.
- For pure Python projects, prefer using `uv venv` or `uv sync` over conda environments or pip.
- Prefer `pyproject.toml` over `setup.py`. 	
- `pyproject.toml` and `requirements.txt` can coexist.
  - Use `pyproject.toml` for unpinned dependencies (or major version pinned) 
  - Use `requirements.txt` for exact version pinned dependencies
- For executable scripts with `#!/usr/bin/env python` include PEP 722 headers for dependencies like `# /// script` etc.
- Order Python imports with most common built-in packages first (typing, logging, sys, os, time, datetime), followed by most common external packages (numpy as np, pandas as pd, requests), followed by other external packages grouped, and finally internal package imports (eg from .utils import foo).
- Include all required imports, both for typing and other parts of the code. 
- For commandline Python scripts, add `#!/usr/bin/env python` and use `if __name__ == "__main__":`.
- Use argparse to make key variables sensible commandline arguments, UNLESS you are told to use typer (https://typer.tiangolo.com/tutorial/)
- Use the logging package writing to stderr for status messages and errors. 
- Follow common conventions for modern Unix commandline tools. 
	- If there is an output file option (-o / --output), allow `-` to indicate printing to stdout. Use io.StringIO, not pd.compat.StringIO.
- For Python projects that might require significant non-Python dependencies (eg bioinformatics projects with additional commandline software), we may use conda.
  - Use -y for conda install and create.
  - Use the conda-forge and bioconda channels
  - If installing conda from scratch, prefer the miniforge3 distribution instead of miniconda3.
- For determining default config file paths etc, used the `platformdirs` package following the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/)

## R

---
description: R programming guidelines for debugging and working with RMarkdown and
  Quarto documents
alwaysApply: false
---

- If my question provides R code to debug, provide an R example, not Python.
- When working withn RMarkdown Rmd or Quarto Qmd, ensure edited code blocks have closing triplebackticks (```).

## Shell scripting

---
description: Shell scripting standards for bash including error handling, syntax conventions,
  and debugging
alwaysApply: false
---

- Assume we have /bin/bash
- Unless specified, use the options: set -euo pipefail
- For debugging, the -x option may help: set -x
- Syntax: 
  - When redirecting to a file, don't add a space after >, do >output_file
  - Use "${VARIBLE}" naming, not $VARIABLE
- If available, run shellcheck and fix any errors highlighted

## Vue.js

---
description: Vue.js component structure, tooling preferences, and UI toolkit recommendations
alwaysApply: false
---

- When writing `.vue` components, the order is `<template>`, `<script>`, `<style>`.
- For simple projects that use Vue from a CDN, use Javascript.
- For larger projects use `pnpm`, and `vite` with Typescript.
- Preferred UI toolkits:
  - PrimeVue: https://primevue.org/cdn/
  - shadcn/vue: https://github.com/unovue/shadcn-vue (docs: https://www.shadcn-vue.com/docs/installation/vite.html)
