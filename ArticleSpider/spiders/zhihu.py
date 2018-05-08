import datetime
from urllib import parse

import scrapy
import re
import json

from scrapy.loader import ItemLoader

from ArticleSpider.items import ZhihuQuestionItem, ZhihuAnswerItem


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']

    # question的第一页answer的请求url
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"
    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    }

    def parse(self, response):
        '''
        提取页面中所有的URL 并过滤跟踪这些URL进行下一步提取
        如果提取出的URL格式为.../question/xxx 就下载之后直接进入解析函数
        '''
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x:True if x.startswith('https') else False, all_urls)
        for url in all_urls:    # https://www.zhihu.com/question/267438860/answer/325595234
            match_obj = re.match(r"(.*/question/(\d+))(/|$).*", url)
            if match_obj:
                qusetion_url = match_obj.group(1)  # 提取question相关页面进行下载然后交给parse_question（）进行处理
                yield scrapy.Request(url, headers=self.headers, callback=self.parse_question)
            else:
                # 如果不是question相关页面，继续进行跟踪
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)

    def parse_question(self, response):
        # 提取qusetion 的 item
        if 'QuestionHeader-title' in response.text:
            # 新版本
            match_obj = re.match(r"(.*/question/(\d+))(/|$).*", response.url)
            if match_obj:
                qusetion_id = match_obj.group(2)

            item_loader = ItemLoader(item=ZhihuQuestionItem, response=response)
            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", qusetion_id)
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comments_num", ".QuestionHeader-actions button::text")
            item_loader.add_css("watch_num", ".NumberBoard-value::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")

            question_item = item_loader.load_item()
        else:
            #老版本页面
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))

            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            # item_loader.add_css("title", ".zh-question-title h2 a::text")
            item_loader.add_xpath("title",
                                  "//*[@id='zh-question-title']/h2/a/text()|//*[@id='zh-question-title']/h2/span/text()")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comments_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            # item_loader.add_css("watch_user_num", "#zh-question-side-header-wrap::text")
            item_loader.add_xpath("watch_num",
                                  "//*[@id='zh-question-side-header-wrap']/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")

            question_item = item_loader.load_item()

        yield  scrapy.Request(self.start_answer_url, headers=self.headers, callback=self.parse_answer)

        yield  question_item

    def parse_answer(self, response):
        # 处理question的answer
        ans_json = json.loads(response.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]

        # 提取answer的具体字段
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["parise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()

            yield answer_item

        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)


        pass


    # scrapy开始时先进入start_requests()
    def start_requests(self):
        # 为了提取_xsrf：要先访问知乎的登录页面，让scrapy在登录页面获取服务器给我们的数据(_xsrf)，再调用login
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.headers, callback=self.login)]

    def login(self, response):
        xsrf = ''
        match_obj = re.match(r'[\s\S]*name="_xsrf" value="(.*?)"', response.text)
        if match_obj:
            xsrf = match_obj.group(1)

        # 如果提取到了xsrf就进行下面的操作，如果没xsrf有就没必要往下做了
        if xsrf:
            post_data = {
                'captcha_type': 'cn',
                '_xsrf': xsrf,
                'phone_num': '13323821327',
                'password': 'zhihu1327',
                'captcha': '',
            }
        else:
            post_data = {
                'captcha_type': 'cn',
                # '_xsrf': xsrf,
                'phone_num': '13323821327',
                'password': 'zhihu1327',
                'captcha': '',
            }
            import time
            captcha_url = 'https://www.zhihu.com/captcha.gif?r=%d&type=login&lang=cn' % (int(time.time() * 1000))
            # scrapy会默认把Request的cookie放进去
            return scrapy.Request(captcha_url, headers=self.headers, meta={'post_data': post_data}, callback=self.login_after_captcha)


    def login_after_captcha(self, response):
        # 保存并打开验证码
        with open('captcha.gif', 'wb') as f:
            f.write(response.body)
            f.close()
        from PIL import Image
        try:
            img = Image.open('captcha.gif')
            img.show()
        except:
            pass
        # 输入验证码
        captcha = {
            'img_size': [200, 44],
            'input_points': [],
        }
        points = [[22.796875, 22], [42.796875, 22], [63.796875, 21], [84.796875, 20], [107.796875, 20],
                  [129.796875, 22], [150.796875, 22]]
        seq = input('请输入倒立字的位置\n>')
        for i in seq:
            captcha['input_points'].append(points[int(i) - 1])
        captcha = json.dumps(captcha)

        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data = response.meta.get('post_data', {})
        post_data['captcha'] = captcha
        return scrapy.FormRequest(
            # 在这里完成像之前的requests的登录操作，每一个Request如果要做下一步处理都要设置callback
            url=post_url,
            formdata=post_data,
            headers=self.headers,
            callback=self.check_login,
        )

    def check_login(self, response):
        # 验证服务器的返回数据判断是否成功
        text_json = json.loads(response.text)
        if 'msg' in text_json and text_json['msg'] == '登录成功':
            print('登录成功！')
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers=self.headers, callback=self.parse)