from typing import List


def string_builder(l: List[str], *elements) -> str:
    """
    :param l: a list of strings
    :param elements: strings
    :return:
    """
    l.extend(elements)

    return "".join(l)
