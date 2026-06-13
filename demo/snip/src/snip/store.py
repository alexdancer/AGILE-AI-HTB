from __future__ import annotations

from pathlib import Path


class SnippetStore:
    """DEMO synthetic store placeholder.

    The real snippet persistence methods are intentionally absent so a live
    agent can implement them under harness governance. The default path is
    deliberately under the repo's DEMO namespace rather than a real home
    directory, keeping the scaffold safe and obviously synthetic.
    """

    def __init__(self, root: Path | str = "DEMO_SNIP_2099_STORE") -> None:
        self.root = Path(root)
