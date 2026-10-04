"""Build the nine-slide presentation, organized in the three-act storyboard."""

# pylint: disable=line-too-long,missing-function-docstring
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
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
OUTPUT = PROJECT_DIR / "docs" / "apresentacao" / "apresentacao_rota_em_dia.pptx"
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


def set_transparency(shape, percent: int = 80) -> None:
    """Set shape fill transparency through the DrawingML alpha channel."""
    solid_fill = shape.fill._xPr.solidFill  # pylint: disable=protected-access
    color_node = solid_fill.getchildren()[0]
    for alpha in color_node.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}alpha"):
        color_node.remove(alpha)
    alpha = OxmlElement("a:alpha")
    alpha.set("val", str((100 - percent) * 1000))
    color_node.append(alpha)


def add_transparent_shape(slide, shape_type, x, y, w, h, color, *, rotation=0):
    """Add a decorative shape with 80 percent transparency."""
    shape = slide.shapes.add_shape(
        shape_type, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(color)
    set_transparency(shape)
    shape.line.fill.background()
    shape.rotation = rotation
    return shape


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
        add_transparent_shape(slide, shape_type, x, y, w, h, color)

    add_transparent_shape(slide, MSO_SHAPE.OVAL, 10.85, 0.92, 1.25, 1.25, YELLOW)
    add_transparent_shape(slide, MSO_SHAPE.RECTANGLE, 11.43, 1.13, 0.09, 0.48, INK)
    add_transparent_shape(slide, MSO_SHAPE.RECTANGLE, 11.45, 1.50, 0.36, 0.09, INK, rotation=20)
    add_transparent_shape(slide, MSO_SHAPE.TEAR, 2.05, 5.85, 0.42, 0.58, BLUE, rotation=20)
    add_transparent_shape(slide, MSO_SHAPE.TEAR, 2.55, 6.23, 0.33, 0.46, BLUE, rotation=20)
    add_transparent_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 10.55, 5.72, 1.82, 0.94, TEAL)
    add_transparent_shape(slide, MSO_SHAPE.RECTANGLE, 10.84, 5.90, 1.22, 0.33, BLUE)
    add_transparent_shape(slide, MSO_SHAPE.OVAL, 10.83, 6.47, 0.31, 0.31, INK)
    add_transparent_shape(slide, MSO_SHAPE.OVAL, 11.78, 6.47, 0.31, 0.31, INK)


def add_header(slide, title: str, number: str, *, color: str = INK) -> None:
    add_text(slide, number, 0.45, 0.35, 0.55, 0.35, size=13, color=color, bold=True)
    add_text(slide, title, 0.88, 0.26, 11.6, 0.7, size=27, color=color, bold=True)


def add_metric_card(slide, value: str, label: str, x: float, y: float, w: float, color: str):
    add_card(slide, x, y, w, 1.25, color=CREAM)
    add_text(slide, value, x + 0.14, y + 0.13, w - 0.28, 0.52, size=25, color=color, bold=True)
    add_text(slide, label, x + 0.14, y + 0.69, w - 0.28, 0.38, size=11.5, color=INK)


def add_slide_number(slide, current: int, total: int) -> None:
    """Add a consistent page number to the bottom-right corner."""
    pill = add_card(slide, 12.18, 7.03, 0.78, 0.28, color=CREAM, line=TEAL)
    pill.fill.fore_color.rgb = rgb(CREAM)
    add_text(
        slide,
        f"{current}/{total}",
        12.22,
        7.055,
        0.70,
        0.20,
        size=9,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
        valign=MSO_ANCHOR.MIDDLE,
        margin=0,
    )


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
    add_picture_contain(slide, ASSET_DIR / "logo-rota-em-dia.png", 0.05, 0.42, 5.35, 5.25)
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
    add_text(slide, "Projeto Integrador · Outubro de 2026", 5.55, 4.34, 6.1, 0.3, size=13, color=INK)
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
    add_header(slide, "Sumário", "01", color=TEAL)
    items = [
        ("1", "O Problema", "R03 e R05 desde 06/04", CORAL),
        ("2", "A Investigação", "Três hipóteses testadas", YELLOW),
        ("3", "Os Dados", "O que a limpeza mudou", BLUE),
        ("4", "A Resolução", "Explicação mais plausível", CORAL),
        ("5", "As Ações", "Limites e próximos passos", CREAM),
    ]
    points = [(1.00, 2.05), (3.43, 3.18), (5.88, 2.05), (8.33, 3.18), (10.77, 2.05)]
    centers = [(x + 0.34, y + 0.34) for x, y in points]
    for start, end in zip(centers, centers[1:]):
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT,
            Inches(start[0]),
            Inches(start[1]),
            Inches(end[0]),
            Inches(end[1]),
        )
        connector.line.color.rgb = rgb(TEAL)
        connector.line.width = Pt(5)

    for index, ((number, title, subtitle, color), (x, y)) in enumerate(zip(items, points)):
        stop = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(0.68), Inches(0.68)
        )
        stop.fill.solid()
        stop.fill.fore_color.rgb = rgb(color)
        stop.line.color.rgb = rgb(TEAL)
        stop.line.width = Pt(2)
        add_text(
            slide,
            number,
            x + 0.08,
            y + 0.11,
            0.52,
            0.42,
            size=20,
            color=INK,
            bold=True,
            align=PP_ALIGN.CENTER,
            valign=MSO_ANCHOR.MIDDLE,
            margin=0,
        )
        label_y = 1.22 if index % 2 == 0 else 4.05
        add_card(slide, x - 0.52, label_y, 1.72, 1.04, color=CREAM, line=TEAL)
        add_text(slide, title, x - 0.42, label_y + 0.15, 1.52, 0.30, size=13.5, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, subtitle, x - 0.42, label_y + 0.52, 1.52, 0.31, size=9.8, color=INK, align=PP_ALIGN.CENTER)

    add_text(
        slide,
        "Uma Investigação Guiada Pelas Evidências",
        3.20,
        5.55,
        6.90,
        0.50,
        size=20,
        color=TEAL,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    add_bus_drawing(slide, 9.95, 5.38, 0.82)


def add_stat_card(slide, value: str, label: str, x: float, y: float, w: float, color: str):
    add_card(slide, x, y, w, 1.55, color=CREAM)
    add_text(slide, value, x + 0.18, y + 0.14, w - 0.36, 0.58, size=28, color=color, bold=True)
    add_text(slide, label, x + 0.18, y + 0.80, w - 0.36, 0.64, size=12.5, color=INK)


def pct(value: float) -> str:
    return f"{value:.0f}%"


def decimal(value: float, places: int = 2) -> str:
    return f"{value:.{places}f}".replace(".", ",")


def slide_problem(prs: Presentation, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CORAL)
    add_doodles(slide, light=False)
    add_header(slide, "Ato 1 · O Problema", "02", color=INK)
    add_card(slide, 0.72, 1.22, 11.9, 1.75, color=CREAM)
    add_text(
        slide,
        f"A pontualidade geral de {decimal(metrics['punctuality'], 1)}% esconde uma ruptura: "
        "R03 e R05 passaram a chegar atrasadas nos turnos diurnos desde 6 de abril.",
        1.08,
        1.50,
        11.2,
        1.2,
        size=24,
        color=TEAL,
        bold=True,
    )
    after_pct = metrics["target_after_shift"] / metrics["target_trips"] * 100
    add_stat_card(
        slide,
        f"{pct(metrics['before_target_punctuality'])} → {pct(metrics['target_punctuality'])}",
        "Pontualidade de R03/R05 de dia, antes e depois de 06/04",
        0.72, 3.30, 3.85, TEAL,
    )
    add_stat_card(
        slide,
        f"{metrics['target_median']:.0f} min",
        "Mediana do atraso das duas rotas de dia, para um limite de 5 min",
        4.74, 3.30, 3.85, CORAL,
    )
    add_stat_card(
        slide,
        f"{metrics['target_after_shift']} de {metrics['target_trips']}",
        f"viagens chegam depois do início do turno (demais rotas: {metrics['other_after_shift']})",
        8.76, 3.30, 3.86, TEAL,
    )
    add_card(slide, 0.72, 5.18, 11.9, 1.18, color=TEAL)
    add_text(
        slide,
        "Por que importa para a fábrica: o ônibus deve chegar 15 minutos antes do turno. "
        f"Com 12 minutos de atraso mediano a folga some, e {pct(after_pct)} dessas viagens "
        "chegam depois da hora de entrada.",
        1.05,
        5.38,
        11.2,
        0.82,
        size=15.5,
        color=CREAM,
        bold=True,
    )


def slide_when(prs: Presentation, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CREAM)
    add_doodles(slide)
    add_header(slide, "Ato 1 · Quando e onde começou", "03")
    add_picture_contain(slide, CHART_DIR / "01_serie_rotas.png", 0.55, 1.07, 8.85, 5.85)
    add_card(slide, 9.62, 1.33, 3.05, 1.38, color=CORAL)
    add_text(slide, "06/04", 9.84, 1.56, 2.58, 0.48, size=28, color=INK, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Início da ruptura", 9.84, 2.09, 2.58, 0.28, size=12, color=INK, align=PP_ALIGN.CENTER)
    add_card(slide, 9.62, 3.02, 3.05, 1.38, color=MINT)
    add_text(slide, "2 de 8 rotas", 9.76, 3.24, 2.78, 0.48, size=24, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "R03 e R05, ambas da zona Leste", 9.76, 3.79, 2.78, 0.28, size=11.5, color=TEAL, align=PP_ALIGN.CENTER)
    add_card(slide, 9.62, 4.72, 3.05, 1.38, color=YELLOW)
    add_text(slide, "Só de dia", 9.76, 4.95, 2.78, 0.48, size=24, color=TEAL, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Manhã e tarde; a noite segue em 96%", 9.76, 5.49, 2.78, 0.28, size=11.5, color=TEAL, align=PP_ALIGN.CENTER)


def slide_hypotheses(prs: Presentation, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CREAM)
    add_doodles(slide)
    add_header(slide, "Ato 2 · Três hipóteses testadas", "04")
    add_card(slide, 0.78, 1.12, 11.75, 1.0, color=TEAL)
    add_text(
        slide,
        "A queda é geral por causa da chuva ou está concentrada em rotas, turnos e períodos específicos?",
        1.15,
        1.38,
        11.0,
        0.55,
        size=20,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
    )
    cards = [
        (
            "H1", "Chuva", BLUE,
            "Parecia a explicação certa: em março todas as rotas pioram. "
            f"Mas sem chuva, R03/R05 têm {pct(metrics['dry_target_punctuality'])} de pontualidade "
            f"de dia e as demais, {pct(metrics['dry_other_punctuality'])}.",
            "Perdeu força · agravante",
        ),
        (
            "H2", "Corredor", CORAL,
            "A ruptura começa em 06/04, só de dia. “Obra na via” aparece em 07/04 "
            "apenas nessas duas rotas.",
            "Ganhou força · mais plausível",
        ),
        (
            "H3", "Ocorrências", YELLOW,
            f"Pane e pneu somam {metrics['mechanical_late']} viagens atrasadas. "
            "São casos severos e dispersos, que não deslocam a distribuição inteira.",
            "Rejeitada como causa principal",
        ),
    ]
    for index, (label, title, text_color, text, verdict) in enumerate(cards):
        x = 0.82 + index * 4.16
        add_card(slide, x, 2.42, 3.68, 3.72, color=text_color)
        add_text(slide, label, x + 0.25, 2.62, 0.72, 0.54, size=25, color=TEAL, bold=True)
        add_text(slide, title, x + 1.02, 2.68, 2.25, 0.45, size=18, color=TEAL, bold=True)
        add_text(slide, text, x + 0.28, 3.30, 3.12, 2.0, size=15, color=INK)
        add_card(slide, x + 0.24, 5.38, 3.20, 0.52, color=TEAL)
        add_text(
            slide, verdict, x + 0.28, 5.46, 3.12, 0.36, size=11.5, color=CREAM, bold=True,
            align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0,
        )
    add_text(slide, "Não buscamos uma resposta escondida. Construímos a explicação mais defensável.", 1.8, 6.4, 9.8, 0.38, size=15, color=TEAL, bold=True, align=PP_ALIGN.CENTER)


def slide_evidence(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, YELLOW)
    add_doodles(slide, light=False)
    add_header(slide, "Ato 2 · Onde o problema se concentra", "05", color=TEAL)
    add_picture_contain(slide, CHART_DIR / "02_heatmap_rota_turno.png", 0.55, 1.06, 6.58, 5.78)
    cards = [
        ("Chuva Agrava", "Correlação moderada (0,46): o efeito aparece em toda a operação, não só em duas rotas.", BLUE),
        ("Obra Localiza", "“Obra na via” surge em 07/04 somente em R03 e R05.", CORAL),
        ("Noite Preserva", "As duas rotas mantêm 96% de pontualidade no turno noturno.", MINT),
    ]
    for index, (title, text, color) in enumerate(cards):
        y = 1.23 + index * 1.48
        add_card(slide, 7.27, y, 5.45, 1.18, color=color)
        add_text(slide, title, 7.55, y + 0.16, 1.65, 0.37, size=16, color=TEAL, bold=True)
        add_text(slide, text, 9.13, y + 0.15, 3.45, 0.90, size=12.5, color=INK)
    add_card(slide, 7.27, 5.72, 5.45, 0.88, color=TEAL)
    add_text(
        slide,
        "Rota × turno: o problema é diurno e restrito a duas rotas.",
        7.54,
        5.95,
        4.92,
        0.42,
        size=16,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
    )


def slide_cleaning(prs: Presentation, raw_stats: dict, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, TEAL)
    add_doodles(slide, light=False)
    add_header(slide, "Ato 2 · O que a limpeza mudou", "06", color=CREAM)
    add_metric_card(slide, "2.463", "Linhas recebidas", 0.76, 1.23, 2.24, CORAL)
    add_metric_card(slide, "11", "Variáveis", 3.18, 1.23, 2.24, TEAL)
    add_metric_card(slide, "102", "Dias de operação", 5.60, 1.23, 2.24, BLUE)
    add_metric_card(slide, "2.448", "Viagens após deduplicar", 8.02, 1.23, 3.15, CORAL)
    add_card(slide, 0.76, 2.88, 5.61, 3.55, color=CREAM)
    add_text(slide, "Antes → Depois da Limpeza", 1.04, 3.12, 4.9, 0.4, size=19, color=TEAL, bold=True)
    changes = [
        (f"{decimal(raw_stats['mean'])} → {decimal(metrics['mean_delay'])}", "min · atraso médio"),
        (f"{decimal(raw_stats['punctuality'], 1)} → {decimal(metrics['punctuality'], 1)}", "% · pontualidade geral"),
        ("Intacta", "ruptura de R03/R05 em 06/04"),
    ]
    for index, (value, label) in enumerate(changes):
        y = 3.78 + index * 0.62
        add_text(slide, value, 1.04, y, 2.35, 0.34, size=16, color=CORAL, bold=True, align=PP_ALIGN.RIGHT)
        add_text(slide, label, 3.55, y + 0.02, 2.7, 0.32, size=13, color=INK)
    add_text(
        slide,
        "A média caiu porque seis atrasos de mais de 700 minutos saíram do cálculo. A conclusão principal sobrevive à limpeza.",
        1.04, 5.62, 5.05, 0.70, size=11.5, color=TEAL, bold=True,
    )
    add_card(slide, 6.68, 2.88, 5.80, 3.55, color=MINT)
    add_text(slide, "O Que Precisou de Cuidado", 6.99, 3.12, 5.1, 0.4, size=19, color=TEAL, bold=True)
    issues = [
        ("15", "Duplicatas exatas"),
        ("145", "Chuvas ausentes"),
        ("12", "Atrasos divergentes"),
        ("6 + 5", "Atrasos e lotações inválidos"),
    ]
    for index, (value, label) in enumerate(issues):
        y = 3.78 + index * 0.57
        add_text(slide, value, 7.01, y, 0.9, 0.32, size=16, color=CORAL, bold=True, align=PP_ALIGN.RIGHT)
        add_text(slide, label, 8.10, y, 3.8, 0.32, size=14, color=INK)
    add_text(slide, "Base bruta preservada · regras reproduzíveis", 7.15, 6.02, 4.75, 0.26, size=11.5, color=TEAL, bold=True, align=PP_ALIGN.CENTER)


def slide_resolution(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, CREAM)
    add_doodles(slide)
    add_header(slide, "Ato 3 · A explicação mais plausível", "07")
    add_picture_contain(slide, CHART_DIR / "06_exploratorio_explicativo.png", 0.55, 1.05, 12.2, 4.55)
    add_card(slide, 0.78, 5.78, 11.75, 1.12, color=TEAL)
    add_text(
        slide,
        "A pontualidade de R03 e R05 caiu nos turnos diurnos desde 6 de abril; obras no corredor "
        "são a explicação mais plausível, a confirmar com GPS e cronogramas.",
        1.10,
        5.98,
        11.1,
        0.76,
        size=16.5,
        color=CREAM,
        bold=True,
        align=PP_ALIGN.CENTER,
    )


def slide_next_steps(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_background(slide, BLUE)
    add_doodles(slide, light=False)
    add_header(slide, "Ato 3 · Limites e próximos passos", "08", color=INK)

    add_card(slide, 0.83, 1.25, 5.63, 3.55, color=CREAM, line=TEAL)
    add_text(slide, "O Que Ainda Não Podemos Afirmar", 1.13, 1.50, 5.0, 0.42, size=19, color=TEAL, bold=True)
    add_multiline(
        slide,
        [
            "Que a obra causou os atrasos: a base mostra coincidência no tempo e no lugar, não causa.",
            "Qual trecho da via é o gargalo: não há GPS nem tempo por trecho.",
            "Quanto o registro do motorista deixa de anotar: um terço dos atrasos não tem ocorrência.",
        ],
        1.10, 2.14, 5.10, 2.6, size=15, bullet=True, spacing=12,
    )

    add_card(slide, 6.86, 1.25, 5.63, 3.55, color=CREAM, line=TEAL)
    add_text(slide, "Ações Recomendadas", 7.16, 1.50, 5.0, 0.42, size=19, color=TEAL, bold=True)
    add_multiline(
        slide,
        [
            "1.  Cruzar o período com o cronograma e a localização das obras públicas.",
            "2.  Coletar GPS e tempo por trecho em R03 e R05 por duas semanas.",
            "3.  Testar desvio de rota ou saída 15 minutos antes nos turnos diurnos.",
        ],
        7.13, 2.14, 5.10, 2.6, size=15, spacing=12,
    )

    links = [
        (0.83, "Abrir Notebook no Colab",
         "https://colab.research.google.com/github/JulianaBallin/TransitTrace/blob/main/transporte_fretado_rota_em_dia.ipynb"),
        (6.86, "Abrir Relatório Técnico",
         "https://github.com/JulianaBallin/TransitTrace/blob/main/docs/relatorio/relatorio_tecnico_rota_em_dia.pdf"),
    ]
    for x, label, address in links:
        link = add_card(slide, x + 0.82, 5.18, 4.00, 0.72, color=TEAL)
        link_text = add_text(
            slide, label, x + 1.00, 5.37, 3.64, 0.28, size=13.5, color=CREAM, bold=True,
            align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, margin=0,
        )
        link_text.click_action.hyperlink.address = address
        link.click_action.hyperlink.address = address
    add_text(
        slide, "Análise completa e reproduzível no repositório TransitTrace", 2.34, 6.20, 8.64, 0.32,
        size=14, color=INK, bold=True, align=PP_ALIGN.CENTER,
    )
    add_text(slide, "Perguntas?", 5.17, 6.62, 3.0, 0.38, size=20, color=TEAL, bold=True, align=PP_ALIGN.CENTER)


def build_slides() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    raw = read_raw_data()
    data, _ = clean_data(raw)
    metrics = summary_metrics(data)
    raw_stats = {
        "mean": float(raw["atraso_min"].mean()),
        "punctuality": float(raw["atraso_min"].le(5).mean() * 100),
    }

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
    slide_when(prs, metrics)
    slide_hypotheses(prs, metrics)
    slide_evidence(prs)
    slide_cleaning(prs, raw_stats, metrics)
    slide_resolution(prs)
    slide_next_steps(prs)

    total = len(prs.slides)
    for current, slide in enumerate(prs.slides, start=1):
        add_slide_number(slide, current, total)

    prs.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build_slides())
