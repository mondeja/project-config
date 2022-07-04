class InvalidBreakageTypeYielderPlugin:
    @staticmethod
    def invalidFoo(*args, **kwargs):
        yield ("foo", {})

    @staticmethod
    def ifInvalidFoo(*args, **kwargs):
        yield ("foo", {})
