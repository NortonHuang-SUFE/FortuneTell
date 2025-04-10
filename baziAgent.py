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

async def bazi_master_tool(user_input: Annotated[str, "用户问题"],
                           year: Annotated[int, "年份"], 
                           month: Annotated[int, "月份"], 
                           day: Annotated[int, "日期"], 
                           time: Annotated[int, "时间（24小时制）"], 
                           minute: Annotated[int, "分钟"] = 0, 
                           gender: Annotated[bool, "是否为女性"] = False, 
                           solar: Annotated[bool, "公历"] = False, 
                           run_month: Annotated[bool, "是否为闰月"] = False) -> str:
    """根据用户输入的阳历或阴历的出生年份、月份、日期、时间，并结合用户是否为女性，得到用户的八字相关数据
    """
    analyzer = BaziAnalyzer()
    result = analyzer.bazi_output(user_input, year, month, day, time, minute, gender, solar, run_month)
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
bazi_master_tool = FunctionTool(bazi_master_tool, description="根据用户的生日信息与问题，分析用户的八字，如果提及了出生地，请用真太阳时的方法调整用户的出生时间")

agentBazi = AssistantAgent(
    name="agentBazi",
    model_client=model_client,
    tools=[bazi_master_tool],
    system_message="""
    你是一个八字命理师，用户会先说生日信息，后面的【】是用户关心的问题。
    你应该首先解析用户的生日，如果用户提了他出生在哪里，请用真太阳时的方法调整用户的出生时间，用真太阳时的时间去传入bazi_master_tool的day和time。
    然后你应该解析用户的问题，然后结合真太阳时去调用bazi_master_tool。
    如果你应该去检查工具输出中有没有事实错误，如果有可以再次调用工具，重新得到答案。
    如果你认为没有问题，请尽量详细的描述出八字分析的结果用于回答用户问题
    """,
    reflect_on_tool_use=True,
)

agentSummary = AssistantAgent(
    name="bazi_summary",
    model_client=model_client,
    tools=[],
    system_message="""
    你是一个杂家，你的任务是在吸收完前面所有agent的发言后，首先判断前面各个命理学家的发言是否有事实错误，如果有，请指出错误，并且不要说【分析完成】
    如果没有错误，请总结前面各个命理学家的发言，如果有相互矛盾的地方，请指出矛盾，总结出来并告诉用户，并给出解释。
    如果你认为可以输出给用户了，说【分析完成】
    """,
)

# 创建终止条件
text_termination = TextMentionTermination("分析完成")

# 创建团队
team = RoundRobinGroupChat([agentBazi, agentSummary], 
                           termination_condition=text_termination,
                           max_turns=10)

async def run_bazi_analysis():
    await team.reset()
    
    async for message in team.run_stream(task="我1995年12月22日早上10点25分出生在北京，想要知道【2025年运势如何，会发生什么大事】"):
        if isinstance(message, TaskResult):
            print("Stop Reason:", message.stop_reason)
        else:
            print(message)

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_bazi_analysis())