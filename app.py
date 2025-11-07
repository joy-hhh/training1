import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components

# ---------------------
# 영상 정보 설정 (✅ 여기를 수정하세요)
# ---------------------
# 시청할 3개의 교육 영상 정보를 이곳에 미리 정의합니다.
# '제목'은 사이드바에 표시될 이름입니다.
# 'video_id'는 Google Sheets에 기록될 고유 ID입니다.
# 'embed_code'는 원드라이브/구글 드라이브에서 복사한 <iframe> 코드입니다.
VIDEO_DATA = {
    "동서양예술의 비교": {
        "video_id": "training_002",
        "embed_code": """
        <iframe src="https://1drv.ms/v/c/2b76dd94852a1ee2/IQTYE-nvWNdvTpXP2MToFyrPAUkHnIN4eFTWwuuZRWOIW0c?width=720&height=480" width="100%" height="500" allow="autoplay"></iframe>
        """
    },
    "세계조각 10선_상": {
        "video_id": "training_003",
        "embed_code": """
        <iframe src="https://1drv.ms/v/c/2b76dd94852a1ee2/IQSUJd3IfYdHTY2OmAPdNaWsAV4-MEVNwcdQX2TA0bUjcLc?width=720&height=480" width="100%" height="500" allow="autoplay"></iframe>
        """
    },
    "세계조각 10선_하": {
        "video_id": "training_004",
        "embed_code": """
        <!-- 🚨 중요: 이 코드를 세 번째 영상의 <iframe> 코드로 교체하세요! -->
        <iframe src="https://1drv.ms/v/c/2b76dd94852a1ee2/IQSSSGYWgw-mQIVP-fIatTnhAc0OPEkIqMT6rRlu4m3G6-A?width=720&height=480" width="100%" height="500" allow="autoplay"></iframe>
        """
    }
}


# ---------------------
# Google Sheets 연결 설정 (기존과 동일)
# ---------------------
@st.cache_resource
def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1Ce6mcwCCe4OBpJLr1RTsCnxNB8G204bA71c-idJd6qA").sheet1
    return sheet

sheet = get_sheet()

# ---------------------
# Streamlit UI 설정
# ---------------------
st.set_page_config(page_title="Video Training Tracker", page_icon="🎥", layout="wide")

# 세션 유지를 위한 JavaScript 코드 (화면에 보이지 않음)
SESSION_KEEP_ALIVE_SCRIPT = """
<script>
const streamlitDoc = window.parent.document;
const observer = new MutationObserver(function (mutations, obs) {
    const iframes = streamlitDoc.querySelectorAll('iframe[title="st.iframe"]');
    if (iframes.length > 0) {
        const streamlitIframe = iframes[0];
        setInterval(() => {
            streamlitIframe.contentWindow.postMessage({
                isStreamlitMessage: true,
                type: "setComponentValue",
                key: "keep-alive",
                value: new Date().getTime()
            }, "*");
        }, 300000); // 5분마다 신호 전송
        obs.disconnect();
    }
});
observer.observe(streamlitDoc.body, { childList: true, subtree: true });
</script>
"""

# ---------------------
# 사이드바 UI
# ---------------------
st.sidebar.title("🎥 교육 영상 시청")
st.sidebar.caption("이름, 등록번호, 이메일을 입력하세요.")

# key를 사용해 st.session_state에 자동으로 저장
st.sidebar.text_input("👤 이름", key="user")
st.sidebar.text_input("👤 등록번호", key="userid")
st.sidebar.text_input("👤 이메일", key="useremail")

st.sidebar.divider()

# VIDEO_DATA의 '제목'들을 리스트로 만들어 라디오 버튼 생성
video_titles = list(VIDEO_DATA.keys())
st.sidebar.radio(
    "시청할 교육 영상을 선택하세요:",
    video_titles,
    key="selected_video_title" # 선택된 영상 제목을 session_state에 저장
)

# ---------------------
# 메인 화면 UI
# ---------------------

# 사이드바에서 모든 정보가 입력되었는지 확인
user_info_complete = (
    st.session_state.get("user") and
    st.session_state.get("userid") and
    st.session_state.get("useremail")
)

if not user_info_complete:
    st.info("먼저 사이드바에서 이름, 등록번호, 이메일을 모두 입력하세요.")
else:
    # 1. 선택된 영상 정보 가져오기
    selected_title = st.session_state.selected_video_title
    video_info = VIDEO_DATA[selected_title]
    video_id = video_info["video_id"]
    embed_code = video_info["embed_code"]
    
    # 2. 메인 화면에 영상 표시
    st.title(f"'{selected_title}' 시청 중...")
    components.html(embed_code, height=510)
    
    # 3. 세션 유지 스크립트 실행
    components.html(SESSION_KEEP_ALIVE_SCRIPT, height=0)

    st.write("▶ 아래 버튼으로 시청 시간을 기록하세요.")

    # 4. 시청 시작/종료 버튼 로직
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("시청 시작", type="primary", key=f"start_{video_id}"):
            st.session_state.start_time = time.time()
            st.success("시청 시작 시간을 기록했습니다.")

    with col2:
        if st.button("시청 종료", type="secondary", key=f"stop_{video_id}"):
            if st.session_state.start_time:
                end_time = time.time()
                elapsed = end_time - st.session_state.start_time
                seoul_tz = ZoneInfo("Asia/Seoul")
                start_dt = datetime.fromtimestamp(st.session_state.start_time, tz=seoul_tz).strftime("%Y-%m-%d %H:%M:%S")
                end_dt = datetime.fromtimestamp(end_time, tz=seoul_tz).strftime("%Y-%m-%d %H:%M:%S")

                # Google Sheets에 현재 사용자 정보와 *선택된 video_id*를 기록
                user = st.session_state.user
                userid = st.session_state.userid
                useremail = st.session_state.useremail
                
                sheet.append_row([user, userid, useremail, video_id, elapsed, start_dt, end_dt])
                st.success(f"✅ 총 {elapsed/60:.1f}분 시청 기록이 Google Sheets에 저장되었습니다.")
                st.session_state.start_time = None
            else:
                st.warning("시청 시작 버튼을 먼저 눌러주세요.")

    st.info("🕐 시청 시간이 50분 이상 되어야 연수 시간 1시간이 인정됩니다.")
    st.divider()
    st.info("💾 시청 로그는 시청종료 버튼 누를 때 Google Sheets에 자동 저장됩니다.")