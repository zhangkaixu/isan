#!/usr/bin/python3
import itertools
import sys
if __name__=='__main__':
    cycle=[]
    file_dict={}
    for item in sys.argv[1:]:
        n,_,file=item.rpartition(':')
        if not n:n='1'
        if file not in file_dict:

            file_dict[file]=open(file,'w') if file else None
        cycle+=[file_dict[file]]*int(n)
    for out_file,line in zip(itertools.cycle(cycle),sys.stdin):
        if out_file:
            print(line.strip(),file=out_file)
