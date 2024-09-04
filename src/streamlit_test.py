import streamlit as st

# 제목
st.title("Streamlit Multiselect Example")

# 멀티셀렉트 옵션 리스트
options = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry', 'Fig', 'Grape']

# 멀티셀렉트 위젯 생성
selected_options = st.multiselect(
    'Choose your favorite fruits:', 
    options, 
    # default=['Apple', 'Banana']
)

# 선택된 옵션 출력
if selected_options:
    st.write("You selected:", selected_options)
else:
    st.write("No fruit selected.")
