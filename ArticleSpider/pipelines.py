# -*- coding: utf-8 -*-
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi
import codecs
import json
import MySQLdb
import MySQLdb.cursors

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')  # codecs 相对于 open 打开文件能避免很多编码问题

    def process_item(self, item,spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item   # 把item返回，因为下一个pipeline可能还需要使用item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    # 调用 Scrapy提供的json export导出json文件
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class MysqlPipeline(object):
    # 同步机制来写入MySQL
    def __init__(self):
        self.conn = MySQLdb.Connect('localhost', 'root', '123456', 'jobbole', charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = '''
            insert into articles(title, url, create_date, fav_nums)
            VALUES(%s, %s, %s, %s)
        '''
        self.cursor.execute(insert_sql, (item['title'], item['url'], item['create_date'], item['fav_nums']))
        self.conn.commit()


class MysqlTwistedPipeline(object):
    # 异步机制来写入mysql
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod    # classmethod 修饰符对应的函数不需要实例化，不需要 self 参数，但第一个参数需要是表示自身类的 cls 参数，可以来调用类的属性，类的方法，实例化对象等
    def from_settings(cls, settings):   # cls 参数表示自身类 MysqlTwistedPipeline
        dbparms = dict(
        host = settings['MYSQL_HOST'],
        db = settings['MYSQL_DBNAME'],
        user = settings['MYSQL_USER'],
        passwd = settings['MYSQL_PASSWORD'],
        charset = 'utf8',
        use_unicode = True,
        cursorclass = MySQLdb.cursors.DictCursor,
        )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbparms)

        return cls(dbpool)

    def process_item(self, item,spider):
        # 使用Twisted把MySQL插入变成异步
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体插入(动态)
        insert_sql, params = item.get_insert_sql()
        cursor.execute(insert_sql, params)


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:   # item字段中有front_image_url的时候才下载文章的封面图片，获得图片的保存路径
            for key, value in results:
                image_file_path = value['path']
            item['front_image_path'] = image_file_path

        return item