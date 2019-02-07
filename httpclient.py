#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
from urllib.parse import urlparse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))

    def construct_request_line(self, method, o):
        path = o.path if len(o.path) > 0 else "/"
        if(len(o.params) > 0):
            path = path + ";" + o.params
        if(len(o.query) > 0):
            path = path + "?" + o.query
        if(len(o.fragment) > 0):
            path = path + "#" + o.fragment

        return "{} {} HTTP/1.1\r\n".format(method, path)

    def construct_headers(self, headers):
        result = ""
        for key, value in headers.items():
            result = result + "{}: {}\r\n".format(key, value)
        return result


    def construct_body(self, args):
        kvs = []
        if(args != None):
            for key, value in args.items():
                kvs.append("{}={}".format(str(key), str(value)))
            return "&".join(kvs)
        else:
            return ""

    def seperate_netloc(self, netloc):
        result = netloc.split(":")
        if(len(result) == 1):
            return (result[0], 80) # default port 80
        else:
            return (result[0], int(result[1]))


    def get_code(self, data):
        first_line = data.split("\r\n")[0]
        if("HTTP" in first_line):
            code = int(first_line.split()[1])
            return code
        else:
            raise ValueError("the host is not a standard http server")

    def get_headers(self, data):
        # https://stackoverflow.com/questions/10380992/get-python-dictionary-from-string-containing-key-value-pairs
        # regex = re.compile(r"\b(\w+)\s*:\s*([^:]*)(?=\s+\w+\s*:|$)")
        
        headers = {}
        raw_headers = data.split("\r\n\r\n")[0].split("\r\n")[1:]
        for item in raw_headers:
            try:
                # this may need be change
                # print(item)
                # key, value = item.split(": ", 1)
                key, value = item.split(":", 1)
                key = key.strip()
                value = value.strip()
            except Exception as e:
                print(e, "only support format 'key: value' ")
                return {}
            headers[key] = value
        return headers

    def get_body(self, data):
        return data.split("\r\n\r\n")[1]
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        # return buffer.decode('utf-8') #???
        # return str(buffer)
        return buffer.decode('latin-1')

    def GET(self, url, args=None):
        code = 500
        body = ""

        # parse the url
        url_encode = urlparse(url)
        hostname, port = self.seperate_netloc(url_encode.netloc)

        # connect to server
        # https://www.geeksforgeeks.org/socket-programming-python/
        host_ip = socket.gethostbyname(hostname)

        # url: https://stackoverflow.com/questions/25447803/python-socket-connection-exception
        # author: mhawke
        try:
            self.connect(host_ip, port)
        except socket.error as exc:
            print("Caught exception socket.error : %s" % exc)
            sys.exit()
        
        # construct request line
        if(url_encode.scheme == 'http' or url_encode.scheme == 'https'):
            request_line_str = self.construct_request_line("GET", url_encode)
        else:
            raise ValueError("clients only handle http request, your request is not http")
            self.close()

        # constuct headers
        headers = {}
        headers['Host'] = url_encode.netloc
        headers['Connection'] = "close"
        header_str = self.construct_headers(headers)

        # assemble request message
        msg = request_line_str + header_str + "\r\n"

        # send the request message to server
        # print("msg\r\n", msg)
        self.sendall(msg)

        # receive the respond from server
        data = self.recvall(self.socket)

        # print("data\r\n", data, "\n", "*"*10)
        self.close()

        # sparse data
        code = self.get_code(data)
        # print("code ", code)
        # print("test", data.split("\r\n\r\n")[0])
        body = self.get_body(data)
        respond_headers = self.get_headers(data)
        # print(respond_headers)
        print(body)

        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 500
        body = ""

        # same step with GET
        # parse the url
        url_encode = urlparse(url)
        # print(url_encode)
        hostname, port = self.seperate_netloc(url_encode.netloc)

        # connect to server
        # https://www.geeksforgeeks.org/socket-programming-python/
        host_ip = socket.gethostbyname(hostname)

        # url: https://stackoverflow.com/questions/25447803/python-socket-connection-exception
        # author: mhawke
        try:
            self.connect(host_ip, port)
        except socket.error as exc:
            print("Caught exception socket.error : %s" % exc)
            sys.exit()
        
        # construct request line
        if(url_encode.scheme == 'http' or url_encode.scheme == 'https'):
            request_line_str = self.construct_request_line("POST", url_encode)
        else:
            raise ValueError("clients only handle http request, your request is not http")
            self.close()

        # construct body
        body_str = self.construct_body(args)

        # constuct headers
        headers = {}
        headers['Host'] = url_encode.netloc
        headers['Connection'] = "close"
        headers['Content-type'] = 'application/x-www-form-urlencoded'
        headers['Content-length'] = str(len(body_str.encode('UTF-8', 'replace')))
        header_str = self.construct_headers(headers)

        # assemble request message
        if(body_str):
            msg = request_line_str + header_str + '\r\n' + body_str
        else:
            msg = request_line_str + header_str + '\r\n'

        # send the request message to server
        # print("msg\r\n", msg)
        self.sendall(msg)

        # receive the respond from server
        data = self.recvall(self.socket)

        # print("data\r\n", data, "\n", "*"*10)
        self.close()

        # sparse data
        code = self.get_code(data)
        # print("code ", code)
        body = self.get_body(data)
        respond_headers = self.get_headers(data)
        # print(respond_headers)
        print(body)


        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
