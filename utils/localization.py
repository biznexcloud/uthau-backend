_nepali_map = {
    "0": "०", "1": "१", "2": "२", "3": "३", "4": "४",
    "5": "५", "6": "६", "7": "७", "8": "८", "9": "९",
}


def to_nepali_digits(text: str) -> str:
    return "".join(_nepali_map.get(ch, ch) for ch in text)
