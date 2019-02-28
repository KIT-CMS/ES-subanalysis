class bcolors:
    class styles:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    def __getattr__(self, name):
        style = getattr(self.styles, name)

        def callable(*args, **kwargs):
            text = style
            for i in args:
                text += str(i)
            text += self.styles.ENDC
            print text
            return style

        return callable
