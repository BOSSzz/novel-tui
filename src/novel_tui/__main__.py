"""Entry point: python -m novel_tui."""

from novel_tui.app import NovelApp


def main() -> None:
    app = NovelApp()
    app.run()


if __name__ == "__main__":
    main()
