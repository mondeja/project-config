class InvalidNoStaticMethodsPlugin:
    def invalidFoo(self, *args, **kwargs):
        pass

    def ifInvalidFoo(self, *args, **kwargs):
        pass
