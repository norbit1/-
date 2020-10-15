import os
import json
import traceback
import asyncio
import aiohttp
import random
import string
import base64
from hoshino import R
from .config import get_config, get_group_config
from .acggov import acggov_init, acggov_fetch_process, acggov_get_setu, acggov_search_setu, acggov_get_ranking_setu, acggov_get_ranking
from .lolicon import lolicon_init, lolicon_get_setu,lolicon_fetch_process, lolicon_search_setu


def check_path():
    state = {}
    sub_dirs = ['acggov', 'lolicon', 'lolicon_r18']
    for item in sub_dirs:
        res = R.img('setu_mix/' + item)
        if not os.path.exists(res.path):
            os.makedirs(res.path)
        state[item] = len(os.listdir(res.path)) // 2
    return state
check_path()

def add_salt(data):
    salt = ''.join(random.sample(string.ascii_letters + string.digits, 6))
    return data + bytes(salt, encoding="utf8")

def format_setu_msg(image):
    base64_str = f"base64://{base64.b64encode(add_salt(image['data'])).decode()}"
    msg = f'id:{image["id"]}\ntitle:{image["title"]}\nauthor:{image["author"]}\n[CQ:image,file={base64_str}]'
    return msg

async def get_setu(group_id):
    source_list = []
    if get_group_config(group_id, 'lolicon'):
        source_list.append(1)
    if get_group_config(group_id, 'lolicon_r18'):
        source_list.append(2)
    if get_group_config(group_id, 'acggov'):
        source_list.append(3)
    source = 0
    if len(source_list) > 0:
        source = random.choice(source_list)
    
    image = None
    if source == 1:
        image = await lolicon_get_setu(0)
    elif source == 2:
        image = await lolicon_get_setu(1)
    elif source == 3:
        image = await acggov_get_setu()
    else:
        return '功能未启用'
    if not image:
        return '获取失败'
    elif image['id'] != 0:
        return format_setu_msg(image)
    else:
        return image['title']

async def search_setu(group_id, keyword):
    source_list = []
    if get_group_config(group_id, 'lolicon') and get_group_config(group_id, 'lolicon_r18'):
        source_list.append(2)
    elif get_group_config(group_id, 'lolicon'):
        source_list.append(0)
    elif get_group_config(group_id, 'lolicon_r18'):
        source_list.append(1)
    if get_group_config(group_id, 'acggov'):
        source_list.append(3)

    if len(source_list) == 0:
        return '无可用模块'

    while len(source_list) > 0:
        source = source_list.pop(random.randint(0, len(source_list) - 1))
        if source == 0:
            image = await lolicon_search_setu(keyword, 0)
        elif source == 1:
            image = await lolicon_search_setu(keyword, 1)
        elif source == 2:
            image = await lolicon_search_setu(keyword, 2)
        elif source == 3:
            image = await acggov_search_setu(keyword)
        if image and image['id'] != 0:
            return format_setu_msg(image)
    return '无搜索结果'

async def get_ranking(group_id, page: int = 0):
    if not get_group_config(group_id, 'acggov'):
        return 'acggov模块未启用'
    return await acggov_get_ranking(page)


async def get_ranking_setu(group_id, number: int) -> (int, str):
    if not get_group_config(group_id, 'acggov'):
        return 'acggov模块未启用'
    image = await acggov_get_ranking_setu(number)
    if not image:
        return '获取失败'
    elif image['id'] != 0:
        return format_setu_msg(image)
    else:
        return image['title']

async def fetch_process():
    tasks = []
    tasks.append(asyncio.ensure_future(acggov_fetch_process()))
    tasks.append(asyncio.ensure_future(lolicon_fetch_process()))
    for task in asyncio.as_completed(tasks):
        await task

acggov_init()
lolicon_init()