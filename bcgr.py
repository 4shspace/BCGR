import streamlit as st
import google.generativeai as genai
import pandas as pd
import io
from openpyxl.styles import Alignment, Font # openpyxl 스타일링을 위해 추가
import os # 환경 변수 사용을 위해 추가

# 학생 특성 목록 (카테고리별 분리 - 키워드 추가됨)
CATEGORIES = {
    "성격 및 태도": [
        "책임감", "성실성", "자기주도성", "인내심", "끈기", "용기", "겸손", "절제력", "솔직함", "정직성",
        "꾸준함", "침착함", "열정", "주의집중력", "신중함", "유연성", "도전정신", "자기통제력", "추진력", "집중력",
        "긍정적 사고", "낙천성", "관용", "대범함", "신념", "자율성", "주체성", "결단력", "합리성", "자기 성찰"
    ],
    "인성 및 관계": [
        "배려심", "공감능력", "협동심", "존중태도", "예의바름", "감사하는 마음", "나눔 실천", "친구들과의 친화력",
        "갈등조정능력", "원만한 대인관계", "공동체 의식", "책임 있는 행동", "리더십", "봉사정신", "긍정적인 마인드",
        "정서적 안정감", "타인을 존중함", "규칙 준수", "역할 수행 능력", "의사소통 능력",
        "너그러움", "동정심", "포용력", "신뢰", "우정", "의리", "헌신", "화합", "상호존중", "정의감"
    ],
    "학습 태도 및 역량": [
        "학습 집중도", "질문하는 태도", "사고력", "창의성", "탐구심", "학습 지속력", "자기 점검 능력", "반성적 사고",
        "성취 동기", "학습 목표 설정 능력", "문제해결력", "논리적 사고력", "정리정돈 습관", "발표력", "자료 활용 능력",
        "목표 지향성", "시간 관리 능력", "수업 참여도", "독서 습관", "실천력",
        "지적 호기심", "비판적 사고", "응용력", "분석력", "종합적 사고", "정보처리능력", "자기효능감", "과제집착력", "학습전략 활용", "메타인지"
    ],
    "학교생활 및 생활습관": [
        "성실한 출결", "생활습관의 안정성", "교칙 준수", "자기 관리 능력", "질서 의식", "청결 유지", "안전 의식",
        "환경 보호 태도", "건강한 생활 태도", "규칙적인 생활",
        "시간 약속 준수", "준비물 관리", "절약 정신", "공공질서 의식", "타인 배려 습관", "정리정돈 생활화", "규칙적인 수면", "균형 잡힌 식습관", "꾸준한 운동", "위생 관념"
    ],
    "감정 및 표현 영역": [
        "감정 표현 능력", "자기 감정 조절 능력", "긍정적 자기 인식", "자존감", "타인의 감정을 이해함", "감정 공유 능력",
        "감정 어휘 사용", "정서적 민감성", "감동하는 능력", "표현력",
        "감정 인식", "감정 수용", "감정 조절 전략", "스트레스 관리", "회복탄력성", "공감적 경청", "비언어적 표현 이해", "예술적 감수성", "풍부한 어휘력", "정서적 공감"
    ],
    "사회성 및 협업": [
        "모둠 활동 참여도", "협업 능력", "토의·토론 태도", "다양한 친구와 어울림", "양보하는 자세", "역할분담을 잘함",
        "공동작업 수행 능력", "다름을 인정함", "타인의 의견 경청", "팀워크를 중시함",
        "의견 조율 능력", "공동 목표 추구", "상호 지원", "건설적 피드백", "다양성 존중", "갈등 예방", "역할 분담의 효율성", "책임감 있는 참여", "공동체 기여", "온라인 협업 능력"
    ],
    "기타 긍정 특성": [
        "자신감", "변화 수용력", "열린 마음", "꾸밈없는 태도", "긍정적 피드백 수용", "반성하는 태도",
        "목표를 향한 열정", "문화 감수성", "봉사활동 참여", "지속 가능한 삶에 대한 관심",
        "유머 감각", "재치", "창의적 발상", "예술적 재능", "리더십 잠재력", "위기 대처 능력", "문제 해결을 위한 노력", "새로운 경험에 대한 개방성", "타문화 이해", "글로벌 마인드"
    ]
}

# API 키 가져오기 함수
def get_api_key():
    """
    Streamlit Secrets 또는 환경 변수에서 API 키를 가져옵니다.
    로컬 테스트 시에는 사이드바 입력을 사용할 수 있도록 합니다.
    """
    # Streamlit Community Cloud 또는 로컬 .streamlit/secrets.toml 파일 사용
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        if api_key:
            return api_key
    except (FileNotFoundError, KeyError): # Secrets 파일이 없거나 키가 없는 경우
        pass

    # 일반 환경 변수 사용
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    
    # 위 방법으로 키를 찾지 못한 경우 (예: 로컬 개발 중 직접 입력)
    # 또는 배포 환경에서 Secrets/환경변수 설정이 안된 경우 사용자에게 입력받도록 fallback
    st.sidebar.warning("API 키가 Secrets 또는 환경 변수에 설정되지 않았습니다. 사이드바에서 직접 입력해주세요.")
    api_key_input_local = st.sidebar.text_input(
        "Gemini API 키를 입력하세요 (로컬 테스트용):",
        type="password",
        help="웹 배포 시에는 Secrets 또는 환경 변수를 사용해야 합니다."
    )
    return api_key_input_local


# Gemini API 호출 함수
def generate_behavior_description(api_key, selected_keywords):
    if not api_key:
        # 이 함수를 호출하기 전에 get_api_key()에서 이미 키가 있는지 확인해야 함
        st.error("API 키가 제공되지 않았습니다. 앱 설정을 확인해주세요.")
        return "API 키가 제공되지 않았습니다."
    if not selected_keywords:
        return "선택된 특성이 없습니다."

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        prompt = f"""
        당신은 초등학교 선생님입니다. 다음은 한 학생에 대해 관찰된 긍정적인 특성 키워드들입니다:
        [{', '.join(selected_keywords)}]

        위 키워드들을 바탕으로, 학생의 학교생활 모습이 잘 드러나는 '행동특성 및 종합의견'을 작성해주세요.
        다음 작성 규칙을 반드시 준수해야 합니다:
        1. 모든 문장은 한국어 명사형 종결어미 (예: '-음', '-함', '-임', '-임이 돋보임', '자세를 지님' 등)로 끝나야 합니다.
        2. 문장들은 서로 자연스럽게 연결되어야 하며, 학생에 대한 긍정적이고 구체적인 관찰 내용이 포함되어야 합니다.
        3. 각 문장은 선택된 키워드들의 의미를 충분히 반영하여 서술해야 합니다.
        4. 한 문장이 70자를 초과할 경우, 의미가 자연스럽게 이어지도록 적절한 지점에서 줄바꿈(\n)을 해주세요. (예: '책임감이 강하여 맡은 일에 최선을 다하며, 학급의 어려운 일에도 솔선수범하는 모습을 보임.' 이 긴 경우, '책임감이 강하여 맡은 일에 최선을 다하며,\n학급의 어려운 일에도 솔선수범하는 모습을 보임.' 과 같이 변경)
        5. 전체적으로 하나의 완성된 문단으로 구성해주세요.
        6. 학생의 이름이나 직접적인 신상 정보는 절대 포함하지 마세요. (예: 'OOO학생은' 과 같은 표현 금지)
        7. 각 키워드의 특성이 잘 드러나도록, 다양한 어휘와 표현을 사용해주세요.

        작성 예시 (선택된 키워드: 책임감, 배려심, 학습 집중도):
        '맡은 일에 대한 책임감이 강하며 어려운 일도 끝까지 해결하려 노력하는 자세가 돋보임.
        주변 친구들에게 배려심이 깊어 다툼 없이 원만하게 지내는 편이며, 타인의 어려움을 보면 먼저 다가가 도움을 주려는 따뜻한 마음을 지님.
        수업 중 학습 집중도가 높아 학업 내용에 대한 이해가 빠르고, 궁금한 점에 대해 적극적으로 질문하는 태도를 보임.'

        위 예시와 규칙을 참고하여, 주어진 키워드에 맞춰 자연스럽고 구체적인 행동 특성 및 종합의견을 작성해주세요.
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}") # 사용자에게 오류 메시지 표시
        return f"API 호출 오류: {str(e)}"


# Excel 파일 생성 함수 (셀 너비 및 줄바꿈 기능 추가)
def create_excel_file(student_data_list):
    if not student_data_list:
        return None

    df = pd.DataFrame(student_data_list)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='학생별 종합의견')
        
        worksheet = writer.sheets['학생별 종합의견']
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 60
        worksheet.column_dimensions['C'].width = 85

        header_font = Font(bold=True, name='Malgun Gothic')
        header_alignment = Alignment(horizontal='center', vertical='center')
        
        for col_letter in ['A', 'B', 'C']:
            header_cell = worksheet[f'{col_letter}1']
            header_cell.font = header_font
            header_cell.alignment = header_alignment

        for row_idx in range(2, worksheet.max_row + 1):
            cell_A = worksheet[f'A{row_idx}']
            cell_A.alignment = Alignment(vertical='top')
            cell_A.font = Font(name='Malgun Gothic')

            cell_B = worksheet[f'B{row_idx}']
            cell_B.alignment = Alignment(wrap_text=True, vertical='top')
            cell_B.font = Font(name='Malgun Gothic')

            cell_C = worksheet[f'C{row_idx}']
            cell_C.alignment = Alignment(wrap_text=True, vertical='top')
            cell_C.font = Font(name='Malgun Gothic')

    processed_data = output.getvalue()
    return processed_data

# Streamlit 앱 UI 구성
st.set_page_config(layout="wide", page_title="학생 행동특성 생성기")
st.title("📝 학생 행동 특성 및 종합의견 생성 도우미")
st.markdown("Gemini API를 활용하여 여러 학생의 특성에 맞는 종합의견 초안을 생성하고 Excel 파일로 저장합니다.")

# --- 사이드바 설정 ---
st.sidebar.header("⚙️ 설정")

# API 키 가져오기 (Secrets 또는 환경변수 우선, 없으면 로컬 입력)
# 이 api_key 변수는 앱 전체에서 사용됩니다.
retrieved_api_key = get_api_key() 

st.sidebar.markdown("[Google AI Studio 바로가기](https://aistudio.google.com/app/apikey)") # API 키 발급 안내는 유지
num_students = st.sidebar.number_input("생성할 학생 수를 입력하세요:", min_value=1, value=1, step=1)
st.sidebar.info("`pandas`와 `openpyxl` 라이브러리가 필요합니다. 설치되지 않은 경우 터미널에서 `pip install pandas openpyxl`을 실행해주세요.")


# --- 메인 화면 ---
st.markdown("---")

# 세션 상태 초기화
if 'student_keywords' not in st.session_state:
    st.session_state.student_keywords = {}
if 'student_descriptions' not in st.session_state:
    st.session_state.student_descriptions = {}
if 'last_num_students' not in st.session_state:
    st.session_state.last_num_students = 0

if num_students != st.session_state.last_num_students:
    st.session_state.student_keywords = {f"학생 {i+1}": [] for i in range(num_students)}
    st.session_state.student_descriptions = {f"학생 {i+1}": "" for i in range(num_students)}
    st.session_state.last_num_students = num_students
else:
    current_student_names = [f"학생 {i+1}" for i in range(num_students)]
    st.session_state.student_keywords = {name: st.session_state.student_keywords.get(name, []) for name in current_student_names}
    st.session_state.student_descriptions = {name: st.session_state.student_descriptions.get(name, "") for name in current_student_names}

# 1. 학생별 특성 선택 섹션
st.header("1. 학생별 특성 선택")
st.info(f"총 {num_students}명의 학생에 대한 특성을 선택합니다. 각 학생 탭에서 특성을 선택해주세요.")

student_tabs = st.tabs([f"학생 {i+1}" for i in range(num_students)])

for i, tab in enumerate(student_tabs):
    student_name = f"학생 {i+1}"
    with tab:
        st.subheader(f"{student_name} 특성 선택")
        if student_name not in st.session_state.student_keywords:
            st.session_state.student_keywords[student_name] = []
        
        default_keywords_for_student = st.session_state.student_keywords.get(student_name, [])
        temp_selected_in_tab = [] 
        cols = st.columns(3)
        cat_keys = list(CATEGORIES.keys())

        for j, category_name in enumerate(cat_keys):
            with cols[j % 3]:
                expanded_default = (j < 3) 
                with st.expander(f"**{category_name}** ({len(CATEGORIES[category_name])}개)", expanded=expanded_default):
                    current_selection_for_category = [kw for kw in default_keywords_for_student if kw in CATEGORIES[category_name]]
                    selected_items_cat = st.multiselect(
                        label=f"{category_name} ({student_name})", 
                        options=CATEGORIES[category_name],
                        key=f"multiselect_{student_name}_{category_name}", 
                        default=current_selection_for_category, 
                        label_visibility="collapsed"
                    )
                    temp_selected_in_tab.extend(selected_items_cat)
        
        st.session_state.student_keywords[student_name] = sorted(list(set(temp_selected_in_tab)))

        if st.session_state.student_keywords[student_name]:
            st.write(f"✅ **{student_name} 선택된 특성:**")
            st.info(', '.join(st.session_state.student_keywords[student_name]))
        else:
            st.write(f"ℹ️ {student_name}의 특성을 선택해주세요.")

st.markdown("---")

# 2. 종합의견 일괄 생성 버튼
st.header("2. 종합의견 일괄 생성")

any_student_has_keywords = any(
    len(st.session_state.student_keywords.get(f"학생 {i+1}", [])) > 0 for i in range(num_students)
)

# 버튼 비활성화 조건에 retrieved_api_key 유무 추가
if st.button("🚀 모든 학생 종합의견 생성하기", type="primary", use_container_width=True,
             disabled=(not retrieved_api_key or not any_student_has_keywords)):
    if not retrieved_api_key: # API 키가 없는 경우 (Secrets/환경변수에도 없고, 로컬 입력도 안된 경우)
        st.error("❗️ Gemini API 키가 설정되지 않았습니다. 앱 관리자에게 문의하거나, 로컬 테스트 시 사이드바에 키를 입력해주세요.")
    elif not any_student_has_keywords:
        st.warning("❗️ 특성이 선택된 학생이 한 명도 없습니다. 각 학생의 특성을 선택해주세요.")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        generated_descriptions_temp = {}
        students_to_process_count = sum(1 for i in range(num_students) if st.session_state.student_keywords.get(f"학생 {i+1}", []))
        
        if students_to_process_count == 0:
            st.warning("❗️ 특성이 선택된 학생이 한 명도 없습니다.")
        else:
            processed_count = 0
            for i in range(num_students):
                student_name = f"학생 {i+1}"
                keywords = st.session_state.student_keywords.get(student_name, [])

                if keywords: 
                    status_text.text(f"'{student_name}'의 종합의견 생성 중... ({processed_count+1}/{students_to_process_count})")
                    # API 호출 시 retrieved_api_key 사용
                    description = generate_behavior_description(retrieved_api_key, keywords) 
                    if "API 호출 오류:" in description or "API 키가 제공되지 않았습니다." in description or "선택된 특성이 없습니다." in description :
                        st.error(f"'{student_name}' 종합의견 생성 실패: {description}")
                        generated_descriptions_temp[student_name] = f"생성 실패: {description}"
                    else:
                        generated_descriptions_temp[student_name] = description
                        st.success(f"'{student_name}' 종합의견 생성 완료!")
                    processed_count += 1
                    progress_bar.progress(processed_count / students_to_process_count)
                else:
                    generated_descriptions_temp[student_name] = st.session_state.student_descriptions.get(student_name, "선택된 특성이 없어 생성하지 않음.")
            
            st.session_state.student_descriptions.update(generated_descriptions_temp)
            if processed_count > 0:
                status_text.text(f"총 {processed_count}명의 학생 종합의견 생성 작업 완료!")
                st.balloons()
            else:
                status_text.text("특성이 선택된 학생이 없어 생성 작업이 진행되지 않았습니다.")

st.markdown("---")

# 3. 생성된 결과 표시 및 다운로드 섹션
st.header("3. 생성된 행동 특성 및 종합의견 확인")

results_for_display_and_download = []
has_results = False
for i in range(num_students):
    student_name = f"학생 {i+1}"
    keywords = st.session_state.student_keywords.get(student_name, [])
    description = st.session_state.student_descriptions.get(student_name, "아직 생성되지 않음 또는 생성 실패")

    if keywords or (description and description not in ["아직 생성되지 않음 또는 생성 실패", "선택된 특성이 없어 생성하지 않음."]):
        has_results = True

    results_for_display_and_download.append({
        "학생 번호": student_name,
        "선택된 특성": ', '.join(keywords) if keywords else "선택된 특성 없음",
        "생성된 종합의견": description
    })

if has_results:
    st.info("아래 펼치기 메뉴에서 학생별 생성된 종합의견을 확인하고, Excel 파일로 다운로드할 수 있습니다.")

    for result_item in results_for_display_and_download:
        show_expander = (result_item["선택된 특성"] != "선택된 특성 없음") or \
                        (result_item["생성된 종합의견"] not in ["아직 생성되지 않음 또는 생성 실패", "선택된 특성이 없어 생성하지 않음."])
        
        if show_expander:
            with st.expander(f"📄 {result_item['학생 번호']} 결과 보기", expanded=False):
                st.markdown(f"**선택된 특성:** {result_item['선택된 특성']}")
                st.markdown(f"**생성된 종합의견:**")
                display_description = result_item['생성된 종합의견'] if result_item['생성된 종합의견'] else "내용 없음"
                st.markdown(f"<div style='white-space: pre-wrap; border: 1px solid #e6e6e6; padding: 10px; border-radius: 5px; background-color: #f9f9f9;'>{display_description}</div>", unsafe_allow_html=True)

    downloadable_data = [
        item for item in results_for_display_and_download 
        if item["선택된 특성"] != "선택된 특성 없음" or \
           (item["생성된 종합의견"] not in ["아직 생성되지 않음 또는 생성 실패", "선택된 특성이 없어 생성하지 않음.", ""])
    ]

    if downloadable_data:
        excel_data = create_excel_file(downloadable_data)
        if excel_data:
            st.download_button(
                label="📥 모든 학생 결과 Excel 파일로 다운로드 (.xlsx)",
                data=excel_data,
                file_name="students_behavior_descriptions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="excel_download_button"
            )
    else:
        st.warning("다운로드할 유효한 데이터가 없습니다. 먼저 종합의견을 생성해주세요.")
else:
    st.info("아직 생성된 종합의견이 없습니다. 학생별 특성을 선택하고 생성 버튼을 눌러주세요.")

st.markdown("---")
st.caption("This app is made by SH(litt.ly/4sh.space)")
