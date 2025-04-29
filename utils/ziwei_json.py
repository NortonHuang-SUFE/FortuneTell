# python_iztro/json2ziwei/solar_api.py

import requests
import json

class SolarAPI:
    def __init__(self, base_url):
        """初始化 SolarAPI 类
        
        :param base_url: API 的基础 URL
        """
        self.base_url = base_url

    def get_astrolabe_data(self, date, timezone, gender, period, is_solar=True):
        """发送 POST 请求以获取星盘数据
        
        :param date: 日期字符串，格式为 "YYYY-MM-DD"
        :param timezone: 时区偏移量
        :param gender: 性别字符串
        :param is_solar: 是否为阳历数据
        :return: 响应的 JSON 数据
        """
        endpoint = "solar" if is_solar else "lunar"
        url = f"{self.base_url}/api/astro/{endpoint}"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "date": date,
            "timezone": timezone,
            "gender": gender,
            "period": period
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()  # 抛出异常以处理错误


def convert_palace_json_to_text(json_data):
    """
    将单个宫位的紫微斗数 JSON 数据转换为文本描述。

    参数:
    json_data (dict): 包含单个宫位紫微斗数信息的 JSON 数据。

    返回:
    str: 描述单个宫位紫微斗数信息的文本字符串。
    """

    output_lines = []

    # 宫位信息
    output_lines.append(f"宫位{json_data['index']}号位，宫位名称是{json_data['name']}。")
    output_lines.append(f"{'是' if json_data['isBodyPalace'] else '不是'}身宫，{'是' if json_data['isOriginalPalace'] else '不是'}来因宫。")
    output_lines.append(f"宫位天干为{json_data['heavenlyStem']}，宫位地支为{json_data['earthlyBranch']}。")

    # 主星
    major_stars_desc = "主星:"
    major_stars_list = []
    for star in json_data['majorStars']:
        brightness_desc = f"亮度为{star['brightness']}" if star['brightness'] else "无亮度标志"
        #  修改部分：使用 get 方法安全获取 mutagen，并判断 None 或 "" 都表示无四化星
        mutagen_value = star.get('mutagen')
        mutagen_desc = "，无四化星" if star['type'] == 'major' and (mutagen_value is None or mutagen_value == "") else f"，{mutagen_value}四化星" if mutagen_value else ""

        star_desc = f"{star['name']}（本命星耀，{brightness_desc}{mutagen_desc}）" if star['scope'] == 'origin' else f"{star['name']}（{star['scope']}星耀，{brightness_desc}{mutagen_desc}）" # 兼容其他scope，虽然例子里只有 origin

        if star['type'] == 'tianma':
            star_desc = f"{star['name']}（本命星耀，无亮度标志）" # 天马 特殊处理
        major_stars_list.append(star_desc)
    major_stars_desc += "，".join(major_stars_list)
    output_lines.append(major_stars_desc)

    # 辅星
    if not json_data['minorStars']:
        output_lines.append("辅星：无")
    else: # 如果有辅星，可以继续扩展代码来处理，目前例子没有辅星
        minor_stars_desc = "辅星："
        minor_stars_list = []
        for star in json_data['minorStars']:
            star_desc = f"{star['name']}（本命星耀）" # 示例中辅星没有更多信息，可以根据实际情况扩展
            minor_stars_list.append(star_desc)
        minor_stars_desc += "，".join(minor_stars_list)
        output_lines.append(minor_stars_desc)

    # 杂耀
    adjective_stars_desc = "杂耀:"
    adjective_stars_list = []
    for star in json_data['adjectiveStars']:
        star_desc = f"{star['name']}（本命星耀）" # 示例中杂耀也没有更多信息
        adjective_stars_list.append(star_desc)
    adjective_stars_desc += "，".join(adjective_stars_list)
    output_lines.append(adjective_stars_desc)

    # 长生 12 神，博士 12 神，流年将前 12 神，流年岁前 12 神
    output_lines.append(f"长生 12 神:{json_data['changsheng12']}。")
    output_lines.append(f"博士 12 神:{json_data['boshi12']}。")
    output_lines.append(f"流年将前 12 神:{json_data['jiangqian12']}。")
    output_lines.append(f"流年岁前 12 神:{json_data['suiqian12']}。")

    # 大限
    decadal_info = json_data.get('decadal') # 使用get方法防止KeyError
    if decadal_info:
        output_lines.append(f"大限:{decadal_info['range'][0]},{decadal_info['range'][1]}(运限天干为{decadal_info['heavenlyStem']}，运限地支为{decadal_info['earthlyBranch']})。")

    # 小限
    if json_data.get('ages'): # 使用get方法防止KeyError
        output_lines.append(f"小限:{','.join(map(str, json_data['ages']))}") # 将数字列表转换为逗号分隔的字符串

    return "\n".join(output_lines)

def convert_main_json_to_text(main_json_data):
    """
    将包含个人信息和宫位数组的紫微斗数 JSON 数据转换为文本描述。

    参数:
    main_json_data (dict): 包含完整紫微斗数信息的 JSON 数据。

    返回:
    str: 描述完整紫微斗数信息的文本字符串。
    """
    output_lines = []

    #  基本信息
    output_lines.append("----------基本信息----------")
    output_lines.append(f"命主性别：{main_json_data.get('gender', '未知')}")
    output_lines.append(f"阳历生日：{main_json_data.get('solarDate', '未知')}")
    output_lines.append(f"阴历生日：{main_json_data.get('lunarDate', '未知')}")
    output_lines.append(f"八字：{main_json_data.get('chineseDate', '未知')}")
    output_lines.append(f"生辰时辰：{main_json_data.get('time', '未知')} ({main_json_data.get('timeRange', '未知')})")
    output_lines.append(f"星座：{main_json_data.get('sign', '未知')}")
    output_lines.append(f"生肖：{main_json_data.get('zodiac', '未知')}")
    output_lines.append(f"身宫地支：{main_json_data.get('earthlyBranchOfBodyPalace', '未知')}")
    output_lines.append(f"命宫地支：{main_json_data.get('earthlyBranchOfSoulPalace', '未知')}")
    output_lines.append(f"命主星：{main_json_data.get('soul', '未知')}")
    output_lines.append(f"身主星：{main_json_data.get('body', '未知')}")
    output_lines.append(f"五行局：{main_json_data.get('fiveElementsClass', '未知')}")
    output_lines.append("----------宫位信息----------")

    # 宫位信息 (如果 palaces 数组存在且不为空)
    palaces_data = main_json_data.get('palaces')
    if palaces_data and isinstance(palaces_data, list):
        if not palaces_data:
            output_lines.append("宫位信息：暂未提供") # 或者其他提示信息
        else:
            for palace_json in palaces_data:
                palace_text = convert_palace_json_to_text(palace_json)
                output_lines.append(palace_text)
                output_lines.append("----------") # 分隔每个宫位的信息
    else:
        output_lines.append("宫位信息：数据格式不正确或缺失")

    return "\n".join(output_lines)

def convert_yearly_json_to_text(yearly_json_data):
    """
    将年度紫微斗数 JSON 数据转换为文本描述，适合大模型阅读。

    参数:
    yearly_json_data (dict): 包含年度紫微斗数信息的 JSON 数据。

    返回:
    str: 描述年度紫微斗数信息的文本字符串。
    """
    output_lines = []
    
    # 基本信息
    output_lines.append(f"阳历日期：{yearly_json_data.get('solarDate', '未知')}")
    output_lines.append(f"阴历日期：{yearly_json_data.get('lunarDate', '未知')}")
    
    # 大限信息
    decadal_info = yearly_json_data.get('decadal', {})
    if decadal_info:
        output_lines.append(f"大限：{decadal_info.get('name', '')}，天干为{decadal_info.get('heavenlyStem', '')}，地支为{decadal_info.get('earthlyBranch', '')}")
        
        # 大限四化星
        mutagen = decadal_info.get('mutagen', [])
        if mutagen:
            output_lines.append(f"大限四化星：{', '.join(mutagen)}")
        
        # 大限星耀
        stars = decadal_info.get('stars', [])
        if stars:
            star_descriptions = []
            for i, palace_stars in enumerate(stars):
                if palace_stars:
                    palace_name = decadal_info.get('palaceNames', [])[i] if i < len(decadal_info.get('palaceNames', [])) else f"宫位{i+1}"
                    star_names = [f"{star.get('name', '')}（{star.get('type', '')}，{star.get('scope', '')}）" for star in palace_stars]
                    star_descriptions.append(f"{palace_name}宫：{', '.join(star_names)}")
            
            if star_descriptions:
                output_lines.append("大限星耀分布：")
                for desc in star_descriptions:
                    output_lines.append(f"  {desc}")
    
    # 流年信息
    yearly_info = yearly_json_data.get('yearly', {})
    if yearly_info:
        output_lines.append(f"流年：{yearly_info.get('name', '')}，天干为{yearly_info.get('heavenlyStem', '')}，地支为{yearly_info.get('earthlyBranch', '')}")
        
        # 流年四化星
        mutagen = yearly_info.get('mutagen', [])
        if mutagen:
            output_lines.append(f"流年四化星：{', '.join(mutagen)}")
        
        # 流年星耀
        stars = yearly_info.get('stars', [])
        if stars:
            star_descriptions = []
            for i, palace_stars in enumerate(stars):
                if palace_stars:
                    palace_name = yearly_info.get('palaceNames', [])[i] if i < len(yearly_info.get('palaceNames', [])) else f"宫位{i+1}"
                    star_names = [f"{star.get('name', '')}（{star.get('type', '')}，{star.get('scope', '')}）" for star in palace_stars]
                    star_descriptions.append(f"{palace_name}宫：{', '.join(star_names)}")
            
            if star_descriptions:
                output_lines.append("流年星耀分布：")
                for desc in star_descriptions:
                    output_lines.append(f"  {desc}")
        
        # 流年将前12神和岁前12神
        yearly_dec_star = yearly_info.get('yearlyDecStar', {})
        if yearly_dec_star:
            jiangqian12 = yearly_dec_star.get('jiangqian12', [])
            suiqian12 = yearly_dec_star.get('suiqian12', [])
            
            if jiangqian12:
                output_lines.append(f"流年将前12神：{', '.join(jiangqian12)}")
            if suiqian12:
                output_lines.append(f"流年岁前12神：{', '.join(suiqian12)}")
    
    return "\n".join(output_lines)

def convert_yearly_array_to_text(yearly_array):
    """
    将年度数组转换为文本描述，每年用横线分隔。

    参数:
    yearly_array (list): 包含年度紫微斗数信息的 JSON 数组。

    返回:
    str: 描述所有年度紫微斗数信息的文本字符串。
    """
    output_lines = []
    output_lines.append("---------大限与流年信息----------")
    for i, yearly_data in enumerate(yearly_array):
        output_lines.append(f"----------{yearly_data.get('solarDate', '未知年份')}----------")
        yearly_text = convert_yearly_json_to_text(yearly_data)
        output_lines.append(yearly_text)
        
        # 如果不是最后一年，添加分隔线
        if i < len(yearly_array) - 1:
            output_lines.append("----------")
    output_lines.append("---------大限与流年信息----------")
    return "\n".join(output_lines)

def get_astrolabe_text(date, hour, gender, period, is_solar=True, base_url="http://localhost:3000"):
    """
    获取紫微斗数文本描述，包括本命盘和流年信息。

    参数:
    date (str): 日期字符串，格式为 "YYYY-MM-DD"
    hour (int): 小时 (0-23)
    minute (int): 分钟 (0-59)
    gender (str): 性别
    period (list): 时间段，格式为 ["YYYY-MM-DD", "YYYY-MM-DD"]
    is_solar (bool): 是否为阳历数据，默认为 True
    base_url (str): API 的基础 URL，默认为 "http://localhost:3000"

    返回:
    str: 完整的紫微斗数文本描述
    """
    # 将时间转换为时辰序号
    timezone = (hour + 1) // 2
    if timezone == 12:  # 处理23:00-1:00的情况
        timezone = 0
    
    # 初始化 API 客户端
    solar_api = SolarAPI(base_url)
    
    # 获取星盘数据
    json_data = solar_api.get_astrolabe_data(date, timezone, gender, period, is_solar)
    
    # 获取本命盘数据
    main_data = json_data.get('astrolabeSolar')
    # 获取流年数据
    yearly_array = json_data.get('arr', [])
    
    # 转换本命盘数据为文本
    main_text = convert_main_json_to_text(main_data)
    # 转换流年数据为文本
    yearly_text = convert_yearly_array_to_text(yearly_array)
    
    # 组合所有文本
    combined_text = f"{main_text}\n\n{yearly_text}"
    
    return combined_text

# 示例使用
#result = get_astrolabe_text("2000-8-16", 14, 30, "女", ["2025-01-01", "2026-01-02"])
#print(result)
