import io

import ruamel.yaml


def dumps(obj, *args, **kwargs):
    f = io.StringIO()
    kws = {"default_flow_style": False, "width": 88888}
    kws.update(kwargs)
    ruamel.yaml.safe_dump(obj, f, *args, **kws)
    return f.getvalue()


loads = ruamel.yaml.safe_load
