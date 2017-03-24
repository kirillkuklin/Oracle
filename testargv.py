from sys import argv
def getopts(argv):
    opts = {}
    while argv:
        if argv[0][0] == '-':
            opts[argv[0]] = argv[1]
            argv = argv[2:]
        else:
            argv = argv[1:]
    return opts

myargs = getopts(argv)
if '-ip' in myargs:
    ip = myargs['-ip']
elif 'username' in myargs:
    username = myargs['-username']
elif 'password' in myargs:
    password = myargs['-password']
elif 'outfile' in myargs:
    outfile = myargs['-outfile']


