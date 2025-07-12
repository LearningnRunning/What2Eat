# src/utils/map_renderer.py

import pydeck as pdk
import streamlit as st


class MapRenderer:
    """지도 렌더링을 담당하는 클래스"""

    def __init__(self):
        self.default_zoom = 13
        self.default_pitch = 50

    def create_scatter_layer(self, data):
        return pdk.Layer(
            "ScatterplotLayer",
            data=data,
            get_position="[diner_lon, diner_lat]",
            get_fill_color="rgba_color",
            get_radius=100,
            pickable=True,
        )

    def render_map(self, data, center_lat, center_lon):
        layer = self.create_scatter_layer(data)
        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=self.default_zoom,
            pitch=self.default_pitch,
        )

        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"html": "<b>{diner_name}</b>({diner_category_middle})"},
        )

        return st.pydeck_chart(deck, use_container_width=True)
