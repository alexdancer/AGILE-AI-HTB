# Homebrew formula scaffold for maintainers

This directory is not a published Homebrew tap. It records the intended formula shape for a future `alexdancer/htb` tap after release artifacts and checksums exist.

Before publishing a Homebrew path:

1. Publish a tagged AGILE-AI-HTB release artifact.
2. Replace the placeholder URL and SHA256 in `agile-ai-htb.rb.example`.
3. Validate the formula in a real tap checkout.
4. Only then update public docs to present `brew tap alexdancer/htb && brew install agile-ai-htb` as live.

Until then, public operator docs should point to `pipx` or the curl installer.
