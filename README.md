![Linting and testing][on-push]

[on-push]: https://github.com/daskol/alai/actions/workflows/on-push.yml/badge.svg

# ALAI: ArchLinux AI

## Overview

ALAI is a `pacman`-based package building harness for ArchLinux User Repository
(AUR) repository database management ArchLinux.

It is aimed at distribution of software for artificial intelligence, machine
learning, and scientific applications in general. The rationale behind it is to
maintain single and uniform environment with support of containerization
technologies across different hosts for training and experimenting with modern
neural networks without much pain.

## Usage

In order to start using it, update [pacman][1] config and add the following
lines to `pacman.conf`.

```ini
# /etc/pacman.conf
[ai]
SigLevel = Optional TrustAll
Server = https://arch.daskol.tech/$repo/os/$arch
```

Then refresh package databases with `pacman -Sy`. Now, you can use it: see list
of prebuilt packages or install JAX with CUDA devices support.

```shell
pacman -Sl ai  # List packages in repo.
pacman -S python-jax python-jaxlib-cuda
```

[1]: https://wiki.archlinux.org/title/pacman
