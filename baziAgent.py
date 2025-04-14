import asyncio
from typing_extensions import Annotated
import json

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
from autogen_agentchat.base import Handoff
from autogen_agentchat.conditions import HandoffTermination

from utils.bazi_json import BaziAnalyzer
from utils.ziwei_json import get_astrolabe_text
from utils.prompt import AgentSystemMessage


### 八字分析工具
async def bazi_paipan_tool(year: Annotated[int, "年份"], 
                           month: Annotated[int, "月份"], 
                           day: Annotated[int, "日期"], 
                           time: Annotated[int, "时间（24小时制）"], 
                           minute: Annotated[int, "分钟"] = 0, 
                           gender: Annotated[bool, "是否为女性"] = False, 
                           solar: Annotated[bool, "公历"] = False, 
                           run_month: Annotated[bool, "是否为闰月"] = False) -> str:
    """
    根据用户输入的阳历或阴历的出生年份、月份、日期、时间，并结合用户是否为女性，得到用户的八字相关数据
    """
    analyzer = BaziAnalyzer()
    result = analyzer.analyze_bazi(year, month, day, time, minute, gender, solar, run_month)
    return result

# async def bazi_analysis_tool(user_input: Annotated[str, "用户问题"],
#                            bazi_json: Annotated[str, "用户从bazi_paipan_tool得到的八字基础数据"]) -> str:
#     """
#     根据用户的问题和用户的八字，给出分析结果
#     """
#     analyzer = BaziAnalyzer()
#     result = analyzer.bazi_output(user_input, bazi_json)
#     return result

### 紫微斗数分析工具
async def ziwei_paipan_tool(date: Annotated[str, "日期"], 
                            timezone: Annotated[int, "一天中的哪个时辰，用中国古代计时法。出生时辰序号【0~12】，0:子；1:丑；2:寅；3:卯；4:辰；5:巳；6:午；7:未；8:申；9:酉；10:戌；11:亥；12:子"], 
                            gender: Annotated[str, "性别，男或女"], 
                            period: Annotated[list, "涉及的日期，格式为 ['YYYY-MM-DD', 'YYYY-MM-DD']"], 
                            is_solar: Annotated[bool, "是否为阳历数据"] = True, 
                            base_url: Annotated[str, "API 的基础 URL"] = "http://localhost:3000") -> str:
    """
    date (str): 日期字符串，格式为 "YYYY-MM-DD"
    timezone (int): 一天中的哪个时辰，用中国古代计时法
    gender (str): 性别，男或女
    period (list): 涉及的日期，格式为 ["YYYY-MM-DD", "YYYY-MM-DD"]
    is_solar (bool): 是否为阳历数据，默认为 True
    base_url (str): API 的基础 URL，默认为 "http://localhost:3000"
    """
    return get_astrolabe_text(date, timezone, gender, period, is_solar=is_solar, base_url=base_url)

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
    temperature=0.3,
    max_tokens=8192
)

# 创建一个使用deepseek-chat模型的client
# model_client = OpenAIChatCompletionClient(
#     model="deepseek-chat",
#     api_key="",
#     base_url="https://api.deepseek.com",
#     model_info={
#         "vision": False,
#         "function_calling": True,
#         "json_output": True,
#         "family": ModelFamily.UNKNOWN,
#         "structured_output": True,
#     },
#     temperature=0.5,
#     max_tokens=8192
# )

# 创建函数工具
# web_search_tool = FunctionTool(web_search, description="在网络上查找信息")
# bazi_analysis_tool = FunctionTool(analyze_bazi_tool, description="根据用户输入，得到用户的四柱八字、大运、流年，这是后面对八字进行分析的基础")
# bazi_interpret_tool = FunctionTool(interpret_bazi_tool, description="根据用户八字、大运、流年，回答用户的问题")
bazi_paipan_tool = FunctionTool(bazi_paipan_tool, description="根据用户的生日信息，得到用户的八字相关的基础信息")
ziwei_paipan_tool = FunctionTool(ziwei_paipan_tool, description="根据用户的生日信息，得到用户的紫微斗数相关的基础信息")



# agentBazi = AssistantAgent(
#     name="agentBazi",
#     model_client=model_client,
#     tools=[bazi_paipan_tool, bazi_analysis_tool],
#     system_message="""
#     你是一个八字命理师，用户会先说生日信息，后面的【】是用户关心的问题。
#     【必须】用户的出生时间默认是北京时间，你应该首先根据用户的出生地，用真太阳时的方法调整用户的出生时间，用真太阳时的时间去传入bazi_paipan_tool的参数。
#     【必须】然后你应该将bazi_paipan_tool的输出【原封不动】作为bazi_analysis_tool的参数【bazi_json】，然后结合用户的关心的问题作为【user_input】。
#     最后你将从bazi_analysis_tool中得到分析结果。分析结果中有这个用户的四柱和分析，如果有事实错误，请你重新调整上述参数，然后重新调用bazi_paipan_tool和bazi_analysis_tool。
#     如果你认为没有问题，请尽量详细的描述出八字分析的结果用于回答用户问题。
#     如果你没有即调用bazi_paipan_tool，也没有调用bazi_analysis_tool，请不要结束你的分析，请继续分析。
#     """,
#     reflect_on_tool_use=True,
# )

agentBazi = AssistantAgent(
    name="agentBazi",
    model_client=model_client,
    tools=[bazi_paipan_tool],
    description="一个熟悉中国八字命理体系的智能助手",
    system_message=AgentSystemMessage.get("baziAgent"),
    reflect_on_tool_use=True,
)

agentZiwei = AssistantAgent(
    name="agentZiwei",
    model_client=model_client,
    tools=[ziwei_paipan_tool],
    description="一个熟悉中国紫薇命理体系的智能助手",
    system_message=AgentSystemMessage.get("ziweiAgent"),
    reflect_on_tool_use=True,
)
agentSummary = AssistantAgent(
    name="summary",
    model_client=model_client,
    tools=[],
    system_message=AgentSystemMessage.get("summary"),
)

# 创建终止条件
text_termination = TextMentionTermination("分析完成")

# 创建团队
team = RoundRobinGroupChat([agentBazi, agentZiwei, agentSummary], 
                           termination_condition=text_termination,
                           max_turns=10)

async def run_bazi_analysis():
    await team.reset()
    
    async for message in team.run_stream(task="我北京时间1995年12月22日早上11点25分出生在成都，想要知道【我的抑郁症2025年会好吗】"):
        if isinstance(message, TaskResult):
            print("Stop Reason:", message.stop_reason)
        else:
            print(message)

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_bazi_analysis())