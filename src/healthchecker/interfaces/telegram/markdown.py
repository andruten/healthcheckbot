from telegram.helpers import escape_markdown


def markdown_escape(value: object) -> str:
    return escape_markdown(str(value), version=1)
