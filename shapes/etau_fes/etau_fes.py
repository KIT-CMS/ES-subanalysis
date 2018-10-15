from shapes import Shapes


class ETauFES(Shapes):
    def __init__(self, **args):
        print "init ETauFES"
        super(ETauFES, self).__init__(**args)


if __name__ == '__main__':
    args = ETauFES.parse_arguments()
    etau_fes = ETauFES(**args)
    print etau_fes
    etau_fes.run()
