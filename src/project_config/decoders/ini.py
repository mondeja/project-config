import configparser


def loads(string: str):
    result = {}
    ini = configparser()
    ini.read_string(string)
    for section in ini.sections():
        result[section] = {}
        for option in ini.options(section):
            result[section][option] = ini.get(section, option)
    return result
