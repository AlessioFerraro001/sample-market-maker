textfile = open("config.txt", "r")
params = textfile.read().split('/')
i = 0
for lines in params:
    print("%d %s" % (i, lines))
    i += 1
textfile.close()