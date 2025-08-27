# app.py
# ------------------------------------------------------------------------------
# Streamlit front-end para el Content Project Manager (CrewAI)
# - Inputs del proyecto (incluye Project Start Date)
# - Ejecuta el crew, muestra resultados
# - PDF con Gantt por persona (chunking, auto-escala, legibilidad mejorada)
# - Fallback: si assignments no tienen fechas, construye Gantt desde tasks
# - Log de ejecución persistente (expander)
# - Previsualización del Gantt en la interfaz
# ------------------------------------------------------------------------------

import os
import sys
import json
import re
import io
from io import BytesIO
from math import ceil
from datetime import datetime, date, timedelta
from contextlib import redirect_stdout, redirect_stderr

import streamlit as st
from dotenv import load_dotenv

# ReportLab
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
)

# Matplotlib para el Gantt (imagen)
import matplotlib
matplotlib.use("Agg")  # backend sin UI
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, AutoDateLocator, DateFormatter

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Project Manager",
    page_icon="🗂️",
    layout="wide",
)

load_dotenv()

ROOT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from content_marketing_project_manager.crew import ContentMarketingProjectManager

# ---------- Helpers -----------------------------------------------------------

def run_crew(inputs: dict):
    """Ejecuta el crew y devuelve (resultado, usage, log_text). Captura stdout/stderr."""
    crew_instance = ContentMarketingProjectManager().crew()
    out_buf, err_buf = io.StringIO(), io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        result = crew_instance.kickoff(inputs=inputs)
        crew_instance.calculate_usage_metrics()
    usage = crew_instance.usage_metrics
    log_text = out_buf.getvalue() + ("\n" + err_buf.getvalue() if err_buf.getvalue() else "")
    return result, usage, log_text


def format_cost(usage):
    cost_per_token = 0.150 / 1_000_000  # ajustar según el modelo
    total_tokens = (usage.prompt_tokens or 0) + (usage.completion_tokens or 0)
    total_cost = total_tokens * cost_per_token
    return total_tokens, total_cost


def safe_slug(texto: str, maxlen: int = 80) -> str:
    """Slug seguro para nombre de archivo."""
    if not texto:
        return "content-project-plan"
    s = re.sub(r"[^A-Za-z0-9\- _]+", "", texto).strip().lower()
    s = re.sub(r"\s+", "-", s)
    return (s or "content-project-plan")[:maxlen]


# ======== Parsing de fechas robusto ===========================================

_WEEK_DAY_RE = re.compile(r"week\s*(\d+)\s*\(?\s*day\s*(\d+)\s*\)?", re.I)
_WEEK_ONLY_RE = re.compile(r"week\s*(\d+)", re.I)

def parse_week_day_to_date(text: str, start_base: date) -> date | None:
    """
    Convierte 'Week 2 (Day 3)' => start_base + (2-1)*7 + (3-1) días.
    Si solo hay 'Week X', toma el día 1 de esa semana.
    """
    if not text:
        return None
    s = str(text)
    m = _WEEK_DAY_RE.search(s)
    if m:
        w = int(m.group(1))
        d = int(m.group(2))
        d = max(1, min(7, d))  # clamp 1..7
        return start_base + timedelta(days=(w - 1) * 7 + (d - 1))
    m2 = _WEEK_ONLY_RE.search(s)
    if m2:
        w = int(m2.group(1))
        return start_base + timedelta(days=(w - 1) * 7)  # día 1 de la semana
    return None


def parse_date_any(s) -> date | None:
    """Intenta parsear fechas comunes ISO/US/EU."""
    if not s:
        return None
    s = str(s).strip()
    fmts = [
        "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"
    ]
    for f in fmts:
        try:
            return datetime.strptime(s, f).date()
        except Exception:
            continue
    return None


def coerce_dates(a: dict, tasks_by_name: dict, start_base: date) -> tuple[date | None, date | None]:
    """
    Obtiene start/end para un assignment:
    - Usa fechas directas si vienen parseables.
    - Si vienen 'Week X (Day Y)', las convierte con start_base.
    - Si solo hay start y ETA en la tarea => end = start + ceil(eta/8)-1 días.
    - Si no hay nada, usa target_publish_date de la tarea como start=end.
    """
    start_txt = a.get("start_date")
    end_txt = a.get("end_date")
    start = parse_date_any(start_txt) or parse_week_day_to_date(start_txt, start_base)
    end = parse_date_any(end_txt) or parse_week_day_to_date(end_txt, start_base)

    if not start and not end:
        tname = a.get("task_name")
        t = tasks_by_name.get(tname) if tname else None
        tpub = parse_date_any(t.get("target_publish_date")) if t else None
        if tpub:
            return tpub, tpub

    if start and not end:
        tname = a.get("task_name")
        t = tasks_by_name.get(tname) if tname else None
        eta_h = None
        if t:
            try:
                eta_h = float(t.get("estimated_time_hours"))
            except Exception:
                eta_h = None
        if eta_h:
            dur_days = max(1, ceil(eta_h / 8.0))  # 8h/día
            end = start + timedelta(days=dur_days - 1)
        else:
            end = start

    if end and not start:
        start = end

    if start and end and end < start:
        start, end = end, start

    return start, end


# ======== Fallback: crear schedule desde tasks ================================

def first_person_from_required(res):
    """Extrae un nombre de required_resources (string, lista, dict...)."""
    if not res:
        return "Unassigned"
    if isinstance(res, str):
        token = re.split(r"[,/;|\n]+", res)
        return (token[0].strip() or "Unassigned")
    if isinstance(res, list) and res:
        return first_person_from_required(res[0])
    if isinstance(res, dict):
        return res.get("name") or res.get("assigned_to") or "Unassigned"
    return "Unassigned"


def fallback_rows_from_tasks(tasks: list, start_base: date):
    """
    Construye barras a partir de tasks cuando assignments no tienen fechas:
    - Si hay target_publish_date → start = end - ETA/8 días.
    - Si no, encadena desde start_base en orden de lista.
    """
    rows = []
    current = start_base
    for t in tasks or []:
        tname = t.get("task_name") or "Task"
        eta_h = None
        try:
            eta_h = float(t.get("estimated_time_hours"))
        except Exception:
            eta_h = None
        dur_days = max(1, ceil((eta_h or 8.0) / 8.0))  # default 1 día si no hay ETA

        publish = parse_date_any(t.get("target_publish_date"))
        if publish:
            start = publish - timedelta(days=dur_days - 1)
            end = publish
            if start < start_base:
                start = start_base
        else:
            start = current
            end = start + timedelta(days=dur_days - 1)
            current = end + timedelta(days=1)

        person = first_person_from_required(t.get("required_resources"))
        rows.append({
            "person": person,
            "task": tname,
            "start": start,
            "end": end
        })
    return rows


# ======== Utilidades para etiquetas y anotaciones =============================

def _shorten(s: str, n: int) -> str:
    s = s or ""
    return s if len(s) <= n else (s[: max(0, n - 1)] + "…")


# ======== Gantt como imágenes (chunking + auto-escala + legibilidad) =========

def build_gantt_images(assignments: list, tasks: list, start_base: date,
                       max_rows_per_chart: int = 25) -> list[BytesIO]:
    """Devuelve una lista de PNGs (BytesIO) con uno o más gráficos Gantt."""
    tasks_by_name = {(t.get("task_name") or "").strip(): t for t in (tasks or [])}
    rows = []

    # 1) Intentar con assignments
    for a in assignments or []:
        start, end = coerce_dates(a, tasks_by_name, start_base)
        if not start or not end:
            continue
        assigned = a.get("assigned_to") or "Unassigned"
        task = a.get("task_name") or "Task"
        rows.append({"person": assigned, "task": task, "start": start, "end": end})

    # 2) Si no hay filas válidas, usar fallback desde tasks
    if not rows:
        rows = fallback_rows_from_tasks(tasks, start_base)

    if not rows:
        return []

    # Ordenar por persona y fecha
    rows.sort(key=lambda r: (r["person"], r["start"]))

    # Particionar en chunks para que cada gráfico sea legible
    chunks = [rows[i:i + max_rows_per_chart] for i in range(0, len(rows), max_rows_per_chart)]
    images = []

    for chunk in chunks:
        persons = [r["person"] for r in chunk]
        tasks_txt = [r["task"] for r in chunk]
        labels = [_shorten(p, 18) for p in persons]  # etiqueta del eje Y: SOLO persona (corta)
        starts = [date2num(datetime.combine(r["start"], datetime.min.time())) for r in chunk]
        durations = [(r["end"] - r["start"]).days + 1 for r in chunk]

        uniq_persons = {p: i for i, p in enumerate(sorted(set(persons)))}
        colors_map = [plt.cm.tab20(uniq_persons[p] % 20) for p in persons]

        # Tamaño para no “estirar”: ancho 9" y alto proporcional a filas (con límites)
        fig_width = 9.0
        fig_height = max(3.2, min(8.0, 0.45 * len(chunk) + 1.4))
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        y_pos = list(range(len(chunk)))
        bars = ax.barh(
            y_pos, durations, left=starts, align="center",
            color=colors_map, edgecolor="black", linewidth=0.3, height=0.6
        )

        ax.set_yticks(y_pos, labels=labels)
        ax.invert_yaxis()

        # Rango X con padding para que las barras usen todo el ancho
        min_x = min(starts)
        max_x = max([s + d for s, d in zip(starts, durations)])
        pad_days = max(1, int((max_x - min_x) * 0.05))
        ax.set_xlim(min_x - pad_days, max_x + pad_days)

        # Menos ticks en X
        ax.xaxis.set_major_locator(AutoDateLocator(minticks=4, maxticks=8))
        ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=30, ha="right")

        ax.set_xlabel("Date")
        ax.set_title("Content Calendar — Gantt (by person)")
        ax.margins(y=0.08)
        ax.grid(axis="x", linestyle="--", alpha=0.3)

        # Anotar nombre de la tarea centrado en cada barra (recortado a 35 chars)
        for i, b in enumerate(bars):
            cx = b.get_x() + b.get_width() / 2.0
            cy = b.get_y() + b.get_height() / 2.0
            ax.text(cx, cy, _shorten(tasks_txt[i], 35), ha="center", va="center", fontsize=8, clip_on=True)

        # Ajuste de márgenes para reducir espacio izquierdo
        plt.subplots_adjust(left=0.18, right=0.98, top=0.88, bottom=0.22)
        fig.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        images.append(buf)

    return images


# ======== PDF ================================================================

def _p(text, styles):
    """Paragraph seguro (escapa caracteres especiales)."""
    if text is None:
        text = ""
    if not isinstance(text, str):
        try:
            text = json.dumps(text, ensure_ascii=False)
        except Exception:
            text = str(text)
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, styles["Small"])


def build_pdf(
    plan: dict,
    meta_title: str,
    meta_author: str,
    meta_subject: str,
    start_base: date
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["Normal"], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="List", parent=styles["Normal"], leftIndent=10, spaceAfter=4))
    story = []

    # Encabezado
    story.append(Paragraph("Content Project Plan", styles["Title"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Small"]))
    story.append(Paragraph(f"Project Start Date: {start_base.isoformat()}", styles["Small"]))
    story.append(Spacer(1, 12))

    # ---------- Tasks ----------
    story.append(Paragraph("Tasks", styles["Heading2"]))
    tasks = plan.get("tasks", [])
    if tasks:
        for t in tasks:
            txt = (
                f"<b>- {t.get('task_name','')}</b> "
                f"({t.get('format','')}) &nbsp; | &nbsp; "
                f"ETA: {t.get('estimated_time_hours','')}h &nbsp; | &nbsp; "
                f"Due: {t.get('target_publish_date') or 'TBD'}"
            )
            story.append(Paragraph(txt, styles["List"]))
    else:
        story.append(Paragraph("No tasks available.", styles["Italic"]))
    story.append(Spacer(1, 10))

    # ---------- Assignments ----------
    story.append(Paragraph("Assignments", styles["Heading2"]))
    assignments = plan.get("assignments", [])
    if assignments:
        for a in assignments:
            txt = (
                f"- {a.get('task_name','')} &rarr; <b>{a.get('assigned_to','')}</b> "
                f"({a.get('role','')}) "
                f"[{a.get('start_date','')} &rarr; {a.get('end_date') or '–'}]"
            )
            story.append(Paragraph(txt, styles["List"]))
    else:
        story.append(Paragraph("No assignments available.", styles["Italic"]))
    story.append(Spacer(1, 12))

    # ---------- Gantt (una o más imágenes, escaladas y con saltos de página) ----------
    story.append(Paragraph("Content Calendar (Gantt)", styles["Heading2"]))
    gantt_pngs = build_gantt_images(assignments, tasks, start_base)
    if gantt_pngs:
        for i, buf in enumerate(gantt_pngs):
            img = Image(buf)
            img.hAlign = "CENTER"
            # Escala la imagen para no exceder el área útil
            img._restrictSize(doc.width, doc.height - 1.0 * inch)
            story.append(img)
            if i < len(gantt_pngs) - 1:
                story.append(PageBreak())
    else:
        story.append(Paragraph("No schedulable items (missing/invalid dates).", styles["Small"]))

    # Metadatos del PDF
    def _add_meta(canvas, _doc):
        canvas.setTitle(meta_title)
        canvas.setAuthor(meta_author)
        canvas.setSubject(meta_subject)

    doc.build(story, onFirstPage=_add_meta, onLaterPages=_add_meta)
    buffer.seek(0)
    return buffer.getvalue()


# ---------- UI ----------------------------------------------------------------

st.title("🗂️ Content Project Manager")

with st.form("inputs_form"):
    st.subheader("Project Details")
    project_type = st.text_input("**Project Type**", value="", label_visibility="visible")
    industry = st.text_input("**Industry**", value="", label_visibility="visible")
    project_objectives = st.text_area("**Objectives**", value="", label_visibility="visible")
    project_requirements = st.text_area("**High-level Requirements (one per line)**", value="", label_visibility="visible")
    team_members = st.text_area("**Team Members (one per line)**", value="", label_visibility="visible")
    # Fecha base para inferir Week/Day y fallback
    project_start_date = st.date_input("**Project Start Date**", value=date.today())
    submitted = st.form_submit_button("Run Plan ✅")

# Session state para persistir resultados/pdf/log/nombre
for key in ("plan", "usage", "pdf_bytes", "exec_log", "pdf_name", "project_start_date"):
    if key not in st.session_state:
        st.session_state[key] = None

if submitted:
    with st.spinner("Running Ejecution ⏳"):
        inputs = dict(
            project_type=project_type,
            industry=industry,
            project_objectives=project_objectives,
            project_requirements=project_requirements,
            team_members=team_members,
        )
        output, usage, log_text = run_crew(inputs)
        plan = output.pydantic.dict()

        # Nombre y metadatos del PDF
        today = datetime.now().strftime("%Y%m%d")
        base = safe_slug(project_type or "content-project")
        pdf_name = f"{base}-{today}.pdf"
        meta_title = f"Content Project Plan — {project_type or 'Project'}"
        meta_author = "Content Project Manager"
        meta_subject = f"Industry: {industry or 'N/A'}"

        st.session_state.project_start_date = project_start_date

        pdf_bytes = build_pdf(
            plan,
            meta_title=meta_title,
            meta_author=meta_author,
            meta_subject=meta_subject,
            start_base=project_start_date,
        )

        st.session_state.plan = plan
        st.session_state.usage = usage
        st.session_state.exec_log = log_text
        st.session_state.pdf_bytes = pdf_bytes
        st.session_state.pdf_name = pdf_name

# ✅ Mensaje de éxito y expander del log **persistentes**
if st.session_state.plan:
    st.success("Ejecution Completed!")
    with st.expander("📜 Ver execution log (agentes, tareas, pasos)", expanded=False):
        st.code(st.session_state.exec_log or "No log available.", language="text")
        st.download_button(
            "⬇️ Descargar log (.txt)",
            data=(st.session_state.exec_log or "").encode("utf-8"),
            file_name="execution_log.txt",
            mime="text/plain",
        )

    usage = st.session_state.usage
    total_tokens, total_cost = format_cost(usage)
    st.caption(f"**Tokens:** {total_tokens}  •  **Estimated cost:** ${total_cost:.4f}")

    st.header("📋 Tasks")
    st.dataframe(st.session_state.plan.get("tasks", []))

    st.header("👥 Assignments")
    st.dataframe(st.session_state.plan.get("assignments", []))

    st.header("🎯 Milestones")
    st.dataframe(st.session_state.plan.get("milestones", []))

    # ======= Previsualización del Gantt en la interfaz =======
    st.header("📅 Content Calendar (Gantt)")
    gantt_imgs = build_gantt_images(
        st.session_state.plan.get("assignments", []),
        st.session_state.plan.get("tasks", []),
        st.session_state.project_start_date or date.today(),
        max_rows_per_chart=25,
    )
    if gantt_imgs:
        # Mostrar la primera imagen directamente
        st.image(gantt_imgs[0].getvalue(), caption="Gantt preview (chart 1)")

        # Si hay más gráficos, mostrarlos en un expander
        if len(gantt_imgs) > 1:
            with st.expander(f"Ver {len(gantt_imgs) - 1} gráfico(s) adicional(es)"):
                for i in range(1, len(gantt_imgs)):
                    st.image(gantt_imgs[i].getvalue(), caption=f"Gantt preview (chart {i+1})")
    else:
        st.write("No calendar summary.")

    # Botón de descarga de PDF
    st.download_button(
        label="📄 Download PDF",
        data=st.session_state.pdf_bytes,
        file_name=st.session_state.pdf_name or "content_project_plan.pdf",
        mime="application/pdf",
    )
