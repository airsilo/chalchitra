# libs/

This folder is intentionally empty in the repository. Place **`libmpv-2.dll`** here before building or running Chalchitra from source.

## Why it's not in the repo

Two reasons:

1. The DLL is roughly **100 MB**, which is close to GitHub's per-file size limit.
2. It's a third-party binary built by the mpv project, not by Chalchitra. Keeping it out of the repo means users always grab a recent, upstream build directly.

## Where to get it

Download the latest **`mpv-dev-lgpl-<date>-git-<hash>-x86_64-v3.7z`** from:

**https://github.com/shinchiro/mpv-winbuild-cmake/releases**

From the extracted archive, copy **`libmpv-2.dll`** into this `libs/` folder. The final layout should look like:

Chalchitra_app/
├── libs/
│ └── libmpv-2.dll
├── src/
└── ...

text

## Choosing the right build

| Your CPU | Recommended file |
|---|---|
| AVX2 supported (Intel 2013+, AMD Zen+) | `mpv-dev-lgpl-…-x86_64-v3.7z` |
| Older than AVX2 | `mpv-dev-lgpl-…-x86_64.7z` |

If you're unsure, try the `v3` build first. If it fails with a message like *"illegal instruction"* or *"%1 is not a valid Win32 application"* on an old CPU, switch to the plain `x86_64` build.

## Verifying it works

From the project root:

```bash
python -c "import os, ctypes; os.environ['PATH'] = r'libs' + os.pathsep + os.environ['PATH']; ctypes.CDLL('libs/libmpv-2.dll'); print('OK')"
If it prints OK, the DLL is fine and Chalchitra will be able to load it.

Licensing
Chalchitra is licensed under GPL v3.0.

libmpv-2.dll is licensed under LGPL v2.1+.

These two licenses are compatible. The LGPL was designed specifically so that applications (including GPL applications) can link against the library. As long as Chalchitra does not modify libmpv's source, no additional obligations apply beyond the credits already listed in the main README.

Do not replace this DLL with a build that uses a different or incompatible license (for example, a proprietary codec pack). If you do, the whole application must comply with that license instead.

text

### What changed vs. the earlier draft

The confusing sentence:

> Chalchitra itself is licensed under GPL v3.0, so all binaries you distribute must include or link to a compatible LGPL/GPL build of libmpv.

…is now replaced with three plain paragraphs under **Licensing** that explain:

- What Chalchitra uses (GPL v3.0)
- What the DLL uses (LGPL v2.1+)
- Why they're compatible
- What happens if someone swaps in a differently-licensed DLL

No legal jargon, no ambiguous conditionals.

### Where this file goes
G:\Chalchitra_app\libs\README.md

text

It should coexist with the empty `libs/` folder that only contains `libmpv-2.dll` on your local machine (the DLL is `.gitignore`d, so only this README gets committed).