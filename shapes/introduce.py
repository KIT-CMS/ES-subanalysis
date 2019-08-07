def introduce_function(original_function, pref=''):
    print 'introduce_function'
    def new_function(*args, **kwargs):
        print pref + original_function.__name__
        x = original_function(*args, **kwargs)
        return x

    return new_function


def introduce_all_class_methods(Cls):
    class NewCls(object):
        def __init__(self, *args, **kwargs):
            self.oInstance = Cls(*args, **kwargs)

        def __getattribute__(self, s):
            # print 'NewCls::__getattribute__', s
            """
            this is called whenever any attribute of a NewCls object is accessed. This function first tries to
            get the attribute off NewCls. If it fails then it tries to fetch the attribute from self.oInstance (an
            instance of the decorated class). If it manages to fetch the attribute from self.oInstance, and
            the attribute is an instance method then `time_this` is applied.
            """
            try:
                x = super(NewCls, self).__getattribute__(s)
            except AttributeError:
                pass
            else:
                return x
            x = self.oInstance.__getattribute__(s)
            if type(x) == type(self.__init__):  # it is an instance method
                return introduce_function(x, self.oInstance.__class__.__name__ + "::")                 # this is equivalent of just decorating the method with time_this
            else:
                return x

    return NewCls
