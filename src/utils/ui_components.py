import random
from streamlit_chat import message
import streamlit as st

@st.cache_data
def choice_avatar():
    avatar_style_list =['avataaars','pixel-art-neutral','adventurer-neutral', 'big-ears-neutral']
    seed_list =[100, "Felix"] + list(range(1,140))

    avatar_style = random.choice(avatar_style_list)
    seed = random.choice(seed_list)
    return avatar_style, seed

# 메시지 카운터 변수 추가
message_counter = 0

def my_chat_message(message_txt, choiced_avatar_style, choiced_seed):
    global message_counter
    message_counter += 1
    return message(message_txt, avatar_style=choiced_avatar_style, seed=choiced_seed, key=f"message_{message_counter}")
