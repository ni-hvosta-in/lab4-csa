def is_number(s: str) -> bool:
    try:
        int(s, 0)
        return True
    except ValueError:
        return False


def is_valid_number(s: str) -> bool:

    if is_number(s):
        n = int(s, 0)
        return -(2**32) <= n <= 2**32 - 1

    return False


def is_valid_number_param(s: str) -> bool:
    if is_number(s):
        n = int(s, 0)
        return -(2**24) <= n <= 2**24 - 1

    return False


def is_valid_string(s: str) -> bool:
    s2 = s.strip('"')
    return len(s) >= 2 and s[0] == '"' and s[-1] == '"' and '"' not in s2


def parse_input(file: str) -> dict[int, list[int]]:
    """парсинг input_file в словарь буферов"""
    io_ports: dict[int, list[int]] = {}

    with open(file, encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()

        assert line.startswith("[") and line.endswith("]"), f"Invalid input format: {line}"

        content = line[1:-1].strip()

        if content == "":
            io_ports[i + 1] = []
            continue

        content_list = content.split(",")
        tokens = []

        for con in content_list:
            tokens.append(con.strip())

        parsed = []

        for token in tokens:
            if is_number(token):
                assert is_valid_number(token), f"Invalid number format: {token}"

                parsed.append(int(token, 0))
            else:
                for char in token:
                    parsed.append(ord(char))

        io_ports[i + 1] = parsed

    return io_ports
