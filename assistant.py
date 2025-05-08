from openai import OpenAI
from dotenv import load_dotenv
from time import sleep
import streamlit as st
import os
import datetime
import re

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
client = OpenAI(api_key=api_key, base_url=base_url)

file = client.files.create(
    file=open("final_data.json", "rb"),
    purpose='assistants'
)
vector_store = client.vector_stores.create(file_ids=[file.id], name='cluster-database')
message_history = []  
MAX_CONTEXT_MESSAGES = 5
assistant = client.beta.assistants.create(
    instructions="""A jsonl file summarizing many rare earth clusters is given to you.
    The jsonl file includes the title and DOI of the document recording the clusters,
    the formula of the clusters, the synthesis process, and their CCDC numbers (optional).
    Please answer the user's questions based on the jsonl file, do not need return the file name in the end.""",
    model="gpt-4o",
    tools=[{"type": 'file_search'}],
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
)

def write_log(txt):
    try:
        # 获取当前时间并格式化为字符串
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 确保日志目录存在
        log_dir = os.path.dirname('./chatbot_log.txt')
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # 写入带时间戳的日志
        with open('./chatbot_log.txt', 'a', encoding='gb18030') as f:
            log_entry = f"[{timestamp}] {txt}\n"  # 添加换行符确保每条日志独立一行
            f.write(log_entry)
    except UnicodeEncodeError:
        # 如果GB18030编码失败，尝试UTF-8作为备选
        try:
            with open('./chatbot_log.txt', 'a', encoding='utf-8') as f:
                log_entry = f"[{timestamp}] {txt}\n"
                f.write(log_entry)
        except Exception as e:
            print(f"无法写入日志文件(UTF-8回退失败): {str(e)}")
    except Exception as e:
        print(f"无法写入日志文件: {str(e)}")

def get_assistant_response(prompt):
    messages = []
    for msg in message_history[-MAX_CONTEXT_MESSAGES:]:
            messages.append(msg)
    messages.append({"role": "user", "content": prompt})

    try:
        thread = client.beta.threads.create()
        client.beta.threads.messages.create(thread_id=thread.id, role='user', content=prompt)
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)

        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == 'completed':
                break
            elif run_status.status == 'failed':
                return "Run failed."
            sleep(1)

        messages = client.beta.threads.messages.list(thread_id=thread.id)
        try:
            output_message = messages.data[0].content[0].text.value
            pattern = r'【\d+[:†].+?】'
            text = re.sub(pattern, '', output_message)
            output_message = text.strip()
            message_history.append({"role": "assistant", "content": output_message})
            write_log(prompt + '\n' + output_message)
        except Exception as e:
            return str(e)
        return output_message

    except Exception as e:
        return f"Error: {str(e)}"

def render_mixed_content(content):
    parts = re.split(r'(\\?\\text\{.*?\}|\\?\\[a-zA-Z]+\{.*?\}|\$.*?\$)', content)
    html_content = ""
    for part in parts:
        if not part:
            continue
            
        if (part.startswith('$') and part.endswith('$')) or \
           ('\\text' in part) or \
           ('\\' in part and '{' in part and '}' in part):
            if html_content:
                st.markdown(bubble_html(html_content), unsafe_allow_html=True)
                html_content = ""
            if part.startswith('$') and part.endswith('$'):
                st.latex(part.strip('$'))
            else:
                st.markdown(f"`{part}`", unsafe_allow_html=True)
        else:
            html_content += part.replace('\n', '<br>')
    if html_content:
        st.markdown(bubble_html(html_content), unsafe_allow_html=True)

def bubble_html(text):
    return f"""
    <div style="font-size: 16px; padding: 10px; border-radius: 10px; background-color: #f0f2f6; margin: 5px 0;">
        {text}
    </div>
    """
