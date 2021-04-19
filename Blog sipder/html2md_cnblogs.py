import os
import re

import html2epub
import html2text
import requests
from bs4 import BeautifulSoup
from parsel import Selector

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'
}


def get_all_article_id(blog_url):
    articleid = []
    page = 1
    while True:
        page_ = '%s/default.html?page=%s' % (blog_url, page)
        content = requests.get(page_, headers=headers).content.decode(errors='ignore')
        soup = BeautifulSoup(content, features="lxml")
        links = soup.select('.postTitle2')
        if not links:
            break
        else:
            for link in links:
                articleid.append(link.attrs['href'])
        page += 1
    return articleid


def get_all_article(csdn):
    for article_id in get_all_article_id(csdn):
        article_url = article_id
        get_article(article_url)


def get_article(article_url):
    __down_article(article_url)


def eq2tex(content):
    content = content.replace('\n\\\\(', '\\\\(')
    content = content.replace(' \\\\(', '\\\\(')
    content = content.replace('\\\\( ', '\\\\(')
    content = content.replace('\\\\(\n', '\\\\(')
    content = content.replace('\\\\(', ' \\\\(')
    content = content.replace('\\\\(', '$')
    
    content = content.replace('\n\\\\)', '\\\\)')
    content = content.replace(' \\\\)', '\\\\)')
    content = content.replace('\\\\)\n', '\\\\)')
    content = content.replace('\\\\) ', '\\\\)')
    content = content.replace('\\\\)', '\\\\) ')
    content = content.replace('\\\\)', '$')

    content = content.replace('\n\\\\[', '\\\\[')
    content = content.replace('\\\\[\n', '\\\\[')
    content = content.replace('\\\\[', '\n\\\\[')
    content = content.replace('\\\\[', '$$')

    content = content.replace('\n\\\\]', '\\\\]')
    content = content.replace('\\\\]\n', '\\\\]')
    content = content.replace('\\\\]', '\\\\]\n')
    content = content.replace('\\\\]', '$$')

    content = content.replace('**\n', '**')
    content = content.replace('\n**', '**')

    content = content.replace('-\n', '-')
    content = content.replace('`\n', '`')
    content = content.replace('\n`', '`')

    # content = content.replace(')\n', ')')
    content = content.replace('\n)', ')')
    # content = content.replace(']\n', ']')
    content = content.replace('\n]', ']')
    content = content.replace('，\n', '，')
    content = content.replace('\n，', '，')


    pos = 0 
    while pos < content.rfind('('):
        start = content.index('(', pos)
        end =  content.index(')', pos)

        string = content[start:end+1]
        string = string.replace('\n', ' ')

        content = content[:start] + string + content[end+1:]


        pos = start + len(string)
        print(string)
    
    print(content.find('\\\\('), ' \\\\(')

    return content
    

def __down_article(article_url):
    get = requests.get(article_url, headers=headers)
    if get.status_code != 200:
        return
    content = get.content.decode(errors='ignore')
    soup = BeautifulSoup(content, features="lxml")
    sel = Selector(text=content)
    user_name = sel.css('.HeaderMainTitle::text').get()
    title = sel.css('title::text').get()
    blogpost_body_ = soup.select('.blogpost-body')[0]
    content = str(blogpost_body_.prettify())
    if 'cnblogs-markdown' in blogpost_body_.attrs['class']:
        print('博客书写类型：markdown')
    else:
        print('博客书写类型，并非支持的markdown，可能需要手动修改！')

    content = html2_markdown_text(content)
    content = eq2tex(content)
    # 转成markdown文件,并保存文件
    save_file(content, safe_file_name(title), safe_file_name(user_name))


def safe_file_name(file_name):
    return re.sub(r'[\|/|:|*|?|"|<|>|\|]', "", file_name)


def html2_markdown_text(content):
    h = html2text.HTML2Text()
    return h.handle(content)


def save_file(content, title, user_name):
    path = './%s' % user_name
    if not os.path.exists(path):
        os.mkdir(path)
    file = '%s/%s.md' % (path, title)
    if not os.path.exists(file):
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("%s 下载成功！" % file)
    else:
        print("%s 已存在！" % file)


def generate_epub_file(chapters, epub_name="epub_name", output_directory="OUTPUT_DIRECTORY"):
    if not chapters:
        return

    epub = html2epub.Epub(epub_name)

    def set_chapter(type, chapter):
        if type in 'content':
            epub.add_chapter(html2epub.create_chapter_from_string(chapter, title=chapter))
        elif type in 'url':
            epub.add_chapter(html2epub.create_chapter_from_url(chapter))
        elif type in 'file':
            epub.add_chapter(html2epub.create_chapter_from_file(chapter))

    for type_chapter in chapters:
        cur_chapter = chapters[type_chapter]
        if not cur_chapter:
            continue
        if isinstance(cur_chapter, str):
            set_chapter(type_chapter, cur_chapter)
        elif isinstance(chapters[type_chapter], list):
            for chapter2 in cur_chapter:
                if not chapter2:
                    continue
                set_chapter(type_chapter, chapter2)
    epub.create_epub(output_directory, epub_name)


if __name__ == '__main__':
    # get_all_article('https://www.cnblogs.com/SivilTaram')
    get_article('https://www.cnblogs.com/SivilTaram/p/graph_neural_network_1.html')
    # get_article('https://www.cnblogs.com/SivilTaram/p/graph_neural_network_2.html')
    # get_article('https://www.cnblogs.com/SivilTaram/p/graph_neural_network_3.html')

