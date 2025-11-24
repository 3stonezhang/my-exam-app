import streamlit as st
import pandas as pd
import os

# --- 页面配置 ---
st.set_page_config(page_title="全题库考试系统", layout="wide")

# --- 核心逻辑：万能读取函数 ---
@st.cache_data
def load_data():
    # 1. 优先尝试读取 CSV
    if os.path.exists("question_bank1.csv"):
        try:
            return pd.read_csv("question_bank1.csv").fillna("")
        except Exception as e:
            st.error(f"找到CSV但读取失败: {e}")
            return None
            
    # 2. 其次尝试读取 Excel (xlsx)
    elif os.path.exists("question_bank.xlsx"):
        try:
            return pd.read_excel("question_bank.xlsx").fillna("")
        except Exception as e:
            st.error(f"找到Excel但读取失败: {e}")
            return None
            
    # 3. 如果都找不到，返回空
    return None

# --- 初始化 Session ---
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'submitted' not in st.session_state: st.session_state.submitted = False
if 'exam_questions' not in st.session_state: st.session_state.exam_questions = []

# --- 侧边栏：设置与调试 ---
with st.sidebar:
    st.title("⚙️ 考试设置")
    
    # 加载数据
    df = load_data()
    
    if df is not None:
        st.success(f"✅ 题库加载成功！共 {len(df)} 题")
        # 题型统计
        st.write(df['题型'].value_counts())
        
        sel_types = st.multiselect("题型过滤", df['题型'].unique(), default=df['题型'].unique())
        if sel_types:
            filtered = df[df['题型'].isin(sel_types)]
            max_q = len(filtered)
            num = st.number_input("题目数量", 1, max_q, min(20, max_q))
            if st.button("开始考试", type="primary"):
                st.session_state.exam_questions = filtered.sample(n=num).to_dict('records')
                st.session_state.user_answers = {}
                st.session_state.submitted = False
                st.rerun()
    else:
        # === 调试信息：帮助你找到文件 ===
        st.error("❌ 未找到题库文件！")
        st.warning("调试模式：当前目录下的文件列表：")
        st.code(os.listdir('.')) # 这一行会列出服务器上所有的文件
        st.info("请确保上传了 'question_bank.csv' 或 'question_bank.xlsx'，且文件名大小写完全一致。")

# --- 主界面 ---
if st.session_state.exam_questions:
    # 进度条
    total = len(st.session_state.exam_questions)
    current = len(st.session_state.user_answers)
    st.progress(current / total if total > 0 else 0)
    
    with st.form("exam_form"):
        for i, q in enumerate(st.session_state.exam_questions):
            st.markdown(f"#### {i+1}. [{q['题型']}] {q['题目']}")
            qid = f"q_{i}"
            
            # 单选
            if q['题型'] == '单选':
                ops = [f"{k[-1]}. {q[k]}" for k in ['选项A','选项B','选项C','选项D','选项E','选项F'] if str(q[k]).strip()]
                st.radio("选项", ops, key=qid, label_visibility="collapsed", index=None)
            
            # 多选
            elif q['题型'] == '多选':
                st.caption("（多选题）")
                for k in ['选项A','选项B','选项C','选项D','选项E','选项F']:
                    if str(q[k]).strip():
                        st.checkbox(f"{k[-1]}. {q[k]}", key=f"{qid}_{k[-1]}")
            
            # 填空/简答
            else:
                st.text_area("你的答案", key=qid)
            
            st.divider()
        
        if st.form_submit_button("提交试卷", type="primary"):
            st.session_state.submitted = True
            st.rerun()

# --- 结果页 ---
if st.session_state.submitted:
    st.markdown("### 📊 考试结果")
    score = 0
    obj_count = 0
    
    for i, q in enumerate(st.session_state.exam_questions):
        correct = str(q['答案']).strip().upper().replace("，", ",")
        
        if q['题型'] == '单选':
            val = st.session_state.get(f"q_{i}")
            user_ans = val[0] if val else "未作答"
            if user_ans == correct: score+=1
            obj_count += 1
            st.info(f"第{i+1}题: {'✅ 正确' if user_ans==correct else '❌ 错误'} (你的答案: {user_ans} | 正确答案: {correct})")
            
        elif q['题型'] == '多选':
            user_ops = []
            for k in ['A','B','C','D','E','F']:
                if st.session_state.get(f"q_{i}_{k}"): user_ops.append(k)
            
            user_set = set(user_ops)
            corr_set = set(correct.split(','))
            
            if user_set == corr_set: score+=1
            obj_count += 1
            st.info(f"第{i+1}题: {'✅ 正确' if user_set==corr_set else '❌ 错误'} (正确答案: {correct})")
            
        else:
            st.warning(f"第{i+1}题 (主观题): 参考答案 -> {correct}")

    if obj_count > 0:
        st.metric("客观题得分", f"{score} / {obj_count}")
