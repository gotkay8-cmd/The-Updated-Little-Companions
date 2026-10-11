"""Dependency-free PNG resizing for Tk 8.6, which lacks fractional image zoom.

Art is decoded once. Exact-size nearest-neighbour copies avoid Tk's intermediate
integer zoom/subsample rounding, and never change a sprite's canvas anchor.
"""
import struct
import zlib
from functools import lru_cache
from pathlib import Path

def chunk(kind,payload):
    return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)

@lru_cache(maxsize=190)
def read_rgba(path):
    data=Path(path).read_bytes();offset=8;packed=bytearray()
    while offset<len(data):
        length=struct.unpack('>I',data[offset:offset+4])[0];kind=data[offset+4:offset+8];body=data[offset+8:offset+8+length];offset+=12+length
        if kind==b'IHDR':w,h,bits,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',body)
        elif kind==b'IDAT':packed.extend(body)
    if bits!=8 or color not in (2,6) or interlace:raise ValueError('Unsupported art PNG format')
    channels=4 if color==6 else 3;stride=w*channels;raw=zlib.decompress(packed);previous=bytearray(stride);rows=[]
    for y in range(h):
        start=y*(stride+1);mode=raw[start];row=bytearray(raw[start+1:start+1+stride])
        for i in range(stride) if mode else ():
            a=row[i-channels] if i>=channels else 0;b=previous[i];c=previous[i-channels] if i>=channels else 0
            if mode==1:value=a
            elif mode==2:value=b
            elif mode==3:value=(a+b)//2
            elif mode==4:
                p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c);value=a if pa<=pb and pa<=pc else b if pb<=pc else c
            elif mode==0:value=0
            else:raise ValueError('Unsupported PNG filter')
            row[i]=(row[i]+value)&255
        previous=row
        rows.append(bytes(row) if channels==4 else b''.join(row[i:i+3]+b'\xff' for i in range(0,stride,3)))
    return w,h,rows

def resized_png(path,width,height):
    w,h,rows=read_rgba(str(path));width=max(1,int(width));height=max(1,int(height))
    offsets=[min(w-1,int((x+.5)*w/width))*4 for x in range(width)]
    scaled={};out=[]
    for y in range(height):
        sy=min(h-1,int((y+.5)*h/height))
        if sy not in scaled:
            row=rows[sy];scaled[sy]=b'\x00'+b''.join(row[x:x+4] for x in offsets)
        out.append(scaled[sy])
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(out),1))+chunk(b'IEND',b'')

@lru_cache(maxsize=96)
def transformed_png(path,width,height,angle):
    """Rotate a runtime sprite about its center, retaining its full alpha bounds."""
    import math
    w,h,rows=read_rgba(str(path));r=math.radians(angle);co=math.cos(r);si=math.sin(r)
    ow=max(1,math.ceil(abs(width*co)+abs(height*si)));oh=max(1,math.ceil(abs(width*si)+abs(height*co)))
    output=[]
    for y in range(oh):
        row=bytearray(ow*4)
        for x in range(ow):
            dx=x+.5-ow/2;dy=y+.5-oh/2
            sx=int((dx*co+dy*si+width/2)*w/width);sy=int((-dx*si+dy*co+height/2)*h/height)
            if 0<=sx<w and 0<=sy<h:row[x*4:x*4+4]=rows[sy][sx*4:sx*4+4]
        output.append(b'\0'+row)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',ow,oh,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(output),1))+chunk(b'IEND',b'')
