import streamlit as st
import pandas as pd # 这里的 pandas 用于考试界面，Streamlit 运行必须有它
import random
import os

st.set_page_config(page_title="全题库考试系统", layout="wide")

@st.cache_data
def load_data():
    if os.path.exists("question_bank.csv"):
        try:
            return pd.read_csv("question_bank.csv").fillna("")
        except:
            return None
    return None

if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'submitted' not in st.session_state: st.session_state.submitted = False
if 'exam_questions' not in st.session_state: st.session_state.exam_questions = []

with st.sidebar:
    st.title("⚙️ 考试设置")
    df = load_data()
    if df is not None:
        st.success(f"题库已加载：共 {len(df)} 题")
        # 题型统计
        st.write(df['题型'].value_counts())
        
        sel_types = st.multiselect("题型过滤", df['题型'].unique(), default=df['题型'].unique())
        if sel_types:
            filtered = df[df['题型'].isin(sel_types)]
            num = st.number_input("题目数量", 1, len(filtered), min(20, len(filtered)))
            if st.button("开始考试", type="primary"):
                st.session_state.exam_questions = filtered.sample(n=num).to_dict('records')
                st.session_state.user_answers = {}
                st.session_state.submitted = False
                st.rerun()
    else:
        st.error("未找到 question_bank.csv")

if st.session_state.exam_questions:
    st.progress(len(st.session_state.user_answers)/len(st.session_state.exam_questions))
    with st.form("exam"):
        for i, q in enumerate(st.session_state.exam_questions):
            st.markdown(f"**{i+1}. [{q['题型']}] {q['题目']}**")
            qid = f"q_{i}"
            
            if q['题型'] == '单选':
                ops = [f"{k[-1]}. {q[k]}" for k in ['选项A','选项B','选项C','选项D','选项E','选项F'] if str(q[k]).strip()]
                st.radio("选项", ops, key=qid, label_visibility="collapsed", index=None)
            elif q['题型'] == '多选':
                for k in ['选项A','选项B','选项C','选项D','选项E','选项F']:
                    if str(q[k]).strip():
                        st.checkbox(f"{k[-1]}. {q[k]}", key=f"{qid}_{k[-1]}")
            else:
                st.text_input("答案", key=qid)
            st.divider()
        
        if st.form_submit_button("提交"):
            st.session_state.submitted = True
            st.rerun()

if st.session_state.submitted:
    st.markdown("### 结果")
    score = 0
    obj_count = 0
    for i, q in enumerate(st.session_state.exam_questions):
        correct = str(q['答案']).strip().upper().replace("，", ",")
        user_ans = "未作答"
        
        if q['题型'] == '单选':
            val = st.session_state.get(f"q_{i}")
            if val: user_ans = val[0]
            if user_ans == correct: score+=1
            obj_count += 1
            st.markdown(f"第{i+1}题: {'✅' if user_ans==correct else '❌'} (你的:{user_ans} | 正确:{correct})")
            
        elif q['题型'] == '多选':
            user_ops = []
            for k in ['A','B','C','D','E','F']:
                if st.session_state.get(f"q_{i}_{k}"): user_ops.append(k)
            if set(user_ops) == set(correct.split(',')): score+=1
            obj_count += 1
            st.markdown(f"第{i+1}题: {'✅' if set(user_ops)==set(correct.split(',')) else '❌'} (正确:{correct})")
            
        else:
            st.markdown(f"第{i+1}题 (主观题): 参考答案 -> {correct}")

    if obj_count > 0:
        st.metric("客观题得分", f"{score}/{obj_count}")
