#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 简单的八字测试脚本

import json
from bazi_json import BaziAnalyzer

def main():
    """
    测试bazi_output方法
    """
    print("测试八字分析...")
    
    # 测试用例: 公历日期，男性
    try:
        bazi_analyzer = BaziAnalyzer()
        result = bazi_analyzer.bazi_output("我的事业运势如何？", 1990, 1, 1, 12, 0, gender=False, solar=True, run_month=-1)
        print("结果:")
        print(json.dumps(json.loads(result), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {str(e)}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main() 