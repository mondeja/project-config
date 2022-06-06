import argparse

from project_config.config import read_config


def check(args: argparse.Namespace) -> bool:
    print("args in check", args)
    config = read_config(args.config)
    print(config)
    return True
