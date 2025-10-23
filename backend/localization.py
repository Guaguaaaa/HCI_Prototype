# backend/localization.py

# 实验中所有 UI 文本的本地化字典
# 键为模块/页面名，值为文本键值对
LOCALIZATION_STRINGS = {
    # --- 全局/常用文本 ---
    "global": {
        "en": {
            "strongly_disagree": "1 (Strongly Disagree)",
            "strongly_agree": "7 (Strongly Agree)",
            "neutral": "4 (Neutral)",
            "continue_to_next": "Continue to Next Step",
            "saving_data": "Saving Data...",
            "loading_chat": "Loading Chat Interface...",
            "error_pid_missing": "Error: Participant ID missing. Please start over.",
            "error_unknown_data_save": "Unknown error during data save.",
            "error_general_fail": "Error: Failed to fetch data.",
        },
        "zh-CN": {
            "strongly_disagree": "1 (非常不同意)",
            "strongly_agree": "7 (非常同意)",
            "neutral": "4 (中立)",
            "continue_to_next": "继续下一步",
            "saving_data": "正在保存数据...",
            "loading_chat": "正在加载聊天界面...",
            "error_pid_missing": "错误：缺少参与者ID。请重新开始。",
            "error_unknown_data_save": "数据保存期间发生未知错误。",
            "error_general_fail": "错误：获取数据失败。",
        }
    },

    # --- index.html (Informed Consent) ---
    "consent": {
        "en": {
            "title": "Research Experiment: Informed Consent Confirmation",
            "title_h3": "Study Summary & Procedure",
            "pdf_important": "IMPORTANT: Please ensure you have read and signed the complete **Informed Consent Form (ICF) PDF** provided by the experimenter before proceeding.",
            "procedure_summary": "You are now confirming your participation in a study regarding **AI explainability and its effect on user perception**. Your total estimated experiment time is **15–20 minutes**.",
            "procedure_steps": "The core steps involve: **Questionnaires → A short dialogue with an AI Agent → Post-experiment Questionnaires.**",
            "rights_title": "Key Rights Summary",
            "voluntary_withdrawal": "Voluntary Participation & Withdrawal: You are participating voluntarily and may exit the study at any time without penalty. If you withdraw, your collected data will be deleted.",
            "anonymity": "Anonymity: All your dialogue metrics and questionnaire responses are anonymous and are used only for academic research.",
            "disclaimer": "Important Disclaimer: The AI Agent is **not a professional**. It does not provide medical or psychological support. If you experience discomfort, please stop immediately and contact the experimenter at **hi@peterguan.com**.",
            "confidentiality_title": "Data Confidentiality",
            "confidentiality_text": "Your privacy is protected. All data will be anonymized using a unique Participant ID and stored securely. No raw conversation text is retained.",
            "checkbox_label": "I have read and understood the summary above, and I confirm I consent to continue with this study.",
            "button_text": "I Agree and Continue",
            "checkbox_error": "Please check the box to confirm your consent."
        },
        "zh-CN": {
            "title": "研究实验：知情同意书确认",
            "title_h3": "研究摘要与流程",
            "pdf_important": "重要提示：在继续之前，请确保您已阅读并签署实验人员提供的完整**知情同意书 (ICF) PDF**。",
            "procedure_summary": "您正在确认参与一项关于**AI 可解释性及其对用户感知影响**的研究。预计总实验时间为 **15–20 分钟**。",
            "procedure_steps": "核心步骤包括：**问卷调查 → 与 AI Agent 的简短对话 → 实验后问卷。**",
            "rights_title": "关键权利摘要",
            "voluntary_withdrawal": "自愿参与和退出：您自愿参与（**Voluntary Participation**），可随时退出实验，不会受到任何惩罚。如果您退出，已收集的数据将被删除。",
            "anonymity": "匿名性：您的所有对话指标和问卷回答都将匿名化，仅用于学术研究。",
            "disclaimer": "重要免责声明：AI Agent **不是专业人士**。它不提供医疗或心理支持。如果您感到不适，请立即停止并联系实验人员：**hi@peterguan.com**。",
            "confidentiality_title": "数据保密性",
            "confidentiality_text": "您的隐私受到保护。所有数据将使用唯一的参与者 ID 进行匿名化并安全存储。不会保留任何原始对话文本。",
            "checkbox_label": "我已阅读并理解上述摘要，并确认我同意继续参与本研究。",
            "button_text": "我同意并继续",
            "checkbox_error": "请勾选此框以确认您的同意。"
        }
    },

    # --- demographics.html ---
    "demographics": {
        "en": {
            "title": "Demographics Survey",
            "intro": "Please provide the following basic information about yourself. Your answers will be kept confidential and used only for statistical analysis.",
            "q1_age": "1. Age (in years):",
            "q2_gender": "2. Gender:",
            "q2_female": "Female",
            "q2_male": "Male",
            "q2_nonbinary": "Non-binary/Other",
            "q2_prefer_not": "Prefer not to say",
            "q3_education": "3. Highest Level of Education Completed:",
            "q3_select": "Select an option",
            "q3_high_school": "High School Diploma or equivalent",
            "q3_associate": "Associate's Degree",
            "q3_bachelor": "Bachelor's Degree",
            "q3_master": "Master's Degree",
            "q3_doctorate": "Doctorate or Professional Degree",
            "q3_other": "Other",
            "q4_frequency": "4. How often do you typically use chatbots (e.g., Siri, ChatGPT, Gemini, emotional support bots)?",
            "q4_never": "1 (Never)",
            "q4_often": "7 (Very Often)",
            "q5_mental_health": "5. Have you ever received psychological counseling or been diagnosed with a mental health issue?",
            "q5_yes": "Yes",
            "q5_no": "No",
            "error_fill_all": "Please fill in all required fields.",
        },
        "zh-CN": {
            "title": "人口统计学调查",
            "intro": "请提供以下关于您的基本信息。您的回答将严格保密，仅用于统计分析。",
            "q1_age": "1. 年龄（岁）：",
            "q2_gender": "2. 性别：",
            "q2_female": "女性",
            "q2_male": "男性",
            "q2_nonbinary": "非二元/其他",
            "q2_prefer_not": "不愿透露",
            "q3_education": "3. 完成的最高教育水平：",
            "q3_select": "选择一个选项",
            "q3_high_school": "高中毕业或同等学历",
            "q3_associate": "大专/副学士学位",
            "q3_bachelor": "学士学位",
            "q3_master": "硕士学位",
            "q3_doctorate": "博士或专业学位",
            "q3_other": "其他",
            "q4_frequency": "4. 您通常使用聊天机器人（如 Siri、ChatGPT、Gemini、情感支持机器人）的频率如何？",
            "q4_never": "1 (从不)",
            "q4_often": "7 (非常频繁)",
            "q5_mental_health": "5. 您是否曾接受过心理咨询或被诊断出患有心理健康问题？",
            "q5_yes": "是",
            "q5_no": "否",
            "error_fill_all": "请填写所有必填字段。",
        }
    },

    # --- baseline_mood.html ---
    "baseline_mood": {
        "en": {
            "title": "Baseline Mood Assessment",
            "intro": "Before beginning the experiment, please answer the following questions to assess your current mood and state of activation.",
            "q1_valence": "1. My mood is generally positive right now (**Valence**).",
            "q1_negative": "1 (Very Negative)",
            "q1_positive": "7 (Very Positive)",
            "q2_arousal": "2. I feel energetic or tense right now (**Arousal**).",
            "q2_calm": "1 (Very Calm / Low Energy)",
            "q2_excited": "7 (Very Excited / High Energy)",
            "neutral": "4 (Neutral)",
            "button_text": "Continue to Instructions",
            "error_answer_all": "Please answer both mood questions.",
        },
        "zh-CN": {
            "title": "基线情绪评估",
            "intro": "在开始实验之前，请回答以下问题，以评估您当前的情绪和激活状态。",
            "q1_valence": "1. 我现在的情绪总体上是积极的（**愉悦度/Valence**）。",
            "q1_negative": "1 (非常消极)",
            "q1_positive": "7 (非常积极)",
            "q2_arousal": "2. 我现在感到精力充沛或紧张（**激活度/Arousal**）。",
            "q2_calm": "1 (非常平静/低能量)",
            "q2_excited": "7 (非常兴奋/高能量)",
            "neutral": "4 (中立)",
            "button_text": "继续阅读说明",
            "error_answer_all": "请回答所有情绪问题。",
        }
    },

    # --- instructions_xai.html / instructions_non_xai.html ---
    "instructions": {
        "en": {
            "title_xai": "Experiment Task Instructions (**XAI Version**)",
            "title_non_xai": "Experiment Task Instructions (**Non-XAI Version**)",
            "task_overview": "Task Overview",
            "task_text": "You are about to begin the main part of the experiment: a conversation with an **AI Emotional Support Agent (The Agent)**. In this task, you will interact with the Agent as you would with an empathetic, non-professional listener.",
            "role_goal": "Your Role & Conversation Goal",
            "role_text": "Please communicate with The Agent naturally, as if sharing your thoughts with a close, supportive friend. **You are playing yourself.**",
            "list_goal": "Goal: Discuss any topics related to your feelings, daily life, recent challenges, or small achievements. The Agent's purpose is to provide emotional support and understanding.",
            "list_avoid": "What to Avoid: Please avoid asking the Agent for professional advice (e.g., coding, legal, medical, or complex financial analysis).",
            "list_duration": "Duration: The conversation should last for approximately 10 to 15 turns (messages back and forth). There is no strict time limit, but please aim for a meaningful interaction.",
            "xai_interface_title": "Interface Explanation (Important)",
            "xai_interface_box": "You will notice that the chat interface has a **dedicated side panel on the right**. This panel displays **explanations (XAI)** about the AI's internal state or decisions.",
            "xai_interface_list1": "The XAI explanation is intended to provide insights into *why* the Agent is responding in a certain way or *how* it perceives your message.",
            "xai_interface_list2": "Your Task: You are free to read these explanations, ignore them, or use them to better understand the Agent. They are there for your reference.",
            "starters_title": "Conversation Starters (Suggestions)",
            "hint_box_text": "If you're unsure where to begin, here are some suggestions to start the conversation:",
            "starter_challenges": "Recent Challenges: 'Did you encounter anything stressful or frustrating at work/school recently?'",
            "starter_achievements": "Small Achievements: 'Is there a small goal you recently accomplished or a little progress you made that you'd like to share?'",
            "starter_daily_life": "Daily Life/Interests: 'Tell the Agent about a TV show you are currently watching, or a daily dilemma you'd like their opinion on.'",
            "starter_relationships": "Relationships: 'Any small conflicts or warm moments you had with friends, family, or colleagues recently?'",
            "ending_title": "Ending the Dialogue",
            "ending_text1": "When you feel you have adequately expressed your feelings and are ready to conclude the task, please click the dedicated **End Dialogue** button.",
            "ending_list1": "Clicking the button will prompt a confirmation dialog to ensure you are ready to proceed.",
            "ending_list2": "Once confirmed, the system will save the final dialogue metrics and automatically advance you to the post-experiment questionnaires.",
            "support_title": "Experiment Support & Withdrawal",
            "support_text1": "Please remember that your participation is **voluntary**. You may withdraw from the experiment at any time without penalty or loss of benefits. If you wish to withdraw, simply inform the experimenter.",
            "support_text2": "If you encounter any technical issues, errors, or have questions during the experiment, please notify the experimenter immediately for assistance.",
            "button_text": "I Understand. Start the Dialogue",
        },
        "zh-CN": {
            "title_xai": "实验任务说明（**XAI 版本**）",
            "title_non_xai": "实验任务说明（**非 XAI 版本**）",
            "task_overview": "任务概览",
            "task_text": "您即将开始实验的主要部分：与一个**AI 情感支持 Agent（Agent）**进行对话。在此任务中，您将以一个富有同理心、非专业倾听者的身份与 Agent 互动。",
            "role_goal": "您的角色与对话目标",
            "role_text": "请以自然的方式与 Agent 交流，就像与一位亲密、支持您的朋友分享想法一样。**您的角色就是您自己。**",
            "list_goal": "目标：讨论任何与您的感受、日常生活、近期挑战或小成就相关的话题。Agent 的目的是提供**情感支持和理解 (Emotional Support and Understanding)**。",
            "list_avoid": "应避免事项：请避免向 Agent 寻求专业建议（例如，编程、法律、医疗或复杂的财务分析）。",
            "list_duration": "时长：对话应持续约 **10 到 15 个回合**（消息往复）。没有严格的时间限制，但请努力进行一次有意义的互动。",
            "xai_interface_title": "界面说明（重要）",
            "xai_interface_box": "您会注意到聊天界面有一个**专用的右侧面板**。该面板显示了关于 AI 内部状态或决策的**解释（XAI）**。",
            "xai_interface_list1": "XAI 解释旨在提供洞察，说明 Agent *为什么*以某种方式回应或 *如何*感知您的消息。",
            "xai_interface_list2": "您的任务：您可以自由阅读这些解释、忽略它们，或利用它们更好地理解 Agent。它们仅供您参考。",
            "starters_title": "对话起始建议",
            "hint_box_text": "如果您不确定从何开始，这里有一些建议：",
            "starter_challenges": "近期挑战：“你最近在工作/学校有没有遇到什么有压力或令人沮丧的事情？”",
            "starter_achievements": "小成就：“你最近有没有完成什么小目标，或者取得了一点进展想分享一下？”",
            "starter_daily_life": "日常生活/兴趣：“告诉 Agent 你正在看的一部电视剧，或者你希望听取它意见的日常困境。”",
            "starter_relationships": "人际关系：“你最近和朋友、家人或同事之间有没有发生什么小摩擦或温馨时刻？”",
            "ending_title": "结束对话",
            "ending_text1": "当您认为自己已充分表达了感受并准备结束任务时，请点击专用的**结束对话**按钮。",
            "ending_list1": "点击按钮后将出现一个确认对话框，以确保您已准备好继续。",
            "ending_list2": "一旦确认，系统将保存最终的对话指标并自动将您带到实验后问卷。",
            "support_title": "实验支持与退出",
            "support_text1": "请记住，您的参与是**自愿的 (Voluntary)**。您可以随时退出实验，不会受到任何惩罚或损失任何福利。如果您希望退出，只需通知实验人员即可。",
            "support_text2": "如果您在实验过程中遇到任何技术问题、错误或有疑问，请立即通知实验人员寻求帮助。",
            "button_text": "我已理解。开始对话",
        }
    },

    # --- post_questionnaire.html ---
    "post_questionnaire": {
        "en": {
            "title": "Post-Experiment Questionnaire",
            "intro": "Please reflect on the conversation you just had with the AI Agent and answer the following questions based on your experience. Select the option that best reflects your agreement with the statement. (1 = Strongly Disagree, 7 = Strongly Agree)",
            "section_a_title": "Section A: Trust (General Reliability and Intent)",
            "q1_reliable": "1. This agent is reliable.",
            "q2_predictable": "2. The agent's behavior is predictable.",
            "q3_dependent": "3. I would rely on this agent when seeking emotional support.",
            "q4_confidence": "4. I believe the agent can correctly identify my emotions.",
            "q5_intent": "5. I think the agent's goal is to help me (not mislead).",
            "q6_skeptic": "6. I am skeptical about the agent's judgments.",

            "section_b_title": "Section B: Perceived Empathy",
            "q7_understood": "7. The agent seemed to understand my feelings.",
            "q8_cared": "8. The agent's responses made me feel cared for.",
            "q9_responsive": "9. The agent's replies were relevant to my emotional state.",
            "q10_warm": "10. The agent conveyed warmth or concern.",
            "q11_respect": "11. I felt the agent respected my emotions and perspective.",
            "q12_insincere": "12. The agent's empathy seemed insincere.",

            "section_c_title": "Section C: Quality Control",
            "q13_attn_check": "13. **ATTENTION CHECK:** To show you are carefully reading the questions, please select \"Strongly Agree\" (i.e., 7) for this item.",
            "q14_manip_check": "14. Did the system display explanations (e.g., highlighted your text and explained why it judged a certain emotion) during the conversation?",
            "q14_yes": "1 = Yes, I saw explanations",
            "q14_no": "2 = No, I did not see explanations",
            "q14_notsure": "3 = Not sure / Didn't pay attention",

            "section_d_title": "Section D: Explanation Feedback (XAI)",
            "q15_useful": "15. The explanation provided by the agent was useful.",
            "q16_clear": "16. The explanation was clear and easy to understand.",
            "q17_sufficient": "17. The amount of explanation was appropriate (not too little/too much).",
            "q18_trusthelp": "18. The explanation made it easier for me to trust the agent's judgment.",

            "button_text": "Continue to Open-Ended Questions",
            "error_answer_all": "Please answer all questions before continuing.",
        },
        "zh-CN": {
            "title": "实验后问卷",
            "intro": "请回顾您与 AI Agent 的对话，根据您的体验回答以下问题。选择最能反映您对陈述的同意程度的选项。 (1 = 非常不同意，7 = 非常同意)",
            "section_a_title": "A 部分：**信任 (Trust)**（总体可靠性和意图）",
            "q1_reliable": "1. 该 Agent 是**可靠的 (reliable)**。",
            "q2_predictable": "2. 该 Agent 的行为是**可预测的 (predictable)**。",
            "q3_dependent": "3. 在寻求情感支持时，我会**依赖 (rely on)** 这个 Agent。",
            "q4_confidence": "4. 我相信该 Agent 可以**正确识别 (correctly identify)** 我的情绪。",
            "q5_intent": "5. 我认为该 Agent 的目标是帮助我（而不是误导）。",
            "q6_skeptic": "6. 我对该 Agent 的判断持**怀疑态度 (skeptical)**。",

            "section_b_title": "B 部分：**感知到的共情 (Perceived Empathy)**",
            "q7_understood": "7. 该 Agent 似乎**理解 (understand)** 我的感受。",
            "q8_cared": "8. 该 Agent 的回应让我感到**被关心 (cared for)**。",
            "q9_responsive": "9. 该 Agent 的回复与我的**情绪状态 (emotional state)** 相关。",
            "q10_warm": "10. 该 Agent 传达了**温暖或关切 (warmth or concern)**。",
            "q11_respect": "11. 我觉得该 Agent 尊重了我的情绪和观点。",
            "q12_insincere": "12. 该 Agent 的共情显得**不真诚 (insincere)**。",

            "section_c_title": "C 部分：质量控制",
            "q13_attn_check": "13. **注意力检查 (ATTENTION CHECK)**：为了表明您正在仔细阅读问题，请为此项选择**“非常同意”（即 7）**。",
            "q14_manip_check": "14. 在对话过程中，系统是否显示了**解释**（例如，突出显示您的文本并解释其判断某种情绪的原因）？",
            "q14_yes": "1 = 是，我看到了解释",
            "q14_no": "2 = 否，我没有看到解释",
            "q14_notsure": "3 = 不确定 / 没有注意",

            "section_d_title": "D 部分：解释反馈 (**XAI**) ",
            "q15_useful": "15. Agent 提供的解释是**有用的 (useful)**。",
            "q16_clear": "16. 该解释是**清晰且易于理解的 (clear and easy to understand)**。",
            "q17_sufficient": "17. 解释的量是**适当的 (appropriate)**（不多不少）。",
            "q18_trusthelp": "18. 该解释使我更容易**相信 Agent 的判断 (trust the agent's judgment)**。",

            "button_text": "继续到开放式问题",
            "error_answer_all": "请回答所有问题后再继续。",
        }
    },

    # --- open_ended_qs.html ---
    "open_ended_qs": {
        "en": {
            "title": "Open-Ended Questions",
            "intro": "Please use the text boxes below to provide additional qualitative feedback on your experience.",
            "q1_trust": "1. Briefly explain: Why do you (or do you not) trust this system? (Aim for 2-3 sentences)",
            "q2_empathy": "2. Briefly explain: Which details made you feel the system was 'empathic' or 'not empathic'? (Aim for 2-3 sentences)",
            "q3_general": "3. What aspect of your interaction with the Agent did you find most confusing or most surprising? Do you have any suggestions for improving the Agent's responses or the interface design?",
            "q4_interview": "4. Would you be willing to be contacted for an optional follow-up interview about your experience?",
            "q4_yes": "Yes, I am willing to be contacted",
            "q4_no": "No, thank you",
            "contact_label": "Please enter your preferred contact email below:",
            "contact_placeholder": "email@example.com",
            "privacy_note_strong": "Privacy Note:",
            "privacy_note_text": "This email will be stored separately from your survey data solely for the purpose of recruitment. Your responses (Q1-Q3) remain completely anonymous.",
            "button_text": "Finish Questionnaire & View Debriefing",
            "error_fill_all": "Please answer all required questions and provide an email if you consented to follow-up.",
        },
        "zh-CN": {
            "title": "开放式问题",
            "intro": "请使用下面的文本框，提供您对实验体验的更多定性反馈。",
            "q1_trust": "1. 请简要解释：您为什么信任（或不信任）该系统？（目标：2-3 句话）",
            "q2_empathy": "2. 请简要解释：哪些细节让您觉得系统**“富有共情 (empathic)”**或**“不富有共情 (not empathic)”**？（目标：2-3 句话）",
            "q3_general": "3. 您与 Agent 互动过程中，发现最**令人困惑 (confusing)** 或最**令人惊讶 (surprising)** 的方面是什么？您对改进 Agent 的回应或界面设计有何建议？",
            "q4_interview": "4. 您是否愿意接受一次关于您体验的可选后续访谈 (optional follow-up interview)？",
            "q4_yes": "是，我愿意接受联系",
            "q4_no": "否，谢谢",
            "contact_label": "请在下方输入您的首选联系邮箱：",
            "contact_placeholder": "email@example.com",
            "privacy_note_strong": "隐私声明：",
            "privacy_note_text": "此邮箱将与您的问卷数据分开存储，仅用于招募目的。您的回答（Q1-Q3）保持完全匿名。",
            "button_text": "完成问卷并查看总结报告",
            "error_fill_all": "请回答所有必填问题，如果您同意后续访谈，请提供邮箱。",
        }
    },

    "debrief": {
        "en": {
            "title": "Experiment Completed!",
            "thank_you": "Thank you very much for your time and thoughtful participation in this research study. Your contribution is highly valuable to our work in Human-Computer Interaction (HCI).",
            "purpose_title": "Study Purpose Revealed",
            "purpose_1": "The primary purpose of this study was to compare **how providing (or not providing) AI-generated explanations** for its emotion judgments affects users' **trust** and **perceived empathy** in an emotional support conversational agent.",
            "purpose_2": "You were randomly assigned to either the **XAI condition** (with explanations) or the **Non-XAI condition** (without explanations). Your feedback helps us determine if transparency improves the user experience with AI support systems.",
            "safety_title": "Mental Health Safety Resources",
            "safety_warning_h3": "⚠️ Important: If You Experienced Distress",
            "safety_warning_p1": "If the emotional conversation task caused you any discomfort or distress, please remember that the AI Agent is not a substitute for a professional therapist.",
            "safety_contact_1": "Los Angeles Crisis Hotline:",
            "safety_contact_2": "Crisis Text Line:",
            "safety_contact_3": "Researcher Contact: If you feel uncomfortable or have lasting concerns, please contact the experimenter:",
            "results_title": "Research Results & Contact",
            "results_p1": "The data from this study is saved anonymously and securely.",
            "contact_p1": "Questions or Concerns:",
            "contact_p2": "Receive Results: If you would like to receive a summary of the research findings once the study is completed, please send an email to the researcher with the subject line: 'Request Research Results.'",
            "end_message": "You have completed all steps of the experiment.",
            "end_message_sub": "You may now close this browser window.",
        },
        "zh-CN": {
            "title": "实验已完成！",
            "thank_you": "非常感谢您的宝贵时间以及对本研究的深思熟虑的参与。您的贡献对于我们在**人机交互 (HCI)** 领域的工作具有极高的价值。",
            "purpose_title": "研究目的揭示",
            "purpose_1": "本研究的主要目的是比较 **提供（或不提供）AI 生成的情感判断解释** 如何影响用户对情感支持对话 Agent 的**信任 (Trust)** 和**感知到的共情 (Perceived Empathy)**。",
            "purpose_2": "您被随机分配到 **XAI 条件**（带有解释）或 **非 XAI 条件**（不带解释）。您的反馈有助于我们确定透明度是否能改善 AI 支持系统的用户体验。",
            "safety_title": "心理健康安全资源",
            "safety_warning_h3": "⚠️ 重要提示：如果您感到不适",
            "safety_warning_p1": "如果情感对话任务给您带来了任何不适或痛苦，请记住 AI Agent 不能替代专业的治疗师。",
            "safety_contact_1": "洛杉矶危机热线：",
            "safety_contact_2": "危机短信专线：",
            "safety_contact_3": "研究人员联系方式：如果您感到不适或有持续的顾虑，请联系实验人员：",
            "results_title": "研究结果与联系方式",
            "results_p1": "本研究的数据已匿名并安全存储。",
            "contact_p1": "问题或疑虑：",
            "contact_p2": "获取结果：如果您希望在研究完成后获得一份研究结果摘要，请发送邮件给研究人员，主题为：“Request Research Results”。",
            "end_message": "您已完成实验的所有步骤。",
            "end_message_sub": "您现在可以关闭此浏览器窗口。",
        }
    }
}


# 辅助函数：根据语言和键获取文本
def get_localized_string(module: str, key: str, language: str) -> str:
    """从本地化字典中安全地获取指定语言的文本"""
    # 优先获取模块内的文本
    if module in LOCALIZATION_STRINGS and key in LOCALIZATION_STRINGS[module].get(language, {}):
        return LOCALIZATION_STRINGS[module][language][key]

    # 其次尝试获取全局文本
    if key in LOCALIZATION_STRINGS["global"].get(language, {}):
        return LOCALIZATION_STRINGS["global"][language][key]

    # 如果找不到任何翻译，则回退到英文版本（默认）
    default_lang = "en"
    if module in LOCALIZATION_STRINGS and key in LOCALIZATION_STRINGS[module].get(default_lang, {}):
        return LOCALIZATION_STRINGS[module][default_lang][key]
    if key in LOCALIZATION_STRINGS["global"].get(default_lang, {}):
        return LOCALIZATION_STRINGS["global"][default_lang][key]

    # 如果连默认英文都找不到，则返回一个错误提示
    return f"[[MISSING_KEY: {module}.{key}]]"


# 主函数，返回一个完整的本地化字典用于 Jinja 模板
def get_localization_for_page(page_module: str, language: str) -> dict:
    """返回给定页面和语言的所有本地化字符串"""

    # 收集当前页面所需的文本
    strings = {}

    # 1. 收集全局文本 (确保所有全局文本都存在)
    for key, value_dict in LOCALIZATION_STRINGS["global"]["en"].items():
        # 尝试获取用户语言，失败则使用英文默认
        strings[key] = LOCALIZATION_STRINGS["global"].get(language, {}).get(key, value_dict)

    # 2. 收集模块特定文本
    page_data = LOCALIZATION_STRINGS.get(page_module, {})
    # 尝试获取用户语言，失败则使用英文默认
    lang_data = page_data.get(language, page_data.get("en", {}))
    strings.update(lang_data)

    return strings