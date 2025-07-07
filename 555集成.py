import json
import os
import re
import sys
import time
from urllib.parse import quote
import requests
import yt_dlp
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

# 日志初始化
logger.add("log/search.log", rotation="1 MB", encoding="utf-8", enqueue=True,retention="1 days",
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")


class final_555:
    def __init__(self):
        self.choice_dicts = {}

    def build_search_code(self, search_content: str, base_url: str = "https://555ys.org/vodsearch/") -> tuple[str, str]:
        try:
            encoded_keyword = quote(search_content)
            if not base_url.endswith('?'):
                base_url += '?'
            full_url = f"{base_url}wd={encoded_keyword}"
            logger.info(f"搜索关键字转换成功：{search_content} → {encoded_keyword}")
            return full_url, encoded_keyword
        except Exception as e:
            logger.error(f"构造搜索 URL 失败：{e}")
            raise

    def get_find_content(self, code, page, result_dict):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "max-age=0",
            "referer": f"https://555ys.org/vodsearch/page/{page}/wd/{code}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }

        cookies = {
            "mx_style": "black",
            "showBtn": "true",
            "PHPSESSID": "test-session",
        }

        url = f"https://555ys.org/vodsearch/page/{page}/wd/{code}/"
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            find_lists = soup.find_all("div", {"class": "module-card-item-title"})

            if find_lists:
                for find_item in find_lists:
                    a_tag = find_item.find("a")
                    if a_tag:
                        title = a_tag.text.strip()
                        link = "https://555ys.org/" + a_tag["href"]
                        result_dict[title] = link
                logger.info(f"第 {page} 页：提取成功，获取 {len(find_lists)} 条记录")
                return True
            else:
                logger.info(f"第 {page} 页：无更多结果")
                return False
        except Exception as e:
            logger.error(f"第 {page} 页抓取失败：{e}")
            return False

    def main1(self):
        while True:
            search_content = input("请输入你所需的电影或电视剧名称：").strip()
            logger.info(f"用户输入搜索内容：{search_content}")

            search_url, result_code = self.build_search_code(search_content)

            find_dicts = {}
            for i in tqdm(range(1, 101), desc="搜索中...", ncols=100):
                if not self.get_find_content(result_code, i, find_dicts):
                    break

            if find_dicts:
                logger.success(f"共采集 {len(find_dicts)} 条结果")
                break
            else:
                logger.warning("未找到任何资源，请尝试重新输入其他关键词。")
                print("⚠️ 没有搜索到任何结果，请重新输入。\n")

        for title, link in find_dicts.items():
            print(f"{title} → {link}")

        print("\n" + "-" * 80)
        user_hope = input("请输入你所需要的资源名称：").strip()
        logger.info(f"用户选择了资源：{user_hope}")
        if user_hope in find_dicts:
            self.get_detail_option(find_dicts[user_hope])
        else:
            logger.warning(f"用户输入不在搜索结果中：{user_hope}")
            print("⚠️ 输入无效，未找到对应资源。请重新运行程序或检查名称是否完全一致。")

    def get_detail_option(self, url):
        headers = {
             "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        }
        cookies = {
            "PHPSESSID": "test-session"
        }

        response = requests.get(url, headers=headers, cookies=cookies)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 多线路播放
        line_titles = soup.select(".module-tab-item")
        play_blocks = soup.select(".module-list")

        if not line_titles or not play_blocks:
            logger.error("未能提取播放线路信息，请检查页面结构")
            return

        all_lines = {}
        for idx, (line, block) in enumerate(zip(line_titles, play_blocks)):
            line_name = line.text.strip() or f"线路{idx + 1}"
            full_line_name = f"{idx + 1} - {line_name}"
            episodes = {}
            for tag in block.select(".module-play-list-link"):
                ep_title = tag.get("title").strip()
                ep_url = "https://555ys.org" + tag["href"]
                episodes[ep_title] = ep_url
            all_lines[full_line_name] = episodes
            logger.info(f"提取播放线路：{full_line_name}，共 {len(episodes)} 集")

        # 用户选择线路
        print("以下为可用播放线路：")
        for i, name in enumerate(all_lines.keys(), 1):
            print(f"{i}. {name}")

        while True:
            line_input = input("请输入线路编号：").strip()
            if line_input.isdigit() and 1 <= int(line_input) <= len(all_lines):
                line_key = list(all_lines.keys())[int(line_input) - 1]
                logger.info(f"用户选择了线路：{line_key}")
                break
            else:
                print("输入错误，请输入有效编号。")

        # 用户选择集数
        ep_dict = all_lines[line_key]
        print(f"\n你选择的线路是【{line_key}】，共 {len(ep_dict)} 集")
        for i, ep in enumerate(ep_dict.keys(), 1):
            print(f"{i:02d}. {ep}")
        while True:
            ep_input = input("请输入你想看的集数名称（请完整复制标题）：").strip()
            if ep_input in ep_dict:
                logger.info(f"用户选择了集数：{ep_input}")
                break
            else:
                print("未找到该集数，请重新输入。")

        # 解析视频链接
        logger.info(f"开始获取 M3U8 链接：{ep_dict[ep_input]}")
        officel_url = self.get_m3u8(ep_dict[ep_input])
        if not officel_url:
            logger.warning("未能获取 M3U8 页面链接，将重新执行线路选择")
            return self.get_detail_option(url)

        vkey = self.get(ep_input, officel_url)
        if not vkey:
            logger.warning("vkey 获取失败，将重新执行线路选择")
            return self.get_detail_option(url)

        m3u8_dict = self.get_m3u81(officel_url, vkey)
        if not m3u8_dict or not isinstance(m3u8_dict, dict) or "url" not in m3u8_dict:
            logger.error("未成功解析 m3u8 地址，用户将重新选择")
            return self.get_detail_option(url)

        m3u8_url = m3u8_dict["url"]
        logger.success(f"成功解析 m3u8 地址：{m3u8_url}")

        # 下载
        downloader = DownLoad(m3u8_url, f'./result/{ep_input[2:]}.mp4')
        if downloader.download():
            logger.success("视频下载完成！")
        else:
            logger.error("视频下载失败。")

    def get_m3u8(self, url):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "referer": "https://555ys.org/v/3878/",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
        }
        cookies = {
            "mx_style": "black",
            "PHPSESSID": "ujcvgfb9bs6k4it2rfn0ct3ri3",
            "showBtn": "true",
            "mac_history_mxpro": "%5B%7B%22vod_name%22%3A%22%E8%A5%BF%E6%B8%B8%E9%99%8D%E9%AD%94%E7%AF%87%E4%B9%8B%E5%BF%AB%E6%B4%BB%E5%9F%8E%22%2C%22vod_url%22%3A%22https%3A%2F%2F555ys.org%2Fp%2F3878-1-1%2F%22%2C%22vod_part%22%3A%22%E6%AD%A3%E7%89%87%22%7D%2C%7B%22vod_name%22%3A%22%E7%81%AB%E5%BD%B1%E5%BF%8D%E8%80%85%EF%BC%9A%E5%BF%8D%E8%80%85%E4%B9%8B%E8%B7%AF%22%2C%22vod_url%22%3A%22https%3A%2F%2F555ys.org%2Fp%2F31319-1-1%2F%22%2C%22vod_part%22%3A%22%E7%81%AB%E5%BD%B1%E5%BF%8D%E8%80%85%EF%BC%9A%E5%BF%8D%E8%80%85%E4%B9%8B%E8%B7%AF%EF%BC%88%E5%8E%9F%E5%A3%B0%E7%89%88%EF%BC%89%22%7D%2C%7B%22vod_name%22%3A%22%E5%8F%98%E5%BD%A2%E9%87%91%E5%88%9A%22%2C%22vod_url%22%3A%22https%3A%2F%2F555ys.org%2Fvodplay%2F20043-7-1%2F%23slide%7B1%7D%22%2C%22vod_part%22%3A%22HD%E4%B8%AD%E5%AD%97%22%7D%5D"
        }

        response = requests.get(url, headers=headers, cookies=cookies)

        # 使用正则提取 player_aaaa 的 JSON 内容
        match = re.search(r'var player_aaaa=({.*?})</script>', response.text)
        if match:
            try:
                json_data = json.loads(match.group(1))
                m3u8_url = json_data.get("url")
                logger.success(f"获取成功，视频源网址为{m3u8_url}")
                return m3u8_url
            except json.JSONDecodeError as e:
                logger.error("JSON 解析失败：", e)
        else:
            print("未找到 player_aaaa 数据")

    def get(self, title, url1):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9",
            "priority": "u=0, i",
            "referer": "https://555ys.org/",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "iframe",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "cross-site",
            "sec-fetch-storage-access": "active",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
        }
        url = "https://xn--3svy77e.site/"
        params = {
            "url": url1,
            "next": "",
            "tittle": title
        }
        response = requests.get(url, headers=headers, params=params)

        # 正则提取 vkey
        match = re.search(r'"vkey"\s*:\s*"([^"]+)"', response.text)
        if match:
            vkey = match.group(1)
            logger.success(f"获取成功，参数vkey为{vkey}")
            return vkey
        else:
            logger.error("未找到 vkey")

    def get_m3u81(self, base_url, vkey):
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "origin": "https://xn--3svy77e.site",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Microsoft Edge\";v=\"138\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-fetch-storage-access": "active",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
            "x-requested-with": "XMLHttpRequest"
        }
        url = "https://xn--3svy77e.site/admin/mizhi_json.php"
        data = {
            "url": base_url,
            "time": int(time.time()),
            "key": "",
            "vkey": vkey
        }
        response = requests.post(url, headers=headers, data=data)
        logger.success("m3u8地址获取完成")
        try:
            return response.json()
        except:
            logger.error(response.text)



class DownLoad:
    def __init__(self, video_url, output_path):
        self.video_url = video_url
        self.output_path = self._get_resource_path(output_path)

        # ✅ 创建 result 文件夹（确保目标目录存在）
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        self.ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": str(self.output_path),
            "merge_output_format": "mp4",
            "concurrent_fragment_downloads": 8,
            "no_warnings": True,
            "http_headers": {
                "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            },
        }

    def _get_resource_path(self, relative_path):
        """返回以当前 .py 文件所在目录为基准的路径"""
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        return os.path.join(base_path, relative_path)

    def download(self):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([self.video_url])
                return True
        except Exception as e:
            return False, str(e)


if __name__ == "__main__":
    obj = final_555()
    obj.main1()