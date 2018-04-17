# -*- coding: utf-8 -*-
from scrapy.pipelines.images import ImagesPipeline
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item

class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            for key, value in results:
                image_file_path = value['path']
            item['front_image_path'] = image_file_path

        return item