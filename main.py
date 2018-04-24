# -*- coding:utf-8 -*-

from scrapy.cmdline import execute
import sys
import os

# print(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy', 'crawl', 'jobbole'])
# execute(['scrapy', 'crawl', 'zhihu'])
# execute(['scrapy', 'crawl', 'lagou'])