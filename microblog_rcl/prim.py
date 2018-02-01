# coding=utf-8
from os import path, makedirs
from time import time
from time import sleep
from random import randint
from datetime import datetime
from configparser import ConfigParser
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

root_path = 'C:/prim/'
user_path = root_path + 'user.ini'
cookies_path = root_path + 'my_cookies.txt'

profile_dir = 'C:/prim/firefoxconf.selenium/'

weibo_login_url = "https://passport.weibo.cn/signin/login"

# defalut_time_to_sleep = 10

_T_WM_expiry = 0  # 初始化新浪微博 Cookies 中 _T_WM 的 expiry 值 ( 登录后设置, 有效期最短的 cookie )

# available_port = -1

write_comment_link_count = 0  # 写入 user.ini 中 last_comment_link 的次数


def base(view):
    """
    选择浏览器启动方式
    :param view: 0 无界面浏览器
    :return:
    """
    exists_path(cookies_path)
    exists_path(user_path)  # 新建空文件, 并设置编码格式以避免编码问题, ConfigParser()对象写入新文件编码为 utf-8 BOM
    conf = ConfigParser()
    conf.read(user_path, encoding='utf-8')
    sections = conf.sections()
    if len(sections) == 0:  # 配置文件 user.ini 为空
        print('user.ini 无记录,开始配置-->')
        print('-----' * 10)
        username = input('请输入微博账号：')
        password = input('请输入微博密码：')
        print('-----' * 10)

        conf.add_section('basic')
        conf.set('basic', 'username', username)
        conf.set('basic', 'password', password)
        conf.set('basic', 'last_comment_link', 'url')

        conf.add_section('repost_users')
        # key = input('添加-->')
        # i = 1
        # users = []
        # while (key != 'n'):
        #     conf.set('repost_list', 'user' + str(i), key)
        #     users.append(key)
        #     i = i + 1
        #     key = input('添加-->')
        print('注意：自动生成纯汉字超话名称')
        print('　　　如果有误，请到', user_path, '中查看')
        print('提示: 空格分隔，回车结束\n')
        print('输入用户名:')
        users_str = input('-->')
        users = users_str.split()

        conf.add_section('super_topic')
        j = 1
        for i in users:
            conf.set('repost_users', 'user' + str(j), i)
            conf.set('super_topic', i, format_str(i))
            j = j + 1

        f = open(user_path, 'w', encoding='utf-8')
        conf.write(f)  # 写入用户信息 使用with open时 保存user.ini 为utf-8带BOM格式 不解
        f.close()
        print(user_path, '配置完成')
        print('-----' * 10)

    profile_dir = 'C:/prim/firefoxconf.selenium/'  # firefox.exe -ProfileManager -no-remote

    headless = Options()
    if view == 0:
        headless.add_argument('-headless')
        print('无界面浏览器启动中...')
        # driver = Firefox(firefox_profile=profile_dir, executable_path= firfox_driver_path,options=headless)
    else:
        print('火狐浏览器启动中...')
    driver = Firefox(firefox_profile=profile_dir, options=headless)

    # 研究发现:
    # 通过`远程启动浏览器会生成一个 user.js 的配置文件 影响程序正常执行
    # user.js 对应语句 user_pref("browser.link.open_newwindow", 2);
    # 需要将选项 新建窗口时以新建标签页代替 勾选 (默认配置就为 3; 2 新建窗口 ( 非1 ,3 ) ; 1 本窗口打开)

    # 尝试使用 profile.set_preference('browser.link.open_newwindow', 3) 设置
    # 在 perfs.js 中 添加了 browser.link.open_newwindow 为 2 ??? 不写则无该设置 不明觉厉
    # 或许是 user.js 对 perfs.js 的影响吧

    # print(profile.path) # 生成C:\Users\username\AppData\Local\Temp\tmprt2mrvtn\webdriver-py-profilecopy
    # 在 C:\Users\username\AppData\Local\Temp\ ( 可运行 %temp% 直接查看目录 ) 生成profile_dir临时文件夹

    # C:\Users\ERRORM~1\AppData\Local\Temp\tmpsc26idf5\webdriver-py-profilecopy 能直接访问 将 \ 替换为 / 不能打开
    # C:/Users/Errormaker/AppData/Local/Temp/tmpfvye7pm4/webdriver-py-profilecopy 需要修改用户名 不解
    # userjs = profile.path.replace('\\', '/', -1).replace('ERRORM~1', 'Errormaker') + '/user.js'
    # os.remove(userjs)

    driver.get('about:preferences')  # 用户设置界面
    link_targeting = driver.find_element_by_css_selector('#linkTargeting')
    if not link_targeting.get_attribute('checked'):
        link_targeting.click()
    driver.get('about:blank')  # 打开空tab
    print('火狐浏览器初始化完成...')
    return driver
    # C:\Users\ERRORM~1\AppData\Local\Temp\rust_mozprofile.2nic6yZFyiBW 浏览器使用的配置文件


def prim_go(driver, view):
    """
    正式流程:
    打开新窗口 --> get_local_cookies() 读写 Cookies 异常则图形化浏览器登录 重新获取 -->
    open_homepage() 打开微博首页手机版 --> 获取 _T_WM 过期时间 --> get_user_conf() 获取转评赞用户列表 -->
    Cookies 过期前两小时注销登录 --> prim() 转评赞循环 直到 Cookies 过期 --> 注销登录
    :param driver:
    :param view:
    :return:
    """
    try:
        if len(driver.window_handles) == 1:
            js = 'window.open()'  # 打开新窗口
            driver.execute_script(js)  # 执行后获取handle,未切换driver,但视觉上被切换到该窗口
        driver.switch_to.window(driver.window_handles[0])  # 视觉与实际统一

        local_cookies = get_local_cookies()

        if len(local_cookies) < 6:  # 本地保存cookies条目少于6条，重写
            input('是否有人监督登录?回车确认')
            log_in()
            local_cookies = get_local_cookies()

        open_homepage(driver, local_cookies)  # cookie登录 第一次使用时local_cookies为空

        global _T_WM_expiry
        if _T_WM_expiry == 0:
            for cookie in local_cookies:
                if cookie[0] == '_T_WM':
                    _T_WM_expiry = int(cookie[2])

        repost_users = get_user_conf()

        cookies_refresh_time = _T_WM_expiry - 2 * 60 * 60
        ticks = int(time())  # 以秒为单位的浮点小数表示当前时间（本地时间不准有影响）
        reget_cookie = cookies_refresh_time - ticks
        cookies_expiry = datetime.fromtimestamp(_T_WM_expiry)  # 格式化时间戳

        page = 1  # page = 1 已在homepage()中打开
        page_limit = 10

        while reget_cookie >= 0:  # 提前两小时重获取cookies
            print('\n当前访问链接:\t', driver.current_url)
            print('Cookies过期时间:\t', cookies_expiry)

            rcl = prim(driver, repost_users)  # 主程序

            ticks = int(time())
            reget_cookie = cookies_refresh_time - ticks

            if page >= page_limit:  # 设置翻页上限
                print('超出翻页上限', page_limit, '回到首页')
                global write_comment_link_count
                write_comment_link_count = 0
                driver.find_element_by_xpath('//div[@class="n"]/*[1]').click()
                page = 1
                continue
            sleep_time = get_random_num(10, 60)
            print('随机等待时间(s)', sleep_time)
            sleep(sleep_time)
            if rcl != 1:
                page += 1
                driver.get('https://weibo.cn/?page=' + str(page))  # 第一次, page == 2
            else:  # rcl == 1 找到上次转评赞链接,返回到首页
                page = 1
                # global write_comment_link_count
                write_comment_link_count = 0

        print('Cookies即将过期,启动图形化浏览器中...')
        log_off(driver)
    except Exception as e:
        print('Error:', e)
    finally:
        if view == 0:  # 出错后关闭无界面浏览器
            driver.close()


def get_local_cookies():
    """
    读取本地 cookis_path 获取Cookies
    :return:
    """
    with open(cookies_path, 'r', encoding='utf-8') as f:
        rows = f.readlines()
    cookies = []
    for row in rows:  # 按行读取本地cookies
        cookie = row.strip('\n').split(' ')  # [0] name; [1] value; [2] expiry
        cookies.append(cookie)
    return cookies


def log_in():
    """
    先查看本地cookies是否过期,避免反复登录获取cookies
    否则，重新登录获取cookies
    手动输入验证码
    :return:
    """
    conf = ConfigParser()
    conf.read(user_path, encoding='utf-8')
    username = conf.get('basic', 'username')
    password = conf.get('basic', 'password')
    print('username:', username)
    print('password:', password)

    # driver.implicitly_wait(10) # 隐性等待，最长等10秒 不注释程序运行极慢
    print('准备登陆Weibo.cn网站...')

    login_driver = Firefox(firefox_profile=profile_dir)
    login_driver.get(weibo_login_url)
    WebDriverWait(login_driver, 10).until(EC.visibility_of_element_located((By.ID, "loginAction")))

    elem_user = login_driver.find_element_by_id("loginName")
    elem_user.send_keys(username)  # 用户名
    elem_pwd = login_driver.find_element_by_id("loginPassword")
    elem_pwd.send_keys(password)  # 密码

    elem_sub = login_driver.find_element_by_id("loginAction")
    elem_sub.click()  # 点击登陆，登录多次或异地登录可能会有验证码
    WebDriverWait(login_driver, 20).until(EC.url_contains('m.weibo.cn'))

    sina_cookies = login_driver.get_cookies()  # 包含多个 cookie 的字典列表
    print('保存本地cookies')
    with open(cookies_path, 'w') as f:
        for cookie in sina_cookies:
            if cookie['name'] == '_T_WM':  # 登录成功,设置全局变量
                global _T_WM_expiry
                _T_WM_expiry = int(cookie['expiry'])
            print(cookie['name'], cookie['value'], cookie['expiry'])
            f.write(cookie['name'] + ' ' + cookie['value'] + ' ' + str(cookie['expiry']) + '\n')  # expiry 为int型
    login_driver.close()

    print('成功记录cookies，已关闭浏览器')


def open_homepage(driver, cookies):
    """
    打开微博首页手机版
    :param driver: 浏览器对象
    :param cookies:
    :return:
    """
    driver.get('https://weibo.cn')  # 未登录,自动跳转到 https://weibo.cn/pub/
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "ut")))  # 登录 注册 div所属的类
    for cookie in cookies:
        driver.add_cookie({'name': cookie[0], 'value': cookie[1]})  # 设置 Cookies
    driver.get('https://weibo.cn')
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "pagelist")))


def get_user_conf():
    """
    获取user.ini相关配置
    现目前仅为获取转评赞用户列表
    :return:
    """
    user_conf = []
    conf = ConfigParser()
    conf.read(user_path, encoding='utf-8')

    items = conf.items('repost_users')
    for i in items:
        user_conf.append(i[1])
    # print(repost_users)
    return user_conf


def prim(driver, repost_users):
    """
    https://weibo.cn/attitude/G0p8SclmQ/add?uid=2763572335&rl=0&gid=10001&st=5e3f95 赞 https://weibo.cn/attitude/G0p8SclmQ/add?uid=2763572335&st=5e3f95
    https://weibo.cn/repost/G0p8SclmQ?uid=5764750867&rl=0&gid=10001 转 https://weibo.cn/repost/G0p8SclmQ
    https://weibo.cn/comment/G0p8SclmQ?uid=5764750867&rl=0&gid=10001#cmtfrm 评 https://weibo.cn/comment/G0p8SclmQ?#cmtfrm 评论并转发

    读取每页微博信息
    :param driver: 浏览器对象
    :param repost_users: 转评赞用户列表
    :return: rcl 找到上次转评赞微博 置为 1
    """
    # print(repost_users)
    rcl = 0
    weibos = driver.find_elements_by_css_selector('div[id^="M_"]')  # 选择其 id 属性值以 "M_" 开头的每个 <div> 元素

    for weibo in enumerate(weibos):
        username = weibo[1].find_element_by_css_selector('[class=nk]').text
        div_list = weibo[1].find_elements_by_css_selector('div')
        if len(div_list) == 3:  # 非原创
            print(weibo[0], '\t转发带图博\t', username)
        elif username in repost_users:  # 指定用户
            is_repost = weibo[1].find_elements_by_xpath("./div[last()]/*[1 and text()='转发理由:']")
            if len(div_list) == 2 and len(is_repost) == 1:
                print(weibo[0], '\t转发无图博\t', username)
            else:  # 原创文字或原创带图博
                eid = RCL(weibo[1], driver, username)
                if eid == 0:
                    print(weibo[0], '\t*转评赞完成\t', username)
                elif eid == 1:  # 找到上次转评赞链接,返回首页,跳出循环,结束prim方法
                    rcl = eid
                    break
                elif eid == 2:
                    print(weibo[0], '\t直播分享博\t', username)
                elif eid == 3:
                    print(weibo[0], '\tlast_comment_link\t')
                    print('\t*未写入转评赞用户\t', username)
        else:
            print(weibo[0], '\t非转评赞用户\t', username)
    return rcl


def log_off(driver):
    """
    在首页点击退出按钮 注销 清空本地cookies
    :param driver: 浏览器对象
    :return:
    """
    driver.get('https://weibo.cn')
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, "ut")))  # 登录 注册 div所属的类

    driver.find_element_by_css_selector("a[href*='logout']").click()  # 经测试 退出后 原cookies未过期依旧能够使用
    expiry_local_cookies()


def get_random_num(begin, end):
    """
    生成一个在区间范围内的数
    :param begin: 最小值
    :param end: 最大值
    :return:
    """
    num = randint(begin, end)
    return num


def make_dirs(dirs):
    """
    创建目录
    :param dirs: 目录路径，可迭代创建
    :return:
    """
    try:
        if not path.exists(dirs):
            makedirs(dirs)
            print('创建目录:', dirs)
    except Exception as e:
        print('Error:', e)


def exists_path(file_path):
    """
    确保文件存在
    :param file_path:
    :return:
    """
    parent_path = file_path[:file_path.rfind('/') + 1]
    make_dirs(parent_path)
    if not path.exists(file_path):
        open(file_path, 'w', encoding='utf-8').close()
        print('新建文件', file_path)
    else:
        print(file_path, '已存在')


def expiry_local_cookies():
    """
    cookies 剩余两小时过期时，清空文件 my_cookies.txt
    :return:
    """
    with open(cookies_path, 'w', encoding='utf-8') as f:
        f.truncate()
    global _T_WM_expiry
    _T_WM_expiry = 0


def is_chinese(uchar):
    """判断一个unicode是否是汉字"""
    if '\u4e00' <= uchar <= '\u9fa5':
        return True
    else:
        return False


def format_str(content):
    """
    过滤常用汉字
    :param content:
    :return:
    """
    content_str = ''
    for i in content:
        if is_chinese(i):
            content_str = content_str + i
    return content_str


def write_comment_link(comment_link):
    """
    写入 last_comment_link
    从首页开始, 最多写入一次
    :param comment_link:
    :return:
    """
    global write_comment_link_count
    if write_comment_link_count <= 0:
        lclink = ConfigParser()
        lclink.read(user_path, encoding='utf-8')
        lclink.set('basic', 'last_comment_link', comment_link)
        with open(user_path, 'w', encoding='utf-8') as f:  # 更新last_like_link
            # print('last_comment_link 更新为:', comment_link)
            print('last_commet_link 已更新')
            lclink.write(f)
        write_comment_link_count += 1


def RCL(weibo, driver, username):
    """
    RCL repost + comment + like
    执行转评赞操作
    :return: eid 事件id
    0 转评赞
    1 找到上次转评赞微博
    2 直播分享博
    3 由于某些异常 导致在事件1发生前的近期转评赞 但未写入 last_comment_link 的微博
    """
    eid = 0  # event id
    conf = ConfigParser()
    conf.read(user_path, encoding='utf-8')
    last_comment_link = conf.get('basic', 'last_comment_link')

    comment_link = weibo.find_element_by_xpath("./div[last()]/*[last()-2]").get_attribute("href")
    like_link = weibo.find_element_by_xpath("./div[last()]/*[last()-4]").get_attribute("href")
    # print('评转链接', comment_link)
    # print('点赞链接', like_link)
    # print(like_link)  # 已转 输出为None
    if comment_link == last_comment_link:
        print('--> 上次转评赞用户', username, '<--')
        print('---' * 4, '返回首页', '---' * 4)
        driver.find_element_by_xpath('//div[@class="n"]/*[1]').click()
        eid = 1  # 找到上次转评赞链接,返回首页,跳出循环,结束prim方法
    elif not like_link:
        eid = 3
        write_comment_link(comment_link)
    else:
        links = weibo.find_elements_by_xpath(".//span[@class='ctt']/a")  # 微博内容中的内嵌链接
        # driver.switch_to.window(driver.window_handles[1])  # 切换到第二个tab
        # 循环前直接切换会报错 Message: Web element reference not seen before
        # link 找不到对象
        for link in links:  # 为空不输出
            inner_link = link.get_attribute("href")
            # print(driver.title, driver.current_url)
            # print(inner_link)
            driver.switch_to.window(driver.window_handles[1])  # 切换到第二个tab
            driver.get(inner_link)
            # print(driver.title)
            if '直播' in driver.title:
                eid = 2
            driver.switch_to.window(driver.window_handles[0])  # 切换到第一个tab
        if eid == 0:
            conf = ConfigParser()
            conf.read(user_path, encoding='utf-8')
            topic_name = conf.get('super_topic', username)

            driver.switch_to.window(driver.window_handles[1])  # 切换到第二个tab
            driver.get(comment_link)

            driver.find_element_by_css_selector('textarea').send_keys('#' + topic_name + '#')
            driver.find_element_by_css_selector('input[name=rt]').click()  # 点击评论并转发按钮
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "ps")))  # <div class="ps">操作成功!</div> 返回消息
            driver.get(like_link)
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "ps")))  # <div class="ps">已赞！</div>

            driver.get('about:blank')

            write_comment_link(comment_link)
            driver.switch_to.window(driver.window_handles[0])
    return eid


if __name__ == '__main__':
    print('使用无界面浏览器启动?(按y确认 tip:登录时会弹出图形化浏览器)')
    view = input('-->')
    if view != 'y':
        view = 1
    else:
        view = 0
    driver = base(view)  # 初始化浏览器
    while True:
        prim_go(driver, view)

    # driver = base(1)
    # cookies = get_local_cookies()
    # open_homepage(driver, cookies)  # homepage test
		
