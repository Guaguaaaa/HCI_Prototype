from flask import Flask, request, jsonify, Response, send_from_directory, render_template_string
from flask_cors import CORS
import os
import json
import time
from datetime import datetime
import csv

from backend import llm_service
from backend import data_manager
from backend.config import VERSION_MAP, EXPERIMENT_STEPS, INSTRUCTION_VERSION_MAP
from backend.localization import get_localization_for_page

# --- Flask App Setup ---
project_root = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(project_root)
app = Flask(__name__, static_folder=project_root)
CORS(app)

data_manager.create_data_dir()


# --- 辅助函数：计算简单文本指标 ---
def calculate_text_metrics(text: str) -> dict:
    """计算字符数、词数和模拟的 token 数"""
    text = text.strip()
    char_count = len(text)
    word_count = len(text.split())
    # 模拟 token 计数: 假设一个字符平均 1/3 个 token
    token_count = max(1, int(char_count / 3))

    return {
        "length_char": char_count,
        "length_word": word_count,
        "length_token": token_count
    }


# --- Jinja2 渲染辅助函数 ---
def render_template_page(template_file_name: str, module_name: str, participant_id: str):
    """
    根据受试者ID从状态中获取语言，然后用正确的本地化文本渲染 HTML 模板。
    """
    # 1. 获取语言 (如果 PID 未初始化，会返回默认 'en')
    language = data_manager.get_participant_language(participant_id)

    # print(f"DEBUG: Rendering {template_file_name} for PID {participant_id} in language: {language}")

    # 2. 获取本地化文本字典
    strings = get_localization_for_page(module_name, language)

    # 3. 读取 HTML 文件内容 (FIX: 根据文件名判断路径)
    if template_file_name == 'index.html':
        file_path = os.path.join(app.static_folder, template_file_name)
    else:
        # 其他所有流程页面都在 html 目录下
        file_path = os.path.join(app.static_folder, 'html', template_file_name)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        # 如果找不到文件，则返回 404 响应
        return Response(f"Template not found: {template_file_name}", status=404)

    # 4. 使用 render_template_string 渲染
    return render_template_string(html_content, strings=strings)


# --- 静态文件服务路由 ---

@app.route('/')
def root():
    """根路由：服务 index.html"""
    # index.html 位于项目根目录
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/index.html')
@app.route('/index.html')
def serve_index():
    """
    根路由和 index.html：渲染 Consent Page 的文本。
    """
    participant_id = request.args.get('pid', None)

    if not participant_id:
        # 如果没有 PID，返回原始静态文件，让前端 JS 处理重定向到 admin_setup
        return send_from_directory(app.static_folder, 'index.html')

    # 如果有 PID，尝试渲染（Consent Page 的本地化模块名为 "consent"）
    # 使用 PID 来获取正确的语言
    return render_template_page('index.html', 'consent', participant_id)


# 确保 html 目录下的所有文件可以被访问 (现在用于渲染模板)
@app.route('/html/<path:filename>')
def serve_html(filename):
    """
    服务 html 目录下的静态文件，对实验流程页面进行 Jinja2 渲染。
    """

    # 流程页面映射表 (key: 文件名, value: localization.py 中的模块名)
    PAGE_MAPPING = {
        "demographics.html": "demographics",
        "baseline_mood.html": "baseline_mood",
        "instructions_xai.html": "instructions",
        "instructions_non_xai.html": "instructions",
        "post_questionnaire.html": "post_questionnaire",
        "open_ended_qs.html": "open_ended_qs",
        "debrief.html": "debrief",
        # XAI_Version.html and non-XAI_version.html are chat interfaces, keep them static for now
    }

    module_name = PAGE_MAPPING.get(filename)

    if module_name:
        # 从 URL 参数中获取 PID，这是唯一的可靠方式
        participant_id = request.args.get('pid', 'DEFAULT')

        # 渲染流程页面
        return render_template_page(filename, module_name, participant_id)

    # 非流程页面 (admin_setup, chat interfaces, assets) 仍作为静态文件服务
    return send_from_directory(os.path.join(app.static_folder, 'html'), filename)

# 确保 assets 目录下的所有文件可以被访问
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """服务 assets 目录下的静态文件"""
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)


# --- 实验初始化路由 ---

@app.route('/start_experiment', methods=['POST'])
def start_experiment():
    """
    实验初始化路由：
    1. 接收 PID, Condition (XAI/NON_XAI) 和 Language (en/zh-CN)。
    2. 清除旧的 LLM 会话。
    3. 初始化会话状态并保存到数据文件。
    4. 返回 Consent 页面 URL。
    """
    try:
        data = request.json
        participant_id = data.get("participant_id")
        condition = data.get("condition")
        language = data.get("language")

        if not participant_id or not condition or not language:
            return jsonify({"error": "Missing participant_id, condition, or language"}), 400

        llm_service.clear_session(participant_id)

        # 初始化数据 (这也会写入 INIT 记录, 包含语言)
        # 假设您已在 data_manager.py 中添加 language 参数
        data_manager.init_participant_session(participant_id, condition, language)

        # 返回 Consent 页面 URL (携带 PID)
        return jsonify({"success": True, "next_url": f"/index.html?pid={participant_id}"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error in /start_experiment: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500


# --- 通用数据保存与流程控制路由 ---

@app.route('/save_data', methods=['POST'])
def save_data():
    """
    通用数据保存路由：用于保存问卷、情绪、知情同意等数据并进行流程控制。
    """
    try:
        data = request.json
        participant_id = data.get("participant_id")
        step_name = data.get("step_name")
        step_data = data.get("data")
        current_step_index = data.get("current_step_index")

        if not participant_id or not step_name or step_data is None or current_step_index is None:
            return jsonify({"error": "Missing required fields"}), 400

        # 1. 保存当前步骤的数据
        data_manager.save_participant_data(participant_id, step_name, step_data)

        # 2. 确定下一个页面的 URL (流程控制)
        next_step_index = current_step_index

        if next_step_index >= len(EXPERIMENT_STEPS):
            next_url = "/html/debrief.html"
        else:
            next_step_key = EXPERIMENT_STEPS[next_step_index]

            # --- 关键逻辑：Instructions 页面版本选择 ---
            if next_step_key == "INSTRUCTIONS":
                status = data_manager.get_participant_status(participant_id)
                condition = status.get("condition", "NON_XAI")
                next_url = INSTRUCTION_VERSION_MAP.get(condition, INSTRUCTION_VERSION_MAP["NON_XAI"])
            # --- 关键逻辑：DIALOGUE 页面版本选择 ---
            elif next_step_key == "DIALOGUE":
                status = data_manager.get_participant_status(participant_id)
                condition = status.get("condition", "NON_XAI")
                next_url = VERSION_MAP.get(condition, VERSION_MAP["NON_XAI"])
            # --- 其他页面 ---
            else:
                next_url = f"/html/{next_step_key.lower()}.html"

        # 3. 返回下一个页面的 URL (FIX: 确保携带 PID)
        return jsonify({
            "success": True,
            "next_url": f"{next_url}?pid={participant_id}",
            "next_step_index": current_step_index + 1
        })

    except Exception as e:
        print(f"Error in /save_data: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500


# --- 聊天交互路由 (核心修改：只记录指标) ---

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message", "")
    participant_id = request.json.get("participant_id", "")
    # 从前端接收 XAI 解释是否显示的状态 (在 XAI 版本中为 True/False)
    explanation_shown = request.json.get("explanation_shown", False)

    if not user_input or not participant_id:
        return Response("⚠️ No message or participant_id provided", status=400, mimetype='text/plain')

    session = llm_service.get_session(participant_id)
    condition = data_manager.get_participant_condition(participant_id)

    # 在流开始前记录回合数（LLM Service 内部会+1）
    current_turn = session['turn_count'] + 1
    user_metrics = calculate_text_metrics(user_input)

    def generate_stream_and_log():
        full_ai_reply = b''

        # 1. 调用 LLM 服务生成流
        stream = llm_service.get_llm_response_stream(participant_id, user_input)

        for chunk in stream:
            full_ai_reply += chunk
            yield chunk

        # 2. 在流结束后，记录回合分析数据 (如果 LLM 成功回复且回合数增加)
        if full_ai_reply and session['turn_count'] == current_turn:
            # 从 session history 获取最新的 AI 消息 (确保它已经被 llm_service 规范化处理)
            ai_message = session['history'][-1]['content']
            agent_metrics = calculate_text_metrics(ai_message)

            turn_data = {
                "user_id": participant_id,
                "condition": condition,
                "turn": current_turn,

                # 用户指标 (情感占位符)
                "user_sentiment_score": None,
                "user_sentiment_label": None,
                "user_input_length_token": user_metrics["length_token"],
                "user_input_length_char": user_metrics["length_char"],
                "user_input_length_word": user_metrics["length_word"],

                # Agent 指标 (情感占位符)
                "agent_sentiment_score": None,
                "agent_sentiment_label": None,
                "agent_response_length_token": agent_metrics["length_token"],
                "agent_response_length_char": agent_metrics["length_char"],
                "agent_response_length_word": agent_metrics["length_word"],

                # XAI 状态
                "explanation_shown": explanation_shown if condition == "XAI" else False
            }

            # 3. 存储回合分析数据
            data_manager.save_turn_data(participant_id, turn_data)

    return Response(generate_stream_and_log(), mimetype='text/plain')


# --- (已修改) /end_dialogue 路由 ---
@app.route('/end_dialogue', methods=['POST'])
def end_dialogue():
    """
    终止对话会话：
    1. 记录结束时间、总轮数和情绪波动占位符。
    2. 转换到下一个实验步骤 (POST_QUESTIONNAIRE)。
    """
    try:
        data = request.json
        participant_id = data.get("participant_id")

        if not participant_id:
            return jsonify({"error": "Missing participant_id"}), 400

        # --- 新增：获取 LLM 会话数据 ---
        session = llm_service.get_session(participant_id)

        # 1. 记录对话结束状态和指标
        DIALOGUE_STEP_INDEX = 3  # "DIALOGUE" 在 EXPERIMENT_STEPS 中的索引

        # --- 修改：添加 total_turns 和 emotion_fluctuation 占位符 ---
        dialogue_end_data = {
            "status": "Completed by user",
            "end_time": time.time(),
            "total_turns": session['turn_count'],
            "emotion_fluctuation": None  # 为未来的情感分析模型预留的占位符
        }

        data_manager.save_participant_data(participant_id, "DIALOGUE_END", dialogue_end_data)

        # 2. 确定下一个步骤的 URL (POST_QUESTIONNAIRE)
        next_step_index = DIALOGUE_STEP_INDEX + 1

        if next_step_index >= len(EXPERIMENT_STEPS):
            next_url = "/html/debrief.html"
        else:
            next_step_key = EXPERIMENT_STEPS[next_step_index]  # 此时为 POST_QUESTIONNAIRE
            next_url = f"/html/{next_step_key.lower()}.html"

        # 3. 返回下一个页面的 URL (修复：确保携带 PID)
        return jsonify({
            "success": True,
            "next_url": f"{next_url}?pid={participant_id}",  # <--- 这一行是关键修复
            "next_step_index": next_step_index
        })

    except Exception as e:
        print(f"Error in /end_dialogue: {e}")
        # 确保返回一个 JSON 错误响应，而不是让 Flask 默认返回 500 HTML
        return jsonify(
            {"error": "Internal server error during dialogue termination. Please contact the experimenter."}), 500


CONTACT_FILE = os.path.join(data_manager.DATA_DIR, "follow_up_contacts.csv")


def save_contact_to_separate_file(participant_id: str, email: str):
    """
    将联系信息写入一个与主要匿名数据分离的 CSV 文件。
    """
    header = ["timestamp", "participant_id", "email"]
    data = [time.time(), participant_id, email]

    file_exists = os.path.exists(CONTACT_FILE)

    try:
        with open(CONTACT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 如果文件不存在，则写入标题行
            if not file_exists:
                writer.writerow(header)

            # 写入数据行
            writer.writerow(data)

        print(f"✅ Contact data saved separately for PID {participant_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save contact data: {e}")
        return False


@app.route('/save_contact', methods=['POST'])
def save_contact():
    """
    用于接收访谈联系信息，并将数据写入与问卷分离的单独文件。
    """
    try:
        data = request.json
        participant_id = data.get("participant_id")
        email = data.get("email")

        if not participant_id or not email:
            return jsonify({"error": "Missing participant_id or email"}), 400

        if save_contact_to_separate_file(participant_id, email):
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to write contact file."}), 500

    except Exception as e:
        print(f"Error in /save_contact: {e}")
        return jsonify({"error": "Internal server error during contact save."}), 500


# --- 运行 Flask 服务器 ---
if __name__ == "__main__":
    print("🚀 Starting Flask server on http://127.0.0.1:5000")
    print(f"💾 Data will be saved to: {data_manager.DATA_DIR}")

    # 关键修改：
    # 1. 设置 threaded=False, processes=1 确保单进程稳定运行
    # 2. 禁用 reloader，防止文件变化导致意外重启
    app.run(debug=False, port=5000, threaded=False, processes=1, use_reloader=False)

    # run on "http://127.0.0.1:5000/html/admin_setup.html"