import struct

def hexdecode(string):
    clist = list(string)
    res = ''
    p = 1
    sep = ''
    nstr = ''
    fstr = ''
    cnum = 0
    for c in clist:
        f = 16 if p == 1 else 1
        cnum += f * {
            '0' : 0,
            '1' : 1,
            '2' : 2,
            '3' : 3,
            '4' : 4,
            '5' : 5,
            '6' : 6,
            '7' : 7,
            '8' : 8,
            '9' : 9,
            'A' : 10,
            'B' : 11,
            'C' : 12,
            'D' : 13,
            'E' : 14,
            'F' : 15,
            'a' : 10,
            'b' : 11,
            'c' : 12,
            'd' : 13,
            'e' : 14,
            'f' : 15
            }[c]
        if p == 1:
            p = 0
        else:
            p = 1
            fstr += 'B'
            nstr += sep + str(cnum)
            sep = ','
            cnum = 0

    fstr = '"' + fstr + '"'
    evalstr = 'struct.pack(' + fstr + ',' + nstr + ')'
    #print(evalstr)
    return eval(evalstr)
