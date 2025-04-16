import asyncio
import threading
import queue
import json
from flask import Flask, request, jsonify
from typing import Dict, Optional, List
import uuid

from baziAgent import run_bazi_analysis, TaskResult

app = Flask(__name__)

# 存储任务状态和消息列表的字典
tasks: Dict[str, Dict] = {}

# 线程锁，用于保护对 tasks 字典的访问
tasks_lock = threading.Lock()

def task_worker(task_id: str, task: str):
    """在单独的线程中运行异步任务"""
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
            message_list.append(str(message))
    
    # 运行任务
    try:
        loop.run_until_complete(run_bazi_analysis_with_queue(task, message_handler))
        with tasks_lock:
            tasks[task_id]["status"] = "completed"
    except Exception as e:
        with tasks_lock:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
    finally:
        loop.close()

async def run_bazi_analysis_with_queue(task: str, message_handler):
    """修改后的 run_bazi_analysis 函数，将消息发送到列表而不是打印"""
    from baziAgent import BaziAnalysisTeam
    
    team_manager = BaziAnalysisTeam()
    team = team_manager.get_team()
    await team.reset()
    
    async for message in team.run_stream(task=task):
        if isinstance(message, TaskResult):
            await message_handler(f"停止原因: {message.stop_reason}")
        else:
            await message_handler(message)

@app.route('/start-task', methods=['POST'])
def start_task():
    """启动一个新的分析任务"""
    data = request.json
    if not data or 'task' not in data:
        return jsonify({"error": "缺少任务描述"}), 400
    
    task = data['task']
    task_id = str(uuid.uuid4())
    
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

@app.route('/get-latest', methods=['GET'])
def get_latest():
    """获取任务的所有消息"""
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 