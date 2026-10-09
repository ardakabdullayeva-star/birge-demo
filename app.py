import streamlit as st
import pandas as pd
from datetime import datetime
import json

# --- НАСТРОЙКА СТРАНИЦЫ (Должна быть первой командой) ---
st.set_page_config(page_title="Бірге", page_icon="🧩", layout="wide")
st.caption("Сеансовый макет: используйте только вымышленные данные. Записи доступны только в этом сеансе и могут исчезнуть при его завершении. Вход по имени не подтверждает личность.")

# Данные существуют только в текущем сеансе Streamlit.
if "records" not in st.session_state:
    st.session_state.records = {name: [] for name in ["teacher_reports", "psychologist_reports", "speech_reports", "defect_reports"]}
if "users" not in st.session_state:
    st.session_state.users = {}

# --- МУЛЬТИЯЗЫЧНЫЙ СЛОВАРЬ ---
LANG_DATA = {'Русский': {'site_title': 'Бірге: от диагноза к результату', 'site_subtitle': 'Единая цифровая платформа психолого-педагогического консилиума', 'tab_survey': '📝 Новое обследование', 'tab_report': '📋 Комплексный отчет', 'tab_history': '📁 Архив записей', 'child_label': 'Код ученика (для анонимности)', 'child_placeholder': 'Например: 1А01', 'date_label': 'Дата обследования', 'save_btn': '💾 Сохранить данные', 'auth_name': 'Ваша Фамилия и Инициалы', 'auth_pwd': 'Ваш личный пароль', 'auth_btn': 'Войти в кабинет', 'extra_notes_label': '✍️ Дополнительные экспертные наблюдения:', 'placeholder_notes': 'Введите информацию...', 'contacts_title': '📞 Контакты:', 'teach_title': 'Карта наблюдений классного руководителя', 'teach_secs': ['Общение', 'Инструкции и внимание', 'Адаптация', 'Сенсорные реакции'], 'teach_q': [['Нуждается в помощи, чтобы вступить в общение', 'Нуждается в помощи, чтобы соблюдать очередность в совместной деятельности'], ['Нуждается в повторении или показе инструкции', 'Нуждается в помощи для возвращения к заданию после отвлечения'], ['Испытывает трудности при переходе к новому заданию', 'Нуждается в поддержке при изменении привычного порядка'], ['Шум, свет или прикосновения затрудняют участие в занятии']], 'psych_title': '🧠 Кабинет Психолога', 'psych_secs': ['Эмоциональное состояние', 'Взаимодействие', 'Учебная деятельность'], 'psych_q': [['Нуждается в поддержке при ошибке или неудаче', 'Проявляет заметное напряжение в учебной ситуации'], ['Нуждается в помощи для участия в совместной деятельности', 'Нуждается в помощи, чтобы сообщить о своих потребностях'], ['Нуждается в поддержке, чтобы начать задание', 'Нуждается в дополнительном времени при смене деятельности']], 'logo_title': '🗣 Кабинет Логопеда', 'logo_secs': ['Понимание речи', 'Выражение мысли', 'Звукопроизношение'], 'logo_q': [['Нуждается в уточнении простого устного обращения', 'Нуждается в показе при выполнении устной инструкции'], ['Испытывает трудности при словесном выражении просьбы', 'Нуждается в помощи для последовательного рассказа о событии'], ['Особенности произношения затрудняют понимание речи окружающими']], 'def_title': '🎓 Кабинет Дефектолога', 'def_secs': ['Освоение заданий', 'Самостоятельность', 'Поддержка'], 'def_q': [['Нуждается в повторном показе способа выполнения', 'Нуждается в помощи для применения способа в похожем задании'], ['Нуждается в помощи при подготовке материалов', 'Нуждается в сопровождении для завершения посильного задания'], ['Нуждается в наглядных опорах', 'Нуждается в разделении задания на короткие шаги']], 'answers': ['Не было возможности оценить', 'Не наблюдалось', 'Иногда', 'Часто']}, 'Қазақша': {'site_title': 'Бірге: диагноздан нәтижеге дейін', 'site_subtitle': 'Психологиялық-педагогикалық консилиумның бірыңғай платформасы', 'tab_survey': '📝 Жаңа тексеру', 'tab_report': '📋 Кешенді есеп', 'tab_history': '📁 Жазбалар архиві', 'child_label': 'Оқушы коды (анонимділік үшін)', 'child_placeholder': 'Мысалы: 1А01', 'date_label': 'Тексеру күні', 'save_btn': '💾 Мәліметтерді сақтау', 'auth_name': 'Тегіңіз бен аты-жөніңіз', 'auth_pwd': 'Жеке құпия сөзіңіз', 'auth_btn': 'Кабинетке кіру', 'extra_notes_label': '✍️ Қосымша сараптамалық бақылаулар:', 'placeholder_notes': 'Ақпаратты енгізіңіз...', 'contacts_title': '📞 Байланыс мәліметтері:', 'teach_title': 'Сынып жетекшісінің бақылау картасы', 'teach_secs': ['Қарым-қатынас', 'Нұсқау және зейін', 'Бейімделу', 'Сенсорлық реакциялар'], 'teach_q': [['Қарым-қатынасты бастау үшін көмек қажет', 'Бірлескен әрекетте кезек сақтау үшін көмек қажет'], ['Нұсқауды қайталау немесе көрсету қажет', 'Алаңдағаннан кейін тапсырмаға қайта оралу үшін көмек қажет'], ['Жаңа тапсырмаға ауысуда қиындық байқалады', 'Үйреншікті тәртіп өзгергенде қолдау қажет'], ['Шу, жарық немесе жанасу сабаққа қатысуға кедергі келтіреді']], 'psych_title': '🧠 Психолог кабинеті', 'psych_secs': ['Эмоциялық жағдай', 'Өзара әрекет', 'Оқу әрекеті'], 'psych_q': [['Қателескенде немесе сәтсіздік кезінде қолдау қажет', 'Оқу жағдайында айқын қобалжу байқалады'], ['Бірлескен әрекетке қатысу үшін көмек қажет', 'Өз қажеттілігін білдіру үшін көмек қажет'], ['Тапсырманы бастау үшін қолдау қажет', 'Әрекетті ауыстыру үшін қосымша уақыт қажет']], 'logo_title': '🗣 Логопед кабинеті', 'logo_secs': ['Сөйлеуді түсіну', 'Ойын жеткізу', 'Дыбыс айту'], 'logo_q': [['Қарапайым ауызша өтінішті нақтылау қажет', 'Ауызша нұсқауды орындау үшін көрсету қажет'], ['Өтінішін сөзбен жеткізуде қиындық байқалады', 'Оқиғаны ретімен баяндау үшін көмек қажет'], ['Дыбыс айту ерекшеліктері сөйлеуді түсінуді қиындатады']], 'def_title': '🎓 Дефектолог кабинеті', 'def_secs': ['Тапсырманы меңгеру', 'Дербестік', 'Қолдау'], 'def_q': [['Орындау тәсілін қайта көрсету қажет', 'Тәсілді ұқсас тапсырмада қолдану үшін көмек қажет'], ['Материалдарды дайындау үшін көмек қажет', 'Шамасы келетін тапсырманы аяқтау үшін сүйемелдеу қажет'], ['Көрнекі тіректер қажет', 'Тапсырманы қысқа қадамдарға бөлу қажет']], 'answers': ['Бағалау мүмкіндігі болмады', 'Байқалмады', 'Кейде', 'Жиі']}}

# --- ГЛОБАЛЬНЫЕ НАСТРОЙКИ ЯЗЫКА ---
if 'language' not in st.session_state: st.session_state.language = 'Русский'
T = LANG_DATA[st.session_state.language]

st.sidebar.title("⚙️ Баптаулар / Настройки")
st.sidebar.radio("Тіл / Язык:", ['Русский', 'Қазақша'], key='lang_choice', 
                 on_change=lambda: setattr(st.session_state, 'language', st.session_state.lang_choice))
st.sidebar.write("---")

# ==========================================
# ФУНКЦИЯ УНИВЕРСАЛЬНОЙ АВТОРИЗАЦИИ
# ==========================================
def login_block(role):
    logged_key, user_key = f"logged_in_{role}", f"user_{role}"
    if not st.session_state.get(logged_key):
        st.subheader(f"Вход / регистрация: {role}")
        with st.form(f"auth_{role}"):
            name = st.text_input(T['auth_name']).strip()
            # Пароли не используются: это сеансовый макет без контроля доступа.
            if st.form_submit_button(T['auth_btn'], type="primary"):
                if name:
                    st.session_state[logged_key] = True
                    st.session_state[user_key] = name
                    st.session_state.users[name] = role
                    st.rerun()
                else: st.warning("Укажите имя.")
        return False
    st.sidebar.success(f"{st.session_state[user_key]} · {role}")
    if st.sidebar.button("Выйти", key=f"logout_{role}"):
        st.session_state[logged_key] = False
        st.rerun()
    return True


def save_record(table, values):
    record = dict(values)
    record['id'] = len(st.session_state.records[table]) + 1
    st.session_state.records[table].append(record)


# ==========================================
# СТРАНИЦЫ ПРИЛОЖЕНИЯ
# ==========================================
def page_home():
    st.markdown(f"<h1 style='text-align: center; color: #2e6c80;'>{T['site_title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: center;'>{T['site_subtitle']}</h4>", unsafe_allow_html=True)
    st.write("---")
    st.info("👈 **Пожалуйста, выберите ваш личный кабинет в боковом меню слева.**")
    st.write("---")
    st.markdown(f"👥 **{T['contacts_title']}**")
    st.markdown("""
    * **ФИО:** Абдуллаева Ардақ Шығайқызы
    * **Телефон / WhatsApp:** +77787954638
    * **Email:** ardak.abdullayeva@aktau7.edu.kz
    """)

def render_history_tab(table_name, name_col, role_title):
    rows = st.session_state.records[table_name]
    if rows:
        st.dataframe(pd.DataFrame([{"Дата": r['d'], "Специалист": r['n'], "Код ученика": r['c'], "Наблюдения": r['not']} for r in reversed(rows)]), use_container_width=True)
    else: st.info("В этом сеансе записей пока нет.")

def page_teacher():
    if login_block("Учитель"):
        st.title(T['teach_title'])
        tabs = st.tabs([T['tab_survey'], T['tab_history']])
        with tabs[0]:
            c_col1, c_col2 = st.columns(2)
            child_name = c_col1.text_input(T['child_label'], placeholder=T['child_placeholder'])
            survey_date = c_col2.date_input(T['date_label'], datetime.now())
            st.write("---")
            asd_score, adhd_score = 0, 0
            observations = {}
            st.caption("Карта наблюдений, не диагностический тест. Ответы не суммируются в балл.")
            for i, section in enumerate(T['teach_secs']):
                st.markdown(f"### {section}")
                for idx, q in enumerate(T['teach_q'][i]):
                    observations[q] = st.radio(q, T['answers'], key=f"teacher_{i}_{idx}", horizontal=True)
            st.write("---")
            extra_notes = st.text_area(T['extra_notes_label'], placeholder='Конкретный пример, сильные стороны ребёнка, что помогло / Нақты мысал, баланың күшті жақтары, қандай қолдау көмектесті')
            if st.button(T['save_btn'], use_container_width=True, type="primary"):
                if child_name:
                    save_record("teacher_reports", {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Учитель"], "c": child_name, "a": asd_score, "ad": adhd_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
                    st.success(f"🎉 Данные сохранены!")
                else: st.error("Пожалуйста, введите код ребенка!")
        with tabs[1]: render_history_tab("teacher_reports", "teacher_name", "Учителя")

def page_psych():
    if login_block("Психолог"):
        st.title(T['psych_title'])
        tabs = st.tabs([T['tab_survey'], T['tab_history']])
        with tabs[0]:
            c_col1, c_col2 = st.columns(2)
            child_name = c_col1.text_input(T['child_label'], placeholder=T['child_placeholder'])
            survey_date = c_col2.date_input(T['date_label'], datetime.now())
            st.write("---")
            total_score = 0
            observations = {}
            st.caption('Карта наблюдений, не диагностический тест. Ответы не суммируются в балл.')
            for i, sec in enumerate(T['psych_secs']):
                st.markdown(f"### {sec}")
                for idx, q in enumerate(T['psych_q'][i]):
                    observations[q] = st.radio(q, T["answers"], key=f"p_q_{i}_{idx}", horizontal=True)
            st.write("---")
            extra_notes = st.text_area(T['extra_notes_label'], placeholder='Конкретный пример, сильные стороны ребёнка, что помогло / Нақты мысал, баланың күшті жақтары, қандай қолдау көмектесті')
            if st.button(T['save_btn'], use_container_width=True, type="primary"):
                if child_name:
                    save_record("psychologist_reports", {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Психолог"], "c": child_name, "s": total_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
                    st.success(f"🎉 Данные сохранены!")
                else: st.error("Введите код ребенка!")
        with tabs[1]: render_history_tab("psychologist_reports", "psych_name", "Психолога")

def page_logo():
    if login_block("Логопед"):
        st.title(T['logo_title'])
        tabs = st.tabs([T['tab_survey'], T['tab_history']])
        with tabs[0]:
            c_col1, c_col2 = st.columns(2)
            child_name = c_col1.text_input(T['child_label'], placeholder=T['child_placeholder'])
            survey_date = c_col2.date_input(T['date_label'], datetime.now())
            st.write("---")
            total_score = 0
            observations = {}
            st.caption('Карта наблюдений, не диагностический тест. Ответы не суммируются в балл.')
            for i, sec in enumerate(T['logo_secs']):
                st.markdown(f"### {sec}")
                for idx, q in enumerate(T['logo_q'][i]):
                    observations[q] = st.radio(q, T["answers"], key=f"l_q_{i}_{idx}", horizontal=True)
            st.write("---")
            extra_notes = st.text_area(T['extra_notes_label'], placeholder='Конкретный пример, сильные стороны ребёнка, что помогло / Нақты мысал, баланың күшті жақтары, қандай қолдау көмектесті')
            if st.button(T['save_btn'], use_container_width=True, type="primary"):
                if child_name:
                    save_record("speech_reports", {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Логопед"], "c": child_name, "s": total_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
                    st.success(f"🎉 Данные сохранены!")
                else: st.error("Введите код ребенка!")
        with tabs[1]: render_history_tab("speech_reports", "speech_name", "Логопеда")

def page_def():
    if login_block("Дефектолог"):
        st.title(T['def_title'])
        tabs = st.tabs([T['tab_survey'], T['tab_history']])
        with tabs[0]:
            c_col1, c_col2 = st.columns(2)
            child_name = c_col1.text_input(T['child_label'], placeholder=T['child_placeholder'])
            survey_date = c_col2.date_input(T['date_label'], datetime.now())
            st.write("---")
            total_score = 0
            observations = {}
            st.caption('Карта наблюдений, не диагностический тест. Ответы не суммируются в балл.')
            for i, sec in enumerate(T['def_secs']):
                st.markdown(f"### {sec}")
                for idx, q in enumerate(T['def_q'][i]):
                    observations[q] = st.radio(q, T["answers"], key=f"d_q_{i}_{idx}", horizontal=True)
            st.write("---")
            extra_notes = st.text_area(T['extra_notes_label'], placeholder='Конкретный пример, сильные стороны ребёнка, что помогло / Нақты мысал, баланың күшті жақтары, қандай қолдау көмектесті')
            if st.button(T['save_btn'], use_container_width=True, type="primary"):
                if child_name:
                    save_record("defect_reports", {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Дефектолог"], "c": child_name, "s": total_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
                    st.success(f"🎉 Данные сохранены!")
                else: st.error("Введите код ребенка!")
        with tabs[1]: render_history_tab("defect_reports", "defect_name", "Дефектолога")

def page_admin():
    if not login_block("Руководитель консилиума"):
        return
    st.title("Кабинет руководителя консилиума")
    students = sorted({r['c'] for rows in st.session_state.records.values() for r in rows})
    if not students:
        st.info("Сначала сохраните наблюдение в одном из кабинетов.")
        return
    child = st.selectbox("Код ученика", students)
    document = ["Бірге: сводный протокол наблюдений", f"Код ученика: {child}"]
    for table, label in [("teacher_reports", "Классный руководитель"), ("psychologist_reports", "Психолог"), ("speech_reports", "Логопед"), ("defect_reports", "Дефектолог")]:
        rows = [r for r in st.session_state.records[table] if r['c'] == child]
        if not rows:
            continue
        r = rows[-1]
        st.subheader(label)
        st.caption(f"{r['n']} · {r['d']}")
        answers = json.loads(r['details'])
        st.table(pd.DataFrame([{"Наблюдение": q, "Ответ": a} for q, a in answers.items()]))
        st.write(r['not'] or "Комментарий не указан")
        document.extend([f"\n{label}: {r['n']} · {r['d']}"] + [f"{q}: {a}" for q, a in answers.items()] + ["Наблюдения: " + r['not']])
    document.append("\nДокумент не является диагностическим заключением. Текст составлен из введённых наблюдений, ИИ не подключён.")
    st.download_button("Скачать протокол", "\n".join(document), file_name="birge_protocol.txt", mime="text/plain")

# ==========================================
# ЗАПУСК НАВИГАЦИИ (STREAMLIT 1.36+)
# ==========================================
pg = st.navigation({
    "Информация": [
        st.Page(page_home, title="Главная страница", icon="🏠", url_path="home")
    ],
    "Кабинеты специалистов": [
        st.Page(page_teacher, title="Учитель", icon="🏫", url_path="teacher"),
        st.Page(page_psych, title="Психолог", icon="🧠", url_path="psychologist"),
        st.Page(page_logo, title="Логопед", icon="🗣", url_path="speech_therapist"),
        st.Page(page_def, title="Дефектолог", icon="🎓", url_path="defectologist")
    ],
    "Управление": [
        st.Page(page_admin, title="Руководитель консилиума", icon="🛡️", url_path="admin")
    ]
})

pg.run()