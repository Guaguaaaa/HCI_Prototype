from flask import Flask, request, jsonify, Response, send_from_directory, render_template_string, redirect, url_for
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


# (calculate_text_metrics 保持不变)
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


# (render_template_page 保持不变, 但现在会接收更多 context 变量)
def render_template_page(template_file_name: str, module_name: str, participant_id: str, context: dict = None):
    """
    根据受试者ID从状态中获取语言，然后用正确的本地化文本和附加 context 渲染 HTML 模板。
    """
    language = data_manager.get_participant_language(participant_id)
    strings = get_localization_for_page(module_name, language)

    # 确定文件路径
    if template_file_name == 'index.html':
        file_path = os.path.join(app.static_folder, template_file_name)
    else:
        file_path = os.path.join(app.static_folder, 'html', template_file_name)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        return Response(f"Template not found: {template_file_name}", status=404)

    # 合并 context 变量
    render_context = {"strings": strings}
    if context:
        render_context.update(context)

    # 使用 render_template_string 渲染
    return render_template_string(html_content, **render_context)


# --- 静态文件服务路由 ---

@app.route('/')
def root():
    """根路由：重定向到 admin_setup 或 index.html (带 pid)"""
    # 简单地重定向到 admin_setup 作为默认入口
    return redirect('/html/admin_setup.html')


@app.route('/index.html')
def serve_index():
    """
    服务 index.html (Consent Page), 验证是否处于步骤 -1。
    """
    participant_id = request.args.get('pid', None)

    if not participant_id:
        return redirect('/html/admin_setup.html')

    status = data_manager.get_participant_status(participant_id)
    # Consent 页面只应在 step_index 为 -1 时访问
    expected_index = status.get("current_step_index", -1)

    if expected_index != -1:
        # 如果不是 -1，重定向到他们应该在的页面
        print(
            f"⚠️ Access Violation: PID {participant_id} requested Consent page but is on step {expected_index}. Redirecting.")
        return redirect_to_expected_step(participant_id, status)

    # 正常渲染 Consent 页面 (注入 step index)
    context = {
        "current_step_index": -1,
        "current_step_name": "CONSENT_AGREEMENT"  # 虽然不在列表里，但 JS 需要
    }
    return render_template_page('index.html', 'consent', participant_id, context=context)


# --- NEW HELPER: Redirect to expected step ---
def redirect_to_expected_step(participant_id: str, status: dict = None):
    """根据状态文件中的 expected_index 重定向用户"""
    if not status:
        status = data_manager.get_participant_status(participant_id)

    expected_index = status.get("current_step_index", -1)
    condition = status.get("condition", "NON_XAI")  # 获取当前条件

    if expected_index == -1:
        expected_url = f"/index.html?pid={participant_id}"
    elif expected_index >= len(EXPERIMENT_STEPS):  # 超出范围，去 Debrief
        expected_url = f"/html/debrief.html?pid={participant_id}"
    else:
        expected_step_key = EXPERIMENT_STEPS[expected_index]
        expected_url = get_url_for_step(expected_step_key, condition, participant_id)

    print(f"🔄 Redirecting PID {participant_id} to expected step {expected_index} at {expected_url}")
    return redirect(expected_url)


# --- NEW HELPER: Get URL for a step key ---
def get_url_for_step(step_key: str, condition: str, participant_id: str) -> str:
    """根据步骤 Key 和当前条件确定正确的 URL"""
    if step_key == "INSTRUCTIONS_1" or step_key == "INSTRUCTIONS_2":
        # Instruction 页面的 URL 取决于 *当前* 条件
        url_path = INSTRUCTION_VERSION_MAP.get(condition, INSTRUCTION_VERSION_MAP["NON_XAI"])
    elif step_key == "DIALOGUE_1" or step_key == "DIALOGUE_2":
        # Dialogue 页面的 URL 也取决于 *当前* 条件
        url_path = VERSION_MAP.get(condition, VERSION_MAP["NON_XAI"])
    elif step_key == "POST_QUESTIONNAIRE_1" or step_key == "POST_QUESTIONNAIRE_2":
        url_path = "/html/post_questionnaire.html"  # 两个问卷使用同一个文件
    elif step_key == "WASHOUT":
        url_path = "/html/washout.html"
    elif step_key == "OPEN_ENDED_QS":
        url_path = "/html/open_ended_qs.html"
    elif step_key == "DEBRIEF":
        url_path = "/html/debrief.html"
    # 处理流程开始的几个页面
    elif step_key == "DEMOGRAPHICS":
        url_path = "/html/demographics.html"
    elif step_key == "BASELINE_MOOD":
        url_path = "/html/baseline_mood.html"
    else:
        # Fallback or error case? Default to debrief?
        print(f"⚠️ Unknown step key encountered: {step_key}. Defaulting to debrief.")
        url_path = "/html/debrief.html"

    return f"{url_path}?pid={participant_id}"


# --- MAJOR REWRITE: serve_html (核心流程控制) ---
@app.route('/html/<path:filename>')
def serve_html(filename):
    """
    服务 html 目录下的文件。
    对 Admin 页面进行保护。
    对实验流程页面执行严格的状态验证和重定向，并注入必要的 context。
    """
    participant_id = request.args.get('pid', None)

    # 1. 阻止参与者访问 Admin 页面
    if "admin_setup.html" in filename:
        if participant_id:
            print(f"🚫 Access Denied: Participant {participant_id} tried to access admin_setup.html")
            return "Access Denied: Participants cannot access this page.", 403
        else:  # 允许实验者访问
            return send_from_directory(os.path.join(app.static_folder, 'html'), filename)

    # 2. 如果没有 PID 就试图访问任何其他 HTML 页面，踢回 admin 设置
    if not participant_id:
        print(f"🚫 Access Denied: Attempted to access {filename} without PID.")
        return redirect('/html/admin_setup.html')

    # 3. 核心：状态验证与渲染逻辑
    try:
        status = data_manager.get_participant_status(participant_id)
        if not status:  # 如果状态文件丢失 (不应发生)
            print(f"🚫 Critical Error: Status file missing for PID {participant_id}.")
            return redirect('/html/admin_setup.html?error=status_missing')

        expected_index = status.get("current_step_index", -1)
        current_condition = status.get("condition", "NON_XAI")

        if expected_index < 0 or expected_index >= len(EXPERIMENT_STEPS):
            # 应该在 Consent (-1) 或 Debrief (>=10)
            if expected_index == -1 and filename == 'index.html':  # (index.html 由 serve_index 处理)
                pass  # Should not reach here
            elif expected_index >= len(EXPERIMENT_STEPS) and filename == 'debrief.html':
                # 允许访问 Debrief 页面
                return render_template_page(filename, "debrief", participant_id)
            else:  # 状态无效或试图访问非 Debrief 页面，重定向
                print(f"⚠️ Invalid state index {expected_index} for PID {participant_id}. Redirecting.")
                return redirect_to_expected_step(participant_id, status)

        # 获取预期的步骤 Key 和对应的 URL
        expected_step_key = EXPERIMENT_STEPS[expected_index]
        expected_url = get_url_for_step(expected_step_key, current_condition, participant_id)
        # 从 URL 中提取预期的文件名 (移除查询参数)
        expected_filename = expected_url.split('?')[0].split('/')[-1]

        # 检查请求的文件名是否与预期匹配
        if filename != expected_filename:
            print(
                f"⚠️ Access Violation: PID {participant_id} requested {filename} but expected {expected_filename} (step {expected_index}). Redirecting.")
            return redirect(expected_url)

        # --- 验证通过 ---
        # 确定 localization 模块名
        module_name = "unknown"
        if expected_step_key.startswith("DEMOGRAPHICS"):
            module_name = "demographics"
        elif expected_step_key.startswith("BASELINE_MOOD"):
            module_name = "baseline_mood"
        elif expected_step_key.startswith("INSTRUCTIONS"):
            module_name = "instructions"
        elif expected_step_key.startswith("DIALOGUE"):
            module_name = "chat_interface"
        elif expected_step_key.startswith("POST_QUESTIONNAIRE"):
            module_name = "post_questionnaire"
        elif expected_step_key.startswith("WASHOUT"):
            module_name = "washout"
        elif expected_step_key.startswith("OPEN_ENDED_QS"):
            module_name = "open_ended_qs"
        elif expected_step_key.startswith("DEBRIEF"):
            module_name = "debrief"

        # 准备注入的 context
        context = {
            "current_step_index": expected_index,
            "current_step_name": expected_step_key
        }
        # 如果是问卷页面，注入条件标志
        if module_name == "post_questionnaire":
            context["is_xai_condition"] = (current_condition == "XAI")
            # (NEW) 动态设置按钮文本
            next_step_is_washout = (expected_step_key == "POST_QUESTIONNAIRE_1")
            button_key = "continue_to_washout" if next_step_is_washout else "continue_to_open_ended"
            # (假设 localization.py 中添加了这两个 key)
            # context["button_text"] = get_localization_for_page(module_name, status.get("language","en")).get(button_key, "Continue")

        # 渲染预期的页面
        return render_template_page(expected_filename, module_name, participant_id, context=context)

    except Exception as e:
        print(f"Error during step validation/rendering for {participant_id} on {filename}: {e}")
        # Log the full traceback for debugging
        import traceback
        traceback.print_exc()
        return "An error occurred during state validation.", 500


# (serve_assets 保持不变)
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """服务 assets 目录下的静态文件"""
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)


# --- MODIFIED: start_experiment ---
@app.route('/start_experiment', methods=['POST'])
def start_experiment():
    """
    实验初始化路由：
    1. 接收 PID, Condition Order (AB/BA) 和 Language。
    2. 清除旧的 LLM 会话。
    3. 初始化会话状态并保存到数据文件 (设置 step_index = -1, condition_order, 和初始 condition)。
    4. 返回 Consent 页面 URL。
    """
    try:
        data = request.json
        participant_id = data.get("participant_id")
        # condition = data.get("condition") # (OLD)
        condition_order = data.get("condition_order")  # (NEW)
        language = data.get("language")

        # if not participant_id or not condition or not language: # (OLD)
        if not participant_id or not condition_order or not language:  # (NEW)
            return jsonify({"error": "Missing participant_id, condition_order, or language"}), 400

        # 清除旧会话 (如果存在)
        llm_service.clear_session(participant_id)

        # 初始化数据 (会写入 INIT 记录, 设置 current_step_index = -1)
        # data_manager.init_participant_session(participant_id, condition, language) # (OLD)
        data_manager.init_participant_session(participant_id, condition_order, language)  # (NEW)

        # 返回 Consent 页面 URL (携带 PID)
        return jsonify({"success": True, "next_url": f"/index.html?pid={participant_id}"})

    except ValueError as e:  # Catch invalid condition_order
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error in /start_experiment: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500


# --- MAJOR REWRITE: save_data (处理新流程) ---
@app.route('/save_data', methods=['POST'])
def save_data():
    """
    通用数据保存路由：保存数据，推进状态，并返回下一步URL。
    新增处理 Washout 验证、状态更新和 XAI 字段填充的逻辑。
    """
    try:
        data = request.json
        participant_id = data.get("participant_id")
        step_name = data.get("step_name")  # e.g., "DEMOGRAPHICS", "POST_QUESTIONNAIRE_1", "WASHOUT"
        step_data = data.get("data")
        current_step_index = data.get("current_step_index")  # 刚刚 *完成* 的步骤索引

        if not participant_id or not step_name or step_data is None or current_step_index is None:
            return jsonify({"error": "Missing required fields"}), 400

        # --- (NEW) Washout 验证 ---
        if step_name == "WASHOUT":
            status = data_manager.get_participant_status(participant_id)
            start_ts = status.get("washout_start_ts")
            if not start_ts:  # 如果没有开始时间戳 (不应发生)
                print(f"Error: Washout start timestamp missing for {participant_id}")
                return jsonify({"error": "Washout start time missing."}), 400

            duration = time.time() - start_ts

            if duration < 300:  # 强制 5 分钟
                print(f"Info: PID {participant_id} tried to submit Washout early ({duration:.1f}s). Denied.")
                return jsonify({"success": False,
                                "error": get_localization_for_page("washout", status.get("language", "en")).get(
                                    "error_early_submit", "Please wait for the full 5-minute break.")}), 400

            # Washout 验证通过
            step_data["duration_seconds"] = round(duration, 2)
            step_data["washout_start_ts"] = start_ts
            print(f"✅ Washout complete for PID {participant_id} after {duration:.1f}s.")

            # (NEW) 清除 LLM 会话并更新到下一个 condition
            llm_service.clear_session(participant_id)
            if not data_manager.update_participant_condition(participant_id):
                # 如果更新 condition 失败，也应阻止流程继续
                return jsonify({"error": "Failed to update participant condition after washout."}), 500

        # --- (NEW) XAI 问卷字段填充 ---
        if step_name in ["POST_QUESTIONNAIRE_1", "POST_QUESTIONNAIRE_2"]:
            status = data_manager.get_participant_status(participant_id)
            current_condition = status.get("condition")
            if current_condition == "NON_XAI":
                # 确保这些键存在且值为 null
                step_data["expl_useful"] = step_data.get("expl_useful", None)
                step_data["expl_clear"] = step_data.get("expl_clear", None)
                step_data["expl_sufficient"] = step_data.get("expl_sufficient", None)
                step_data["expl_trusthelp"] = step_data.get("expl_trusthelp", None)

        # 1. 保存当前步骤的数据
        if not data_manager.save_participant_data(participant_id, step_name, step_data):
            return jsonify({"error": "Failed to save participant data."}), 500

        # 2. 确定下一个步骤的索引
        next_step_index = current_step_index + 1

        # 3. 更新状态文件中的步骤索引
        if not data_manager.update_participant_step(participant_id, next_step_index):
            return jsonify({"error": "Failed to update participant step."}), 500

        # --- (NEW) Washout 开始时间戳记录 ---
        if step_name == "POST_QUESTIONNAIRE_1":
            try:
                status_path = os.path.join(data_manager.DATA_DIR, f"P_{participant_id}_status.json")
                status_data = data_manager.get_participant_status(participant_id)  # 重新读取以获取最新的 index
                if status_data.get("current_step_index") == EXPERIMENT_STEPS.index("WASHOUT"):  # 确认已进入 Washout 步骤
                    status_data["washout_start_ts"] = time.time()
                    with open(status_path, 'w', encoding='utf-8') as f:
                        json.dump(status_data, f, ensure_ascii=False, indent=4)
                    print(f"⏱️ Washout timer started for PID {participant_id}")
                else:
                    print(
                        f"Warning: Did not record washout_start_ts for {participant_id}. Expected index {EXPERIMENT_STEPS.index('WASHOUT')}, got {status_data.get('current_step_index')}")
            except Exception as e:
                print(f"Error recording washout_start_ts for {participant_id}: {e}")
                # 不阻止流程，但记录错误

        # 4. 确定下一个页面的 URL (使用更新后的状态)
        status = data_manager.get_participant_status(participant_id)  # 确保使用最新状态
        current_condition = status.get("condition")

        if next_step_index >= len(EXPERIMENT_STEPS):
            next_url_path = "/html/debrief.html"
        else:
            next_step_key = EXPERIMENT_STEPS[next_step_index]
            # get_url_for_step 需要当前 condition 来决定 instruction/dialogue URL
            next_url_path = get_url_for_step(next_step_key, current_condition, participant_id).split('?')[
                0]  # Remove PID for response

        # 5. 返回下一个页面的 URL (携带 PID)
        return jsonify({
            "success": True,
            "next_url": f"{next_url_path}?pid={participant_id}",
            "next_step_index": next_step_index
        })

    except Exception as e:
        print(f"Error in /save_data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {e}"}), 500


# --- MODIFIED: chat (添加 session_part) ---
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message", "")
    participant_id = request.json.get("participant_id", "")
    # explanation_shown 在 XAI_Version.html 中可能为 true/false， NonXAI 中不存在
    explanation_shown = request.json.get("explanation_shown", False)

    if not user_input or not participant_id:
        return Response("⚠️ No message or participant_id provided", status=400, mimetype='text/plain')

    # 获取当前状态以确定 condition 和 session_part
    status = data_manager.get_participant_status(participant_id)
    condition = status.get("condition", "UNKNOWN")
    current_index = status.get("current_step_index")

    session_part = 1  # 默认是第一部分
    if current_index == EXPERIMENT_STEPS.index("DIALOGUE_2"):  # 7
        session_part = 2

    session = llm_service.get_session(participant_id)
    # 在流开始前记录回合数（LLM Service 内部会+1）
    current_turn = session['turn_count'] + 1
    user_metrics = calculate_text_metrics(user_input)

    def generate_stream_and_log():
        full_ai_reply = b''
        stream_error = None  # Track potential errors during streaming

        try:
            # 1. 调用 LLM 服务生成流
            stream = llm_service.get_llm_response_stream(participant_id, user_input)

            for chunk in stream:
                full_ai_reply += chunk
                yield chunk

        except Exception as e:
            stream_error = e  # Capture error
            print(f"Error during LLM stream for {participant_id}: {e}")
            yield f"⚠️ Backend LLM error: {e}".encode('utf-8')  # Inform frontend

        finally:
            # 2. 在流结束后，记录回合分析数据 (仅当没有流错误且 LLM 有回复)
            if not stream_error and full_ai_reply and session.get('turn_count',
                                                                  0) == current_turn:  # Safely get turn_count
                # 从 session history 获取最新的 AI 消息
                # (需要确保 llm_service 在 finally 块中添加了 history)
                ai_message = ""
                if session.get('history') and session['history'][-1]['role'] == 'ai':
                    ai_message = session['history'][-1]['content']

                agent_metrics = calculate_text_metrics(ai_message)

                turn_data = {
                    "user_id": participant_id,
                    "condition": condition,
                    "turn": current_turn,
                    "session_part": session_part,  # (NEW)
                    "user_sentiment_score": None,  # (Placeholder)
                    "user_sentiment_label": None,  # (Placeholder)
                    "user_input_length_token": user_metrics["length_token"],
                    "user_input_length_char": user_metrics["length_char"],
                    "user_input_length_word": user_metrics["length_word"],
                    "agent_sentiment_score": None,  # (Placeholder)
                    "agent_sentiment_label": None,  # (Placeholder)
                    "agent_response_length_token": agent_metrics["length_token"],
                    "agent_response_length_char": agent_metrics["length_char"],
                    "agent_response_length_word": agent_metrics["length_word"],
                    # explanation_shown is only relevant for XAI condition
                    "explanation_shown": explanation_shown if condition == "XAI" else False
                }

                # 3. 存储回合分析数据
                data_manager.save_turn_data(participant_id, turn_data)
            elif stream_error:
                print(f"Info: Turn data not saved for {participant_id} turn {current_turn} due to stream error.")
            elif not full_ai_reply:
                print(f"Info: Turn data not saved for {participant_id} turn {current_turn} because AI reply was empty.")
            # else: # turn count mismatch or other issue
            #    print(f"Warning: Turn data may not be saved for {participant_id} turn {current_turn}. Session turn: {session.get('turn_count', 0)}")

    return Response(generate_stream_and_log(), mimetype='text/plain')


# --- MODIFIED: end_dialogue (区分 _1 和 _2) ---
@app.route('/end_dialogue', methods=['POST'])
def end_dialogue():
    """
    终止对话会话：
    1. 记录结束时间、总轮数等，并区分是 DIALOGUE_END_1 还是 _2。
    2. 推进状态到下一步 (POST_QUESTIONNAIRE_1 或 _2)。
    3. 返回下一个实验步骤 URL。
    """
    try:
        data = request.json
        participant_id = data.get("participant_id")

        if not participant_id:
            return jsonify({"error": "Missing participant_id"}), 400

        session = llm_service.get_session(participant_id)
        status = data_manager.get_participant_status(participant_id)
        current_index = status.get("current_step_index")

        # 确定是哪个对话结束
        step_name = "DIALOGUE_END_UNKNOWN"
        dialogue_step_index = -1
        if current_index == EXPERIMENT_STEPS.index("DIALOGUE_1"):  # 3
            step_name = "DIALOGUE_END_1"
            dialogue_step_index = current_index
        elif current_index == EXPERIMENT_STEPS.index("DIALOGUE_2"):  # 7
            step_name = "DIALOGUE_END_2"
            dialogue_step_index = current_index
        else:
            print(f"Error: /end_dialogue called at unexpected step index {current_index} for {participant_id}")
            return jsonify({"error": "Dialogue ended at unexpected step."}), 400

        # 1. 记录对话结束状态和指标
        dialogue_end_data = {
            "status": "Completed by user",
            "end_time": time.time(),
            "total_turns": session.get('turn_count', 0),  # Safely get turn count
            "session_part": 1 if step_name == "DIALOGUE_END_1" else 2,  # (NEW)
            "emotion_fluctuation": None  # (Placeholder)
        }

        if not data_manager.save_participant_data(participant_id, step_name, dialogue_end_data):
            return jsonify({"error": "Failed to save dialogue end data."}), 500

        # 2. 确定下一个步骤的索引
        next_step_index = dialogue_step_index + 1  # 4 或 8

        # 3. 更新状态文件中的步骤索引
        if not data_manager.update_participant_step(participant_id, next_step_index):
            return jsonify({"error": "Failed to update participant step after dialogue end."}), 500

        # 4. 确定下一个步骤的 URL (需要更新后的状态来获取 condition)
        status = data_manager.get_participant_status(participant_id)  # Re-read status
        current_condition = status.get("condition")

        if next_step_index >= len(EXPERIMENT_STEPS):
            next_url_path = "/html/debrief.html"
        else:
            next_step_key = EXPERIMENT_STEPS[next_step_index]  # POST_QUESTIONNAIRE_1 or _2
            next_url_path = get_url_for_step(next_step_key, current_condition, participant_id).split('?')[0]

        # 5. 返回下一个页面的 URL
        return jsonify({
            "success": True,
            "next_url": f"{next_url_path}?pid={participant_id}",
            "next_step_index": next_step_index
        })

    except Exception as e:
        print(f"Error in /end_dialogue: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(
            {"error": "Internal server error during dialogue termination. Please contact the experimenter."}), 500


# (save_contact 和 save_contact_to_separate_file 保持不变)
CONTACT_FILE = os.path.join(data_manager.DATA_DIR, "follow_up_contacts.csv")


def save_contact_to_separate_file(participant_id: str, email: str):
    """
    将联系信息写入一个与主要匿名数据分离的 CSV 文件。
    """
    header = ["timestamp", "participant_id", "email"]
    # Ensure timestamp matches the format expected if read by spreadsheet software
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = [timestamp_str, participant_id, email]

    file_exists = os.path.exists(CONTACT_FILE)

    try:
        with open(CONTACT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists or os.path.getsize(CONTACT_FILE) == 0:  # Check size too
                writer.writerow(header)
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


# (运行 Flask 服务器的 main 保持不变)
if __name__ == "__main__":
    print("🚀 Starting Flask server on http://127.0.0.1:5000")
    print(f"💾 Data will be saved to: {data_manager.DATA_DIR}")
    print(f"🔄 Experiment Flow Steps: {EXPERIMENT_STEPS}")

    # For production/in-person experiments, debug=False is crucial
    # use_reloader=False prevents Flask from starting twice (important for state)
    # threaded=False or processes=1 might be necessary if state isn't thread-safe (Ollama interaction might be)
    # app.run(debug=False, port=5000, threaded=True, use_reloader=False)

    # Run in single-threaded mode for debugging LLM connection issues
    print("🚦 Running Flask in single-threaded mode for debugging.")
    app.run(debug=False, port=5000, threaded=False, use_reloader=False)

    # run on "http://127.0.0.1:5000/html/admin_setup.html"