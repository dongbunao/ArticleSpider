import requests

try:
    import cookielib
except:
    import http.cookiejar as cookielib

import re
import time
import json


def get_xsrf():
    # 获取xsrf code
    response = session.get('https://www.zhihu.com', headers=header)
    # print(response.text)
    match_obj = re.match('[\s\S]*name="_xsrf" value="(.*?)"', response.text)
    if match_obj:
        return match_obj.group(1)
    return ''


def get_captcha():
    # 验证码URL是按照时间戳的方式命名的
    captcha_url = 'https://www.zhihu.com/captcha.gif?r=%d&type=login&lang=cn' % (int(time.time() * 1000))
    response = session.get(captcha_url, headers=header)
    # 保存验证码到当前目录
    with open('captcha.gif', 'wb') as f:
        f.write(response.content)
        f.close()

    # 自动打开刚获取的验证码
    from PIL import Image
    try:
        img = Image.open('captcha.gif')
        img.show()
        img.close()
    except:
        pass

    captcha = {
        'img_size': [200, 44],
        'input_points': [],
    }
    points = [[22.796875, 22], [42.796875, 22], [63.796875, 21], [84.796875, 20], [107.796875, 20], [129.796875, 22],
              [150.796875, 22]]
    seq = input('请输入倒立字的位置\n>')
    for i in seq:
        captcha['input_points'].append(points[int(i) - 1])
    return json.dumps(captcha)


def zhihu_login(account, password):
    # 知乎登录
    if re.match('1\d{10}', account):
        print('手机号码登录')
        post_url = 'https://www.zhihu.com/login/phone_num'
        post_data = {
            'captcha_type': 'cn',
            '_xsrf': get_xsrf(),
            'phone_num': account,
            'password': password,
            'captcha': get_captcha(),
        }

        response_text = session.post(post_url, data=post_data, headers=header)
        response_text = json.loads(response_text.text)
        if 'msg' in response_text and response_text['msg'] == '登录成功':
            print('登录成功！')
        else:
            print('登录失败')


if __name__ == '__main__':
    agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
    header = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-agent': agent,
    }
    session = requests.session()
    zhihu_login('13323821327', 'zhihu1327')

    url = 'https://www.zhihu.com/question/267438860/answer/325595234'
    match_obj = re.match(r"(.*/question/(\d+))(/|$).*", url)
    if match_obj:
        request_url = match_obj.group(1)
        question_id = match_obj.group(2)
