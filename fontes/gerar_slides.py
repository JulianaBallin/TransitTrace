"""Build the eight-slide presentation for the final project."""

# pylint: disable=line-too-long,missing-function-docstring
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from analise import (
    BLUE,
    CORAL,
    CREAM,
    INK,
    MINT,
    TEAL,
    YELLOW,
    clean_data,
    read_raw_data,
    summary_metrics,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_DIR / "assets"
CHART_DIR = PROJECT_DIR / "graficos"
OUTPUT = PROJECT_DIR / "apresentacao_rota_em_dia.pptx"
FONT = "Noto Sans"


def rgb(hex_color: str) -> RGBColor:
    value = hex_color.lstrip("#")
    return RGBColor.from_string(value)


def set_background(slide, color: str) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = rgb(color)


def add_text(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: float = 20,
    color: str = INK,
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    valign=MSO_ANCHOR.TOP,
    margin: float = 0.04,
    font: str = FONT,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    paragraph.text = text
    paragraph.font.name = font
    paragraph.font.size = Pt(size)
    paragraph.font.bold = bold
    paragraph.font.color.rgb = rgb(color)
    return box


def add_multiline(
    slide,
    lines: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: float = 18,
    color: str = INK,
    bullet: bool = False,
    spacing: float = 8,
):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.08)
    for index, line in enumerate(lines):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.font.name = FONT
        paragraph.font.size = Pt(size)
        paragraph.font.color.rgb = rgb(color)
        paragraph.space_after = Pt(spacing)
        if bullet:
            paragraph.text = f"•  {line}"
    return box


def add_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: str = CREAM,
    radius=True,
    line: str | None = None,
):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(color)
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1.2)
    else:
        shape.line.fill.background()
    return shape


def add_picture_contain(slide, path: Path, x: float, y: float, w: float, h: float):
    with Image.open(path) as image:
        source_ratio = image.width / image.height
    box_ratio = w / h
    if source_ratio >= box_ratio:
        width = w
        height = w / source_ratio
        left = x
        top = y + (h - height) / 2
    else:
        height = h
        width = h * source_ratio
        left = x + (w - width) / 2
        top = y
    return slide.shapes.add_picture(
        str(path), Inches(left), Inches(top), width=Inches(width), height=Inches(height)
    )


def add_doodles(slide, *, light: bool = True) -> None:
    pale = CREAM if light else TEAL
    colors = [YELLOW, CORAL, BLUE, pale]
    doodles = [
        (MSO_SHAPE.OVAL, -0.22, -0.20, 0.74, 0.74, colors[0]),
        (MSO_SHAPE.ARC, 12.40, -0.18, 0.95, 0.95, colors[2]),
        (MSO_SHAPE.STAR_8_POINT, 12.48, 6.62, 0.70, 0.70, colors[1]),
        (MSO_SHAPE.MOON, -0.24, 6.55, 0.72, 0.72, colors[3]),
    ]
    for shape_type, x, y, w, h, color in doodles:
        shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(color)
        shape.line.fill.background()


def add_header(slide, title: str, number: str, *, color: str = INK) -> None:
    add_text(slide, number, 0.45, 0.35, 0.55, 0.35, size=13, color=color, bold=True)
    add_text(slide, title, 0.88, 0.26, 11.6, 0.7, size=27, color=color, bold=True)


def add_metric_card(slide, value: str, label: str, x: float, y: float, w: float, color: str):
    add_card(slide, x, y, w, 1.25, color=CREAM)
    add_text(slide, value, x + 0.14, y + 0.13, w - 0.28, 0.52, size=25, color=color, bold=True)
    add_text(slide, label, x + 0.14, y + 0.69, w - 0.28, 0.38, size=11.5, color=INK)


def add_bus_drawing(slide, x: float, y: float, scale: float = 1.0) -> None:
    body = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x), Inches(y), Inches(2.0 * scale), Inches(1.2 * scale),
    )
    body.fill.solid()
    body.fill.fore_color.rgb = rgb(TEAL)
    body.line.fill.background()
    window = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(x + 0.24 * scale), Inches(y + 0.19 * scale),
        Inches(1.52 * scale), Inches(0.48 * scale),
    )
    window.fill.solid()
    window.fill.fore_color.rgb = rgb(BLUE)
    window.line.fill.background()
    for wheel_x in [x + 0.32 * scale, x + 1.48 * scale]:
        wheel = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(wheel_x), Inches(y + 0.98 * scale),
            Inches(0.34 * scale), Inches(0.34 * scale),
        )
        wheel.fill.solid()
        wheel.fill.fore_color.rgb = rgb(INK)
        wheel.line.fill.background()
    for lamp_x in [x + 0.24 * scale, x + 1.58 * scale]:
        lamp = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(lamp_x), Inches(y + 0.77 * scale),
            Inches(0.16 * scale), Inches(0.16 * scale),
        )
        lamp.fill.solid()
        lamp.fill.fore_color.rgb = rgb(YELLOW)
        lamp.line.fill.background()


def slide_cover(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CREAM)
    add_doodles(slide)
    add_picture_contain(slide, ASSET_DIR / "logo-rota-em-dia.png", 0.45, 0.78, 5.0, 4.7)
    add_text(slide, "Rota em Dia", 5.25, 1.28, 7.0, 0.9, size=42, color=TEAL, bold=True)
    add_text(
        slide,
        "Por que os ônibus fretados\nestão chegando atrasados?",
        5.28,
        2.14,
        6.8,
        1.25,
        size=25,
        color=INK,
        bold=False,
    )
    add_card(slide, 5.25, 3.64, 6.7, 1.34, color=MINT)
    add_text(slide, "Fundamentos de IA e Programação", 5.55, 3.92, 6.1, 0.35, size=16, color=TEAL, bold=True)
    add_text(slide, "Projeto integrador · outubro de 2026", 5.55, 4.34, 6.1, 0.3, size=13, color=INK)
    add_text(
        slide,
        "Juliana Ballin Lima  ·  Fernanda de Oliveira da Costa  ·  Pedro Henrique Oliveira Dias",
        0.76,
        6.58,
        11.8,
        0.34,
        size=11.5,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    add_picture_contain(slide, ASSET_DIR / "logo-uea.png", 10.42, 0.20, 1.35, 0.58)
    add_picture_contain(slide, ASSET_DIR / "logo-sialabs.png", 11.85, 0.12, 0.94, 0.74)


def slide_summary(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, MINT)
    add_doodles(slide, light=False)
    add_header(slide, "sumário", "01", color=TEAL)
    items = [
        ("1", "o problema", "Atrasos no transporte fretado"),
        ("2", "as perguntas", "Três hipóteses concorrentes"),
        ("3", "o dataset", "2.463 viagens e auditoria"),
        ("4", "o achado", "R03 e R05 desde 06/04"),
        ("5", "a demonstração", "Notebook Colab executável"),
    ]
    for index, (number, title, subtitle) in enumerate(items):
        x = 0.84 + (index % 3) * 4.07
        y = 1.45 + (index // 3) * 2.20
        w = 3.55 if index < 3 else 5.58
        if index >= 3:
            x = 0.84 + (index - 3) * 5.95
        add_card(slide, x, y, w, 1.65, color=CREAM)
        add_text(slide, number, x + 0.20, y + 0.18, 0.55, 0.55, size=28, color=CORAL, bold=True)
        add_text(slide, title, x + 0.82, y + 0.20, w - 1.02, 0.42, size=18, color=TEAL, bold=True)
        add_text(slide, subtitle, x + 0.82, y + 0.73, w - 1.05, 0.45, size=12, color=INK)
    add_bus_drawing(slide, 9.92, 5.46, 0.9)


def slide_problem(prs: Presentation, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CORAL)
    add_doodles(slide, light=False)
    add_header(slide, "o problema", "02", color=CREAM)
    add_card(slide, 0.72, 1.22, 7.35, 3.55, color=CREAM)
    add_text(
        slide,
        "Colaboradores chegam atrasados à linha porque os ônibus fretados não cumprem o horário planejado.",
        1.08,
        1.58,
        6.65,
        1.12,
        size=24,
        color=TEAL,
        bold=True,
    )
    add_text(
        slide,
        "O RH precisa saber se a piora é geral, onde ela se concentra e qual explicação os dados realmente sustentam.",
        1.08,
        3.03,
        6.5,
        0.88,
        size=16,
        color=INK,
    )
    add_metric_card(slide, "8", "rotas", 8.48, 1.30, 1.75, TEAL)
    add_metric_card(slide, "3", "turnos", 10.39, 1.30, 1.75, CORAL)
    add_metric_card(slide, "≤ 5 min", "limite de pontualidade", 8.48, 2.82, 3.66, TEAL)
    add_metric_card(slide, "15 min", "margem até o início do turno", 8.48, 4.34, 3.66, CORAL)
    add_bus_drawing(slide, 1.05, 5.34, 0.9)
    add_text(
        slide,
        f"Pontualidade geral tratada: {metrics['punctuality']:.1f}%",
        3.25,
        5.66,
        4.7,
        0.48,
        size=18,
        color=CREAM,
        bold=True,
    )
    add_text(slide, "fev · mar · abr · mai", 8.78, 6.35, 3.2, 0.34, size=13, color=CREAM, bold=True, align=PP_ALIGN.CENTER)


def slide_questions(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CREAM)
    add_doodles(slide)
    add_header(slide, "perguntas e hipóteses", "03")
    add_card(slide, 0.78, 1.12, 11.75, 1.18, color=TEAL)
    add_text(
        slide,
        "A queda é geral por causa da chuva ou está concentrada em rotas, turnos e períodos específicos?",
        1.15,
        1.43,
        11.0,
        0.58,
        size=21,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    cards = [
        ("H1", "chuva", "A chuva forte explica a piora de pontualidade.", BLUE),
        ("H2", "corredor", "R03 e R05 enfrentam uma restrição compartilhada.", CORAL),
        ("H3", "ocorrências", "Pane, trânsito e pneus explicam a mudança.", YELLOW),
    ]
    for index, (label, title, text, color) in enumerate(cards):
        x = 0.82 + index * 4.16
        add_card(slide, x, 2.75, 3.68, 2.85, color=color)
        add_text(slide, label, x + 0.25, 2.99, 0.72, 0.54, size=25, color=TEAL, bold=True)
        add_text(slide, title, x + 1.02, 3.05, 2.25, 0.45, size=18, color=TEAL, bold=True)
        add_text(slide, text, x + 0.30, 3.81, 3.05, 0.90, size=15, color=INK, align=PP_ALIGN.CENTER)
        add_text(slide, "testar · comparar · limitar", x + 0.42, 5.03, 2.80, 0.25, size=10, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Não buscamos uma resposta escondida. Construímos a explicação mais defensável.", 1.8, 6.35, 9.8, 0.38, size=16, color=TEAL, bold=True, align=PP_ALIGN.CENTER)


def slide_dataset(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, TEAL)
    add_doodles(slide, light=False)
    add_header(slide, "dataset e qualidade", "04", color=CREAM)
    add_metric_card(slide, "2.463", "linhas recebidas", 0.76, 1.23, 2.24, CORAL)
    add_metric_card(slide, "11", "variáveis", 3.18, 1.23, 2.24, TEAL)
    add_metric_card(slide, "102", "dias de operação", 5.60, 1.23, 2.24, BLUE)
    add_metric_card(slide, "2.448", "viagens após deduplicar", 8.02, 1.23, 3.15, CORAL)
    add_card(slide, 0.76, 2.88, 5.61, 3.55, color=CREAM)
    add_text(slide, "o que a base descreve", 1.04, 3.12, 4.9, 0.4, size=19, color=TEAL, bold=True)
    add_multiline(
        slide,
        [
            "data, turno, rota, zona e empresa",
            "horários previsto e realizado",
            "atraso, passageiros e chuva",
            "ocorrência registrada pelo motorista",
        ],
        1.04,
        3.73,
        4.92,
        2.2,
        size=15,
        bullet=True,
        spacing=11,
    )
    add_card(slide, 6.68, 2.88, 5.80, 3.55, color=MINT)
    add_text(slide, "o que precisou de cuidado", 6.99, 3.12, 5.1, 0.4, size=19, color=TEAL, bold=True)
    issues = [
        ("15", "duplicatas exatas"),
        ("145", "chuvas ausentes"),
        ("12", "atrasos divergentes"),
        ("6 + 5", "atrasos e lotações inválidos"),
    ]
    for index, (value, label) in enumerate(issues):
        y = 3.78 + index * 0.57
        add_text(slide, value, 7.01, y, 0.9, 0.32, size=16, color=CORAL, bold=True, align=PP_ALIGN.RIGHT)
        add_text(slide, label, 8.10, y, 3.8, 0.32, size=14, color=INK)
    add_text(slide, "Base bruta preservada · regras reproduzíveis", 7.15, 6.02, 4.75, 0.26, size=11.5, color=TEAL, bold=True, align=PP_ALIGN.CENTER)


def slide_result(prs: Presentation, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CREAM)
    add_doodles(slide)
    add_header(slide, "resultado principal", "05")
    add_picture_contain(slide, CHART_DIR / "01_serie_rotas.png", 0.55, 1.07, 8.85, 5.85)
    add_card(slide, 9.62, 1.33, 3.05, 1.38, color=CORAL)
    add_text(slide, "06/04", 9.84, 1.56, 2.58, 0.48, size=28, color=CREAM, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "início da ruptura", 9.84, 2.09, 2.58, 0.28, size=12, color=CREAM, align=PP_ALIGN.CENTER)
    add_card(slide, 9.62, 3.02, 3.05, 1.38, color=MINT)
    add_text(slide, f"{metrics['target_punctuality']:.0f}%", 9.84, 3.24, 2.58, 0.48, size=28, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "pontualidade R03/R05 · dia", 9.76, 3.79, 2.72, 0.28, size=11.5, color=TEAL, align=PP_ALIGN.CENTER)
    add_card(slide, 9.62, 4.72, 3.05, 1.38, color=YELLOW)
    add_text(slide, f"{metrics['target_median']:.0f} min", 9.84, 4.95, 2.58, 0.48, size=28, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "mediana de atraso", 9.84, 5.49, 2.58, 0.28, size=12, color=TEAL, align=PP_ALIGN.CENTER)


def slide_evidence(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, YELLOW)
    add_doodles(slide, light=False)
    add_header(slide, "evidências e conclusão", "06", color=TEAL)
    add_picture_contain(slide, CHART_DIR / "02_heatmap_rota_turno.png", 0.55, 1.06, 6.58, 5.78)
    cards = [
        ("chuva agrava", "Correlação moderada, mas o efeito aparece em toda a operação.", BLUE),
        ("obra localiza", "“Obra na via” surge em 07/04 somente em R03 e R05.", CORAL),
        ("noite preserva", "As duas rotas mantêm 96% de pontualidade no turno noturno.", MINT),
    ]
    for index, (title, text, color) in enumerate(cards):
        y = 1.23 + index * 1.48
        add_card(slide, 7.27, y, 5.45, 1.18, color=color)
        add_text(slide, title, 7.55, y + 0.16, 1.65, 0.37, size=16, color=TEAL, bold=True)
        add_text(slide, text, 9.13, y + 0.15, 3.25, 0.70, size=12.5, color=INK)
    add_card(slide, 7.27, 5.72, 5.45, 0.88, color=TEAL)
    add_text(
        slide,
        "Hipótese mais plausível: restrição diurna no corredor compartilhado.",
        7.54,
        5.95,
        4.92,
        0.42,
        size=16,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
    )


def slide_notebook(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CREAM)
    add_doodles(slide)
    add_header(slide, "demonstração do notebook", "07")
    add_card(slide, 0.70, 1.13, 7.52, 5.88, color="#F2F5F5", line=TEAL)
    add_card(slide, 0.94, 1.42, 7.04, 0.50, color=TEAL)
    add_text(slide, "Rota em Dia · Google Colab", 1.19, 1.55, 4.2, 0.22, size=12, color=CREAM, bold=True)
    steps = [
        ("1", "carregar", "CSV + diagnóstico"),
        ("2", "investigar", "estatística + hipóteses"),
        ("3", "limpar", "pipeline + validação"),
        ("4", "explicar", "5 gráficos + conclusão"),
    ]
    for index, (number, title, detail) in enumerate(steps):
        y = 2.20 + index * 1.03
        add_card(slide, 1.10, y, 6.68, 0.78, color=CREAM, line="#D0DADA")
        add_text(slide, number, 1.31, y + 0.15, 0.48, 0.38, size=19, color=CORAL, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, title, 1.98, y + 0.15, 1.72, 0.33, size=15, color=TEAL, bold=True)
        add_text(slide, detail, 3.65, y + 0.16, 3.62, 0.33, size=13, color=INK)
    add_card(slide, 8.55, 1.20, 4.12, 2.08, color=MINT)
    add_text(slide, "executar tudo", 8.91, 1.56, 3.42, 0.45, size=24, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "16 células de código\n20 células de texto", 8.91, 2.25, 3.42, 0.62, size=14, color=INK, align=PP_ALIGN.CENTER)
    add_card(slide, 8.55, 3.63, 4.12, 2.45, color=CORAL)
    add_text(slide, "próximos passos", 8.89, 3.92, 3.45, 0.40, size=20, color=CREAM, bold=True, align=PP_ALIGN.CENTER)
    add_multiline(
        slide,
        ["cruzar cronograma de obras", "coletar GPS por trecho", "testar desvio ou antecipação"],
        8.93,
        4.53,
        3.30,
        1.28,
        size=13,
        color=CREAM,
        bullet=True,
        spacing=6,
    )
    add_text(slide, "perguntas?", 9.15, 6.53, 3.0, 0.38, size=20, color=TEAL, bold=True, align=PP_ALIGN.CENTER)


def build_slides() -> Path:
    raw = read_raw_data()
    data, _ = clean_data(raw)
    metrics = summary_metrics(data)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    prs.core_properties.title = "Rota em Dia · Transporte fretado"
    prs.core_properties.subject = "Projeto integrador de Fundamentos de IA e Programação"
    prs.core_properties.author = "Juliana Ballin Lima; Fernanda de Oliveira da Costa; Pedro Henrique Oliveira Dias"
    prs.core_properties.keywords = "transporte fretado, análise de dados, pontualidade"

    slide_cover(prs)
    slide_summary(prs)
    slide_problem(prs, metrics)
    slide_questions(prs)
    slide_dataset(prs)
    slide_result(prs, metrics)
    slide_evidence(prs)
    slide_notebook(prs)

    prs.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build_slides())
