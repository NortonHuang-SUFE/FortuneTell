import asyncio
from typing_extensions import Annotated
import json
from typing import Literal, Dict, Any
from pydantic import BaseModel
import logging
import codecs
import time
from datetime import datetime
import re

from autogen_core.tools import FunctionTool
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.models import ModelFamily
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.base import TaskResult
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import StructuredMessage

from utils.bazi_json import BaziAnalyzer
from utils.ziwei_json import get_astrolabe_text
from utils.prompt import AgentSystemMessage, ToolDescription
from config import QWEN_MAX_CONFIG, DEEPSEEK_CONFIG, ZHIPU_CONFIG, QWEN3_CONFIG

# 配置日志，同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_messages.log', encoding='utf-8'),
    ]
)

class MessageHandler:
    """消息处理器，根据规范处理不同类型的消息"""
    
    @staticmethod
    def handle_message(message: Dict[str, Any]) -> None:
        """根据消息类型处理消息，并进行相应的日志记录和显示"""
        try:
            # 记录到日志
            logging.info(f"收到消息: {str(message)}")

            message_type = message.get("type") if isinstance(message, dict) else message.type

            # 只处理特定类型的消息
            if message.source == "agentBazi":
                if message_type not in ["ToolCallRequestEvent", "TextMessage","ToolCallExecutionEvent"]:
                    return
                
                if message_type == "ToolCallRequestEvent":
                    print(f"{{ type: {message_type}, source: {message.source}, message: {{ params: {message.content[0].arguments} }} }}")
                elif message_type == "ToolCallExecutionEvent":
                    # 提取关键信息
                    content = message.content[0].content
                    try:
                        bazi_data = json.loads(content)
                        extracted_data = {
                            "性别": next((item.split(": ")[1] for item in bazi_data["基本信息"] if "性别" in item), ""),
                            "真太阳时": next((item.split(": ")[1] for item in bazi_data["基本信息"] if "公历" in item), ""),
                            "命宫": next((item.split(": ")[1] for item in bazi_data["基本信息"] if "命宫" in item), ""),
                            "胎元": next((item.split(": ")[1] for item in bazi_data["基本信息"] if "胎元" in item), ""),
                            "四柱": next((item for item in bazi_data["四柱"] if "四柱：" in item), "").replace("四柱：", ""),
                            "五行分数": next((item for item in bazi_data["五行分数"] if "五行分数" in item), "").replace("五行分数: ", ""),
                            "五行总结": next((item for item in bazi_data["五行分数"] if "八字强弱" in item), "").replace("八字强弱: ", ""),
                            "格局分析": {
                                "调候": next((item for item in bazi_data["格局分析"] if "调候" in item), "").replace("调候: ", ""),
                                "格局选用": next((item for item in bazi_data["格局分析"] if "格局选用" in item), "").replace("格局选用: ", ""),
                                "命宫分析": next((item for item in bazi_data["格局分析"] if "命宫:" in item), "").replace("命宫: ", ""),
                                "坐支分析": next((item for item in bazi_data["格局分析"] if "坐:" in item), "").replace("坐: ", "")
                            }
                        }
                        print(f"{{ type: {message_type}, source: {message.source}, message: {json.dumps(extracted_data, ensure_ascii=False)} }}")
                    except json.JSONDecodeError:
                        print("你需要的json数据")
                elif message_type == "TextMessage":
                    content = message.content
                    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if match:
                        print(f"{{ type: {message_type}, source: {message.source}, message: {match.group(1)} }}")
                    else:
                        print(f"{{ type: {message_type}, source: {message.source}, message: {content} }}")

            elif message.source == "agentZiwei":
                if message_type not in ["ToolCallRequestEvent", "TextMessage"]:
                    return
                if message_type == "ToolCallRequestEvent":
                    print(f"{{ type: {message_type}, source: {message.source}, message: {{ params: {message.content[0].arguments} }} }}")
                elif message_type == "TextMessage":
                    content = message.content
                    match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if match:
                        print(f"{{ type: {message_type}, source: {message.source}, message: {match.group(1)} }}")
                    else:
                        print(f"{{ type: {message_type}, source: {message.source}, message: {content} }}")
            elif message.source == "summary":
                if message_type not in ["TextMessage"]:
                    return
                if message_type == "TextMessage":
                    content = message.content
                    print(content)
        except Exception as e:
            logging.error(f"处理消息时出错: {str(e)}")

class BaziAnalysisTeam:
    """
    一个封装了八字和紫微斗数分析团队的类。
    该类初始化所有必要的代理、工具和团队本身。
    """
    
    def __init__(self):
        try:
            logging.info("开始初始化模型客户端...")
            
            # 初始化模型客户端
            self.model_client_qwenMax = OpenAIChatCompletionClient(
                model=QWEN_MAX_CONFIG["model"],
                api_key=QWEN_MAX_CONFIG["api_key"],
                base_url=QWEN_MAX_CONFIG["base_url"],
                model_info=QWEN_MAX_CONFIG["model_info"],
                temperature=QWEN_MAX_CONFIG["temperature"],
                max_tokens=QWEN_MAX_CONFIG["max_tokens"]
            )
            logging.info("QWEN模型客户端初始化成功")

            self.model_client_deepseekR1 = OpenAIChatCompletionClient(
                model=DEEPSEEK_CONFIG["model"],
                api_key=DEEPSEEK_CONFIG["api_key"],
                base_url=DEEPSEEK_CONFIG["base_url"],
                model_info=DEEPSEEK_CONFIG["model_info"],
                temperature=DEEPSEEK_CONFIG["temperature"],
                max_tokens=DEEPSEEK_CONFIG["max_tokens"]
            )
            logging.info("Deepseek模型客户端初始化成功")

            self.model_client_glmZ1Airx = OpenAIChatCompletionClient(
                model=ZHIPU_CONFIG["model"],
                api_key=ZHIPU_CONFIG["api_key"],
                base_url=ZHIPU_CONFIG["base_url"],
                model_info=ZHIPU_CONFIG["model_info"],
                temperature=ZHIPU_CONFIG["temperature"],
                max_tokens=ZHIPU_CONFIG["max_tokens"]
            )
            logging.info("ZHIPU模型客户端初始化成功")
            
            # 初始化工具
            logging.info("开始初始化工具...")
            self.bazi_paipan_tool = FunctionTool(self._bazi_paipan_tool, description=ToolDescription.get("bazi_paipan_tool"))
            self.ziwei_paipan_tool = FunctionTool(self._ziwei_paipan_tool, description=ToolDescription.get("ziwei_paipan_tool"))
            logging.info("工具初始化成功")
            
            # 初始化代理
            logging.info("开始初始化代理...")
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
                model_client=self.model_client_glmZ1Airx,
                system_message=AgentSystemMessage.get("summary"),
            )
            logging.info("代理初始化成功")
            
            # 创建终止条件
            self.text_termination = TextMentionTermination("分析完成")
            
            # 创建团队
            self.team = RoundRobinGroupChat(
                [self.agentBazi, self.agentZiwei, self.agentSummary], 
                termination_condition=self.text_termination,
                max_turns=10,
            )
            logging.info("团队初始化完成")
            
        except Exception as e:
            logging.error(f"初始化BaziAnalysisTeam时出错: {str(e)}")
            raise
    
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
        try:
            analyzer = BaziAnalyzer()
            result = json.dumps(analyzer.analyze_bazi(year, month, day, time, minute, gender, solar, run_month), ensure_ascii=False, indent=None)
            
            # 清理特殊字符
            result = result.replace('\u3000', ' ')
            result = result.replace('\\n', ' ')
            result = result.replace('\\t', ' ')
            result = result.replace('\\r', ' ')
            result = ' '.join(result.split())
            
            return result
        except Exception as e:
            logging.error(f"八字排盘工具执行出错: {str(e)}")
            return f"八字排盘出错: {str(e)}"

    async def _ziwei_paipan_tool(self, date: Annotated[str, "日期，格式为YYYY-MM-DD"], 
                                hour: Annotated[int, "出生时间（24小时制）"], 
                                gender: Annotated[str, "性别，男或女"], 
                                period: Annotated[list, "涉及的日期，格式为 ['YYYY-MM-DD', 'YYYY-MM-DD']"]) -> str:
        """
        根据用户输入的出生日期、时间和性别，获取紫微斗数命盘信息
        """
        try:
            return get_astrolabe_text(date, hour, gender, period, is_solar=True, base_url="http://localhost:3000")
        except Exception as e:
            logging.error(f"紫微斗数排盘工具执行出错: {str(e)}")
            return f"紫微斗数排盘出错: {str(e)}"
    
    def get_team(self):
        """返回初始化好的团队"""
        return self.team


async def run_bazi_analysis(task):
    """使用给定的任务运行分析"""
    try:
        team_manager = BaziAnalysisTeam()
        team = team_manager.get_team()
        await team.reset()
        
        async for message in team.run_stream(task=task):
            MessageHandler.handle_message(message)
    except Exception as e:
        logging.error(f"运行八字分析时出错: {str(e)}")
        raise

# 示例任务
task = "用户是北京时间1996年1月1日0:31【24小时制】出生在重庆永川的男生，今天是2025年4月15日，想要知道【我的直系领导什么时候能够被调走】"
    
# 运行异步函数
if __name__ == "__main__":
    try:
        asyncio.run(run_bazi_analysis(task))
    except Exception as e:
        logging.error(f"主程序运行出错: {str(e)}")