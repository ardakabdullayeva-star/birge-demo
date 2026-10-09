"""Бірге: демонстрация маршрута школьных наблюдений, только вымышленные данные."""
import html
import io
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.set_page_config(page_title="Бірге: от диагноза к результату", page_icon="🤝", layout="wide")
DB = Path(__file__).with_name("demo.sqlite3")
ROLES = ["Классный руководитель", "Учитель-предметник", "Психолог", "Логопед", "Дефектолог", "Педагог-ассистент", "Руководитель консилиума"]
SITUATIONS = ["Урок", "Перемена", "Общение", "Самостоятельное задание", "Другая ситуация"]
FONT = str(Path(__file__).with_name("DejaVuSans.ttf"))
BOLD = str(Path(__file__).with_name("DejaVuSans-Bold.ttf"))


ANSWERS = ["Не было возможности оценить", "Не наблюдалось", "Иногда", "Часто"]
TEACHER_ITEMS = {
    "Общение": ["Нуждается в дополнительной помощи, чтобы вступить в общение", "Испытывает трудности с очередностью в совместной игре или разговоре"],
    "Инструкции и внимание": ["Нуждается в повторении или наглядном показе инструкции", "Нуждается в помощи, чтобы вернуться к заданию после отвлечения"],
    "Адаптация и сенсорные реакции": ["Испытывает заметные трудности при переходе к новому заданию", "Реагирует на шум, свет или прикосновения так, что это мешает участию в занятии"],
}
CARDS = {
    "Классный руководитель": TEACHER_ITEMS,
    "Учитель-предметник": TEACHER_ITEMS,
    "Психолог": {
        "Эмоциональное состояние": ["Нуждается в поддержке при ошибке или неудаче", "Проявляет заметное напряжение в учебной ситуации"],
        "Взаимодействие": ["Нуждается в помощи для участия в совместной деятельности", "Нуждается в помощи, чтобы сообщить о своих потребностях"],
        "Учебная деятельность": ["Нуждается в поддержке, чтобы начать задание", "Нуждается в дополнительном времени при смене деятельности"],
    },
    "Логопед": {
        "Понимание речи": ["Нуждается в уточнении простого устного обращения", "Нуждается в дополнительном показе при выполнении устной инструкции"],
        "Выражение мысли": ["Испытывает трудности при словесном объяснении просьбы", "Нуждается в помощи, чтобы последовательно рассказать о событии"],
        "Звукопроизношение": ["Особенности произношения затрудняют понимание речи окружающими"],
    },
    "Дефектолог": {
        "Освоение заданий": ["Нуждается в повторном показе способа выполнения", "Нуждается в помощи, чтобы применить освоенный способ в похожем задании"],
        "Самостоятельность": ["Нуждается в помощи при подготовке материалов", "Нуждается в сопровождении для завершения посильного задания"],
        "Поддержка": ["Нуждается в наглядных опорах", "Нуждается в разделении задания на короткие шаги"],
    },
    "Педагог-ассистент": {
        "Участие и самостоятельность": ["Нуждается в подсказке, чтобы включиться в занятие", "Нуждается в сопровождении при переходе между школьными ситуациями"],
        "Обращение за помощью": ["Нуждается в поддержке, чтобы попросить помощь или перерыв", "Нуждается в помощи во взаимодействии со сверстниками"],
    },
}


def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with connect() as c:
        c.execute("CREATE TABLE IF NOT EXISTS pupils (id INTEGER PRIMARY KEY, code TEXT UNIQUE, grade TEXT, consent INTEGER DEFAULT 0, approved INTEGER DEFAULT 0, approver TEXT DEFAULT '', approved_at TEXT DEFAULT '')")
        c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, pupil_id INTEGER, day TEXT, role TEXT, author TEXT, situation TEXT, observation TEXT, strength TEXT, support TEXT, created_at TEXT)")
        columns = {row[1] for row in c.execute("PRAGMA table_info(notes)")}
        for name in ("card", "method"):
            if name not in columns:
                c.execute(f"ALTER TABLE notes ADD COLUMN {name} TEXT DEFAULT '{{}}'")
        if not c.execute("SELECT 1 FROM pupils").fetchone():
            c.execute("INSERT INTO pupils (code,grade,consent) VALUES ('ДЕМО-01','1 класс',1)")
            seed = [
                ("Классный руководитель", "А. А. Учитель", "Урок", "При смене задания ученику потребовалось дополнительное время, чтобы начать работу.", "Уверенно выполняет задания с наглядным образцом.", "Показать последовательность действий на карточке."),
                ("Учитель-предметник", "Б. Б. Учитель", "Общение", "Во время общей инструкции ученик дважды попросил повторить отдельный шаг.", "Охотно отвечает на конкретный вопрос.", "Давать короткую инструкцию по одному шагу."),
                ("Психолог", "В. В. Психолог", "Перемена", "При шуме в коридоре ученик отошёл в тихое место и вернулся после паузы.", "Сам обратился к взрослому за помощью.", "Предусмотреть спокойное место для короткого перерыва."),
            ]
            for role, author, situation, observation, strength, support in seed:
                c.execute("INSERT INTO notes (pupil_id,day,role,author,situation,observation,strength,support,created_at) VALUES (1,?,?,?,?,?,?,?,?)", (date.today().isoformat(), role, author, situation, observation, strength, support, datetime.now().isoformat()))


def pupil():
    with connect() as c:
        return c.execute("SELECT * FROM pupils WHERE id=1").fetchone()


def notes():
    with connect() as c:
        return c.execute("SELECT * FROM notes WHERE pupil_id=1 ORDER BY day,id").fetchall()


def pdf_document(title, sections, footer):
    pdfmetrics.registerFont(TTFont("DejaVu", FONT))
    pdfmetrics.registerFont(TTFont("DejaVuBold", BOLD))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="BirgeTitle", fontName="DejaVuBold", fontSize=15, leading=21, alignment=TA_CENTER, spaceAfter=15))
    styles.add(ParagraphStyle(name="BirgeHead", fontName="DejaVuBold", fontSize=10, leading=15, spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="BirgeBody", fontName="DejaVu", fontSize=9, leading=14, spaceAfter=6))
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(595,842), leftMargin=48, rightMargin=48, topMargin=50, bottomMargin=50)
    story = [Paragraph(html.escape(title), styles["BirgeTitle"])]
    for heading, items in sections:
        story.append(Paragraph(html.escape(heading), styles["BirgeHead"]))
        for item in items:
            story.append(Paragraph(html.escape(item).replace("\n", "<br/>"), styles["BirgeBody"]))
    story += [Spacer(1,16), Paragraph(html.escape(footer), styles["BirgeBody"])]
    doc.build(story)
    return buffer.getvalue()


def parent_sections(p, rows):
    return [
        ("Сведения", [f"Код ученика: {p['code']}. Класс: {p['grade']}. Дата: {date.today().strftime('%d.%m.%Y')}."]),
        ("Сильные стороны", [f"• {r['strength']}" for r in rows if r['strength']] or ["Пока нет записей."]),
        ("Наблюдения в школе", [f"• {r['situation']}: {r['observation']}" for r in rows] or ["Пока нет записей."]),
        ("Какая поддержка предлагается", [f"• {r['support']}" for r in rows if r['support']] or ["Пока нет предложений."]),
        ("Следующий шаг", ["Обсудить наблюдения с семьёй. При необходимости семья может обратиться за консультацией в ПМПК."]),
    ]


def internal_sections(p, rows):
    out = [("Статус", [f"Код: {p['code']}; класс: {p['grade']}; согласие на работу специалистов: {'отмечено' if p['consent'] else 'не отмечено'}."])]
    for r in rows:
        out.append((f"{r['role']} | {r['day']} | {r['author']}", [f"Ситуация: {r['situation']}. Наблюдение: {r['observation']}", f"Сильная сторона: {r['strength'] or 'не указана'}", f"Приём поддержки: {r['support'] or 'не указан'}"]))
        card = json.loads(r["card"] or "{}")
        if card.get("answers"):
            out.append(("Карта наблюдений", ["Период: " + (card.get("period") or "не указан")] + [f"{q}: {a}" for q, a in card["answers"].items()]))
        method = json.loads(r["method"] or "{}")
        if method.get("Название"):
            out.append(("Методика специалиста", [f"{k}: {v}" for k, v in method.items() if v]))

    out.append(("Для обсуждения консилиумом", ["Сопоставить наблюдения в разных условиях, обсудить с родителями способы поддержки и решить, нужны ли дополнительные консультации."]))
    return out


init()
p = pupil()
rows = notes()
st.title("Бірге: от диагноза к результату")
st.caption("Совместная работа педагогов, специалистов и семьи")
st.info("Демоверсия показывает совместную работу школы. Она не проводит диагностику и не даёт медицинского заключения. Встроенный текст протокола составляется по шаблону; подключение ИИ планируется отдельно.")
role = st.sidebar.selectbox("Кабинет", ROLES)
st.sidebar.write("**Ученик:** ДЕМО-01 · 1 класс")
st.sidebar.caption("Переключение ролей без пароля доступно только в демоверсии. Не вводите реальные данные детей.")

if role == "Руководитель консилиума":
    st.header("Согласие и проверка документов")
    consent = st.checkbox("Получено согласие законного представителя на работу специалистов школы", value=bool(p["consent"]))
    if consent != bool(p["consent"]):
        with connect() as c:
            c.execute("UPDATE pupils SET consent=?,approved=0,approver='',approved_at='' WHERE id=1", (int(consent),))
        st.rerun()
    st.subheader("Внутренний проект протокола")
    st.write(f"Записей специалистов: **{len(rows)}**")
    for r in rows:
        with st.expander(f"{r['role']} · {r['day']} · {r['situation']}"):
            st.write(r['observation'])
            st.write("**Сильная сторона:**", r['strength'])
            st.write("**Предложенный приём:**", r['support'])
            card_data = json.loads(r["card"] or "{}")
            if card_data.get("answers"):
                st.caption("Период: " + (card_data.get("period") or "не указан"))
                for question, answer in card_data["answers"].items():
                    st.write(f"{question}: {answer}")
            method_data = json.loads(r["method"] or "{}")
            if method_data.get("Название"):
                st.markdown("**Методика специалиста**")
                for key, value in method_data.items():
                    if value: st.write(f"{key}: {value}")
    st.download_button("Скачать внутренний проект PDF", pdf_document("Бірге · проект протокола наблюдений", internal_sections(p,rows), "Демонстрационный документ. Не является диагностическим заключением."), file_name="birge_internal_demo.pdf", mime="application/pdf")
    st.subheader("Сводка для родителей")
    st.caption("Сайт не отправляет документ автоматически. Руководитель проверяет содержание до передачи семье.")
    for title, items in parent_sections(p, rows):
        st.markdown(f"**{title}**")
        for item in items: st.write(item)
    with st.form("approve"):
        approver = st.text_input("ФИО руководителя консилиума", value=p["approver"])
        approve = st.form_submit_button("Утвердить сводку для родителей", disabled=not bool(p["consent"]) or not rows)
        if approve:
            if not approver.strip(): st.error("Укажите ФИО руководителя.")
            else:
                with connect() as c:
                    c.execute("UPDATE pupils SET approved=1, approver=?, approved_at=? WHERE id=1", (approver.strip(),datetime.now().strftime("%d.%m.%Y %H:%M")))
                st.rerun()
    if p["approved"]:
        st.success(f"Утверждено: {p['approver']} · {p['approved_at']}")
        st.download_button("Скачать PDF для родителей", pdf_document("Бірге · сводка наблюдений для родителей", parent_sections(p,rows), f"Проверил(а): {p['approver']}. {p['approved_at']}. Документ не содержит диагноза."), file_name="birge_parents_demo.pdf", mime="application/pdf", type="primary")
    else:
        st.warning("Скачать родительскую сводку можно после утверждения.")
else:
    st.header(f"Кабинет: {role}")
    if not p["consent"] and role not in ("Классный руководитель", "Учитель-предметник"):
        st.warning("Записи специалиста станут доступны после отметки о согласии родителей руководителем консилиума.")
    else:
        with st.form("new_note", clear_on_submit=True):
            author = st.text_input("Фамилия и инициалы сотрудника")
            day = st.date_input("Дата наблюдения", value=date.today())
            situation = st.selectbox("Где это произошло", SITUATIONS)
            st.subheader("Карта наблюдений")
            st.caption("Авторская карта для организации наблюдений, не стандартизированный тест. Оцените выбранную ситуацию за указанный период. Ответы не суммируются в диагностический балл.")
            period = st.text_input("Период наблюдения", placeholder="Например: первая учебная неделя октября")
            card = {}
            for section, questions in CARDS[role].items():
                st.markdown(f"**{section}**")
                for number, question in enumerate(questions):
                    card[question] = st.radio(question, ANSWERS, key=f"card_{role}_{section}_{number}", horizontal=True)
            st.subheader("Пример и способы поддержки")
            observation = st.text_area("Что именно наблюдали (без предположения о диагнозе)", placeholder="Опишите конкретный эпизод, без оценочных ярлыков")
            strength = st.text_area("Что у ребёнка получилось")
            support = st.text_area("Какой приём помог или предлагается попробовать")
            method = {}
            if role in ("Психолог", "Логопед", "Дефектолог"):
                st.subheader("Методики специалиста (необязательно)")
                st.caption("Укажите методику, которую вы действительно использовали: название, источник, возраст и языковую версию. Заполнение этих полей не подтверждает её валидность. Бланки тестов здесь не воспроизводятся.")
                method_name = st.text_input("Название методики")
                method_source = st.text_input("Источник и версия")
                method_age = st.text_input("Возрастной диапазон и язык")
                method_result = st.text_area("Результат и профессиональная интерпретация")
                method = {"Название": method_name, "Источник и версия": method_source, "Возраст и язык": method_age, "Результат": method_result}
            if st.form_submit_button("Сохранить наблюдение", type="primary"):
                if not author.strip() or not observation.strip(): st.error("Укажите автора и конкретный пример наблюдения.")
                else:
                    with connect() as c:
                        c.execute("INSERT INTO notes (pupil_id,day,role,author,situation,observation,strength,support,created_at) VALUES (1,?,?,?,?,?,?,?,?)", (day.isoformat(),role,author.strip(),situation,observation.strip(),strength.strip(),support.strip(),datetime.now().isoformat()))
                        new_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
                        c.execute("UPDATE notes SET card=?, method=? WHERE id=?", (json.dumps({"period": period, "answers": card}, ensure_ascii=False), json.dumps(method, ensure_ascii=False), new_id))
                        c.execute("UPDATE pupils SET approved=0,approver='',approved_at='' WHERE id=1")
                    st.rerun()
    st.subheader("История наблюдений")
    for r in reversed(rows):
        st.markdown(f"**{r['day']} · {r['role']} · {r['situation']}**")
        st.write(r["observation"])
