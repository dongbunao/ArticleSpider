# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import datetime
import re
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from w3lib.html import remove_tags

from ArticleSpider.utils.common import extract_num
from ArticleSpider.settings import SQL_DATETIME_FORMAT

class ArticlespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, '%Y/%m/%d').date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


def return_value(value):
    return value


def get_nums(values):
    match_re = re.match(r'.*?(\d+).*', values)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return  nums


def remove_comment_tags(value):
    if '评论' in value:
        return ''
    else:
        return value


class ArticleItemLoader(ItemLoader):
    # 自定义 ItemLoader
    default_output_processor = TakeFirst()


class JobBoleArticleItem(scrapy.Item):
    # 伯乐在线文章类
    title = scrapy.Field()
    create_date = scrapy.Field(
        input_processor = MapCompose(date_convert)
    )
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(
        output_processor = MapCompose(return_value)
    )
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    tags = scrapy.Field(
        input_processor=MapCompose(remove_comment_tags),
        output_processor=Join(',')
    )
    content = scrapy.Field()

    def get_insert_sql(self):
        # 插入伯乐在线文章的sql语句
        insert_sql = '''
                    insert into articles(title, url, create_date, fav_nums)
                    VALUES(%s, %s, %s, %s)
                '''
        params = (self['title'], self['url'], self['create_date'], self['fav_nums'])

        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    # 知乎问题类
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        # 插入知乎question的sql语句
        insert_sql = '''
            insert into zhihu_question(zhihu_id, topics, url, title, content, answer_num,
            comments_num, watch_num, click_num, crawl_time)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE content=VALUE(content), answer_unm=VALUE(answer_num),
            watch_num=VALUE(watch_num), click_num=VALUE(click_num)
        '''
        zhihu_id = self['zhihu_id'][0]
        topics = ','.join(self['topics'])
        url = self['url'][0]
        title = ''.join(self['title'])
        content = ''.join(self['content'])
        answer_num = extract_num(''.join(self['answer_num']))
        comments_num = extract_num(''.join(self['comments_num']))

        if len(watch_num = extract_num(''.join(self['watch_num']))) == 2:
            watch_num = int(self['watch_num'][0])
            click_num = int(self['watch_num'][1])
        else:
            watch_num = int(self['watch_num'][0])
            click_num = 0

        crawl_time = datetime.datetime.now().strftime(SQL_DATETIME_FORMAT)

        params = (zhihu_id, topics, url, title, content, answer_num, comments_num, watch_num, click_num, crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    #知乎的问题回答item
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    parise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        #插入知乎question表的sql语句
        insert_sql = """
            insert into zhihu_answer(zhihu_id, url, question_id, author_id, content, parise_num, comments_num,
              create_time, update_time, crawl_time
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), parise_num=VALUES(parise_num),
              update_time=VALUES(update_time)
        """

        create_time = datetime.datetime.fromtimestamp(self["create_time"]).strftime(SQL_DATETIME_FORMAT)
        update_time = datetime.datetime.fromtimestamp(self["update_time"]).strftime(SQL_DATETIME_FORMAT)
        params = (
            self["zhihu_id"], self["url"], self["question_id"],
            self["author_id"], self["content"], self["parise_num"],
            self["comments_num"], create_time, update_time,
            self["crawl_time"].strftime(SQL_DATETIME_FORMAT),
        )

        return insert_sql, params


class LaGouJobItemLoader(ItemLoader):
    # 自定义 ItemLoader
    default_output_processor = TakeFirst()


def remove_splish(value):
    # 去掉工作城市中的斜线
    return value.replace('/', '')


def handle_jobaddr(value):
    addr_list = value.split('\n')
    addr_list = [item.strip() for item in addr_list if item.strip() != '查看地图']
    return ''.join(addr_list)


class LaGouJobItem(scrapy.Item):
    # 拉勾网职位信息
    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor = MapCompose(remove_splish)
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(remove_splish)
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(remove_splish)
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field()
    job_addr = scrapy.Field(
        input_processor=MapCompose(remove_tags, handle_jobaddr)
    )
    company_url = scrapy.Field()
    company_name = scrapy.Field()
    tags = scrapy.Field(
        input_processor=Join(',')
    )
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()

    def get_insert_sql(self):
        #插入拉钩职位表（lagou_job）的sql语句
        insert_sql = """
            insert into lagou_job(title, url, url_object_id, salary, job_city, work_years, degree_need,
              job_type, publish_time, job_advantage, job_desc, job_addr, company_url, company_name, tags, crawl_time
              ) 
              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_desc=VALUES(job_desc), crawl_update_time=VALUES(crawl_update_time)
        """
        crawl_update_time = self["crawl_update_time"].strftime(SQL_DATETIME_FORMAT)
        params = (
            self["title"], self["url"], self["url_object_id"], self["salary"], self["job_city"], self["work_years"],
            self["degree_need"], self["job_type"], self["publish_time"], self["job_advantage"], self["job_desc"], self["job_addr"],
            self["company_url"],  self["company_name"], self["tags"], self["crawl_time"].strftime(SQL_DATETIME_FORMAT)
        )

        return insert_sql, params