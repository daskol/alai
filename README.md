![Linting and testing][on-push]

[on-push]: https://github.com/daskol/alai/actions/workflows/on-push.yml/badge.svg

# ALAI: ArchLinux AI

## Overview

ALAI is a `pacman`-based build harness for ArchLinux repository database
management ArchLinux.

## Usage

```bash
alias alai='python -m alai'
```

```bash
alai --log-level debug build-graph repo.toml
```
