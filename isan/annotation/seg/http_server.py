#!/usr/bin/python3
import http.server
import cgi
import urllib.parse

import sys
import webbrowser
import multiprocessing

import time
import subprocess
import json

html='''
<style>
#a:hover{background:#003000;}  
span.n{background:yellow;}
span.s{background:blue;}
span.c{background:white;}
</style>

<script>
url="$(url)"
sen_id="$(sen_id)"
start_id=-1
function selection_start(id){
    start_id=id
}
function selection_end(id){
    if(start_id==-1)return
    //alert(start_id+" "+id)
    if(start_id>id){
        tmp=id
        id=start_id
        start_id=tmp
    }
    //alert(start_id)
    ele=document.getElementById('i'+start_id)
    if(ele){ele.className='s'}
    for(i=start_id+1;i<=id;i++){
        ele=document.getElementById('i'+i)
        if(ele){ele.className='c'}
    }
    ele=document.getElementById('i'+(id+1))
    if(ele){ele.className='s'}
    start_id=-1
}
function click(ele){
    if(event.button==0){
        if(ele.className=='s'){
            ele.className='n'
        }else{
            ele.className='s'
        }
    }
    else if(event.button==2){
        if(ele.className=='c'){
            ele.className='n'
        }else{
            ele.className='c'
        }
    }
}
function control(cmd){
    if(cmd=='stop'){
        window.location.href=encodeURI(url+"stop")
        return
    }
    if(cmd=='continue'){
        window.location.href=encodeURI(url+"")
        return
    }
    if(cmd=='discard'){
        window.location.href=encodeURI(url+"discard")
        return
    }
    
}
function submit(){
    anno=['s']
    id=1
    while(1){
        ele=document.getElementById('i'+id)
        if(ele){
            if(ele.className=='s'){
                anno.push('s')
            }else if (ele.className=='c'){
                anno.push('c')
            }else{
                anno.push('sc')
            }
        }else{
            anno.push('s')
            break;
        }
        id++
    }
    window.location.href=encodeURI(url+""+sen_id+" "+anno.join(' '))
}


</script>
$(sen_id)
<div onselectstart="return false;" oncontextmenu="return false">
$(sequence)
</div>
<a onclick="submit();">提交</a>
<a onclick="control('continue');">继续</a>
<a onclick="control('discard');">排除</a>
<a onclick="control('stop');">终止</a>

'''
'''

<a id='c0' onmousedown="selection_start(0)" onmouseup="selection_end(0)" >也</a>
<span id='i1' class='n' onmousedown=click(this)>？</span>
<span id='c1' onmousedown="selection_start(1)" onmouseup="selection_end(1)" >记</span>
<span id='i2' class='n' onmousedown=click(this)>？</span>
<span id='c1' onmousedown="selection_start(2)" onmouseup="selection_end(2)">得</span>

'''

class MyHttpHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path=urllib.parse.unquote(self.path)
        if path.endswith('.ico'):
            return
        if len(path)>1:
            print(path)
        rtn=html
        sen=anno()
        raw,seq=sen['raw'],sen['anno']
        s=[]
        for id,c in enumerate(raw):
            s.append('''<a onmousedown="selection_start(%d)" onmouseup="selection_end(%d)" >%s</a>'''%(id,id,c))
            if id<len(raw)-1:
                s.append('''<span id='i%d' class='n' onmousedown=click(this)>?</span>'''%(id+1))
        rtn=rtn.replace('$(sequence)',''.join(s))
        rtn=rtn.replace('$(url)',url)
        rtn=rtn.replace('$(sen_id)',sen['id'])
        self.send_response(200)
        self.send_header( "Content-type", "text/html" )
        self.end_headers()
        
        self.wfile.write(rtn.encode('utf8'))
    

def run(server_class=http.server.HTTPServer, handler_class=http.server.BaseHTTPRequestHandler
            ,addr=('', 8082)):
    server_address = addr
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()
    return httpd;


class Anno:
    def __init__(self):
        self.data=[]
        for line in open("sample.json"):
            sen=json.loads(line)
            self.data.append(sen)
        self.ind=0
    def __call__(self,string=""):
        if string=='stop':
            
            return
        if self.ind>=len(self.data):
            return ''
        sen=self.data[self.ind]
        self.ind+=1
        return sen
            
anno=Anno()


if __name__=="__main__":
    
    

    lock=multiprocessing.Lock()


    print('server started')

    url="http://166.111.138.130:8082/"
    port=8082
    if len(sys.argv)>1:
        url="http://166.111.138.130:"+sys.argv[1]+"/"
        port=int(sys.argv[1])
    
    print(url)
    run(handler_class=MyHttpHandler, addr=('',port))

