import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components
from config.constants import (
    DEFAULT_ADDRESS_INFO_LIST,
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
    pick_random_diners,
    search_menu,
    select_radius,
)
from utils.geolocation import geocode, search_your_address
from utils.ui_components import choice_avatar, display_results, my_chat_message
from config.constants import GOOGLE_ANALYTIC_ID, MICROSOFT_CLARITY_ID

script = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GOOGLE_ANALYTIC_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GOOGLE_ANALYTIC_ID}');
</script>

<!-- Microsoft Clarity -->
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){{
        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments);}};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    }})(window, document, "clarity", "script", "{MICROSOFT_CLARITY_ID}");
</script>
"""

components.html(script, height=0)


# ─────────────────────────────────────────────────────────────
# 0. Fragment 재실행 여부를 확인하기 위한 session_state 설정
# ─────────────────────────────────────────────────────────────
if "app_runs" not in st.session_state:
    st.session_state.app_runs = 0
if "fragment_runs" not in st.session_state:
    st.session_state.fragment_runs = 0


# ─────────────────────────────────────────────────────────────
# 1. 기존 SessionState, SearchManager, MapRenderer 등 원본 그대로
# ─────────────────────────────────────────────────────────────
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
            # 챗봇 관련 상태 추가
            "chat_step": "greeting",
            "avatar_style": None,
            "seed": None,
            "df_filtered": None,
            "radius_kilometers": None,
            "radius_distance": None,
            "search_option": None,
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


@st.dialog("음식점 위치")
def show_restaurant_map(restaurant):
    """음식점 상세정보와 위치를 보여주는 다이얼로그"""
    # 음식점 상세 정보 표시
    num_address = restaurant.get("diner_num_address", None)
    road_address = restaurant.get("diner_road_address", None)

    st.subheader(f"🏪 {restaurant['diner_name']}")
    if num_address:
        st.write(f"📍 {num_address}")
    if road_address:
        st.write(f"📍 {road_address}")

    if restaurant["diner_menu_name"]:
        st.write(f"🍴 메뉴: {'/'.join(restaurant['diner_menu_name'][:5])}")
    if restaurant["diner_tag"]:
        st.write(f"🏷️ 태그: {'/'.join(restaurant['diner_tag'][:5])}")

    st.write("---")

    # 현재 위치 확인
    if "user_lat" not in st.session_state or "user_lon" not in st.session_state:
        location = streamlit_geolocation()
        if location["latitude"] is not None and location["longitude"] is not None:
            st.session_state.user_lat = location["latitude"]
            st.session_state.user_lon = location["longitude"]
        else:
            st.session_state.user_lat = DEFAULT_ADDRESS_INFO_LIST[2]
            st.session_state.user_lon = DEFAULT_ADDRESS_INFO_LIST[1]

    # 현재 위치와 음식점 위치를 포함하는 데이터 생성
    map_data = pd.DataFrame({
        "lat": [st.session_state.user_lat, restaurant["diner_lat"]],
        "lon": [st.session_state.user_lon, restaurant["diner_lon"]],
        "name": ["현재 위치", restaurant["diner_name"]],
        "color": [[0, 0, 255], [255, 0, 0]],  # 파란색(현재위치), 빨간색(음식점)
    })

    # 지도 설정
    view_state = pdk.ViewState(
        latitude=(st.session_state.user_lat + restaurant["diner_lat"]) / 2,
        longitude=(st.session_state.user_lon + restaurant["diner_lon"]) / 2,
        zoom=11,
        pitch=50,
    )

    # 레이어 설정
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius=50,
        pickable=True,
        radiusScale=2,
    )

    # 지도 렌더링
    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{name}"},
        map_style="mapbox://styles/mapbox/light-v10",
    )

    st.pydeck_chart(deck, use_container_width=True)
    if st.button("닫기"):
        st.session_state.show_map = False
        st.session_state.selected_restaurant = None
        st.rerun()


@st.cache_resource
def get_session_state():
    """세션 상태 인스턴스 반환"""
    return SessionState()


def select_location():
    option = st.radio(
        "위치를 선택하세요",
        ("키워드로 검색으로 찾기(강남역 or 강남대로 328)", "주변에서 찾기"),
    )
    if option == "주변에서 찾기":
        with st.spinner("📍 현재 위치를 찾는 중입니다..."):
            location = streamlit_geolocation()
            if location["latitude"] is not None or location["longitude"] is not None:
                st.session_state.user_lat, st.session_state.user_lon = (
                    location["latitude"],
                    location["longitude"],
                )
                st.session_state.address = geocode(
                    st.session_state.user_lon, st.session_state.user_lat
                )
                st.success("✅ 위치를 찾았습니다!")
                st.rerun()
            # else:
            #     st.error("❌ 위치를 찾을 수 없습니다. 기본 위치로 설정됩니다.")
            #     st.session_state.address = DEFAULT_ADDRESS_INFO_LIST[0]
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


@st.dialog("위치 변경")
def change_location():
    """위치 변경을 위한 다이얼로그"""

    user_lat, user_lon, address = select_location()
    st.session_state.user_lat, st.session_state.user_lon, st.session_state.address = (
        user_lat,
        user_lon,
        address,
    )

    return user_lat, user_lon, address


# ─────────────────────────────────────────────────────────────
# 2. What2EatApp 클래스 (원본) ─ ranking_page, chat_page 제공
# ─────────────────────────────────────────────────────────────
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
        # 현재 위치 표시 및 수정 옵션
        st.subheader("📍 현재 위치")
        if "address" not in st.session_state:
            change_location()
        else:
            st.write(st.session_state.address)
            if st.button("위치 변경"):
                change_location()

        # 쩝슐랭 등급 선택
        st.subheader("🏅 쩝슐랭 등급 선택")
        selected_grades = st.multiselect(
            "보고 싶은 쩝슐랭 등급을 선택하세요 (다중 선택 가능)",
            options=["🌟", "🌟🌟", "🌟🌟🌟"],
            default=["🌟🌟🌟"],
        )
        selected_grade_values = [GRADE_MAP[grade] for grade in selected_grades]

        # 지역 선택
        self.df_diner[["city", "region"]] = (
            self.df_diner["diner_num_address"]
            .str.split(" ", n=2, expand=True)
            .iloc[:, :2]
        )

        ZONE_LIST = list(self.df_diner["city"].unique())
        zone = st.selectbox("지역을 선택하세요", ZONE_LIST, index=0)
        selected_zone_all = f"{zone} 전체"

        # 선택한 지역의 데이터 필터링
        filtered_zone_df = self.df_diner[self.df_diner["city"] == zone]

        # 상세 지역 선택
        city_options = list(filtered_zone_df["region"].dropna().unique())
        city_label = st.selectbox(
            "상세 지역을 선택하세요", [selected_zone_all] + city_options
        )

        if city_label:
            filtered_zone_df["diner_category_large"] = filtered_zone_df[
                "diner_category_large"
            ].fillna("기타")
            if city_label == selected_zone_all:
                filtered_city_df = filtered_zone_df
            else:
                filtered_city_df = filtered_zone_df[
                    filtered_zone_df["region"] == city_label
                ]

            # 중간 카테고리 선택 및 필터링
            available_categories = filtered_city_df["diner_category_large"].unique()
            selected_category = st.selectbox(
                "중간 카테고리를 선택하세요", ["전체"] + list(available_categories)
            )

            if selected_category != "전체":
                filtered_city_df = filtered_city_df[
                    filtered_city_df["diner_category_large"] == selected_category
                ]

            # 세부 카테고리 선택 및 필터링
            available_small_categories = (
                filtered_city_df["diner_category_middle"].fillna("기타").unique()
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
            # 수정: 복사본을 만들고 fillna 적용
            filtered_city_df_copy = filtered_city_df.copy()
            filtered_city_df_copy["diner_category_middle"] = filtered_city_df_copy[
                "diner_category_middle"
            ].fillna(filtered_city_df_copy["diner_category_large"])

            ranked_df = filtered_city_df_copy.sort_values(
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
                    "diner_num_address",
                    # 'diner_road_address',
                    "region",
                ]
            ]

            if not ranked_df.empty:
                # 지도 다이얼로그를 위한 상태 추가
                if "show_map" not in st.session_state:
                    st.session_state.show_map = False
                if "selected_restaurant" not in st.session_state:
                    st.session_state.selected_restaurant = None

                # 음식점 목록을 카드 형태로 표시
                ranked_df = ranked_df[:100]
                for _, row in ranked_df.iterrows():
                    with st.container():
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col1:
                            st.write(grade_to_stars(row["diner_grade"]))
                        with col2:
                            st.write(
                                f"**[{row['diner_name']}]({row['diner_url']})** | {row['diner_category_middle']} | {row['region']}"
                            )
                        with col3:
                            if st.button("상세정보", key=f"map_{row['diner_name']}"):
                                st.session_state.show_map = True
                                st.session_state.selected_restaurant = row
                                show_restaurant_map(
                                    st.session_state.selected_restaurant
                                )
                        st.divider()

            else:
                st.warning("해당 조건의 랭킹 데이터가 없습니다.")

    def chat_page(self):
        # 아바타 선택 및 초기화
        if st.session_state.avatar_style is None:
            st.session_state.avatar_style, st.session_state.seed = choice_avatar()

        avatar_style = st.session_state.avatar_style
        seed = st.session_state.seed

        # 단계 1: 인사 및 위치 확인
        if st.session_state.chat_step == "greeting":
            my_chat_message("안녕! 오늘 머먹?", avatar_style, seed)

            if "address" not in st.session_state:
                change_location()

            my_chat_message(
                f"{st.session_state.address} 근처에서 찾아볼게! 만약 다른 위치에서 찾고 싶다면 아래 버튼을 눌러!",
                avatar_style,
                seed,
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("위치 변경", use_container_width=True):
                    change_location()
            with col2:
                if st.button("다음 단계로", use_container_width=True):
                    st.session_state.chat_step = "select_radius"
                    st.rerun()

        # 단계 2: 반경 선택
        elif st.session_state.chat_step == "select_radius":
            my_chat_message("어디까지 갈겨?", avatar_style, seed)
            radius_kilometers, radius_distance = select_radius(avatar_style, seed)

            # 반경 내 데이터 필터링
            df_geo_filtered = get_filtered_data(
                self.df_diner, st.session_state.user_lat, st.session_state.user_lon
            )

            df_geo_filtered = df_geo_filtered[(df_geo_filtered["diner_grade"].notna())]

            # diner_grade 값 확인 (1 이상인지)
            df_quality = df_geo_filtered[df_geo_filtered["diner_grade"] >= 1]

            # 찐맛집(diner_grade >= 1)이 있는지 확인
            if len(df_quality) == 0:
                my_chat_message(
                    "찐맛집이 근처에 없어... 😢\n반경을 좀 더 넓게 설정해볼까?",
                    avatar_style,
                    seed,
                )
                return

            df_geo_filtered = df_quality

            if len(df_geo_filtered):
                df_geo_filtered_radius = df_geo_filtered[
                    df_geo_filtered["distance"] <= radius_kilometers
                ]
                st.session_state.df_filtered = df_geo_filtered_radius[
                    df_geo_filtered_radius["bayesian_score"].notna()
                ]

                if len(st.session_state.df_filtered):
                    radius_col1, radius_col2 = st.columns([2, 1])
                    with radius_col2:
                        if st.session_state.chat_step != "greeting":
                            if st.button("처음으로"):
                                st.session_state.chat_step = "greeting"
                                st.rerun()
                    with radius_col1:
                        if st.button("다음 단계로", use_container_width=True):
                            st.session_state.chat_step = "search_method"
                            st.rerun()
                else:
                    my_chat_message(
                        "헉.. 이 반경에는 찐맛집이 없네..😢\n다른 반경을 선택해볼까?",
                        avatar_style,
                        seed,
                    )
            else:
                my_chat_message(
                    "헉.. 주변에 맛집이 없대.. \n다른 위치를 찾아볼까?",
                    avatar_style,
                    seed,
                )
                if st.button("위치 다시 선택하기", use_container_width=True):
                    st.session_state.chat_step = "greeting"
                    st.rerun()

        # 단계 3: 검색 방법 선택
        elif st.session_state.chat_step == "search_method":
            search_option = st.radio(
                "검색 방법을 선택하세요",
                ("카테고리로 찾기", "메뉴로 찾기", "랜덤 추천 받기"),
                index=0,
            )

            if st.button("선택 완료", use_container_width=True):
                st.session_state.search_option = search_option
                st.session_state.chat_step = "search"
                st.rerun()

        # 단계 4: 검색 실행
        elif st.session_state.chat_step == "search":
            if st.session_state.search_option == "메뉴로 찾기":
                menu_search = st.text_input("찾고 싶은 메뉴를 입력하세요")
                if menu_search:
                    df_menu_filtered = st.session_state.df_filtered[
                        st.session_state.df_filtered.apply(
                            lambda row: search_menu(row, menu_search), axis=1
                        )
                    ]
                    display_results(
                        df_menu_filtered,
                        st.session_state.radius_kilometers,
                        st.session_state.radius_distance,
                        avatar_style,
                        seed,
                    )

            elif st.session_state.search_option == "랜덤 추천 받기":
                if st.button("랜덤 뽑기", use_container_width=True):
                    result = self.search_manager.get_random_recommendations(
                        st.session_state.df_filtered
                    )
                    if result:
                        show_restaurant_map(result)

            else:  # 카테고리로 찾기
                my_chat_message("뭐 먹을겨?", avatar_style, seed)
                diner_category_lst = list(
                    st.session_state.df_filtered["diner_category_large"].unique()
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
                            st.session_state.df_filtered,
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
                                    st.session_state.radius_kilometers,
                                    st.session_state.radius_distance,
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
        # 검색 초기화 버튼
        if st.session_state.chat_step not in [
            "greeting",
            "select_radius",
            "search_method",
        ]:
            if st.button("처음부터 다시 찾기"):
                st.session_state.chat_step = "greeting"
                st.rerun()


# ─────────────────────────────────────────────────────────────
# 3. fragment로 나눈 뒤, 내부에서 해당 페이지 함수만 호출
# ─────────────────────────────────────────────────────────────
@st.fragment
def chat_page_fragment(app: What2EatApp):
    """chat_page 부분만 부분 재실행"""
    st.session_state.fragment_runs += 1
    app.chat_page()


@st.fragment
def ranking_page_fragment(app: What2EatApp):
    """ranking_page 부분만 부분 재실행"""
    st.session_state.fragment_runs += 1
    app.ranking_page()


# ─────────────────────────────────────────────────────────────
# 4. 메인 진입점 ─ 페이지 전환 & fragment 호출
# ─────────────────────────────────────────────────────────────
def main():
    # 전체 앱 실행 횟수 카운트
    st.session_state.app_runs += 1
    st.set_page_config(
        page_title="머먹?",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.logo(
        link="https://what2eat-chat.streamlit.app/",
        image=LOGO_SMALL_IMG_PATH,
        icon_image=LOGO_TITLE_IMG_PATH,
    )

    app = What2EatApp()

    # 사이드바에서 페이지 선택
    selected_page = st.sidebar.radio(
        "페이지 선택", ["🤤 오늘 머먹?", "🕺🏽 니가 가본 그집"]
    )

    # 선택된 페이지에 따라 해당 함수 호출
    if selected_page == "🤤 오늘 머먹?":
        chat_page_fragment(app)
    else:
        ranking_page_fragment(app)


if __name__ == "__main__":
    main()
