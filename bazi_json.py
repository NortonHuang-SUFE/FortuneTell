#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 作者: 基于钉钉、抖音或微信pythontesting 钉钉群21734177的代码
# 创建日期: 2023

import argparse
import collections
import json
import datetime
import io
import sys
from contextlib import redirect_stdout

from lunar_python import Lunar, Solar
from colorama import init

from datas import *
from sizi import summarys
from common import *
from yue import months

def get_gen(gan, zhis):
    zhus = []
    zhongs = []
    weis = []
    result = ""
    for item in zhis:
        zhu = zhi5_list[item][0]
        if ten_deities[gan]['本'] == ten_deities[zhu]['本']:
            zhus.append(item)

    for item in zhis:
        if len(zhi5_list[item]) == 1:
            continue
        zhong = zhi5_list[item][1]
        if ten_deities[gan]['本'] == ten_deities[zhong]['本']:
            zhongs.append(item)

    for item in zhis:
        if len(zhi5_list[item]) < 3:
            continue
        zhong = zhi5_list[item][2]
        if ten_deities[gan]['本'] == ten_deities[zhong]['本']:
            weis.append(item)

    if not (zhus or zhongs or weis):
        return "无根"
    else:
        result = result + "强：{}{}".format(''.join(zhus), chr(12288)) if zhus else result
        result = result + "中：{}{}".format(''.join(zhongs), chr(12288)) if zhongs else result
        result = result + "弱：{}".format(''.join(weis)) if weis else result
        return result

def gan_zhi_he(zhu):
    gan, zhi = zhu
    if ten_deities[gan]['合'] in zhi5[zhi]:
        return "|"
    return ""

def get_gong(zhis, gans):
    result = []
    for i in range(3):
        if  gans[i] != gans[i+1]:
            continue
        zhi1 = zhis[i]
        zhi2 = zhis[i+1]
        if abs(Zhi.index(zhi1) - Zhi.index(zhi2)) == 2:
            value = Zhi[(Zhi.index(zhi1) + Zhi.index(zhi2))//2]
            #if value in ("丑", "辰", "未", "戌"):
            result.append(value)
        if (zhi1 + zhi2 in gong_he) and (gong_he[zhi1 + zhi2] not in zhis):
            result.append(gong_he[zhi1 + zhi2]) 
            
        #if (zhi1 + zhi2 in gong_hui) and (gong_hui[zhi1 + zhi2] not in zhis):
            #result.append(gong_hui[zhi1 + zhi2])             
        
    return result

class BaziAnalyzer:
    def __init__(self):
        self.output_sections = {}
        self.current_section = "基本信息"
        self.capture_buffer = io.StringIO()
        
    def add_to_section(self, text):
        """向当前部分添加文本"""
        if self.current_section not in self.output_sections:
            self.output_sections[self.current_section] = []
        
        self.output_sections[self.current_section].append(text)
    
    def set_section(self, section_name):
        """更改当前部分"""
        self.current_section = section_name
    
    def capture_print_output(self, func, *args, **kwargs):
        """捕获函数的打印输出到当前部分"""
        # 创建一个StringIO对象来捕获输出
        with redirect_stdout(self.capture_buffer):
            result = func(*args, **kwargs)
        
        # 获取捕获的输出
        captured_output = self.capture_buffer.getvalue()
        self.capture_buffer = io.StringIO()  # 重置缓冲区
        
        # 按行分割并将非空行添加到当前部分
        for line in captured_output.split('\n'):
            if line.strip():
                self.add_to_section(line.strip())
        
        return result
    
    def analyze_bazi(self, year, month, day, time, minute=0, gender=False, solar=False, run_month=False):
        """
        分析八字并返回JSON结果
        
        参数:
            year: 年份(整数)
            month: 月份(整数)
            day: 日期(整数)
            time: 小时(整数)
            gender: 女性为True，男性为False(布尔值)
            solar: 公历为True，农历为False(布尔值)
            run_month: 如果是闰月则为True(布尔值)
            minute: 分钟(整数)，默认为0
        
        返回:
            包含分析结果的JSON字符串
        """
        self.output_sections = {}
        self.current_section = "基本信息"
        
        # 创建一个解析器对象传递给原始代码
        parser = argparse.ArgumentParser()
        options = parser.parse_args([])
        options.year = year
        options.month = month
        options.day = day
        options.time = time
        options.n = gender
        options.g = solar
        options.r = run_month
        options.b = False
        options.start = 1850
        options.end = '2030'
        
        # 设置日期信息
        if options.g:
            solar = Solar.fromYmdHms(int(options.year), int(options.month), int(options.day), int(options.time), int(minute), 0)
            lunar = solar.getLunar()
        else:
            month_ = int(options.month)*-1 if options.r else int(options.month)
            lunar = Lunar.fromYmdHms(int(options.year), month_, int(options.day), int(options.time), int(minute), 0)
            solar = lunar.getSolar()

        day = lunar
        ba = lunar.getEightChar() 
        gans = collections.namedtuple("Gans", "year month day time")(
            year=ba.getYearGan(), month=ba.getMonthGan(), 
            day=ba.getDayGan(), time=ba.getTimeGan())
        zhis = collections.namedtuple("Zhis", "year month day time")(
            year=ba.getYearZhi(), month=ba.getMonthZhi(), 
            day=ba.getDayZhi(), time=ba.getTimeZhi())

        # 将基本信息添加到JSON输出
        self.add_to_section(f"性别: {'女' if options.n else '男'}")
        self.add_to_section(f"公历: {solar.getYear()}年{solar.getMonth()}月{solar.getDay()}日 {solar.getHour()}:{solar.getMinute()}")
        
        yun = ba.getYun(not options.n)
        self.add_to_section(f"农历: {lunar.getYear()}年{lunar.getMonth()}月{lunar.getDay()}日 {lunar.getHour()}:{lunar.getMinute()}")
        self.add_to_section(f"上运时间: {yun.getStartSolar().toFullString().split()[0]}")
        self.add_to_section(f"命宫: {ba.getMingGong()}")
        self.add_to_section(f"胎元: {ba.getTaiYuan()}")
        
        self.add_to_section(f"前节气: {lunar.getPrevJieQi(True)}, {lunar.getPrevJieQi(True).getSolar().toYmdHms()}")
        self.add_to_section(f"后节气: {lunar.getNextJieQi(True)}, {lunar.getNextJieQi(True).getSolar().toYmdHms()}")
        
        # 设置计算所需的变量
        me = gans.day
        month = zhis.month
        alls = list(gans) + list(zhis)
        zhus = [item for item in zip(gans, zhis)]

        # 这里我们设置原始代码中需要的变量
        gan_shens = []
        for seq, item in enumerate(gans):    
            if seq == 2:
                gan_shens.append('--')
            else:
                gan_shens.append(ten_deities[me][item])
                
        zhi_shens = [] # 地支的主气神
        for item in zhis:
            d = zhi5[item]
            zhi_shens.append(ten_deities[me][max(d, key=d.get)])
            
        shens = gan_shens + zhi_shens

        zhi_shens2 = [] # 地支的所有神，包含余气和尾气, 混合在一起
        zhi_shen3 = [] # 地支所有神，字符串格式
        for item in zhis:
            d = zhi5[item]
            tmp = ''
            for item2 in d:
                zhi_shens2.append(ten_deities[me][item2])
                tmp += ten_deities[me][item2]
            zhi_shen3.append(tmp)
        shens2 = gan_shens + zhi_shens2
            
        
        # 计算五行分数
        scores = {"金":0, "木":0, "水":0, "火":0, "土":0}
        gan_scores = {"甲":0, "乙":0, "丙":0, "丁":0, "戊":0, "己":0, "庚":0, "辛":0,
                    "壬":0, "癸":0}   

        for item in gans:  
            scores[gan5[item]] += 5
            gan_scores[item] += 5

        for item in list(zhis) + [zhis.month]:  
            for gan in zhi5[item]:
                scores[gan5[gan]] += zhi5[item][gan]
                gan_scores[gan] += zhi5[item][gan]
                
        # 计算八字强弱
        # 子平真诠的计算
        weak = True
        me_status = []
        for item in zhis:
            me_status.append(ten_deities[me][item])
            if ten_deities[me][item] in ('长', '帝', '建'):
                weak = False
                
        if weak:
            if shens.count('比') + me_status.count('库') > 2:
                weak = False
                
        # 计算五行得分
        me_attrs_ = ten_deities[me].inverse
        strong = gan_scores[me_attrs_['比']] + gan_scores[me_attrs_['劫']] \
            + gan_scores[me_attrs_['枭']] + gan_scores[me_attrs_['印']]

        # 计算大运（主要命运周期）
        seq = Gan.index(gans.year)
        if options.n:
            if seq % 2 == 0:
                direction = -1
            else:
                direction = 1
        else:
            if seq % 2 == 0:
                direction = 1
            else:
                direction = -1

        dayuns = []
        gan_seq = Gan.index(gans.month)
        zhi_seq = Zhi.index(zhis.month)
        for i in range(12):
            gan_seq += direction
            zhi_seq += direction
            dayuns.append(Gan[gan_seq%10] + Zhi[zhi_seq%12])
            
        # 设置部分并处理分析的不同部分
        
        # 四柱和天干地支分析
        self.set_section("四柱")
        self.add_to_section(' '.join(list(gans)) + ' | ' + ' '.join(list(gan_shens)))
        self.add_to_section(' '.join(list(zhis)) + ' | ' + ' '.join(list(zhi_shens)))
        self.add_to_section('四柱：' + ' '.join([''.join(item) for item in zip(gans, zhis)]))
        
        self.set_section("年月日时")
        self.add_to_section(f"【年】{temps[gans.year]}:{temps[zhis.year]}{ten_deities[gans.year].inverse['建']}{gan_zhi_he(zhus[0])}")
        self.add_to_section(f"【月】{temps[gans.month]}:{temps[zhis.month]}{ten_deities[gans.month].inverse['建']}{gan_zhi_he(zhus[1])}")
        self.add_to_section(f"【日】{temps[me]}:{temps[zhis.day]}{gan_zhi_he(zhus[2])}")
        self.add_to_section(f"【时】{temps[gans.time]}:{temps[zhis.time]}{ten_deities[gans.time].inverse['建']}{gan_zhi_he(zhus[3])}")
        
        # 天干分析
        self.set_section("天干")
        self.add_to_section(f"{gans.year}{yinyang(gans.year)}{gan5[gans.year]}【{ten_deities[me][gans.year]}】{check_gan(gans.year, gans)}")
        self.add_to_section(f"{gans.month}{yinyang(gans.month)}{gan5[gans.month]}【{ten_deities[me][gans.month]}】{check_gan(gans.month, gans)}")
        self.add_to_section(f"{me}{yinyang(me)}{gan5[me]}{check_gan(me, gans)}")
        self.add_to_section(f"{gans.time}{yinyang(gans.time)}{gan5[gans.time]}【{ten_deities[me][gans.time]}】{check_gan(gans.time, gans)}")
        
        # 地支分析
        self.set_section("地支")
        self.add_to_section(f"{zhis.year}{yinyang(zhis.year)}{ten_deities[gans.year][zhis.year]}{ten_deities[gans.month][zhis.year]}【{ten_deities[me][zhis.year]}】{ten_deities[gans.time][zhis.year]}{get_empty(zhus[2],zhis.year)}")
        self.add_to_section(f"{zhis.month}{yinyang(zhis.month)}{ten_deities[gans.year][zhis.month]}{ten_deities[gans.month][zhis.month]}【{ten_deities[me][zhis.month]}】{ten_deities[gans.time][zhis.month]}{get_empty(zhus[2],zhis.month)}")
        self.add_to_section(f"{zhis.day}{yinyang(zhis.day)}{ten_deities[gans.year][zhis.day]}{ten_deities[gans.month][zhis.day]}【{ten_deities[me][zhis.day]}】{ten_deities[gans.time][zhis.day]}")
        self.add_to_section(f"{zhis.time}{yinyang(zhis.time)}{ten_deities[gans.year][zhis.time]}{ten_deities[gans.month][zhis.time]}【{ten_deities[me][zhis.time]}】{ten_deities[gans.time][zhis.time]}{get_empty(zhus[2],zhis.time)}")
        
        # 地支藏干
        self.set_section("地支藏干")
        for seq, item in enumerate(zhis):
            out = ''
            multi = 2 if item == zhis.month and seq == 1 else 1
            for gan in zhi5[item]:
                out = out + "{}{}{}　".format(gan, gan5[gan], ten_deities[me][gan])
            self.add_to_section(out.rstrip('　'))
            
        # 地支关系
        self.set_section("地支关系")
        for seq, item in enumerate(zhis):
            output = ''
            others = zhis[:seq] + zhis[seq+1:] 
            for type_ in zhi_atts[item]:
                flag = False
                if type_ in ('害',"破","会",'刑'):
                    continue
                for zhi in zhi_atts[item][type_]:
                    if zhi in others:
                        if not flag:
                            output = output + "　" + type_ + "：" if type_ not in ('冲','暗') else output + "　" + type_
                            flag = True
                        if type_ not in ('冲','暗'):
                            output += zhi
            output = output.lstrip('　')
            self.add_to_section(output)
            
        # 地支次要关系
        self.set_section("地支次要关系")
        for seq, item in enumerate(zhis):
            output = ''
            others = zhis[:seq] + zhis[seq+1:] 
            for type_ in zhi_atts[item]:
                flag = False
                if type_ not in ('害',"破","会",'刑'):
                    continue
                for zhi in zhi_atts[item][type_]:
                    if zhi in others:
                        if not flag:
                            output = output + "　" + type_ + "："
                            flag = True
                        output += zhi
            output = output.lstrip('　')
            self.add_to_section(output)
            
        # 五行根
        self.set_section("五行根")
        for item in gans:
            self.add_to_section(get_gen(item, zhis))
            
        # 纳音和关系
        self.set_section("纳音和关系")
        for seq, item in enumerate(zhus):
            # 检查空亡 
            result = "{}－{}".format(nayins[item], '亡') if zhis[seq] == wangs[zhis[0]] else nayins[item]
            
            # 天干与地支关系
            result = relations[(gan5[gans[seq]], zhi_wuhangs[zhis[seq]])] + result
                
            # 检查劫杀 
            result = "{}－{}".format(result, '劫杀') if zhis[seq] == jieshas[zhis[0]] else result
            # 检查元辰
            result = "{}－{}".format(result, '元辰') if zhis[seq] == Zhi[(Zhi.index(zhis[0]) + direction*-1*5)%12] else result    
            self.add_to_section(result)
            
        # 神煞
        self.set_section("神煞")
        strs = ['','','','',]

        all_shens = set()
        all_shens_list = []

        for item in year_shens:
            for i in (1,2,3):
                if zhis[i] in year_shens[item][zhis.year]:    
                    strs[i] = item if not strs[i] else strs[i] + chr(12288) + item
                    all_shens.add(item)
                    all_shens_list.append(item)
                    
        for item in month_shens:
            for i in range(4):
                if gans[i] in month_shens[item][zhis.month] or zhis[i] in month_shens[item][zhis.month]:     
                    strs[i] = item if not strs[i] else strs[i] + chr(12288) + item
                    if i == 2 and gans[i] in month_shens[item][zhis.month]:
                        strs[i] = strs[i] + "●"
                    all_shens.add(item)
                    all_shens_list.append(item)
                    
        for item in day_shens:
            for i in (0,1,3):
                if zhis[i] in day_shens[item][zhis.day]:     
                    strs[i] = item if not strs[i] else strs[i] + chr(12288) + item    
                    all_shens.add(item)
                    all_shens_list.append(item)
                    
        for item in g_shens:
            for i in range(4):
                if zhis[i] in g_shens[item][me]:    
                    strs[i] = item if not strs[i] else strs[i] + chr(12288) + item
                    all_shens.add(item)
                    all_shens_list.append(item)
        
        for seq in range(4):
            if strs[seq]:
                self.add_to_section(f"位置{seq+1}: {strs[seq]}")
                
        # 大运
        self.set_section("大运")
        self.add_to_section("大运: " + " ".join(dayuns))
        
        # 五行分数
        self.set_section("五行分数")
        self.add_to_section(f"五行分数: {scores}")
        self.add_to_section(f"八字强弱: {strong}, 通常>29为强，需要参考月份、坐支等")
        self.add_to_section(f"weak: {weak}")
        
        # 格局分析
        self.set_section("格局分析")
        
        me_lu = ten_deities[me].inverse['建']
        me_jue = ten_deities[me].inverse['绝']
        me_tai = ten_deities[me].inverse['胎']
        me_di = ten_deities[me].inverse['帝']
        shang = ten_deities[me].inverse['伤']
        yin = ten_deities[me].inverse['印']
        xiao = ten_deities[me].inverse['枭']
        cai = ten_deities[me].inverse['财']
        piancai = ten_deities[me].inverse['才']
        guan = ten_deities[me].inverse['官']
        sha = ten_deities[me].inverse['杀']
        jie = ten_deities[me].inverse['劫']
        shi = ten_deities[me].inverse['食']
        
        self.add_to_section(f"调候: {tiaohous['{}{}'.format(me, zhis[1])]}")
        self.add_to_section(f"金不换大运: {jinbuhuan['{}{}'.format(me, zhis[1])]}")
        self.add_to_section(f"金不换大运说明: {jins['{}'.format(me)]}")
        self.add_to_section(f"格局选用: {ges[ten_deities[me]['本']][zhis[1]]}")
        
        # 特定格局检查
        if len(set('寅申巳亥')&set(zhis)) == 0:
            self.add_to_section("缺四生: 一生不敢作为")
        if len(set('子午卯酉')&set(zhis)) == 0:
            self.add_to_section("缺四柱地支缺四正，一生避是非")
        if len(set('辰戌丑未')&set(zhis)) == 0:
            self.add_to_section("四柱地支缺四库，一生没有潜伏性凶灾。")
            
        # 其他特殊格局分析
        jus = []
        for item in zhi_hes:
            if set(item).issubset(set(zhis) | set(get_gong(zhis, gans))):
                self.add_to_section(f"三合局: {item}")
                jus.append(ju[ten_deities[me].inverse[zhi_hes[item]]])
                
        for item in zhi_huis:
            if set(item).issubset(set(zhis) | set(get_gong(zhis, gans))):
                self.add_to_section(f"三会局: {item}")
                jus.append(ju[ten_deities[me].inverse[zhi_huis[item]]])
        
        # 命宫
        minggong = Zhi[::-1][(Zhi.index(zhis[1]) + Zhi.index(zhis[3]) -6) % 12]
        self.add_to_section(f"命宫: {minggong} {minggongs[minggong]}")
        self.add_to_section(f"坐: {rizhus[me+zhis.day]}")
        
        # 天罗地网
        if '辰' in zhis and '巳' in zhis:
            self.add_to_section("地网: 地支辰巳。天罗: 戌亥。天罗地网全凶。")
            
        if '戌' in zhis and '亥' in zhis:
            self.add_to_section("天罗: 戌亥。地网: 地支辰巳。天罗地网全凶。")
        
        # 六亲分析
        self.set_section("六亲分析")
        liuqins = bidict({'才': '父亲', "财": '财' if options.n else '妻', "印": '母亲', "枭": '偏印' if options.n else '祖父',
                         "官": '丈夫' if options.n else '女儿', "杀": '情夫' if options.n else '儿子', "劫": '兄弟' if options.n else '姐妹', 
                         "比": '姐妹' if options.n else '兄弟', "食": '女儿' if options.n else '下属', "伤": '儿子' if options.n else '孙女'})
                         
        for item in Gan:
            self.add_to_section(f"{item}: {ten_deities[me][item]} {liuqins[ten_deities[me][item]]}- {ten_deities[item][zhis[0]]} {ten_deities[item][zhis[1]]} {ten_deities[item][zhis[2]]} {ten_deities[item][zhis[3]]}")
        
        # 穷通宝鉴
        if me+zhis.month in months:
            self.set_section("穷通宝鉴")
            self.add_to_section(months[me+zhis.month])
        
        # 三命通会
        sum_index = ''.join([me, '日', *zhus[3]])
        if sum_index in summarys:
            self.set_section("三命通会")
            self.add_to_section(summarys[sum_index])
            
        # 星宿
        self.set_section("星宿")
        self.add_to_section(f"星宿: {lunar.getXiu()}, {lunar.getXiuSong()}")
        
        # 建除
        seq = 12 - Zhi.index(zhis.month)
        self.add_to_section(f"建除: {jianchus[(Zhi.index(zhis.day) + seq)%12][0]}")
        
        # 添加大运和流年分析
        self.set_section("大运流年")
        
        for dayun in yun.getDaYun()[1:]:
            gan_ = dayun.getGanZhi()[0]
            zhi_ = dayun.getGanZhi()[1]
            fu = '*' if (gan_, zhi_) in zhus else " "
            zhi5_ = ''
            for gan in zhi5[zhi_]:
                zhi5_ = zhi5_ + "{}{}　".format(gan, ten_deities[me][gan]) 
            
            zhi__ = set() # 大运地支关系
            
            for item in zhis:
                for type_ in zhi_atts[zhi_]:
                    if item in zhi_atts[zhi_][type_]:
                        zhi__.add(type_ + ":" + item)
            zhi__ = '  '.join(zhi__)
            
            empty = chr(12288)
            if zhi_ in empties[zhus[2]]:
                empty = '空'        
            
            jia = ""
            if gan_ in gans:
                for i in range(4):
                    if gan_ == gans[i]:
                        if abs(Zhi.index(zhi_) - Zhi.index(zhis[i])) == 2:
                            jia = jia + "  --夹：" +  Zhi[( Zhi.index(zhi_) + Zhi.index(zhis[i]) )//2]
                        if abs( Zhi.index(zhi_) - Zhi.index(zhis[i]) ) == 10:
                            jia = jia + "  --夹：" +  Zhi[(Zhi.index(zhi_) + Zhi.index(zhis[i]))%12]
                    
            out = f"大运: {dayun.getStartAge()}岁 {dayun.getGanZhi()} "
            out += f"{nayins[(gan_, zhi_)]} {ten_deities[me][gan_]}:{gan_} {ten_deities[me][zhi_]}:{zhi_} "
            out += f"藏干: {zhi5_.strip()} {jia}"
            
            self.add_to_section(out)
            
            # 流年分析
            zhis2 = list(zhis) + [zhi_]
            gans2 = list(gans) + [gan_]
            
            for liunian in dayun.getLiuNian():
                gan2_ = liunian.getGanZhi()[0]
                zhi2_ = liunian.getGanZhi()[1]
                fu2 = '*' if (gan2_, zhi2_) in zhus else " "
                
                zhi6_ = ''
                for gan in zhi5[zhi2_]:
                    zhi6_ = zhi6_ + "{}{}　".format(gan, ten_deities[me][gan])        
                
                # 流年地支关系
                zhi__ = set()
                for item in zhis2:
                    for type_ in zhi_atts[zhi2_]:
                        if type_ == '破':
                            continue
                        if item in zhi_atts[zhi2_][type_]:
                            zhi__.add(type_ + ":" + item)
                zhi__ = '  '.join(zhi__)
                
                empty = chr(12288)
                if zhi2_ in empties[zhus[2]]:
                    empty = '空'
                    
                jia = ""
                if gan2_ in gans2:
                    for i in range(5):
                        if gan2_ == gans2[i]:
                            zhi1 = zhis2[i]
                            if abs(Zhi.index(zhi2_) - Zhi.index(zhis2[i])) == 2:
                                jia = jia + "  --夹：" +  Zhi[( Zhi.index(zhi2_) + Zhi.index(zhis2[i]) )//2]
                            if abs( Zhi.index(zhi2_) - Zhi.index(zhis2[i]) ) == 10:
                                jia = jia + "  --夹：" +  Zhi[(Zhi.index(zhi2_) + Zhi.index(zhis2[i]))%12]  

                            if (zhi1 + zhi2_ in gong_he) and (gong_he[zhi1 + zhi2_] not in zhis):
                                jia = jia + "  --拱：" + gong_he[zhi1 + zhi2_]
                
                out = f"流年: {liunian.getAge()}岁 {liunian.getYear()}年 {gan2_+zhi2_} "
                out += f"{nayins[(gan2_, zhi2_)]} {ten_deities[me][gan2_]}:{gan2_} {ten_deities[me][zhi2_]}:{zhi2_} "
                out += f"藏干: {zhi6_.strip()} {jia}"
                
                # 检测特殊组合
                all_zhis = set(zhis2) | {zhi2_}
                specials = []
                
                if set('戌亥辰巳').issubset(all_zhis):
                    specials.append("天罗地网：戌亥辰巳")
                if set('寅申巳亥').issubset(all_zhis) and len(set('寅申巳亥')&set(zhis)) == 2:
                    specials.append("四生：寅申巳亥")   
                if set('子午卯酉').issubset(all_zhis) and len(set('子午卯酉')&set(zhis)) == 2:
                    specials.append("四败：子午卯酉")  
                if set('辰戌丑未').issubset(all_zhis) and len(set('辰戌丑未')&set(zhis)) == 2:
                    specials.append("四库：辰戌丑未")
                
                if specials:
                    out += " " + " ".join(specials)
                
                self.add_to_section(out)
        
        return self.output_sections

def analyze_bazi(year, month, day, time, minute=0, gender=False, solar=False, run_month=False):
    """
    分析一个人的八字并返回JSON结果
    
    参数:
        year: 年份(整数或字符串)
        month: 月份(整数或字符串)
        day: 日期(整数或字符串)
        time: 小时(整数或字符串)
        minute: 分钟(整数或字符串)，默认为0
        gender: 女性为True，男性为False(布尔值)
        solar: 公历为True，农历为False(布尔值)
        run_month: 如果是闰月则为True(布尔值)
    
    返回:
        包含分析结果的JSON字符串
    """
    # 如果输入是字符串，则转换为整数
    year = int(year)
    month = int(month)
    day = int(day)
    time = int(time)
    minute = int(minute)
    
    analyzer = BaziAnalyzer()
    result = analyzer.analyze_bazi(year, month, day, time, minute, gender, solar, run_month)
    
    return json.dumps(result, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description='分析八字并输出JSON')
    parser.add_argument('year', help='年份')
    parser.add_argument('month', help='月份')
    parser.add_argument('day', help='日期')
    parser.add_argument('time', help='时间(24小时制)')
    parser.add_argument('-m', '--minute', type=int, default=0, help='分钟，默认为0')
    parser.add_argument('-b', action='store_true', default=False, help='直接输入八字')
    parser.add_argument('-g', action='store_true', default=False, help='是否采用公历')
    parser.add_argument('-r', action='store_true', default=False, help='是否为闰月，仅仅使用于农历')
    parser.add_argument('-n', action='store_true', default=False, help='是否为女，默认为男')
    
    args = parser.parse_args()
    
    if args.b:
        print("此版本不支持直接输入八字。")
        return
    
    result = analyze_bazi(args.year, args.month, args.day, args.time, args.minute,
                         gender=args.n, solar=args.g, run_month=args.r)
    
    print(result)

if __name__ == "__main__":
    main() 
