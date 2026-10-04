"""Build the final A4 technical report as a styled PDF."""

# pylint: disable=line-too-long,too-many-arguments,too-many-positional-arguments
# pylint: disable=too-many-locals,too-many-statements,non-ascii-name

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    CondPageBreak,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

from analise import (
    BLUE,
    CORAL,
    CREAM,
    GRAY,
    INK,
    LIGHT_GRAY,
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
OUTPUT = PROJECT_DIR / "relatorio_tecnico_rota_em_dia.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/noto")


pdfmetrics.registerFont(TTFont("NotoSans", FONT_DIR / "NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Bold", FONT_DIR / "NotoSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoSans-Italic", FONT_DIR / "NotoSans-Italic.ttf"))
pdfmetrics.registerFontFamily(
    "NotoSans",
    normal="NotoSans",
    bold="NotoSans-Bold",
    italic="NotoSans-Italic",
)


class ReportDocTemplate(SimpleDocTemplate):
    """Collect section entries while ReportLab builds the document."""

    def afterFlowable(self, flowable):
        """Register first- and second-level headings in the table of contents."""
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in {"Heading1", "Heading2"}:
            return
        level = 0 if style_name == "Heading1" else 1
        text = flowable.getPlainText()
        key = f"section-{level}-{self.page}-{abs(hash(text))}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


def hex_color(value: str):
    """Convert a hexadecimal color to a ReportLab color."""
    return colors.HexColor(value)


def draw_image_contain(canvas, path: Path, x, y, width, height):
    """Draw an image inside a fixed box without distortion."""

    with PILImage.open(path) as image:
        ratio = image.width / image.height
    box_ratio = width / height
    if ratio >= box_ratio:
        draw_width = width
        draw_height = width / ratio
        draw_x = x
        draw_y = y + (height - draw_height) / 2
    else:
        draw_height = height
        draw_width = height * ratio
        draw_x = x + (width - draw_width) / 2
        draw_y = y
    canvas.drawImage(
        str(path),
        draw_x,
        draw_y,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )


def cover_page(canvas, _doc):
    """Draw the full-page cover."""
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(hex_color(CREAM))
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setFillColor(hex_color(TEAL))
    canvas.rect(0, 170, width, 485, fill=1, stroke=0)
    canvas.setFillColor(hex_color(MINT))
    canvas.rect(0, 0, width, 170, fill=1, stroke=0)
    canvas.setFillColor(hex_color(YELLOW))
    canvas.circle(26, height - 28, 42, fill=1, stroke=0)
    canvas.setFillColor(hex_color(CORAL))
    canvas.circle(width - 26, 185, 34, fill=1, stroke=0)

    draw_image_contain(canvas, ASSET_DIR / "logo-uea.png", 45, height - 105, 150, 62)
    draw_image_contain(canvas, ASSET_DIR / "logo-sialabs.png", width - 114, height - 115, 68, 78)
    draw_image_contain(canvas, ASSET_DIR / "logo-rota-em-dia.png", width - 248, 425, 192, 145)

    canvas.setFont("NotoSans-Bold", 10)
    canvas.setFillColor(hex_color(YELLOW))
    canvas.drawString(54, 548, "RELATÓRIO TÉCNICO · PROJETO INTEGRADOR")
    canvas.setFont("NotoSans-Bold", 34)
    canvas.setFillColor(colors.white)
    canvas.drawString(54, 492, "Rota em Dia")
    canvas.setFont("NotoSans", 17)
    canvas.drawString(54, 456, "Análise da pontualidade do transporte fretado")
    canvas.setStrokeColor(hex_color(YELLOW))
    canvas.setLineWidth(3)
    canvas.line(54, 432, 165, 432)
    canvas.setFont("NotoSans", 10.5)
    canvas.drawString(54, 402, "Fundamentos de IA e Programação")
    canvas.drawString(54, 384, "Viagens de fevereiro a maio de 2026")

    canvas.setFillColor(hex_color(INK))
    canvas.setFont("NotoSans-Bold", 8)
    canvas.drawString(54, 135, "EQUIPE")
    canvas.setFont("NotoSans", 8.5)
    canvas.drawString(54, 118, "Juliana Ballin Lima")
    canvas.drawString(54, 103, "Fernanda de Oliveira da Costa")
    canvas.drawString(54, 88, "Pedro Henrique Oliveira Dias")
    canvas.setFont("NotoSans-Bold", 8)
    canvas.drawString(300, 135, "INSTITUIÇÃO")
    canvas.setFont("NotoSans", 8.5)
    canvas.drawString(300, 118, "Universidade do Estado do Amazonas")
    canvas.drawString(300, 103, "SiaLabs")
    canvas.setFont("NotoSans-Bold", 8)
    canvas.drawString(300, 77, "DATA")
    canvas.setFont("NotoSans", 8.5)
    canvas.drawString(300, 60, "Outubro de 2026 · Manaus, AM")
    canvas.restoreState()


def later_pages(canvas, doc):
    """Draw the header and footer used after the cover."""
    width, height = A4
    canvas.saveState()
    canvas.setStrokeColor(hex_color(MINT))
    canvas.setLineWidth(0.8)
    canvas.line(doc.leftMargin, height - 44, width - doc.rightMargin, height - 44)
    canvas.setFillColor(hex_color(TEAL))
    canvas.setFont("NotoSans-Bold", 7.5)
    canvas.drawString(doc.leftMargin, height - 36, "Rota em Dia | Relatório técnico")
    canvas.setFillColor(hex_color(GRAY))
    canvas.setFont("NotoSans", 7)
    canvas.drawRightString(width - doc.rightMargin, height - 36, "Fundamentos de IA e Programação")
    canvas.setStrokeColor(hex_color(LIGHT_GRAY))
    canvas.line(doc.leftMargin, 37, width - doc.rightMargin, 37)
    canvas.setFillColor(hex_color(GRAY))
    canvas.setFont("NotoSans", 7)
    canvas.drawString(doc.leftMargin, 25, "Universidade do Estado do Amazonas · SiaLabs")
    canvas.drawRightString(width - doc.rightMargin, 25, f"Página {doc.page}")
    canvas.restoreState()


def build_styles():
    """Create the report typography and paragraph styles."""
    sample = getSampleStyleSheet()
    styles = {
        "Body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="NotoSans",
            fontSize=9,
            leading=13.5,
            textColor=hex_color(INK),
            alignment=TA_JUSTIFY,
            spaceAfter=7,
        ),
        "BodySmall": ParagraphStyle(
            "BodySmall",
            parent=sample["BodyText"],
            fontName="NotoSans",
            fontSize=7.5,
            leading=10.5,
            textColor=hex_color(INK),
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            parent=sample["Heading1"],
            fontName="NotoSans-Bold",
            fontSize=17,
            leading=21,
            textColor=hex_color(TEAL),
            spaceBefore=4,
            spaceAfter=10,
            keepWithNext=True,
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=sample["Heading2"],
            fontName="NotoSans-Bold",
            fontSize=12.5,
            leading=16,
            textColor=hex_color(TEAL),
            spaceBefore=9,
            spaceAfter=6,
            keepWithNext=True,
        ),
        "TOCTitle": ParagraphStyle(
            "TOCTitle",
            parent=sample["Heading1"],
            fontName="NotoSans-Bold",
            fontSize=20,
            textColor=hex_color(TEAL),
            spaceAfter=14,
        ),
        "FigureTitle": ParagraphStyle(
            "FigureTitle",
            parent=sample["BodyText"],
            fontName="NotoSans-Bold",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=hex_color(TEAL),
            spaceBefore=5,
            spaceAfter=5,
            keepWithNext=True,
        ),
        "Caption": ParagraphStyle(
            "Caption",
            parent=sample["BodyText"],
            fontName="NotoSans-Italic",
            fontSize=7,
            leading=9.5,
            alignment=TA_CENTER,
            textColor=hex_color(GRAY),
            spaceBefore=4,
            spaceAfter=9,
        ),
        "Callout": ParagraphStyle(
            "Callout",
            parent=sample["BodyText"],
            fontName="NotoSans-Bold",
            fontSize=11.5,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.white,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=sample["BodyText"],
            fontName="NotoSans",
            fontSize=8.7,
            leading=12,
            leftIndent=12,
            firstLineIndent=-8,
            bulletIndent=2,
            alignment=TA_JUSTIFY,
            textColor=hex_color(INK),
            spaceAfter=4,
        ),
    }
    return styles


def paragraph(text: str, style):
    """Create a report paragraph."""
    return Paragraph(text, style)


def bullet(text: str, styles):
    """Create a compact bullet paragraph."""
    return Paragraph(f"•&nbsp;&nbsp;{text}", styles["Bullet"])


def styled_table(data, widths, *, header=True, font_size=7.3, alignments=None):
    """Create a striped table with the project palette."""
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "NotoSans"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 3),
        ("TEXTCOLOR", (0, 0), (-1, -1), hex_color(INK)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, hex_color("#B8C9C9")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), hex_color(TEAL)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "NotoSans-Bold"),
            ]
        )
        for row in range(1, len(data)):
            if row % 2 == 0:
                commands.append(("BACKGROUND", (0, row), (-1, row), hex_color("#EFF6F3")))
    if alignments:
        for column, alignment in enumerate(alignments):
            commands.append(("ALIGN", (column, 0), (column, -1), alignment))
    table.setStyle(TableStyle(commands))
    return table


def metric_cards(metrics):
    """Create the three headline metric cards."""
    cards = []
    values = [
        (f"{metrics['punctuality']:.1f}%", "pontualidade geral"),
        (f"{metrics['median_delay']:.0f} min", "mediana do atraso"),
        (f"{metrics['after_shift']}", "viagens após o início do turno"),
    ]
    for value, label in values:
        cards.append(
            Table(
                [
                    [Paragraph(value, ParagraphStyle(
                        "Metric", fontName="NotoSans-Bold", fontSize=19,
                        textColor=hex_color(CORAL), alignment=TA_CENTER, leading=22
                    ))],
                    [Paragraph(label, ParagraphStyle(
                        "MetricLabel", fontName="NotoSans", fontSize=7.5,
                        textColor=hex_color(INK), alignment=TA_CENTER, leading=10
                    ))],
                ],
                colWidths=[5.05 * cm],
                rowHeights=[0.72 * cm, 0.66 * cm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), hex_color(CREAM)),
                        ("BOX", (0, 0), (-1, -1), 0.8, hex_color(MINT)),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                ),
            )
        )
    return Table([[cards[0], cards[1], cards[2]]], colWidths=[5.2 * cm] * 3)


def figure(path: Path, title: str, caption: str, styles, width=16.0 * cm):
    """Create a titled figure with a centered explanatory caption."""

    with PILImage.open(path) as image:
        ratio = image.height / image.width
    image = Image(str(path), width=width, height=width * ratio)
    return KeepTogether(
        [
            Paragraph(title, styles["FigureTitle"]),
            image,
            Paragraph(caption, styles["Caption"]),
        ]
    )


def build_report() -> Path:
    """Build and save the complete technical report."""
    raw = read_raw_data()
    data, quality = clean_data(raw)
    metrics = summary_metrics(data)
    styles = build_styles()

    left_margin = 1.65 * cm
    right_margin = 1.65 * cm
    top_margin = 1.8 * cm
    bottom_margin = 1.55 * cm
    doc = ReportDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=right_margin,
        leftMargin=left_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        title="Rota em Dia · Relatório técnico",
        author="Juliana Ballin Lima; Fernanda de Oliveira da Costa; Pedro Henrique Oliveira Dias",
        subject="Análise da pontualidade do transporte fretado",
    )
    page_frame = Frame(
        left_margin,
        bottom_margin,
        doc.width,
        doc.height,
        id="report-frame",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(
                id="First",
                frames=page_frame,
                onPage=cover_page,
                autoNextPageTemplate="Later",
            ),
            PageTemplate(id="Later", frames=page_frame, onPage=later_pages),
        ]
    )

    story = [Spacer(1, doc.height - 2), PageBreak()]

    story.extend(
        [
            Paragraph("Sumário", styles["TOCTitle"]),
        ]
    )
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1", fontName="NotoSans-Bold", fontSize=9.5, leading=16,
            leftIndent=0, firstLineIndent=0, textColor=hex_color(TEAL),
        ),
        ParagraphStyle(
            "TOC2", fontName="NotoSans", fontSize=8.3, leading=14,
            leftIndent=14, firstLineIndent=0, textColor=hex_color(INK),
        ),
    ]
    story.extend([toc, CondPageBreak(20 * cm)])

    story.extend(
        [
            Paragraph("1. Resumo executivo", styles["Heading1"]),
            paragraph(
                "Este relatório investiga por que os atrasos do transporte fretado aumentaram, onde se concentram e quais evidências sustentam a explicação mais plausível. Foram analisadas viagens de oito rotas e três turnos entre 2 de fevereiro e 30 de maio de 2026. A análise segue as quatro etapas do curso: exploração inicial, estatística descritiva, limpeza reproduzível e análise exploratória com visualizações.",
                styles["Body"],
            ),
            metric_cards(metrics),
            Spacer(1, 9),
            Table(
                [[Paragraph(
                    "A pontualidade de R03 e R05 caiu nos turnos diurnos desde 6 de abril; obras no corredor são a explicação mais plausível, a confirmar com GPS e cronogramas.",
                    styles["Callout"],
                )]],
                colWidths=[16.0 * cm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), hex_color(TEAL)),
                        ("BOX", (0, 0), (-1, -1), 0, colors.white),
                        ("LEFTPADDING", (0, 0), (-1, -1), 16),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                        ("TOPPADDING", (0, 0), (-1, -1), 15),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
                    ]
                ),
            ),
            Spacer(1, 10),
            paragraph(
                f"Após 6 de abril, a pontualidade de R03/R05 nos turnos da manhã e tarde cai para {metrics['target_punctuality']:.1f}%, contra {metrics['other_punctuality']:.1f}% nas demais rotas diurnas. A mediana do atraso do grupo crítico chega a {metrics['target_median']:.0f} minutos, enquanto as demais rotas chegam {abs(metrics['other_median']):.0f} minutos adiantadas. O padrão aparece antes da atribuição de causa e permanece após a limpeza dos dados.",
                styles["Body"],
            ),
            Paragraph("1.1 Decisão analítica", styles["Heading2"]),
            bullet("A chuva forte tem associação com o atraso e funciona como agravante geral.", styles),
            bullet("Falhas mecânicas e pneus furados explicam casos severos, mas não uma ruptura sustentada.", styles),
            bullet("A hipótese de restrição diurna no corredor compartilhado por R03 e R05 é a mais consistente, sem constituir prova causal.", styles),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("2. Problema, objetivo e perguntas", styles["Heading1"]),
            Paragraph("2.1 Contexto", styles["Heading2"]),
            paragraph(
                "Os colaboradores de uma fábrica de eletroeletrônicos do Distrito Industrial de Manaus chegam em ônibus fretados. Cada veículo deve chegar à fábrica 15 minutos antes do início do turno. O aumento de reclamações motivou a análise do período chuvoso entre fevereiro e maio de 2026.",
                styles["Body"],
            ),
            Paragraph("2.2 Objetivo", styles["Heading2"]),
            paragraph(
                "Identificar quando a pontualidade se deteriorou, em quais rotas e turnos a mudança se concentra, quais hipóteses são compatíveis com os dados e quais informações adicionais são necessárias para confirmar a explicação operacional.",
                styles["Body"],
            ),
            Paragraph("2.3 Perguntas investigativas", styles["Heading2"]),
            bullet("A piora ocorre em toda a operação ou em grupos específicos?", styles),
            bullet("Duas rotas com atraso médio semelhante apresentam a mesma variabilidade?", styles),
            bullet("Existe um ponto de ruptura temporal ou apenas oscilação por chuva?", styles),
            bullet("Ocorrências severas representam casos isolados ou um padrão recorrente?", styles),
            bullet("A limpeza altera o diagnóstico inicial?", styles),
            Paragraph("2.4 Hipóteses concorrentes", styles["Heading2"]),
        ]
    )
    hypothesis_table = [
        ["Hipótese", "Evidência inicial", "Verificação necessária"],
        ["H1 · Chuva", "Período chuvoso e registros de chuva forte", "Comparar todas as rotas e períodos"],
        ["H2 · Corredor R03/R05", "Menor pontualidade nas duas rotas", "Localizar início, turno e ocorrência"],
        ["H3 · Ocorrências pontuais", "Pane, trânsito, pneu e obra", "Separar severidade de recorrência"],
    ]
    story.extend(
        [
            styled_table(hypothesis_table, [3.4 * cm, 6.0 * cm, 6.6 * cm], font_size=7.7),
            Spacer(1, 8),
            paragraph(
                "As hipóteses são tratadas como concorrentes. Um padrão que fortalece uma explicação também precisa ser comparado a evidências que poderiam enfraquecê-la. A conclusão final usa a expressão “mais plausível” e não “causa comprovada”.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("3. Dataset e método", styles["Heading1"]),
            Paragraph("3.1 Escopo da base", styles["Heading2"]),
            paragraph(
                f"A base bruta contém {len(raw):,} linhas e 11 colunas. Após remover 15 duplicatas exatas, permanecem {len(data):,} viagens, com 24 registros por dia de operação: oito rotas multiplicadas por três turnos. O calendário contém 102 dias de operação; domingos não aparecem e não foram tratados como ausência.",
                styles["Body"],
            ),
        ]
    )
    dictionary = [
        ["Campo", "Significado", "Uso principal"],
        ["data, turno", "Momento operacional", "Série temporal e recortes"],
        ["rota, zona_origem, empresa", "Estrutura do serviço", "Comparação entre grupos"],
        ["horario_previsto, horario_chegada", "Planejado e realizado", "Recálculo do atraso"],
        ["atraso_min", "Minutos adiantado ou atrasado", "Pontualidade e severidade"],
        ["passageiros", "Ocupação do veículo", "Validação de capacidade"],
        ["chuva_mm", "Chuva no período da viagem", "Associação com atraso"],
        ["ocorrencia", "Registro do motorista", "Contexto operacional"],
    ]
    story.extend(
        [
            styled_table(dictionary, [4.1 * cm, 6.8 * cm, 5.1 * cm], font_size=7.4),
            Paragraph("3.2 Indicadores", styles["Heading2"]),
            paragraph(
                "O indicador principal é a pontualidade: viagens que chegaram até cinco minutos após o horário previsto divididas pelo total de viagens com atraso válido. Indicadores complementares são a mediana do atraso e a proporção de viagens com atraso acima de 15 minutos, condição em que o ônibus chega depois do início do turno.",
                styles["Body"],
            ),
            Paragraph("3.3 Sequência analítica", styles["Heading2"]),
        ]
    )
    workflow = [[
        Paragraph("1<br/><b>observar</b>", styles["BodySmall"]),
        Paragraph("2<br/><b>comparar</b>", styles["BodySmall"]),
        Paragraph("3<br/><b>limpar</b>", styles["BodySmall"]),
        Paragraph("4<br/><b>explicar</b>", styles["BodySmall"]),
        Paragraph("5<br/><b>recomendar</b>", styles["BodySmall"]),
    ]]
    workflow_table = Table(workflow, colWidths=[3.1 * cm] * 5, rowHeights=[1.45 * cm])
    workflow_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), hex_color(BLUE)),
        ("BACKGROUND", (1, 0), (1, 0), hex_color(YELLOW)),
        ("BACKGROUND", (2, 0), (2, 0), hex_color(MINT)),
        ("BACKGROUND", (3, 0), (3, 0), hex_color(CORAL)),
        ("BACKGROUND", (4, 0), (4, 0), hex_color(TEAL)),
        ("TEXTCOLOR", (4, 0), (4, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
        ("INNERGRID", (0, 0), (-1, -1), 2, colors.white),
    ]))
    story.extend(
        [
            workflow_table,
            Spacer(1, 10),
            paragraph(
                "A base bruta é preservada. A análise inicial usa os campos como recebidos; a estatística identifica assimetria e extremos; o pipeline declara cada transformação; por fim, as visualizações respondem perguntas específicas. Essa sequência evita ajustar os dados para confirmar uma hipótese previamente escolhida.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("4. Limpeza, validação e rastreabilidade", styles["Heading1"]),
            paragraph(
                "O diagnóstico revelou problemas planejados para a atividade didática. Nenhuma linha foi eliminada por atraso alto legítimo, pane mecânica ou pneu furado. Apenas duplicatas comprovadamente idênticas foram removidas; os demais valores inválidos foram marcados como ausentes no campo afetado, preservando a viagem para análises compatíveis.",
                styles["Body"],
            ),
        ]
    )
    quality_rows = [["Problema", "Evidência", "Tratamento", "Impacto"]]
    for _, row in quality.iterrows():
        quality_rows.append([
            Paragraph(escape(str(row["problema"])), styles["BodySmall"]),
            Paragraph(escape(str(row["evidencia"])), styles["BodySmall"]),
            Paragraph(escape(str(row["tratamento"])), styles["BodySmall"]),
            Paragraph(escape(str(row["impacto"])), styles["BodySmall"]),
        ])
    story.extend(
        [
            styled_table(quality_rows, [3.1 * cm, 4.0 * cm, 5.2 * cm, 3.7 * cm], font_size=6.8),
            Paragraph("4.1 Decisões críticas", styles["Heading2"]),
            bullet("Os horários são padronizados para HH:MM e o atraso é recalculado para resolver 12 divergências.", styles),
            bullet("Seis atrasos acima de 12 horas são fisicamente incompatíveis com a operação descrita e ficam ausentes no indicador.", styles),
            bullet("Cinco valores de passageiros acima de 44 lugares ficam ausentes apenas nessa variável.", styles),
            bullet("As 145 ausências de chuva não são imputadas; o gráfico chuva × atraso usa somente pares observados.", styles),
            Paragraph("4.2 Antes e depois", styles["Heading2"]),
        ]
    )
    comparison_table = [
        ["Indicador", "Antes", "Depois"],
        ["Registros", f"{len(raw):,}", f"{len(data):,}"],
        ["Rótulos de rota", f"{raw['rota'].nunique()}", f"{data['rota'].nunique()}"],
        ["Rótulos de turno", f"{raw['turno'].nunique()}", f"{data['turno'].nunique()}"],
        ["Atraso médio", f"{raw['atraso_min'].mean():.2f} min", f"{data['atraso_min'].mean():.2f} min"],
        ["Pontualidade", f"{raw['atraso_min'].le(5).mean() * 100:.1f}%", f"{data['pontual'].mean() * 100:.1f}%"],
    ]
    story.extend(
        [
            styled_table(comparison_table, [6.0 * cm, 5.0 * cm, 5.0 * cm], font_size=8, alignments=["LEFT", "CENTER", "CENTER"]),
            Spacer(1, 8),
            paragraph(
                "A média cai de forma importante porque os extremos inválidos deixam de distorcer o resultado. A mediana, a ruptura temporal e a concentração em R03/R05 permanecem. Assim, a conclusão principal sobrevive ao processo de limpeza.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    route_summary = data.groupby("rota").agg(
        viagens=("atraso_min", "count"),
        pontualidade=("pontual", "mean"),
        média=("atraso_min", "mean"),
        mediana=("atraso_min", "median"),
        desvio=("atraso_min", "std"),
        após_turno=("apos_inicio_turno", "sum"),
    )
    route_summary["pontualidade"] *= 100
    route_rows = [["Rota", "Viagens", "Pontualidade", "Média", "Mediana", "Desvio", "> 15 min"]]
    for route, row in route_summary.iterrows():
        route_rows.append([
            route,
            f"{int(row['viagens'])}",
            f"{row['pontualidade']:.1f}%",
            f"{row['média']:.1f}",
            f"{row['mediana']:.1f}",
            f"{row['desvio']:.1f}",
            f"{int(row['após_turno'])}",
        ])
    story.extend(
        [
            Paragraph("5. Resultados", styles["Heading1"]),
            Paragraph("5.1 Visão geral e comparação por rota", styles["Heading2"]),
            paragraph(
                f"Na base tratada, a pontualidade geral é {metrics['punctuality']:.1f}%, a mediana do atraso é {metrics['median_delay']:.0f} minuto e {metrics['after_shift']} viagens ({metrics['after_shift_pct']:.1f}%) chegam depois do início do turno. A tabela evidencia que R03 e R05 são as únicas rotas com pontualidade abaixo de 70%.",
                styles["Body"],
            ),
            styled_table(route_rows, [2.0 * cm, 2.2 * cm, 3.0 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm], font_size=7.3, alignments=["LEFT", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "CENTER"]),
            Paragraph("5.2 Variabilidade", styles["Heading2"]),
            paragraph(
                "R03 e R05 apresentam mediana positiva e desvio padrão próximo de dez minutos. As demais rotas têm mediana negativa, indicando chegada adiantada, e dispersão menor. Esse contraste mostra por que duas médias parecidas em um recorte agregado não garantem o mesmo risco operacional.",
                styles["Body"],
            ),
            figure(
                CHART_DIR / "04_distribuicao_r03_r05.png",
                "Figura 1 · Distribuição do atraso em R03 e R05 antes e depois da ruptura",
                "A caixa representa o intervalo interquartil e a linha interna representa a mediana. Os pontos extremos foram ocultados apenas para facilitar a leitura; nenhum valor legítimo foi removido do cálculo.",
                styles,
                width=14.6 * cm,
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("6. Ruptura temporal e concentração", styles["Heading1"]),
            figure(
                CHART_DIR / "01_serie_rotas.png",
                "Figura 2 · R03 e R05 mudam de patamar a partir de 6 de abril",
                "Série da mediana diária com janela móvel de sete dias de operação. R03 e R05 são destacadas; as demais rotas ficam em cinza. A linha amarela marca 6 de abril de 2026.",
                styles,
                width=16.2 * cm,
            ),
            Paragraph("6.1 Evidência", styles["Heading2"]),
            paragraph(
                f"Até 4 de abril, R03 e R05 se comportam de forma semelhante às demais rotas. A partir de 6 de abril, a mediana móvel das duas rotas diurnas sobe para uma faixa de aproximadamente 7 a 15 minutos. No período posterior, a pontualidade do grupo crítico é {metrics['target_punctuality']:.1f}%, contra {metrics['other_punctuality']:.1f}% nas demais rotas diurnas.",
                styles["Body"],
            ),
            Paragraph("6.2 Interpretação e limitação", styles["Heading2"]),
            paragraph(
                "O padrão caracteriza uma mudança de patamar localizada. A coincidência temporal é consistente com uma nova restrição operacional, mas a série não identifica sozinha o evento responsável. A data de 6 de abril deve ser tratada como ponto de investigação, não como causalidade comprovada.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("7. Onde o problema se concentra", styles["Heading1"]),
            figure(
                CHART_DIR / "02_heatmap_rota_turno.png",
                "Figura 3 · Pontualidade por rota e turno após 6 de abril",
                "Os valores mostram o percentual de viagens pontuais. Cores quentes indicam menor pontualidade. O contraste isola R03 e R05 nos turnos da manhã e tarde.",
                styles,
                width=13.3 * cm,
            ),
            paragraph(
                "O heatmap reduz duas explicações alternativas. Primeiro, o problema não afeta todas as rotas da Viação Beta: R07 e R08 permanecem estáveis. Segundo, R03 e R05 alcançam 96% de pontualidade no turno noturno. A combinação rota × turno aponta para uma condição diurna no corredor compartilhado, e não para falha geral da empresa ou dos veículos.",
                styles["Body"],
            ),
            Paragraph("7.1 Mudança por turno", styles["Heading2"]),
        ]
    )
    turn_table = [
        ["Rota", "Manhã", "Tarde", "Noite", "Leitura"],
        ["R03", "10%", "40%", "96%", "Queda diurna severa"],
        ["R05", "4%", "21%", "96%", "Queda diurna severa"],
        ["Demais", "83% a 94%", "77% a 94%", "88% a 94%", "Operação preservada"],
    ]
    story.extend(
        [
            styled_table(turn_table, [2.4 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 6.1 * cm], font_size=7.7, alignments=["LEFT", "CENTER", "CENTER", "CENTER", "LEFT"]),
            Spacer(1, 9),
            paragraph(
                "O turno noturno funciona como grupo de comparação dentro das mesmas rotas. A estabilidade noturna enfraquece a hipótese de defeito permanente nos ônibus e fortalece a busca por uma condição de tráfego ou via que opere principalmente durante o dia.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    late = data[data["pontual"].eq(False)]
    occurrence_rows = [["Ocorrência", "Atrasos > 5 min", "% dos atrasos", "Mediana (min)", "> 15 min"]]
    occurrence_stats = late.groupby("ocorrencia").agg(
        viagens=("ocorrencia", "size"),
        mediana=("atraso_min", "median"),
        após=("apos_inicio_turno", "sum"),
    ).sort_values("viagens", ascending=False)
    for occurrence, row in occurrence_stats.iterrows():
        occurrence_rows.append([
            occurrence,
            f"{int(row['viagens'])}",
            f"{row['viagens'] / len(late) * 100:.1f}%",
            f"{row['mediana']:.1f}",
            f"{int(row['após'])}",
        ])
    story.extend(
        [
            Paragraph("8. Ocorrências e chuva", styles["Heading1"]),
            figure(
                CHART_DIR / "03_ocorrencias_atrasos.png",
                "Figura 4 · Viagens atrasadas por ocorrência registrada",
                "Contagem de viagens com atraso acima de cinco minutos. A categoria “Nenhuma” evidencia que o campo de ocorrência não explica sozinho todos os atrasos.",
                styles,
                width=14.8 * cm,
            ),
            styled_table(occurrence_rows, [4.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm], font_size=7.1, alignments=["LEFT", "CENTER", "CENTER", "CENTER", "CENTER"]),
            Paragraph("8.1 Severidade e recorrência", styles["Heading2"]),
            paragraph(
                "Chuva forte é a ocorrência mais frequente entre os atrasos. Pane mecânica tem mediana superior a 30 minutos e responde por muitos casos que ultrapassam o início do turno, porém aparece em apenas 30 viagens. Ocorrências severas justificam respostas operacionais próprias, mas sua baixa frequência não explica o deslocamento de toda a distribuição em R03/R05.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    rain = data.dropna(subset=["chuva_mm", "atraso_min"]).copy()
    correlation = rain[["chuva_mm", "atraso_min"]].corr(method="spearman").iloc[0, 1]
    rain["faixa"] = pd.cut(
        rain["chuva_mm"],
        [-0.001, 0, 10, 25, float("inf")],
        labels=["Sem chuva", "Leve (0-10]", "Moderada (10-25]", "Forte (>25)"],
    )
    rain_stats = rain.groupby("faixa", observed=True).agg(
        viagens=("atraso_min", "size"),
        pontualidade=("pontual", "mean"),
        mediana=("atraso_min", "median"),
        após=("apos_inicio_turno", "sum"),
    )
    rain_rows = [["Chuva", "Viagens", "Pontualidade", "Mediana", "> 15 min"]]
    for label, row in rain_stats.iterrows():
        rain_rows.append([
            str(label), f"{int(row['viagens'])}", f"{row['pontualidade'] * 100:.1f}%",
            f"{row['mediana']:.1f} min", f"{int(row['após'])}",
        ])
    story.extend(
        [
            Paragraph("9. Chuva como fator agravante", styles["Heading1"]),
            figure(
                CHART_DIR / "05_chuva_atraso.png",
                "Figura 5 · Chuva e atraso por grupo de rotas",
                "Cada ponto representa uma viagem com chuva e atraso observados. A linha tracejada marca cinco minutos. O eixo vertical foi limitado a 65 minutos para preservar a leitura dos casos operacionais.",
                styles,
                width=15.3 * cm,
            ),
            styled_table(rain_rows, [4.2 * cm, 2.8 * cm, 3.2 * cm, 3.0 * cm, 2.8 * cm], font_size=7.5, alignments=["LEFT", "CENTER", "CENTER", "CENTER", "CENTER"]),
            Spacer(1, 8),
            paragraph(
                f"A correlação de Spearman entre chuva e atraso é {correlation:.2f}, compatível com associação moderada. Acima de 25 mm, a pontualidade cai acentuadamente em toda a operação. Entretanto, depois de 6 de abril R03/R05 continuam atrasadas mesmo com chuva baixa, enquanto as demais rotas permanecem próximas do planejado. A chuva agrava, mas não é explicação suficiente para a ruptura localizada.",
                styles["Body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("10. Discussão das hipóteses", styles["Heading1"]),
        ]
    )
    final_hypotheses = [
        ["Hipótese", "Evidência a favor", "Evidência contra ou limitação", "Decisão"],
        [
            Paragraph("H1 · Chuva", styles["BodySmall"]),
            Paragraph("Associação moderada e 180 atrasos com chuva forte.", styles["BodySmall"]),
            Paragraph("Efeito geral; não coincide com a concentração em R03/R05.", styles["BodySmall"]),
            Paragraph("Agravante, não causa principal.", styles["BodySmall"]),
        ],
        [
            Paragraph("H2 · Corredor", styles["BodySmall"]),
            Paragraph("Ruptura em 06/04, somente diurna; obra surge em 07/04 apenas nas duas rotas.", styles["BodySmall"]),
            Paragraph("Faltam cronograma da obra e GPS para localizar o trecho.", styles["BodySmall"]),
            Paragraph("Mais plausível; precisa confirmação.", styles["BodySmall"]),
        ],
        [
            Paragraph("H3 · Ocorrências isoladas", styles["BodySmall"]),
            Paragraph("Pane e pneu causam atrasos severos.", styles["BodySmall"]),
            Paragraph("Poucos casos; não explicam deslocamento sustentado da distribuição.", styles["BodySmall"]),
            Paragraph("Rejeitada como explicação principal.", styles["BodySmall"]),
        ],
    ]
    story.extend(
        [
            styled_table(final_hypotheses, [3.0 * cm, 4.6 * cm, 4.9 * cm, 3.5 * cm], font_size=6.7),
            Paragraph("10.1 Explicação mais plausível", styles["Heading2"]),
            paragraph(
                "A explicação mais plausível é uma restrição diurna no corredor compartilhado pelas rotas R03 e R05, compatível com obra na via. A ruptura começa em 6 de abril; o primeiro registro de obra aparece em 7 de abril; os registros de obra se limitam às duas rotas; e o turno noturno permanece estável. O conjunto é coerente, mas ainda observacional.",
                styles["Body"],
            ),
            Paragraph("10.2 O que os dados não permitem afirmar", styles["Heading2"]),
            bullet("Não é possível provar que a obra causou os atrasos.", styles),
            bullet("Não é possível identificar o trecho crítico sem GPS ou tempo por segmento.", styles),
            bullet("O registro de ocorrência pode ser incompleto e depende do motorista.", styles),
            bullet("A chuva é medida no período da viagem, não ao longo de todo o percurso.", styles),
            Paragraph("10.3 Do gráfico exploratório ao explicativo", styles["Heading2"]),
            figure(
                CHART_DIR / "06_exploratorio_explicativo.png",
                "Figura 6 · Comparação entre a visão exploratória e a mensagem final",
                "A versão final reduz as oito linhas a dois grupos comparáveis, destaca a data de ruptura e mantém unidades e contexto. A seleção visual não altera os dados; apenas prioriza a mensagem sustentada pelas evidências.",
                styles,
                width=15.5 * cm,
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("11. Recomendações e próximos passos", styles["Heading1"]),
            Paragraph("11.1 Ações propostas", styles["Heading2"]),
        ]
    )
    actions = [
        ["Prioridade", "Ação", "Como medir", "Critério de decisão"],
        ["1", "Cruzar a janela com cronogramas e localização das obras públicas.", "Data, trecho e horário da intervenção.", "Coincidência espacial e temporal com R03/R05."],
        ["2", "Coletar GPS e tempo por trecho durante duas semanas.", "Mediana e P90 do tempo por segmento e turno.", "Trecho responsável pela maior variação diurna."],
        ["3", "Testar desvio ou saída 15 minutos antes em piloto controlado.", "Pontualidade, duração e impacto nos passageiros.", "Melhora sustentável sem ampliar excessivamente o tempo de viagem."],
    ]
    story.extend(
        [
            styled_table(actions, [2.1 * cm, 5.6 * cm, 4.4 * cm, 3.9 * cm], font_size=7.2),
            Paragraph("11.2 Monitoramento recomendado", styles["Heading2"]),
            bullet("Painel semanal de pontualidade por rota × turno, com mediana e P90 do atraso.", styles),
            bullet("Registro obrigatório de ocorrência para atrasos acima de cinco minutos.", styles),
            bullet("Alerta quando a mediana móvel de sete dias superar cinco minutos por três dias de operação.", styles),
            bullet("Revisão do piloto após duas semanas, comparando com as demais rotas e com o turno noturno.", styles),
            Paragraph("11.3 Pontos de aprendizado", styles["Heading2"]),
            bullet("A média geral pode esconder um problema localizado em rota, turno e período.", styles),
            bullet("A limpeza deve ser rastreável e preservar observações legítimas, mesmo quando são extremas.", styles),
            bullet("Mediana e distribuição são mais informativas que a média quando há assimetria.", styles),
            bullet("Associação visual, sequência temporal e plausibilidade operacional não substituem evidência causal.", styles),
            bullet("Um gráfico explicativo exige título afirmativo, contraste funcional, anotação e remoção de ruído.", styles),
            PageBreak(),
        ]
    )

    story.extend(
        [
            Paragraph("12. Conclusão", styles["Heading1"]),
            paragraph(
                "A análise mostra que o problema não é uma piora uniforme do transporte fretado. O principal movimento ocorre a partir de 6 de abril de 2026 nas rotas R03 e R05, durante manhã e tarde. A pontualidade noturna das mesmas rotas permanece elevada, e as demais rotas mantêm desempenho próximo do planejado.",
                styles["Body"],
            ),
            paragraph(
                "A chuva forte aumenta o risco de atraso em toda a operação e precisa ser considerada no planejamento. Contudo, ela não explica por que apenas R03 e R05 mudam de patamar. A sequência temporal, a concentração diurna e os registros de obra exclusivamente nas duas rotas tornam a restrição no corredor compartilhado a explicação mais plausível. A confirmação depende do cruzamento com cronogramas de obra e dados de GPS.",
                styles["Body"],
            ),
            Table(
                [[Paragraph(
                    "Conclusão técnica: evidência suficiente para priorizar investigação e piloto operacional, mas insuficiente para declarar causalidade.",
                    styles["Callout"],
                )]],
                colWidths=[16.0 * cm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), hex_color(CORAL)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 16),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                    ("TOPPADDING", (0, 0), (-1, -1), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
                ]),
            ),
            Paragraph("12.1 Reprodutibilidade", styles["Heading2"]),
            paragraph(
                "O arquivo transporte_fretado_rota_em_dia.ipynb contém a exploração, as estatísticas, o pipeline de limpeza, as cinco visualizações, a revisão das hipóteses e a preparação da narrativa. O arquivo pode ser aberto no Google Colab e executado integralmente com o CSV entregue na mesma pasta.",
                styles["Body"],
            ),
            Paragraph("12.2 Materiais do curso utilizados", styles["Heading2"]),
            bullet("Unidade 1: fundamentos de Python para dados e IA.", styles),
            bullet("Unidade 2: tendência central, variabilidade, quartis e outliers.", styles),
            bullet("Unidade 3: diagnóstico, padronização, filtragem e rastreabilidade.", styles),
            bullet("Unidade 4: barras, linhas, boxplot, dispersão, heatmap e leitura crítica.", styles),
            Spacer(1, 18),
            HRFlowable(width="100%", thickness=1, color=hex_color(MINT)),
            Spacer(1, 8),
            paragraph(
                "Arquivos principais: notebook Colab, apresentação em PowerPoint, relatório técnico em PDF, CSV bruto, CSV tratado, logo do projeto e gráficos de apoio.",
                styles["BodySmall"],
            ),
        ]
    )

    doc.multiBuild(story)
    return OUTPUT


if __name__ == "__main__":
    print(build_report())
