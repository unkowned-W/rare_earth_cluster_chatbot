import streamlit as st
from assistant import get_assistant_response, render_mixed_content
from Visualization import VisualizeCIF
st.set_page_config(page_title="Rare_Earth_Cluster Chatbot", page_icon="💬")
'''稀土团簇合成数据机器人'''
st.markdown("""
    <style>
        .chat-container {
            max-width: 700px;
            margin: auto;
        }
        .chat-bubble {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: inline-block;
            max-width: 80%;
        }
        .user {
            background-color: #0078ff;
            color: white;
            align-self: flex-end;
        }
        .assistant {
            background-color: #f1f1f1;
            color: black;
            align-self: flex-start;
        }
    </style>
""", unsafe_allow_html=True)
    
if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "你好！我是稀土团簇合成小助手！"}]
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    
for message in st.session_state.messages:
    role_class = "user" if message["role"] == "user" else "assistant"
    st.markdown(f"""
        <div class='chat-bubble {role_class}'>
            {message["content"]}
        </div>
    """, unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
    
    # 用户输入框和发送按钮
with st.form("chat_form_1", clear_on_submit=True):
    user_input = st.text_input("请输入消息：", key="user_input_1")
    submit_button_1 = st.form_submit_button("发送")
if submit_button_1 and user_input:
    # 记录用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    # 显示用户消息
    st.markdown(f"""
        <div class='chat-bubble user'>
            {user_input}
        </div>
    """, unsafe_allow_html=True)
        
    try:
        content = get_assistant_response(user_input)
        render_mixed_content(content) #格式化输出
        st.session_state.messages.append({"role": "assistant", "content": content})  
    except Exception as e:
        st.error(f"发生错误: {e}")

st.markdown("上传 CIF 文件，查看晶体结构的 3D 模型")
uploaded_file = st.file_uploader("选择 CIF 文件", type=["cif"], key="file_uploader")
if uploaded_file:
    cif_data = uploaded_file.getvalue().decode("utf-8")
    st.success(f"已上传文件: {uploaded_file.name}")
    with st.expander("查看 CIF 文件内容"):
        st.code(cif_data)
    if st.button("开始可视化"):
        visualizer = VisualizeCIF(cif_data=cif_data)
        with st.spinner("生成 3D 模型中..."):
            visualizer.run()
