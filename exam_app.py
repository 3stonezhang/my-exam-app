import streamlit as st
import pandas as pd
import random

# --- 1. 页面整体配置 ---
st.set_page_config(
    page_title="理论知识考试系统", 
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. 样式美化 (CSS) ---
st.markdown("""
<style>
    /* 调整主标题样式 */
    .main-title {font-size: 32px; font-weight: bold; color: #2c3e50; text-align: center; margin-bottom: 20px;}
    /* 题目样式 */
    .question-box {background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; border-left: 5px solid #4CAF50;}
    .q-type-badge {background-color: #e8f5e9; color: #2e7d32; padding: 4px 8px; border-radius: 4px; font-size: 14px; font-weight: bold; margin-right: 10px;}
    .q-text {font-size: 18px; font-weight: 600; color: #333;}
    /* 答案解析区域 */
    .answer-analysis {background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 10px; border: 1px solid #e9ecef;}
</style>
""", unsafe_allow_html=True)

# --- 3. 核心功能函数 ---
@st.cache_data
def load_excel_data(file_path):
    try:
        # 读取Excel，确保所有内容都读取为字符串，避免数字被转成浮点数
        df = pd.read_excel(file_path, dtype=str)
        df = df.fillna("") # 把空值填为空字符串
        return df
    except FileNotFoundError:
        return None

def reset_exam():
    """重置考试状态"""
    st.session_state.user_answers = {}
    st.session_state.submitted = False
    st.session_state.show_analysis = False
    st.session_state.current_seed = random.randint(1, 100000) # 用于打乱题目

# --- 4. 初始化 Session State ---
if 'user_answers' not in st.session_state: st.session_state.user_answers = {}
if 'submitted' not in st.session_state: st.session_state.submitted = False
if 'exam_subset' not in st.session_state: st.session_state.exam_subset = []
if 'current_seed' not in st.session_state: st.session_state.current_seed = 0

# --- 5. 侧边栏：设置区 ---
with st.sidebar:
    st.title("⚙️ 考试控制台")
    
    # 读取本地题库
    df = load_excel_data("question_bank.xlsx")
    
    if df is None:
        st.error("❌ 未找到 'question_bank.xlsx'")
        st.info("请先运行 generate_data.py 生成题库！")
        st.stop()
    
    # 题库统计
    type_counts = df['题型'].value_counts()
    st.write("📊 **题库概览**")
    st.dataframe(type_counts, use_container_width=True)
    
    st.divider()
    
    # 筛选设置
    st.subheader("📝 出卷设置")
    selected_types = st.multiselect(
        "选择题型",
        options=df['题型'].unique(),
        default=df['题型'].unique()
    )
    
    # 过滤数据
    filtered_df = df[df['题型'].isin(selected_types)]
    max_q = len(filtered_df)
    
    num_q = st.number_input(f"抽取题目数量 (最大 {max_q})", min_value=1, max_value=max_q, value=min(10, max_q))
    
    # 开始考试按钮
    if st.button("🚀 生成新试卷", type="primary", use_container_width=True):
        if max_q == 0:
            st.error("没有符合条件的题目！")
        else:
            # 随机抽题
            subset = filtered_df.sample(n=num_q).to_dict('records')
            st.session_state.exam_subset = subset
            reset_exam()
            st.rerun()

# --- 6. 主界面：答题区 ---
st.markdown('<div class="main-title">🎓 智能在线考试系统</div>', unsafe_allow_html=True)

if not st.session_state.exam_subset:
    st.info("👈 请在左侧侧边栏点击“生成新试卷”开始考试。")
    st.write("目前题库已自动加载，包含单选、多选、填空和简答题。")
else:
    # 进度提示
    total_q = len(st.session_state.exam_subset)
    st.caption(f"当前试卷共 {total_q} 题")
    
    # 表单区域
    with st.form(key=f"exam_form_{st.session_state.current_seed}"):
        for i, q in enumerate(st.session_state.exam_subset):
            q_type = q['题型']
            q_title = q['题目']
            q_id = f"q_{i}" # 唯一ID
            
            # 题目渲染
            st.markdown(f"""
            <div class="question-box">
                <span class="q-type-badge">{q_type}</span>
                <span class="q-text">{i+1}. {q_title}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # 选项渲染逻辑
            if q_type == '单选':
                # 收集非空的选项
                options = []
                for opt_key in ['选项A', '选项B', '选项C', '选项D', '选项E']:
                    if q[opt_key].strip():
                        # 显示格式： "A. 内容"
                        label = f"{opt_key[-1]}. {q[opt_key]}"
                        options.append(label)
                
                # 单选组件
                st.radio(
                    "请选择:", 
                    options, 
                    key=q_id, 
                    index=None, 
                    label_visibility="collapsed"
                )
                
            elif q_type == '多选':
                st.caption("（请勾选所有正确选项）")
                for opt_key in ['选项A', '选项B', '选项C', '选项D', '选项E']:
                    if q[opt_key].strip():
                        label = f"{opt_key[-1]}. {q[opt_key]}"
                        # 多选使用 checkbox，key需要区分
                        st.checkbox(label, key=f"{q_id}_{opt_key[-1]}")
                        
            elif q_type in ['填空', '简答']:
                st.text_area("请输入答案：", key=q_id, height=100)
            
            st.write("") # 增加间距

        st.divider()
        # 提交按钮
        submitted = st.form_submit_button("✅ 提交试卷", type="primary", use_container_width=True)
        if submitted:
            st.session_state.submitted = True
            st.rerun()

# --- 7. 结果分析区 ---
if st.session_state.submitted:
    st.markdown("### 📊 考试结果分析")
    
    score = 0
    auto_check_count = 0 # 能够自动判分的题目数
    
    for i, q in enumerate(st.session_state.exam_subset):
        q_type = q['题型']
        correct_ans = q['答案'].strip().upper().replace("，", ",") # 标准化答案
        user_ans_str = "未作答"
        is_correct = False
        
        st.markdown(f"**第 {i+1} 题 ({q_type})**")
        
        # --- 判分逻辑 ---
        if q_type == '单选':
            user_val = st.session_state.get(f"q_{i}")
            if user_val:
                user_ans_str = user_val[0] # 取 A. xxx 的 A
            
            if user_ans_str == correct_ans:
                score += 1
                is_correct = True
            auto_check_count += 1
            
        elif q_type == '多选':
            # 收集用户选的所有选项
            user_opts = []
            for char in ['A', 'B', 'C', 'D', 'E']:
                if st.session_state.get(f"q_{i}_{char}"):
                    user_opts.append(char)
            
            if user_opts:
                user_ans_str = ",".join(user_opts)
            
            # 集合比较 (忽略顺序)
            if set(user_opts) == set(correct_ans.split(',')):
                score += 1
                is_correct = True
            auto_check_count += 1
            
        else:
            # 主观题
            user_ans_str = st.session_state.get(f"q_{i}", "")
            # 主观题不自动计分，只展示
            is_correct = None 

        # --- 显示反馈 ---
        if is_correct is True:
            st.success("✅ 回答正确")
        elif is_correct is False:
            st.error(f"❌ 回答错误。正确答案是：{correct_ans}")
        else:
            st.warning(f"📝 主观题请自行核对。参考答案：{correct_ans}")

        # 显示解析
        if q['解析']:
            st.info(f"💡 解析：{q['解析']}")
        
        st.divider()

    # 显示总分 (仅计算客观题)
    if auto_check_count > 0:
        final_score = (score / auto_check_count) * 100
        st.markdown(f"""
        <div style="background-color:#d4edda; color:#155724; padding:20px; border-radius:10px; text-align:center;">
            <h2>客观题得分：{final_score:.1f} 分</h2>
            <p>答对 {score} / {auto_check_count} 题</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("本试卷全为主观题，请参考答案自行评分。")