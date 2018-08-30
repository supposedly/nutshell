from bidict import bidict


def generate_cardinals(d):
    """{'name': ('N', 'E', ...)} >>> {'name': {'N' :: 1, 'E' :: 2, ...}}"""
    return {k: bidict(map(reversed, enumerate(v, 1))) for k, v in d.items()}

