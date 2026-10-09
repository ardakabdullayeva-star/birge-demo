import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import json

# --- НАСТРОЙКА СТРАНИЦЫ (Должна быть первой командой) ---
st.set_page_config(page_title="Бірге", page_icon="🧩", layout="wide")

# --- ПОДКЛЮЧЕНИЕ К SUPABASE ---
@st.cache_resource
def init_connection():
    return create_engine(st.secrets["DATABASE_URL"])

engine = init_connection()

def init_db():
    with engine.begin() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT)'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS teacher_reports 
                     (id SERIAL PRIMARY KEY, date TEXT, teacher_name TEXT, child_id TEXT, 
                      asd_score INTEGER, adhd_score INTEGER, details TEXT, adhd_details TEXT, notes TEXT, lang TEXT)'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS psychologist_reports 
                     (id SERIAL PRIMARY KEY, date TEXT, psych_name TEXT, child_id TEXT, 
                      total_score INTEGER, details TEXT, notes TEXT, lang TEXT)'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS speech_reports 
                     (id SERIAL PRIMARY KEY, date TEXT, speech_name TEXT, child_id TEXT, 
                      total_score INTEGER, details TEXT, notes TEXT, lang TEXT)'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS defect_reports 
                     (id SERIAL PRIMARY KEY, date TEXT, defect_name TEXT, child_id TEXT, 
                      total_score INTEGER, details TEXT, notes TEXT, lang TEXT)'''))

init_db()

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
    logged_key = f"logged_in_{role}"
    user_key = f"user_{role}"
    
    if logged_key not in st.session_state: st.session_state[logged_key] = False
    if user_key not in st.session_state: st.session_state[user_key] = ""
    
    if not st.session_state[logged_key]:
        st.markdown(f"<h2 style='text-align: center;'>Вход: {role}</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form(key=f"auth_{role}"):
                u_name = st.text_input(T['auth_name']).strip()
                u_pwd = st.text_input(T['auth_pwd'], type="password")
                submit = st.form_submit_button(T['auth_btn'], use_container_width=True, type="primary")
                
                if submit:
                    if role == "Админ":
                        if (u_name.lower() == "ардак" or u_name.lower() == "директор") and u_pwd == st.secrets["ADMIN_PASSWORD"]:
                            st.session_state[logged_key] = True
                            st.session_state[user_key] = "Абдуллаева А.Ш."
                            st.rerun()
                        else: st.error("Неверный логин или пароль!")
                    elif u_name and u_pwd:
                        with engine.connect() as conn:
                            result = conn.execute(text("SELECT password, role FROM users WHERE username = :u AND role = :r"), {"u": u_name, "r": role}).fetchone()
                            if result:
                                if result[0] == u_pwd:
                                    st.session_state[logged_key] = True
                                    st.session_state[user_key] = u_name
                                    st.rerun()
                                else: st.error("Неверный пароль!")
                            else:
                                user_exists = conn.execute(text("SELECT role FROM users WHERE username = :u"), {"u": u_name}).fetchone()
                                if user_exists:
                                    st.error(f"Пользователь зарегистрирован как {user_exists[0]}! Перейдите в правильный кабинет слева.")
                                else:
                                    with engine.begin() as insert_conn:
                                        insert_conn.execute(text("INSERT INTO users (username, password, role) VALUES (:u, :p, :r)"), {"u": u_name, "p": u_pwd, "r": role})
                                    st.session_state[logged_key] = True
                                    st.session_state[user_key] = u_name
                                    st.rerun()
                    else:
                        st.warning("Заполните все поля.")
        return False
    else:
        st.sidebar.success(f"👤 {st.session_state[user_key]} ({role})")
        if st.sidebar.button("Выйти / Шығу", key=f"logout_{role}", use_container_width=True):
            st.session_state[logged_key] = False
            st.session_state[user_key] = ""
            st.rerun()
        return True

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
    try:
        df = pd.read_sql_query(f"SELECT date as \"Дата\", {name_col} as \"ФИО Специалиста\", child_id as \"Код ребенка\", notes as \"Комментарий\" FROM {table_name} ORDER BY id DESC", engine)
        st.dataframe(df, use_container_width=True) if not df.empty else st.info(f"Нет записей в архиве {role_title}.")
    except Exception as e: st.error(f"Ошибка загрузки архива: {e}")

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
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO teacher_reports (date, teacher_name, child_id, asd_score, adhd_score, details, adhd_details, notes, lang) VALUES (:d, :n, :c, :a, :ad, :details, '', :not, :l)"),
                                     {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Учитель"], "c": child_name, "a": asd_score, "ad": adhd_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
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
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO psychologist_reports (date, psych_name, child_id, total_score, details, notes, lang) VALUES (:d, :n, :c, :s, :details, :not, :l)"),
                                     {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Психолог"], "c": child_name, "s": total_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
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
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO speech_reports (date, speech_name, child_id, total_score, details, notes, lang) VALUES (:d, :n, :c, :s, :details, :not, :l)"),
                                     {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Логопед"], "c": child_name, "s": total_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
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
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO defect_reports (date, defect_name, child_id, total_score, details, notes, lang) VALUES (:d, :n, :c, :s, :details, :not, :l)"),
                                     {"d": survey_date.strftime("%d.%m.%Y"), "n": st.session_state["user_Дефектолог"], "c": child_name, "s": total_score, "not": extra_notes, "details": json.dumps(observations, ensure_ascii=False), "l": st.session_state.language})
                    st.success(f"🎉 Данные сохранены!")
                else: st.error("Введите код ребенка!")
        with tabs[1]: render_history_tab("defect_reports", "defect_name", "Дефектолога")

def page_admin():
    if login_block("Админ"):
        st.title("🛡️ Панель Администратора")
        admin_tabs = st.tabs(["📊 Контроль и Специфика", "📋 Формирование ПМПК", "🗄️ База Данных"])
        
        with admin_tabs[0]:
            st.subheader("👥 Зарегистрированные специалисты")
            users_df = pd.read_sql_query('SELECT username as "ФИО Специалиста", role as "Роль / Кабинет", password as "Текущий Пароль" FROM users', engine)
            st.dataframe(users_df, use_container_width=True)
            if not users_df.empty:
                user_to_del = st.selectbox("Кого удалить из системы?", users_df["ФИО Специалиста"].tolist())
                if st.button(f"❌ Удалить доступ для {user_to_del}", type="primary"):
                    with engine.begin() as conn:
                        conn.execute(text("DELETE FROM users WHERE username = :u"), {"u": user_to_del})
                    st.success(f"Специалист удален!")
                    st.rerun()

        with admin_tabs[1]:
            st.subheader("📋 Генерация комплексного отчета ПМПК")
            try:
                t_kids = pd.read_sql_query("SELECT DISTINCT child_id FROM teacher_reports", engine)['child_id'].tolist()
                p_kids = pd.read_sql_query("SELECT DISTINCT child_id FROM psychologist_reports", engine)['child_id'].tolist()
                l_kids = pd.read_sql_query("SELECT DISTINCT child_id FROM speech_reports", engine)['child_id'].tolist()
                d_kids = pd.read_sql_query("SELECT DISTINCT child_id FROM defect_reports", engine)['child_id'].tolist()
                all_kids = sorted(list(set(t_kids + p_kids + l_kids + d_kids)))
            except: all_kids = []
            
            if all_kids:
                selected_kid = st.selectbox("🎯 Выберите код ученика:", all_kids)
                if st.button("Сформировать сводный протокол", type="primary"):
                    st.write("---")
                    st.markdown(f"### 📄 Сводная экспертная оценка по ученику: **{selected_kid}**")
                    t_rep = pd.read_sql_query(text("SELECT * FROM teacher_reports WHERE child_id = :c ORDER BY id DESC LIMIT 1"), engine, params={"c": selected_kid})
                    p_rep = pd.read_sql_query(text("SELECT * FROM psychologist_reports WHERE child_id = :c ORDER BY id DESC LIMIT 1"), engine, params={"c": selected_kid})
                    for table, name_col, label in [("teacher_reports", "teacher_name", "Учитель"), ("psychologist_reports", "psych_name", "Психолог"), ("speech_reports", "speech_name", "Логопед"), ("defect_reports", "defect_name", "Дефектолог")]:
                        report = pd.read_sql_query(text(f"SELECT * FROM {table} WHERE child_id = :c ORDER BY id DESC LIMIT 1"), engine, params={"c": selected_kid})
                        if not report.empty:
                            row = report.iloc[0]
                            st.subheader(f"{label}: {row[name_col]}")
                            try:
                                answers = json.loads(row['details'])
                                st.table(pd.DataFrame([{"Наблюдение": question, "Ответ": answer} for question, answer in answers.items()]))
                            except (ValueError, TypeError, AttributeError):
                                st.info("Старая запись: подробные ответы не сохранялись. Диагностические баллы не интерпретируются.")
                            st.write("Наблюдения:", row['notes'] or "Не указаны")
                    st.caption("Сводный протокол наблюдений. Не является диагнозом. ИИ не подключён.")
            else: st.info("В базе пока нет заполненных анкет.")
            
        with admin_tabs[2]:
            st.write("Сырые данные базы (Архив всех таблиц)")
            raw_tabs = st.tabs(["Учителя", "Психологи"])
            with raw_tabs[0]: st.dataframe(pd.read_sql_query("SELECT * FROM teacher_reports", engine), use_container_width=True)
            with raw_tabs[1]: st.dataframe(pd.read_sql_query("SELECT * FROM psychologist_reports", engine), use_container_width=True)

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
        st.Page(page_admin, title="Администратор", icon="🛡️", url_path="admin")
    ]
})

pg.run()