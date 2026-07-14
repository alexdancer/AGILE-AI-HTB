# Homebrew formula scaffold for maintainers

This directory is not a published Homebrew tap. It records the intended formula shape for a future `alexdancer/foremanctl` tap after release artifacts and checksums exist.

Before publishing a Homebrew path:

1. Publish a tagged Foreman AI HQ release artifact.
2. Replace the placeholder URL and SHA256 in `foreman-ai-hq.rb.example`.
3. Validate the formula in a real tap checkout.
4. Only then update public docs to present `brew tap alexdancer/foremanctl && brew install foreman-ai-hq` as live.

Until then, public operator docs should point to `pipx` or the curl installer.
