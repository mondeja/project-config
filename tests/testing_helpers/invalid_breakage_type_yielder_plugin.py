class InvalidBreakageTypeYielderPlugin:
    @staticmethod
    def invalidFoo(*args, **kwargs):  # noqa: U100
        yield ("foo", {})

    @staticmethod
    def ifInvalidFoo(*args, **kwargs):  # noqa: U100
        yield ("foo", {})
