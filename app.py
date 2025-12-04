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

# 세션 유지 스크립트 (1분 간격)
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
        }, 60000); 
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
st.sidebar.caption("교육생 정보를 입력하세요.")

st.sidebar.text_input("👤 이름", key="user")
st.sidebar.text_input("👤 등록번호", key="userid")
st.sidebar.text_input("👤 이메일", key="useremail")

st.sidebar.divider()

video_titles = list(VIDEO_DATA.keys())
st.sidebar.radio(
    "시청할 교육 영상을 선택하세요:",
    video_titles,
    key="selected_video_title"
)

# ---------------------
# 메인 로직 시작
# ---------------------

# 1. 현재 선택된 영상 정보 가져오기
selected_title = st.session_state.selected_video_title
video_info = VIDEO_DATA[selected_title]
current_video_id = video_info["video_id"] # 현재 화면에 떠있는 영상 ID
embed_code = video_info["embed_code"]

# 2. 🚨 핵심 기능: URL 복구 로직 (영상 ID까지 비교!)
# URL에 저장된 정보가 있는지 확인
url_saved_start = st.query_params.get("saved_start")
url_active_video = st.query_params.get("active_video") # URL에 저장된 영상 ID

# 현재 선택된 영상과 URL에 저장된 영상 ID가 *일치할 때만* 복구
if url_saved_start and url_active_video == current_video_id:
    try:
        st.session_state.start_time = float(url_saved_start)
    except:
        st.session_state.start_time = None
else:
    # 영상이 다르거나 기록이 없으면, 현재 영상에 대한 시작 시간은 없는 것임
    st.session_state.start_time = None


# ---------------------
# 메인 화면 표시
# ---------------------
user_info_complete = (
    st.session_state.get("user") and
    st.session_state.get("userid") and
    st.session_state.get("useremail")
)

if not user_info_complete:
    st.info("👈 먼저 사이드바에서 이름, 등록번호, 이메일을 모두 입력해주세요.")
else:
    st.title(f"📺 {selected_title}")
    
    # 영상 표시
    components.html(embed_code, height=510)
    # 세션 유지 실행
    components.html(SESSION_KEEP_ALIVE_SCRIPT, height=0)

    # ---------------------
    # 상태 메시지
    # ---------------------
    if st.session_state.start_time:
        seoul_tz = ZoneInfo("Asia/Seoul")
        start_dt_str = datetime.fromtimestamp(st.session_state.start_time, tz=seoul_tz).strftime("%Y-%m-%d %H:%M:%S")
        # 경고창 대신 성공 메시지로 안심시키기
        st.success(f"✅ [시청 중] 시작 시간: {start_dt_str}")
        st.caption("시청 시작 시간을 유지하고 있습니다. 종료 시 반드시 아래 '시청 종료' 버튼을 눌러주세요.")
    else:
        st.write("🔽 아래 '시청 시작' 버튼을 눌러 교육을 시작하세요.")

    st.divider()
    col1, col2 = st.columns(2)
    
    # ---------------------
    # 버튼 로직
    # ---------------------
    with col1:
        # 시작 버튼
        if st.button("▶️ 시청 시작", type="primary", key=f"start_{current_video_id}", use_container_width=True):
            current_time = time.time()
            st.session_state.start_time = current_time
            
            # 🚨 중요: 시작 시간 AND 현재 영상 ID를 함께 URL에 저장
            st.query_params["saved_start"] = str(current_time)
            st.query_params["active_video"] = current_video_id # <-- 영상 ID 저장
            
            st.rerun()

    with col2:
        # 종료 버튼
        if st.button("⏹️ 시청 종료 (기록 저장)", type="secondary", key=f"stop_{current_video_id}", use_container_width=True):
            if st.session_state.start_time:
                end_time = time.time()
                elapsed = end_time - st.session_state.start_time
                
                seoul_tz = ZoneInfo("Asia/Seoul")
                start_dt = datetime.fromtimestamp(st.session_state.start_time, tz=seoul_tz).strftime("%Y-%m-%d %H:%M:%S")
                end_dt = datetime.fromtimestamp(end_time, tz=seoul_tz).strftime("%Y-%m-%d %H:%M:%S")

                user = st.session_state.user
                userid = st.session_state.userid
                useremail = st.session_state.useremail
                
                # 구글 시트 저장 시도
                if sheet:
                    try:
                        sheet.append_row([user, userid, useremail, current_video_id, elapsed, start_dt, end_dt])
                        st.balloons() # 축하 효과
                        st.success(f"💾 저장 완료! 총 {elapsed/60:.1f}분 시청했습니다.")
                    except Exception as e:
                        st.error(f"저장 중 오류 발생: {e}")
                else:
                    st.error("구글 시트 연결 오류. 관리자에게 문의하세요.")

                # 🚨 중요: 기록 후 URL 파라미터 싹 지우기 (초기화)
                st.session_state.start_time = None
                st.query_params.clear() # URL 깨끗하게 비움
                
                time.sleep(3) # 메시지 읽을 시간 줌
                st.rerun()
                
            else:
                st.warning("⚠️ 시청 기록이 없습니다. '시청 시작'을 먼저 눌러주세요.")

    st.info("🕐 시청 시간이 50분 이상 되어야 연수 시간 1시간이 인정됩니다. (여러번 시청하는 경우 각각의 시간 누적 합산 기준 50분)")
    st.divider()
    st.info("💾 시청 로그는 시청종료 버튼 누를 때 Google Sheets에 자동 저장됩니다.")