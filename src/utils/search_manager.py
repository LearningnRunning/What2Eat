# src/utils/search_manager.py

import streamlit as st

from utils.data_processing import pick_random_diners, search_menu


class SearchManager:
    """검색 관련 기능을 담당하는 클래스"""

    def __init__(self, df):
        self.df = df

    def search_by_menu(self, menu_search, filtered_df):
        return filtered_df[
            filtered_df.apply(lambda row: search_menu(row, menu_search), axis=1)
        ]

    def get_random_recommendations(self, filtered_df, num_to_select=5):
        if not st.session_state.result_queue:
            new_results = pick_random_diners(filtered_df, num_to_select)
            if new_results is not None:
                st.session_state.result_queue.extend(
                    new_results.to_dict(orient="records")
                )
        return (
            st.session_state.result_queue.pop(0)
            if st.session_state.result_queue
            else None
        )
