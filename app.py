import asyncio
import threading
import queue
import json
from flask import Flask, request, jsonify
from typing import Dict, Optional, List
import uuid
import logging
import socket
import io
from contextlib import redirect_stdout

from baziAgent import run_bazi_analysis, TaskResult, MessageHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_messages.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# 存储任务状态和消息列表的字典
tasks: Dict[str, Dict] = {}

# 线程锁，用于保护对 tasks 字典的访问
tasks_lock = threading.Lock()

def task_worker(task_id: str, task: str):
    """在单独的线程中运行异步任务"""
    try:
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 创建消息列表
        message_list = []
        
        # 更新任务状态
        with tasks_lock:
            tasks[task_id]["status"] = "running"
            tasks[task_id]["message_list"] = message_list
        
        # 定义消息处理函数
        async def message_handler(message):
            with tasks_lock:
                # 使用StringIO捕获print输出
                output = io.StringIO()
                with redirect_stdout(output):
                    MessageHandler.handle_message(message)
                captured_output = output.getvalue()
                if captured_output:
                    message_list.append(captured_output.strip())
        
        # 运行任务
        try:
            loop.run_until_complete(run_bazi_analysis_with_queue(task, message_handler))
            with tasks_lock:
                tasks[task_id]["status"] = "completed"
        except Exception as e:
            logging.error(f"任务执行出错: {str(e)}")
            with tasks_lock:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["error"] = str(e)
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"任务工作线程出错: {str(e)}")
        with tasks_lock:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)

async def run_bazi_analysis_with_queue(task: str, message_handler):
    """修改后的 run_bazi_analysis 函数，将消息发送到列表而不是打印"""
    try:
        from baziAgent import BaziAnalysisTeam
        
        team_manager = BaziAnalysisTeam()
        team = team_manager.get_team()
        await team.reset()
        
        async for message in team.run_stream(task=task):
            if isinstance(message, TaskResult):
                await message_handler(f"停止原因: {message.stop_reason}")
            else:
                await message_handler(message)
    except Exception as e:
        logging.error(f"运行八字分析时出错: {str(e)}")
        raise

@app.route('/start-task', methods=['POST'])
def start_task():
    """启动一个新的分析任务"""
    try:
        data = request.json
        if not data or 'task' not in data:
            return jsonify({"error": "缺少任务描述"}), 400
        
        task = data['task']
        task_id = str(uuid.uuid4())
        
        logging.info(f"开始新任务: {task_id}")
        
        # 初始化任务状态
        with tasks_lock:
            tasks[task_id] = {
                "status": "pending",
                "task": task,
                "message_list": []
            }
        
        # 在新线程中启动任务
        thread = threading.Thread(target=task_worker, args=(task_id, task))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "task_id": task_id,
            "status": "started",
            "message": "任务已启动"
        })
    except Exception as e:
        logging.error(f"启动任务时出错: {str(e)}")
        return jsonify({"error": f"启动任务失败: {str(e)}"}), 500

@app.route('/get-latest', methods=['GET'])
def get_latest():
    """获取任务的所有消息"""
    try:
        task_id = request.args.get('task_id')
        if not task_id:
            return jsonify({"error": "缺少任务ID"}), 400
        
        with tasks_lock:
            if task_id not in tasks:
                return jsonify({"error": "任务不存在"}), 404
            
            task_info = tasks[task_id]
            status = task_info["status"]
            
            # 如果任务已完成或失败，返回最终状态
            if status in ["completed", "failed"]:
                return jsonify({
                    "status": status,
                    "messages": task_info.get("message_list", []),
                    "message": "任务已完成" if status == "completed" else f"任务失败: {task_info.get('error', '未知错误')}"
                })
            
            # 获取消息列表
            message_list = task_info.get("message_list", [])
            if not message_list:
                return jsonify({"status": "running", "messages": [], "message": "请等待"})
            
            return jsonify({
                "status": "running",
                "messages": message_list,
                "message": "有新的消息"
            })
    except Exception as e:
        logging.error(f"获取任务状态时出错: {str(e)}")
        return jsonify({"error": f"获取任务状态失败: {str(e)}"}), 500

if __name__ == '__main__':
    try:
        logging.info("正在启动服务器...")
        print("\n" + "="*50)
        print("FortuneTell 服务器正在启动...")
        print("="*50 + "\n")
        
        # 检查端口是否被占用
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', 5001))
            sock.close()
        except socket.error:
            logging.error("端口 5001 已被占用，请检查是否有其他程序正在运行")
            print("错误：端口 5001 已被占用，请检查是否有其他程序正在运行")
            exit(1)
            
        print("服务器配置信息：")
        print(f"- 主机: 0.0.0.0")
        print(f"- 端口: 5001")
        print(f"- 调试模式: 关闭")
        print(f"- 多线程: 启用")
        print(f"- 进程数: 1")
        print("\n" + "="*50)
        print("服务器已成功启动！")
        print("您可以通过以下方式访问服务器：")
        print("1. 本地访问: http://localhost:5001")
        print("2. 网络访问: http://<您的IP地址>:5001")
        print("="*50 + "\n")
        
        app.run(debug=False, host='0.0.0.0', port=5001, threaded=True, processes=1)
    except Exception as e:
        logging.error(f"服务器启动失败: {str(e)}")
        print(f"\n错误：服务器启动失败: {str(e)}") 