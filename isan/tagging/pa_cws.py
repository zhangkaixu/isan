#!/usr/bin/python3



class codec:
    @staticmethod
    def decode(line):
        raw,*bds=line.split()
        bds=[[int(it) for it in x.split(',')] for x in bds]
        if len(raw)!=len(bds)-1:
            print(raw,bds)
            print('raw and annotation do not match')
        return raw,bds


if __name__ == '__main__':
    line='什么样 0,2 0,3 0,3 0,3'
    codec.decode(line)

