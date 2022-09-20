class InvalidNoStaticMethodsPlugin:
    def invalidFoo(self, *args, **kwargs):  # noqa: U100
        pass

    def ifInvalidFoo(self, *args, **kwargs):  # noqa: U100
        pass
