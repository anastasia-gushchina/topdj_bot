import re


def escape_markdown(text: str) -> str:
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def chunk_list_safe(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]
