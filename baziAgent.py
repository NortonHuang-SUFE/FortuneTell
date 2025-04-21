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
from config import QWEN_MAX_CONFIG, DEEPSEEK_CONFIG


class BaziAnalysisTeam:
    """
    一个封装了八字和紫微斗数分析团队的类。
    该类初始化所有必要的代理、工具和团队本身。
    """
    
    def __init__(self):
        # 初始化模型客户端
        self.model_client_qwenMax = OpenAIChatCompletionClient(
            model=QWEN_MAX_CONFIG["model"],
            api_key=QWEN_MAX_CONFIG["api_key"],
            base_url=QWEN_MAX_CONFIG["base_url"],
            model_info=QWEN_MAX_CONFIG["model_info"],
            temperature=QWEN_MAX_CONFIG["temperature"],
            max_tokens=QWEN_MAX_CONFIG["max_tokens"]
        )

        self.model_client_deepseekR1 = OpenAIChatCompletionClient(
            model=DEEPSEEK_CONFIG["model"],
            api_key=DEEPSEEK_CONFIG["api_key"],
            base_url=DEEPSEEK_CONFIG["base_url"],
            model_info=DEEPSEEK_CONFIG["model_info"],
            temperature=DEEPSEEK_CONFIG["temperature"],
            max_tokens=DEEPSEEK_CONFIG["max_tokens"]
        )
        
        # 初始化工具
        self.bazi_paipan_tool = FunctionTool(self._bazi_paipan_tool, description="根据用户的生日信息，得到用户的八字相关的基础信息")
        self.ziwei_paipan_tool = FunctionTool(self._ziwei_paipan_tool, description="根据用户的生日信息，得到用户的紫微斗数相关的基础信息")
        
        # 初始化代理
        self.agentBazi = AssistantAgent(
            name="agentBazi",
            model_client=self.model_client_qwenMax,
            tools=[self.bazi_paipan_tool],
            description="一个熟悉中国八字命理体系的智能助手",
            system_message=AgentSystemMessage.get("baziAgent"),
            reflect_on_tool_use=True,
        )

        self.agentZiwei = AssistantAgent(
            name="agentZiwei",
            model_client=self.model_client_qwenMax,
            tools=[self.ziwei_paipan_tool],
            description="一个熟悉中国紫薇命理体系的智能助手",
            system_message=AgentSystemMessage.get("ziweiAgent"),
            reflect_on_tool_use=True,
        )

        self.agentSummary = AssistantAgent(
            name="summary",
            model_client=self.model_client_deepseekR1,
            system_message=AgentSystemMessage.get("summary"),
        )
        
        # 创建终止条件
        self.text_termination = TextMentionTermination("分析完成")
        
        # 创建团队
        self.team = RoundRobinGroupChat(
            [self.agentBazi, self.agentZiwei, self.agentSummary], 
            termination_condition=self.text_termination,
            max_turns=10
        )
    
    async def _bazi_paipan_tool(self, year: Annotated[int, "年份"], 
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
        result = json.dumps(analyzer.analyze_bazi(year, month, day, time, minute, gender, solar, run_month), ensure_ascii=False, indent=None)
        
        # 清理特殊字符
        # 替换全角空格为普通空格
        result = result.replace('\u3000', ' ')
        # 替换其他可能的特殊字符
        result = result.replace('\\n', ' ')
        result = result.replace('\\t', ' ')
        result = result.replace('\\r', ' ')
        # 移除多余的空格
        result = ' '.join(result.split())
        
        return result

    async def _ziwei_paipan_tool(self, date: Annotated[str, "日期"], 
                                timezone: Annotated[int, "一天中的哪个时辰，用中国古代计时法。出生时辰序号【0~12】，0:子；1:丑；2:寅；3:卯；4:辰；5:巳；6:午；7:未；8:申；9:酉；10:戌；11:亥；12:子"], 
                                gender: Annotated[str, "性别，男或女"], 
                                period: Annotated[list, "涉及的日期，格式为 ['YYYY-MM-DD', 'YYYY-MM-DD']"], 
                                is_solar: Annotated[bool, "是否为阳历数据"] = True) -> str:
        """
        date (str): 日期字符串，格式为 "YYYY-MM-DD"
        timezone (int): 一天中的哪个时辰，用中国古代计时法
        gender (str): 性别，男或女
        period (list): 涉及的日期，格式为 ["YYYY-MM-DD", "YYYY-MM-DD"]
        is_solar (bool): 是否为阳历数据，默认为 True
        base_url (str): API 的基础 URL，默认为 "http://localhost:3000"
        """
        return get_astrolabe_text(date, timezone, gender, period, is_solar=is_solar, base_url="http://localhost:3000")
    
    def get_team(self):
        """返回初始化好的团队"""
        return self.team


async def run_bazi_analysis(task):
    """使用给定的任务运行分析"""
    team_manager = BaziAnalysisTeam()
    team = team_manager.get_team()
    await team.reset()
    
    async for message in team.run_stream(task=task):
        if isinstance(message, TaskResult):
            print("停止原因:", message.stop_reason)
        else:
            print(message)


# 示例任务
task = "用户是北京时间1996年11月2日10:58【24小时制】出生在重庆永川的男生，今天是2025年4月15日，想要知道【我的直系领导什么时候能够被调走】"
    
# 运行异步函数
if __name__ == "__main__":
    asyncio.run(run_bazi_analysis(task))