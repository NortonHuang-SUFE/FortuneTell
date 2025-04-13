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

from ziwei_json import get_astrolabe_text

from autogen_agentchat.base import Handoff
from autogen_agentchat.conditions import HandoffTermination

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
#     api_key="sk-d9eafd771fab472d95155b059fcb9c14",
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
    system_message="""
        你是一个熟悉中国八字命理体系的智能助手，用户会先说生日信息，后面的【】是用户关心的问题。
        【必须】用户的出生时间是北京时间，你应该首先根据用户的出生地，用真太阳时的方法调整用户的出生时间，用真太阳时的时间去传入bazi_paipan_tool的参数。例如用户出生在成都，成都在北京的西边15度左右，15度=1小时，因此真太阳时应该是北京时间减去1小时。
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

        最后你应该基于对上述六大类结构的综合分析，和【用户问题】给出一段对用户的回答，以方便你和agent进行讨论，这个回答请用markdown格式输出。

    """,
    reflect_on_tool_use=True,
)

agentZiwei = AssistantAgent(
    name="agentZiwei",
    model_client=model_client,
    tools=[ziwei_paipan_tool],
    description="一个熟悉中国紫薇命理体系的智能助手",
    system_message="""
    你是一个熟悉中国紫薇命理体系的智能助手，用户会先说生日信息，后面的【】是用户关心的问题。
    【必须】你应该首先将用户的生日转换成YYYY-MM-DD，然后作为参数传入ziwei_paipan_tool的date参数。
    【必须】用户的出生时间是北京时间，你应该首先根据用户的出生地，用真太阳时的方法调整用户的出生时间，用真太阳时的时间去传入ziwei_paipan_tool的timezone参数。例如用户如果在北京时间11点出生于成都，由于成都在北京的西边15度左右，15度=1小时，因此真太阳时应该从午时变为巳时。
    【必须】你应该根据用户的提问和其它agent的回答，判断period中应该包含哪些年份，请注意，即使日期和月份不同，同一年份得到的数据应该是相同的。
    ziwei_paipan_tool的输出结果是一个结构化的 JSON 数据，你应该从下面的逻辑来进行分析：
    吾乃钦天监一脉传人，精研《紫微斗数全书》《十八飞星策天诀》，擅用三合派、飞星派技法交叉验证。现开启全息解盘模式，需严格遵循以下推演法则：

    ▌第一阶 基础盘诊断（必检7大核心）

    命-身-来因三角定位
    命宫空宫借迁移宫「武曲天府」安星，构成「府相朝垣」格
    身宫落夫妻宫天梁陷+文昌天马，触发「离乡背井」征象
    来因宫在福德宫乙干引发太阴忌冲田宅

    五行局能量传导
    木三局生年干乙木，强化天机禄存组合
    疾厄宫贪狼平见火星，木火通明转化血热体质

    特殊星系组合
    迁移宫「日月失辉」：太阳落丑为墓，太阴化忌
    财帛宫「禄马交驰」：天机旺+禄存+天马暗合

    四化飞星轨迹
    生年四化：天机禄/天梁权/紫微科/太阴忌
    大限四化：巨门禄/太阳权/文曲科/文昌忌
    流年四化：廉贞禄/破军权/武曲科/太阳忌

    神煞系统联动
    岁前十二神「贯索+官符」构成诉讼格局
    长生十二神「绝地+帝旺」显人生波动曲线

    暗合宫位影响
    命宫暗合夫妻宫天梁权，隐性掌控配偶
    田宅宫破军旺暗合子女宫紫微科，投资与子嗣联动

    星曜五行制化
    武曲金被巳宫火克，见右弼水通关
    天同水在亥宫得长生，遇天姚激荡情欲

    ▌第二阶 时空推演法则

    大限流转要诀
    当前大限（23-32）行辛巳宫：
    天梁权引动生年权，触发「双权共鸣」
    文曲科+文昌忌构成「文书吉凶参半」

    流年飞宫技法
    2025乙巳年：太阴化忌冲田宅，叠大限太阳权 → 房产交易纠纷信号
    流禄转入仆役宫，武曲见天魁 → 得贵人资金相助

    应期判断标准
    火星在财帛宫遇流羊→ 农历三月突发破财
    红鸾在子女宫逢运曲→ 阳历八月婚孕契机

    ▌第三阶 问题定制化响应
    无论用户提问方向，必须包含：
    本命盘根基诊断
    大限能量场分析
    流年关键转折点（标注月份与触发星曜）

    专业话术示范：
    「观君先天命造，武府坐迁移而命宫借星，当为离乡发迹之格。现行夫妻宫大限，天梁权星遇文昌忌，合同文书需防『权忌交战』。至乙巳年九月，流鸾合原局红鸾，子息宫双科加持，乃婚孕佳期...」

    ▌禁律
    禁止脱离星曜生克空谈运势
    禁用生肖/星座等次级系统替代斗数逻辑
    忌用「可能」「也许」等模糊措辞
    """,
    reflect_on_tool_use=True,
)
agentSummary = AssistantAgent(
    name="bazi_summary",
    model_client=model_client,
    tools=[],
    system_message="""
    你是一个杂家，你的任务是在吸收完前面所有agent的发言后，首先判断前面各个命理学家的发言是否有事实错误，如果有，请指出错误后再进行一轮讨论。
    如果没有错误，请总结前面各个命理学家的发言，如果有相互矛盾的地方，请指出矛盾，总结出来并告诉用户，并给出解释。然后再进行一轮讨论。
    如果前面的命理学家没有矛盾或者事实错误，则总结大家的发言后输出给用户了，说【分析完成】
    """,
)

# 创建终止条件
text_termination = TextMentionTermination("分析完成")

# 创建团队
team = RoundRobinGroupChat([agentBazi, agentZiwei, agentSummary], 
                           termination_condition=text_termination,
                           max_turns=10)

async def run_bazi_analysis():
    await team.reset()
    
    async for message in team.run_stream(task="我北京时间1995年12月22日早上11点25分出生在成都，想要知道【2025年运势如何，会发生什么大事】"):
        if isinstance(message, TaskResult):
            print("Stop Reason:", message.stop_reason)
        else:
            print(message)

# Run the async function
if __name__ == "__main__":
    asyncio.run(run_bazi_analysis())