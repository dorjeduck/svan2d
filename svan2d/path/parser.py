import re

# Regex to match a command letter or a number (including signs, decimals, and exponents)
# This handles the complex, comma-less, space-optional SVG syntax like M100-20L10,30
COMMAND_OR_COORD_RE = re.compile(
    r"([MLHVZCQSTAmlhvzcqst])|((?:[-+]?)(?:[0-9]*\.)?[0-9]+(?:[eE][-+]?[0-9]+)?)"
)


def tokenize_path(path_string: str) -> list[str]:
    """
    Tokenizes an SVG path string into a list of command letters and coordinate values (as strings).

    This function is crucial for handling the compressed nature of SVG path data,
    where numbers and commands often run together without separators (e.g., M100-20L50).
    """
    # Use the regex to find all command letters and coordinate numbers
    tokens = COMMAND_OR_COORD_RE.findall(path_string.strip())

    # Flatten the list of tuples returned by findall
    # Each match is ('Command', '') or ('', 'Coordinate')
    result = []
    for cmd, coord in tokens:
        if cmd:
            result.append(cmd)
        elif coord:
            result.append(coord)

    return result


def parse_coordinates(
    tokens: list[str], num_args: int
) -> tuple[list[float], list[str]]:
    """
    Extracts a specified number of coordinates from the beginning of a token list.

    Args:
        tokens: The remaining tokens in the path string.
        num_args: The number of coordinate values expected (e.g., 2 for L, 4 for Q, 6 for C).

    Returns:
        A tuple: ([parsed_floats], [remaining_tokens])

    Raises:
        ValueError: If not enough numeric tokens are found.
    """
    if len(tokens) < num_args:
        raise ValueError(
            f"Expected {num_args} coordinates but found only {len(tokens)}"
        )

    coords = []
    remaining_tokens = tokens[:]

    for i in range(num_args):
        if not remaining_tokens:
            raise ValueError(
                f"Unexpected end of path data: expected coordinate "
                f"{i + 1} of {num_args}"
            )
        token = remaining_tokens.pop(0)
        try:
            coords.append(float(token))
        except ValueError:
            raise ValueError(
                f"Invalid path data: expected numeric coordinate "
                f"{i + 1} of {num_args}, got command '{token}'"
            )

    return coords, remaining_tokens
