import pydeck as pdk
import streamlit as st
from config.constants import (
    DEFAULT_ADDRESS_INFO_LIST,
    GRADE_COLORS,
    GRADE_MAP,
    GUIDE_IMG_PATH,
    LOGO_IMG_PATH,
    LOGO_SMALL_IMG_PATH,
    LOGO_TITLE_IMG_PATH,
    PRIORITY_ORDER,
)
from streamlit_geolocation import streamlit_geolocation
from utils.data_loading import load_static_data
from utils.data_processing import (
    category_filters,
    get_filtered_data,
    grade_to_stars,
    hex_to_rgba,
    pick_random_diners,
    search_menu,
    select_radius,
)
from utils.geolocation import geocode, search_your_address
from utils.ui_components import choice_avatar, display_results, my_chat_message


class SessionState:
    """세션 상태를 관리하는 클래스"""

    def __init__(self):
        self.states = {
            "generated": [],
            "past": [],
            "user_lat": DEFAULT_ADDRESS_INFO_LIST[2],
            "user_lon": DEFAULT_ADDRESS_INFO_LIST[1],
            "address": DEFAULT_ADDRESS_INFO_LIST[0],
            "result_queue": [],
            "previous_category_small": [],
            "consecutive_failures": 0,
        }

    def initialize(self):
        """세션 상태 초기화"""
        for key, default_value in self.states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value


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


@st.cache_resource
def get_session_state():
    """세션 상태 인스턴스 반환"""
    return SessionState()


def select_location():
    option = st.radio(
        "위치를 선택하세요",
        ("주변에서 찾기", "키워드로 검색으로 찾기(강남역 or 강남대로 328)"),
    )
    if option == "주변에서 찾기":
        location = streamlit_geolocation()
        if location["latitude"] is not None or location["longitude"] is not None:
            st.session_state.user_lat, st.session_state.user_lon = (
                location["latitude"],
                location["longitude"],
            )
            st.session_state.address = geocode(
                st.session_state.user_lon, st.session_state.user_lat
            )
        else:
            st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]
    elif option == "키워드로 검색으로 찾기(강남역 or 강남대로 328)":
        search_your_address()
    return (
        st.session_state.user_lat,
        st.session_state.user_lon,
        st.session_state.address,
    )


@st.cache_data
def load_app_data():
    """앱 데이터 로딩을 위한 독립 함수"""
    df_diner, _, _, _ = load_static_data(
        LOGO_IMG_PATH, LOGO_TITLE_IMG_PATH, GUIDE_IMG_PATH
    )
    df_diner.rename(columns={"index": "diner_idx"}, inplace=True)
    return df_diner


class What2EatApp:
    """What2Eat 앱의 메인 클래스"""

    def __init__(self):
        self.session_state = get_session_state()
        self.session_state.initialize()
        self.map_renderer = MapRenderer()
        self.df_diner = load_app_data()
        self.search_manager = SearchManager(self.df_diner)

    def ranking_page(self):
        st.title("지역별 카테고리 랭킹")

        # 쩝슐랭 등급 선택
        st.subheader("🏅 쩝슐랭 등급 선택")
        selected_grades = st.multiselect(
            "보고 싶은 쩝슐랭 등급을 선택하세요 (다중 선택 가능)",
            options=["🌟", "🌟🌟", "🌟🌟🌟"],
            default=["🌟🌟🌟"],
        )

        # 선택한 등급 숫자로 매핑
        selected_grade_values = [GRADE_MAP[grade] for grade in selected_grades]

        # 지역 선택
        self.df_diner[["city", "region"]] = (
            self.df_diner["diner_num_address"]
            .str.split(" ", n=2, expand=True)
            .iloc[:, :2]
        )
        ZONE_LIST = sorted(list(self.df_diner["city"].unique()))
        zone = st.selectbox("지역을 선택하세요", ZONE_LIST, index=4)
        selected_zone_all = f"{zone} 전체"

        # 선택한 지역의 데이터 필터링
        filtered_zone_df = self.df_diner[self.df_diner["city"] == zone]

        # 상세 지역 선택
        city_options = list(filtered_zone_df["region"].dropna().unique())
        city_label = st.selectbox(
            "상세 지역을 선택하세요", [selected_zone_all] + city_options
        )

        if city_label:
            if city_label == selected_zone_all:
                filtered_city_df = filtered_zone_df
            else:
                filtered_city_df = filtered_zone_df[
                    filtered_zone_df["region"] == city_label
                ]

            # 중간 카테고리 선택 및 필터링
            available_categories = (
                filtered_city_df["diner_category_large"].dropna().unique()
            )
            selected_category = st.selectbox(
                "중간 카테고리를 선택하세요", ["전체"] + list(available_categories)
            )

            if selected_category != "전체":
                filtered_city_df = filtered_city_df[
                    filtered_city_df["diner_category_large"] == selected_category
                ]

            # 세부 카테고리 선택 및 필터링
            available_small_categories = (
                filtered_city_df["diner_category_middle"].dropna().unique()
            )
            selected_small_category = st.selectbox(
                "세부 카테고리를 선택하세요",
                ["전체"] + list(available_small_categories),
            )

            if selected_small_category != "전체":
                filtered_city_df = filtered_city_df[
                    filtered_city_df["diner_category_middle"] == selected_small_category
                ]

            # 쩝슐랭 등급 필터링
            filtered_city_df = filtered_city_df[
                filtered_city_df["diner_grade"].isin(selected_grade_values)
            ]

            # 세부 카테고리별 랭킹 표시
            st.subheader(
                f"{selected_category if selected_category != '전체' else '전체 중간 카테고리'} 카테고리 ({selected_small_category if selected_small_category != '전체' else '전체'}) 랭킹"
            )
            filtered_city_df["diner_category_middle"].fillna(
                filtered_city_df["diner_category_large"], inplace=True
            )

            ranked_df = filtered_city_df.sort_values(
                by="bayesian_score", ascending=False
            )[
                [
                    "diner_name",
                    "diner_url",
                    "diner_category_middle",
                    "diner_grade",
                    "diner_lat",
                    "diner_lon",
                    "diner_menu_name",
                    "diner_tag",
                ]
            ]

            center_latitude, center_longitude = (
                ranked_df.iloc[0, 4],
                ranked_df.iloc[0, 5],
            )
            # 각 음식점의 핀 정보 생성
            ranked_df["color"] = ranked_df["diner_grade"].map(GRADE_COLORS)
            ranked_df["rgba_color"] = ranked_df["color"].apply(lambda x: hex_to_rgba(x))

            data_for_map = ranked_df[
                [
                    "diner_lat",
                    "diner_lon",
                    "diner_name",
                    "rgba_color",
                    "diner_category_middle",
                ]
            ]

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=data_for_map,
                get_position="[diner_lon, diner_lat]",
                get_fill_color="rgba_color",  # RGBA 값으로 접근
                get_radius=100,
                pickable=True,
            )

            view_state = pdk.ViewState(
                latitude=center_latitude, longitude=center_longitude, zoom=13, pitch=50
            )
            # 지도 렌더링
            map_deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"html": "<b>{diner_name}</b>({diner_category_middle})"},
            )

            # Pydeck을 사용하여 지도 렌더링 및 상호작용 결과 확인
            st.pydeck_chart(map_deck, use_container_width=True)
            # 데이터프레임 표시
            st.dataframe(
                ranked_df[
                    [
                        "diner_grade",
                        "diner_name",
                        "diner_category_middle",
                        "diner_url",
                        "diner_menu_name",
                        "diner_tag",
                    ]
                ].rename(
                    columns={
                        "diner_name": "음식점명",
                        "diner_category_middle": "세부 카테고리",
                        "diner_url": "카카오맵링크",
                        "diner_menu_name": "메뉴",
                        "diner_tag": "해시태그",
                        "diner_grade": "쩝슐랭",
                    }
                ),
                use_container_width=True,
            )

    def chat_page(self):
        # 아바타 선택 및 초기 메시지
        avatar_style, seed = choice_avatar()
        my_chat_message("안녕! 오늘 머먹?", avatar_style, seed)
        # my_chat_message(
        #     "잠깐! AI 머먹을 시험 시행 중이야 한번 써볼래? \n [AI 머먹 이용하기](https://laas.wanted.co.kr/sandbox/share?project=PROMPTHON_PRJ_463&hash=f11097aa25dde2ef411ac331f47c1a3d1199331e8c4d10adebd7750576f442ff)",
        #     avatar_style,
        #     seed,
        # )

        # 메인 로직
        user_lat, user_lon, user_address = select_location()
        my_chat_message(user_address, avatar_style, seed)

        # 최대 반경 10km로 데이터 필터링 (캐시 사용)
        df_geo_filtered = get_filtered_data(self.df_diner, user_lat, user_lon)

        if len(df_geo_filtered):
            my_chat_message("어디까지 갈겨?", avatar_style, seed)

            radius_kilometers, radius_distance = select_radius(avatar_style, seed)

            # 선택된 반경으로 다시 필터링
            df_geo_filtered_radius = df_geo_filtered[
                df_geo_filtered["distance"] <= radius_kilometers
            ]
            df_geo_filtered_real_review = df_geo_filtered_radius[
                df_geo_filtered_radius["bayesian_score"].notna()
            ]
            # df_geo_filtered_real_review = df_geo_filtered_radius.query(f"(diner_review_avg >= diner_review_avg) and (real_good_review_cnt >= 5)")

            search_option = st.radio(
                "검색 방법을 선택하세요",
                ("카테고리로 찾기", "메뉴로 찾기", "랜덤 추천 받기"),
                index=0,
            )  # , '추천 받기'
            # diner_nearby_cnt = len(df_geo_filtered)
            if search_option == "메뉴로 찾기":
                menu_search = st.text_input("찾고 싶은 메뉴를 입력하세요")
                if menu_search:
                    df_menu_filtered = df_geo_filtered_real_review[
                        df_geo_filtered_real_review.apply(
                            lambda row: search_menu(row, menu_search), axis=1
                        )
                    ]
                    display_results(
                        df_menu_filtered,
                        radius_kilometers,
                        radius_distance,
                        avatar_style,
                        seed,
                    )
            elif search_option == "랜덤 추천 받기":
                # 버튼 클릭 시 처리
                if st.button("랜덤 뽑기"):
                    if not st.session_state.result_queue:
                        # 새로 5개를 뽑아서 큐에 저장
                        new_results = pick_random_diners(
                            df_geo_filtered_real_review, num_to_select=5
                        )
                        if new_results is None:
                            st.error(
                                "추천할 레스토랑이 더 이상 없습니다. 다시 시도해주세요!"
                            )
                        else:
                            st.session_state.result_queue.extend(
                                new_results.to_dict(orient="records")
                            )

                    # 큐에서 하나를 꺼내기
                    if st.session_state.result_queue:
                        result = st.session_state.result_queue.pop(
                            0
                        )  # 큐에서 첫 번째 항목 제거
                        if result is None:
                            my_chat_message(
                                "야, 추천할 레스토랑이 더 이상 없어. 다른 옵션 골라보거나 한 번 더 눌러봐!",
                                avatar_style,
                                seed,
                            )

                            st.error("추천할 레스토랑이 없어!")
                        else:
                            diner_name = result["diner_name"]
                            diner_category_middle = result["diner_category_middle"]
                            diner_url = result["diner_url"]
                            diner_grade = result["diner_grade"]
                            diner_tag = result["diner_tag"]
                            diner_menu = result["diner_menu_name"]
                            diner_distance = round(result["distance"] * 1000, 2)

                            introduction = (
                                f"✨ **입벌려! 추천 들어간다** ✨\n\n"
                                f"📍 [{diner_name}]({diner_url}) ({diner_category_middle})\n"
                                f"🗺️ 여기서 대략 **{diner_distance}m** 떨어져 있어.\n\n"
                            )

                            introduction += f"{grade_to_stars(diner_grade)}\n\n"

                            if diner_tag:
                                introduction += (
                                    f"🔑 **주요 키워드**: {'/'.join(diner_tag)}\n"
                                )
                            if diner_menu:
                                introduction += (
                                    f"🍴 **주요 메뉴**: {'/'.join(diner_menu[:10])}\n"
                                )

                            introduction += "\n가서 맛있게 먹고 와! 😋"

                            my_chat_message(introduction, avatar_style, seed)
            else:
                my_chat_message("뭐 먹을겨?", avatar_style, seed)
                diner_category_lst = list(
                    df_geo_filtered_real_review["diner_category_large"].unique()
                )

                sorted_diner_category_lst = sorted(
                    diner_category_lst, key=lambda x: PRIORITY_ORDER.get(x, 3)
                )

                if sorted_diner_category_lst:
                    diner_category = st.multiselect(
                        label="첫번째 업태",
                        options=sorted_diner_category_lst,
                        label_visibility="hidden",
                    )
                    if bool(diner_category):
                        df_geo_mid_category_filtered = category_filters(
                            diner_category,
                            df_geo_filtered_real_review,
                            df_geo_filtered_radius,
                        )
                        if len(df_geo_mid_category_filtered):
                            my_chat_message(
                                "세부 업종에서 안 당기는 건 빼!", avatar_style, seed
                            )
                            unique_categories = (
                                df_geo_mid_category_filtered["diner_category_middle"]
                                .unique()
                                .tolist()
                            )
                            selected_category = st.multiselect(
                                label="세부 카테고리",
                                options=unique_categories,
                                default=unique_categories,
                            )
                            if selected_category:
                                df_geo_small_category_filtered = (
                                    df_geo_mid_category_filtered[
                                        df_geo_mid_category_filtered[
                                            "diner_category_middle"
                                        ].isin(selected_category)
                                    ].sort_values(by="bayesian_score", ascending=False)
                                )
                                display_results(
                                    df_geo_small_category_filtered,
                                    radius_kilometers,
                                    radius_distance,
                                    avatar_style,
                                    seed,
                                )
                else:
                    my_chat_message(
                        "헉.. 주변에 찐맛집이 없대.. \n 다른 메뉴를 골라봐",
                        avatar_style,
                        seed,
                    )
        else:
            my_chat_message(
                "헉.. 주변에 맛집이 없대.. \n 다른 위치를 찾아봐", avatar_style, seed
            )

    def run(self):
        search = st.Page(self.chat_page(), title="오늘 머먹?", icon="🧑‍🍳")
        ranking = st.Page(self.ranking_page(), title="니가 가본 그집", icon="🏠")

        home = [search, ranking]

        pg = st.navigation({"Home": home})
        pg.run()


if __name__ == "__main__":
    st.set_page_config(page_title="머먹?", page_icon=LOGO_SMALL_IMG_PATH, layout="wide")
    app = What2EatApp()
    app.run()
