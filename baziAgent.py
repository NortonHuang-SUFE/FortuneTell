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

async def bazi_analysis_tool(user_input: Annotated[str, "用户问题"],
                           bazi_json: Annotated[str, "用户从bazi_paipan_tool得到的八字基础数据"]) -> str:
    """
    根据用户的问题和用户的八字，给出分析结果
    """
    analyzer = BaziAnalyzer()
    result = analyzer.bazi_output(user_input, bazi_json)
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
bazi_paipan_tool = FunctionTool(bazi_paipan_tool, description="根据用户的生日信息，得到用户的八字相关的基础信息")
bazi_analysis_tool = FunctionTool(bazi_analysis_tool, description="根据用户的基础八字和用户的问题，分析并回答用户的问题")



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
    system_message="""
        你是一个悉中国八字命理体系的智能助手，用户会先说生日信息，后面的【】是用户关心的问题。
        【必须】用户的出生时间默认是北京时间，你应该首先根据用户的出生地，用真太阳时的方法调整用户的出生时间，用真太阳时的时间去传入bazi_paipan_tool的参数。
        bazi_paipan_tool的输出结果是一个结构化的 JSON 数据，该数据是基于用户的出生信息自动生成的命理分析报告，包含以下六大类结构：

            1. 命盘基础信息（Basic Info）：四柱、天干地支、纳音、藏干、星宿等。
               - 字段：基本信息、四柱、年月日时、天干、地支、地支藏干、纳音和关系、星宿

            2. 五行与格局分析（Five Elements & Structure）：五行得分、用神喜忌、命格类型等。
               - 字段：五行分数、五行根、格局分析

            3. 十神与六亲分析（Ten Spirits & Family Relationship）：十神分布及与六亲的对应分析。
               - 字段：六亲分析、天干（十神）、地支藏干（十神）

            4. 神煞与地支作用（Auspicious/Unlucky Stars & Interactions）：命盘中的吉凶神煞、地支关系。
               - 字段：神煞、地支关系、地支次要关系

            5. 大运与流年走势（Luck Cycles & Annual Trends）：十年一大运，每年一流年，分析人生运势节奏。
               - 字段：大运、大运流年

            6. 古籍命理参考（Classical Text Reference）：引用《穷通宝鉴》《三命通会》等古籍内容用于命理解读。
               - 字段：穷通宝鉴、三命通会

        你应基于用户问题的语义，定位 JSON 中对应字段，尽可能用全信息，进行合理解释或预测。可引用原文，但需通俗解释。允许综合多字段信息形成判断。

        最后你应该基于对上述六大类结构的综合分析，和【用户问题】给出一段对用户的回答，以方便你和agent进行讨论。

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
    
    async for message in team.run_stream(task="我1995年12月22日早上10点25分出生在成都，想要知道【2025年运势如何，会发生什么大事】"):
        if isinstance(message, TaskResult):
            print("Stop Reason:", message.stop_reason)
        else:
            print(message)

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_bazi_analysis())