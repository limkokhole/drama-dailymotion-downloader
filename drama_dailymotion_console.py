# -*- coding: utf-8 -*-
# The MIT License (MIT)
# Copyright (c) 2020 limkokhole@gmail.com
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

__author__ = 'Lim Kok Hole'
__copyright__ = 'Copyright 2020'
__credits__ = ['Stack Overflow Links']
__license__ = 'MIT'
__version__ = 1.0
__maintainer__ = 'Lim Kok Hole'
__email__ = 'limkokhole@gmail.com'
__status__ = 'Production'

import sys, os, traceback

PY3 = sys.version_info[0] >= 3
if not PY3:
    print('Sorry, but python 2 already RIP. Abort.')
    sys.exit()

import re
from threading import Thread
import base64
import youtube_dl

import requests
from bs4 import BeautifulSoup

# Jan 2020, Google will unify UA in future, good news :D
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36'
BOLD_ONLY = ['bold']

import argparse
from argparse import RawTextHelpFormatter
arg_parser = argparse.ArgumentParser(
    description='Dailymotion 連續劇下載器', formatter_class=RawTextHelpFormatter)

def quit(msgs, exit=True):
    if not isinstance(msgs, list):
        msgs = [msgs]
    for msg in msgs:
        if msg == '\n': # Empty line without bg color
            print('\n')
        else:
            #cprint(msg, 'white', 'on_red', attrs=BOLD_ONLY)
            print(msg)
    if exit:
        #cprint('中止。', 'white', 'on_red', attrs=BOLD_ONLY)
        print('中止。')
        sys.exit()

arg_parser.add_argument('-any', '--any-website', dest='any_website', action='store_true', help='不下載主題 drama dailymotion 而是下載其它網站例如 YouTube。')
arg_parser.add_argument('-d', '--dir', help='目錄路徑。')
arg_parser.add_argument('-from-ep', '--from-ep', dest='from_ep', default=1, type=int, help='從第幾集開始下載。')
arg_parser.add_argument('-to-ep', '--to-ep', dest='to_ep',
                        type=int, help='到第幾集停止下載。')
arg_parser.add_argument('url', nargs='?', help='連續劇網址。')
args, remaining = arg_parser.parse_known_args()

def main(arg_dir, arg_from_ep, arg_to_ep, arg_url, custom_stdout, arg_any_website):

    try:
        sys.stdout = custom_stdout

        if not arg_url:
            print('網址參數: ' + repr(arg_url))
            quit('[!] [e1] 請輸入網址參數, 例子： https://dramaq.de/cn191023b/。 中止。')

        if not arg_dir:
            quit('[!] 請用 `-d DIR` 參數輸入目錄路徑。中止。')

        dir_path_m = os.path.abspath(arg_dir)
        if not os.path.isdir(dir_path_m):
            try:
                os.makedirs(dir_path_m)
            except OSError:
                quit('[i] 無法創建目錄。中止。')

        urls = []

        if not arg_any_website:

            try:
                if '.html' in arg_url.split('/')[-1]:
                    template_url = '/'.join(arg_url.split('/')[:-1]) + '/'
                elif not arg_url.endswith('/'):
                    template_url = arg_url + '/'
                else:
                    template_url = arg_url

                if not template_url.startswith('http'):
                    # http supposed to auto-redirect to https
                    template_url = 'http://' + template_url

            except Exception as e:
                quit('[!] [e1] 請輸入網址參數, 例子： https://dramaq.de/cn191023b/。 中止。')

            if not arg_to_ep:
                quit('[!] 請用 `--to-ep N` 參數輸入下載到第幾集停止。 中止。')
            arg_to_ep+=1

            http_headers = {
                'User-Agent': UA
            }
            
            for ep in range(arg_from_ep, arg_to_ep):
                url = ''.join([template_url, str(ep), '.html']) 

                print('嘗試 URL: {}'.format(url) )
                r = requests.get(url, allow_redirects=True, headers=http_headers, timeout=30)
                # Use .content instead of .text(), https://stackoverflow.com/q/36833357/1074998
                soup = BeautifulSoup(r.content, 'html.parser')
                #cols = soup.findAll( 'a', text = re.compile("/*Dailymotion$")} )
                cols = soup.findAll( 'a' )
                # E.g. <a href="#4" data-data="91lI4dDOwZnSml2UJFjM1ZHcRxmdrJyW6IycklmIsIibvlGdv1WeslWYEJiOiU2YyV3bzJye"><strong>片源五</strong><small>Dailymotion</small></a>
                
                try:
                    for c in cols:
                        if 'dailymotion' in c.text.lower():
                            print(c.text) #片源五Dailymotion
                            print('base64 (之前): ' + c.get('data-data')) #91lIFFUMnZXen5WM1NlT0kldrl3NrJyW6IycklmIsIibvlGdv1WeslWYEJiOiU2YyV3bzJye
                            # Reverse first then decode with base64
                            decoded_dailymotion = str(base64.b64decode( c.get('data-data')[::-1] ) )
                            print('base64 (之後): ' + repr(decoded_dailymotion)) #b'{"source":"Dailymotion","ids":["k7ykvY4NSu1ngyvg1AE"]}'
                            vid = decoded_dailymotion.split('"ids":["')[1].split('"')[0]
                            url = 'https://www.dailymotion.com/embed/video/' + str(vid)
                            print('vid: ' + repr(url))
                            if not url:
                                raise Exception('Come on, I know Python: No url vid.')
                            urls.append(url)
                    if not urls:
                        raise Exception('Come on, I really know Python: No url vids.')
                except Exception as e:
                    print(traceback.format_exc())
                    quit('解析失败。请去 https://github.com/limkokhole/drama-dailymotion-downloader 开 issue。')

        else:
            urls.append(arg_url)

        print('网址: ' + repr(urls))

        #ep_url = 'https://www.dailymotion.com/embed/video/k63bEEZe7ORnoRvoNaz'

        threads = []
        def download( ep_url ):
            try: # This one shouldn't pass .mp4 ep_path
                youtube_dl.YoutubeDL(params={'-c': '', '-q': '', '--no-mtime': '',
                    'outtmpl': dir_path_m + '/%(title)s-%(upload_date)s-%(id)s.%(ext)s'}).download([ep_url])
            except youtube_dl.utils.DownloadError:
                print(traceback.format_exc())
                sys.exit()
                
        #for url in ['https://www.dailymotion.com/embed/video/k63bEEZe7ORnoRvoNaz', ]
        for url in urls:
            t = Thread( target=download, args=(url,) )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
        

    except Exception:
        # Need to catch & print exception explicitly to pass to duboku_gui to show err log
        print(traceback.format_exc())

    print('[😄] 全部下載工作完畢。您已可以關閉窗口, 或下載別的視頻。')

if __name__ == "__main__":
    main(args.dir, args.from_ep, args.to_ep, args.url, sys.stdout, args.any_website)

