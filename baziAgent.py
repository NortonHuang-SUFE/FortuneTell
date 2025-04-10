import asyncio
from autogen_core.tools import FunctionTool
from autogen_core import CancellationToken
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.messages import StructuredMessage, TextMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.base import TaskResult
import json

from bazi_json import BaziAnalyzer
from typing_extensions import Annotated



from autogen_agentchat.base import Handoff
from autogen_agentchat.conditions import HandoffTermination

# # 使用BaziAnalyzer定义一个八字分析工具
# async def analyze_bazi_tool(user_input: str) -> str:
#     """分析用户的八字（中国星相学）信息"""
#     analyzer = BaziAnalyzer()
#     result = analyzer.analyze_bazi(user_input, verbose=False, stream_output=False)
#     return json.dumps(result, ensure_ascii=False)

# # 使用BaziAnalyzer定义一个八字解读工具
# async def interpret_bazi_tool(user_input: str) -> str:
#     """解读用户的八字信息"""
#     analyzer = BaziAnalyzer()
#     result = analyzer.interpret_bazi(user_input, verbose=False, stream_output=False)
#     return json.dumps(result, ensure_ascii=False)

async def bazi_master_tool(year: Annotated[int, "年份"], 
                           month: Annotated[int, "月份"], 
                           day: Annotated[int, "日期"], 
                           time: Annotated[int, "时间"], 
                           minute: Annotated[int, "分钟"] = 0, 
                           gender: Annotated[bool, "是否为女性"] = False, 
                           solar: Annotated[bool, "公历"] = False, 
                           run_month: Annotated[bool, "是否为闰月"] = False) -> str:
    """根据用户输入的阳历或阴历的出生年份、月份、日期、时间，并结合用户是否为女性，得到用户的八字相关数据
    """
    analyzer = BaziAnalyzer()
    result = analyzer.analyze_bazi(year, month, day, time, minute, gender, solar, run_month)
    return result

# 创建一个使用qwen-max模型的client
model_client = OpenAIChatCompletionClient(
    model="qwen-max",
    api_key="sk-c6adb72453d441ef974b99056d2e7e92",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model_info={
        "vision": False,
        "function_calling": True,
        "json_output": True,
        "family": ModelFamily.UNKNOWN,
        "structured_output": True,
    },
)

# 创建函数工具
# web_search_tool = FunctionTool(web_search, description="在网络上查找信息")
# bazi_analysis_tool = FunctionTool(analyze_bazi_tool, description="根据用户输入，得到用户的四柱八字、大运、流年，这是后面对八字进行分析的基础")
# bazi_interpret_tool = FunctionTool(interpret_bazi_tool, description="根据用户八字、大运、流年，回答用户的问题")
bazi_master_tool = FunctionTool(bazi_master_tool, description="根据用户生日信息，得到用户的四柱八字、大运、流年，这是后面对八字进行分析的基础")

agentPaipan = AssistantAgent(
    name="bazi_paipan",
    model_client=model_client,
    tools=[bazi_master_tool],
    handoffs=[Handoff(target="user", message="Transfer to user.")],
    system_message="""
    你是一个八字排盘师，根据用户输入的信息，调用工具对用户进行排盘。
    首先，你需要分析用户的问题是否涵盖了出生的年份、月份、日期、时间，其中时间需要是24小时制。
    如果用户的问题中没有涵盖这些信息，请把任务转移给用户"
    如果用户的问题中涵盖了这些信息，请调用工具，并把调用工具后的json进行输出，最后回复用户："排盘完成"
    """,
)

# 创建用户代理
user_proxy = UserProxyAgent("user", input_func=input)  # 使用input()从控制台获取用户输入

# 创建终止条件
handoff_termination = HandoffTermination(target="user")
text_termination = TextMentionTermination("排盘完成")

# 创建团队
team = RoundRobinGroupChat([agentPaipan, user_proxy], 
                           termination_condition=handoff_termination | text_termination)

async def run_analysis():
    print("=== 八字分析系统 ===")
    print("请输入您的问题，输入'exit'退出系统。")
    
    while True:
        user_input = input("您: ")
        if user_input.lower() == 'exit':
            break
            
        await team.reset() 
        async for message in team.run_stream(task=user_input):
            if isinstance(message, TaskResult):
                print("Stop Reason:", message.stop_reason)
            else:
                print(message)
        
        print("\n-----------------------------------------")
    
    await model_client.close()
    print("系统已退出，感谢使用！")

if __name__ == "__main__":
    asyncio.run(run_analysis())