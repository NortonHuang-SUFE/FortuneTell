#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 测试bazi_output方法的脚本

import json
from bazi_json import bazi_output

def test_bazi_output():
    """
    测试bazi_output方法的各种情况
    """
    print("开始测试bazi_output方法...")
    
    # 测试用例1: 公历日期，男性
    print("\n测试用例1: 公历日期，男性")
    try:
        result = bazi_output(1990, 1, 1, 12, 0, gender=False, solar=True, run_month=-1, 
                            user_question="我的事业运势如何？")
        print("结果:")
        print(json.dumps(json.loads(result), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {str(e)}")
    
    # 测试用例2: 农历日期，女性
    print("\n测试用例2: 农历日期，女性")
    try:
        result = bazi_output(1990, 1, 1, 12, 0, gender=True, solar=False, run_month=-1, 
                            user_question="我的婚姻运势如何？")
        print("结果:")
        print(json.dumps(json.loads(result), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {str(e)}")
    
    # 测试用例3: 农历闰月
    print("\n测试用例3: 农历闰月")
    try:
        result = bazi_output(1990, 6, 1, 12, 0, gender=False, solar=False, run_month=-1, 
                            user_question="我的财运如何？")
        print("结果:")
        print(json.dumps(json.loads(result), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {str(e)}")
    
    # 测试用例4: 简单八字分析，不包含用户问题
    print("\n测试用例4: 简单八字分析，不包含用户问题")
    try:
        result = bazi_output(1990, 1, 1, 12, 0, gender=False, solar=True, run_month=-1, 
                            user_question="")
        print("结果:")
        print(json.dumps(json.loads(result), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"错误: {str(e)}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test_bazi_output() 