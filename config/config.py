import os
from configparser import ConfigParser


def config(filename="database.ini", section="postgresql"):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, filename)

    parser = ConfigParser()
    parser.read(config_path, encoding="utf-8")

    if not parser.has_section(section):
        raise Exception(f"Секция {section} не найдена в файле {config_path}")

    return {key: val for key, val in parser.items(section)}
