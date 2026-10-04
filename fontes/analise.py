"""Prepare, validate, analyze, and visualize the shuttle transport dataset."""

# pylint: disable=too-many-locals,too-many-statements

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_DIR / "dataset"
DATA_PATH = DATASET_DIR / "projeto_integrador_transporte_fretado.csv"
CHART_DIR = PROJECT_DIR / "graficos"

CREAM = "#FFF8E8"
TEAL = "#005A67"
MINT = "#65C3A5"
CORAL = "#F06449"
YELLOW = "#F6BD38"
BLUE = "#37A9E8"
INK = "#17343A"
GRAY = "#A7B0B3"
LIGHT_GRAY = "#E8EEEE"


def read_raw_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Read the preserved source CSV."""
    return pd.read_csv(path)


def parse_dates(values: pd.Series) -> pd.Series:
    """Parse the ISO and day-first layouts of the source file explicitly.

    ``format="mixed"`` with ``dayfirst=True`` swaps day and month of ISO strings
    in pandas 3, so each known layout is parsed on its own.
    """
    text = values.astype("string").str.strip()
    is_iso = text.str.fullmatch(r"\d{4}-\d{2}-\d{2}").fillna(False)
    parsed = pd.to_datetime(text.where(is_iso), format="%Y-%m-%d", errors="coerce")
    return parsed.fillna(
        pd.to_datetime(text.where(~is_iso), format="%d/%m/%Y", errors="coerce")
    )


def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the declared cleaning rules and return data plus an audit log."""
    data = raw.copy()
    duplicate_mask = raw.duplicated(keep="first")

    data["data"] = parse_dates(data["data"])
    data["turno"] = (
        data["turno"]
        .astype("string")
        .str.strip()
        .str.casefold()
        .replace({"manha": "manhã", "noturno": "noite"})
        .str.title()
    )
    route_number = data["rota"].astype("string").str.extract(r"(\d+)", expand=False)
    data["rota"] = route_number.astype("Int64").map(
        lambda value: f"R{value:02d}" if pd.notna(value) else pd.NA
    )

    for column in ["zona_origem", "empresa", "ocorrencia"]:
        data[column] = data[column].astype("string").str.strip()

    for column in ["horario_previsto", "horario_chegada"]:
        data[column] = (
            data[column]
            .astype("string")
            .str.strip()
            .str.replace("h", ":", regex=False)
            .str.slice(0, 5)
        )

    data = data.loc[~duplicate_mask].copy()
    scheduled = pd.to_datetime(
        data["data"].dt.strftime("%Y-%m-%d") + " " + data["horario_previsto"],
        errors="coerce",
    )
    arrived = pd.to_datetime(
        data["data"].dt.strftime("%Y-%m-%d") + " " + data["horario_chegada"],
        errors="coerce",
    )
    data["atraso_informado"] = data["atraso_min"]
    data["atraso_calculado"] = (arrived - scheduled).dt.total_seconds() / 60

    divergent_delay = ~np.isclose(
        data["atraso_informado"], data["atraso_calculado"], equal_nan=True
    )
    impossible_delay = ~data["atraso_calculado"].between(-60, 120)
    impossible_capacity = ~data["passageiros"].between(0, 44)

    data["atraso_min"] = data["atraso_calculado"].mask(impossible_delay)
    data["passageiros"] = data["passageiros"].mask(impossible_capacity)
    data["pontual"] = data["atraso_min"].le(5).where(data["atraso_min"].notna())
    data["apos_inicio_turno"] = (
        data["atraso_min"].gt(15).where(data["atraso_min"].notna())
    )
    data["mes"] = data["data"].dt.to_period("M").astype("string")
    data["semana"] = data["data"].dt.to_period("W-SUN").apply(
        lambda period: period.start_time
    )
    data["periodo_ruptura"] = np.where(
        data["data"] < pd.Timestamp("2026-04-06"),
        "Antes de 06/04",
        "Desde 06/04",
    )
    data["grupo_rotas"] = np.where(
        data["rota"].isin(["R03", "R05"]), "R03 e R05", "Demais rotas"
    )

    quality = pd.DataFrame(
        [
            {
                "problema": "Categorias inconsistentes",
                "evidencia": "30 rótulos de rota e 8 rótulos de turno",
                "tratamento": "Extração do número da rota e mapa de equivalências",
                "impacto": "8 rotas e 3 turnos comparáveis",
            },
            {
                "problema": "Valores ausentes",
                "evidencia": f"{int(raw['chuva_mm'].isna().sum())} ausências em chuva_mm",
                "tratamento": "Manter ausente e excluir somente da análise chuva × atraso",
                "impacto": "Sem imputar chuva desconhecida",
            },
            {
                "problema": "Duplicados",
                "evidencia": f"{int(duplicate_mask.sum())} linhas totalmente repetidas",
                "tratamento": "Remoção após validar igualdade de todos os campos",
                "impacto": f"{len(raw)} → {len(data)} viagens",
            },
            {
                "problema": "Atraso divergente",
                "evidencia": f"{int(divergent_delay.sum())} divergências entre horários e atraso",
                "tratamento": "Recalcular a partir dos horários padronizados",
                "impacto": "Indicador coerente e reproduzível",
            },
            {
                "problema": "Valores inválidos",
                "evidencia": (
                    f"{int(impossible_delay.sum())} atrasos > 120 min e "
                    f"{int(impossible_capacity.sum())} lotações > 44"
                ),
                "tratamento": "Marcar como ausente, preservando a viagem",
                "impacto": "Extremos impossíveis não distorcem médias",
            },
        ]
    )
    return data, quality


def summary_metrics(data: pd.DataFrame) -> dict[str, float | int | str]:
    """Calculate the headline metrics reused by all deliverables."""
    after_change = data[data["data"] >= "2026-04-06"]
    target_day = after_change[
        after_change["rota"].isin(["R03", "R05"])
        & after_change["turno"].isin(["Manhã", "Tarde"])
    ]
    other_day = after_change[
        ~after_change["rota"].isin(["R03", "R05"])
        & after_change["turno"].isin(["Manhã", "Tarde"])
    ]
    before_target = data[
        (data["data"] < "2026-04-06")
        & data["rota"].isin(["R03", "R05"])
        & data["turno"].isin(["Manhã", "Tarde"])
    ]

    return {
        "rows_raw": 2463,
        "rows_clean": int(len(data)),
        "valid_delays": int(data["atraso_min"].notna().sum()),
        "punctuality": float(data["pontual"].mean() * 100),
        "median_delay": float(data["atraso_min"].median()),
        "after_shift": int(data["apos_inicio_turno"].sum()),
        "after_shift_pct": float(data["apos_inicio_turno"].mean() * 100),
        "before_target_punctuality": float(before_target["pontual"].mean() * 100),
        "target_punctuality": float(target_day["pontual"].mean() * 100),
        "other_punctuality": float(other_day["pontual"].mean() * 100),
        "target_median": float(target_day["atraso_min"].median()),
        "other_median": float(other_day["atraso_min"].median()),
        "roadwork_start": "07/04/2026",
        "roadwork_routes": int(
            data.loc[data["ocorrencia"].eq("Obra na via"), "rota"].nunique()
        ),
    }


def _set_chart_style() -> None:
    sns.set_theme(style="whitegrid", font="DejaVu Sans")
    plt.rcParams.update(
        {
            "figure.facecolor": CREAM,
            "axes.facecolor": CREAM,
            "axes.edgecolor": LIGHT_GRAY,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.titleweight": "bold",
            "axes.titlesize": 15,
            "axes.titlepad": 14,
            "grid.color": "#D8E0E0",
            "grid.linewidth": 0.7,
        }
    )


def _save(fig: plt.Figure, name: str) -> Path:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / name
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path


def create_charts(data: pd.DataFrame) -> list[Path]:
    """Create the publication-ready charts used in the deliverables."""
    _set_chart_style()
    paths: list[Path] = []

    daily = (
        data.groupby(["data", "rota"], observed=True)["atraso_min"]
        .median()
        .unstack()
        .rolling(7, min_periods=4)
        .median()
    )
    fig, ax = plt.subplots(figsize=(12, 5.8))
    for route in daily.columns:
        color = GRAY
        width = 1.3
        alpha = 0.62
        if route == "R03":
            color, width, alpha = CORAL, 3.0, 1.0
        elif route == "R05":
            color, width, alpha = TEAL, 3.0, 1.0
        ax.plot(daily.index, daily[route], color=color, lw=width, alpha=alpha)
    ax.axvline(pd.Timestamp("2026-04-06"), color=YELLOW, lw=2.3, ls="--")
    ax.annotate(
        "06/04\nmudança de patamar",
        xy=(pd.Timestamp("2026-04-06"), 5),
        xytext=(pd.Timestamp("2026-03-12"), 7.5),
        arrowprops={"arrowstyle": "->", "color": INK},
        fontsize=10,
        color=INK,
    )
    ax.text(daily.index[-1], daily["R05"].iloc[-1] + 0.8, "R05", color=TEAL, weight="bold")
    ax.text(daily.index[-1], daily["R03"].iloc[-1] - 1.0, "R03", color=CORAL, weight="bold")
    ax.set_title("R03 e R05 mudam de patamar a partir de 6 de abril")
    ax.set_xlabel("Data da viagem")
    ax.set_ylabel("Mediana móvel de 7 dias do atraso (min)")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.grid(axis="x", visible=False)
    sns.despine(ax=ax)
    paths.append(_save(fig, "01_serie_rotas.png"))

    after = data[data["data"] >= "2026-04-06"]
    heatmap = (
        after.pivot_table(index="rota", columns="turno", values="pontual", aggfunc="mean")
        .reindex(columns=["Manhã", "Tarde", "Noite"])
        .mul(100)
        .astype(float)
    )
    fig, ax = plt.subplots(figsize=(7.5, 5.9))
    cmap = sns.blend_palette([CORAL, YELLOW, MINT], as_cmap=True)
    sns.heatmap(
        heatmap,
        annot=True,
        fmt=".0f",
        cmap=cmap,
        vmin=0,
        vmax=100,
        linewidths=2,
        linecolor=CREAM,
        cbar_kws={"label": "Pontualidade (%)"},
        ax=ax,
    )
    ax.set_title("Após 6 de abril, o problema fica nas rotas R03 e R05 durante o dia")
    ax.set_xlabel("Turno")
    ax.set_ylabel("Rota")
    paths.append(_save(fig, "02_heatmap_rota_turno.png"))

    late = data[data["pontual"].eq(False)]
    occurrences = late["ocorrencia"].value_counts().sort_values()
    colors = [GRAY if label == "Nenhuma" else CORAL for label in occurrences.index]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(occurrences.index, occurrences.values, color=colors)
    ax.bar_label(bars, padding=5, color=INK, fontsize=10)
    ax.set_title("Chuva forte lidera os atrasos, mas um terço não tem ocorrência registrada")
    ax.set_xlabel("Viagens com atraso acima de 5 minutos")
    ax.set_ylabel("")
    ax.grid(axis="y", visible=False)
    sns.despine(ax=ax)
    paths.append(_save(fig, "03_ocorrencias_atrasos.png"))

    box_data = data[data["rota"].isin(["R03", "R05"])].copy()
    fig, ax = plt.subplots(figsize=(9, 5.8))
    sns.boxplot(
        data=box_data,
        x="rota",
        y="atraso_min",
        hue="periodo_ruptura",
        hue_order=["Antes de 06/04", "Desde 06/04"],
        palette=[GRAY, CORAL],
        showfliers=False,
        ax=ax,
    )
    ax.axhline(5, color=TEAL, ls="--", lw=1.6, label="Limite de pontualidade")
    ax.set_title("A distribuição do atraso se desloca nas rotas R03 e R05")
    ax.set_xlabel("Rota")
    ax.set_ylabel("Atraso (min)")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, title="Período", frameon=False, ncol=3, loc="upper left")
    sns.despine(ax=ax)
    paths.append(_save(fig, "04_distribuicao_r03_r05.png"))

    rain = data.dropna(subset=["chuva_mm", "atraso_min"]).copy()
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    for group, color, alpha in [
        ("Demais rotas", GRAY, 0.34),
        ("R03 e R05", CORAL, 0.62),
    ]:
        subset = rain[rain["grupo_rotas"].eq(group)]
        ax.scatter(
            subset["chuva_mm"],
            subset["atraso_min"],
            s=25,
            alpha=alpha,
            color=color,
            label=group,
            edgecolors="none",
        )
    ax.axhline(5, color=TEAL, ls="--", lw=1.5)
    ax.set_title("Chuva forte eleva atrasos, mas não explica a ruptura localizada")
    ax.set_xlabel("Chuva no período da viagem (mm)")
    ax.set_ylabel("Atraso (min)")
    ax.set_ylim(-15, 65)
    ax.legend(frameon=False)
    sns.despine(ax=ax)
    paths.append(_save(fig, "05_chuva_atraso.png"))

    daytime = data[data["turno"].isin(["Manhã", "Tarde"])].copy()
    grouped = (
        daytime.groupby(["data", "grupo_rotas"], observed=True)["atraso_min"]
        .median()
        .unstack()
        .rolling(7, min_periods=4)
        .median()
    )
    median_after = (
        daytime[daytime["data"] >= "2026-04-06"]
        .groupby("grupo_rotas", observed=True)["atraso_min"]
        .median()
    )

    def minutes(value: float) -> str:
        return f"{value:.0f} min".replace("-", "−")

    fig, (left, right) = plt.subplots(1, 2, figsize=(13.2, 5.4), sharey=True)
    for route in daily.columns:
        left.plot(daily.index, daily[route], lw=1.25, alpha=0.75, label=route)
    left.set_title("Antes · versão exploratória, 8 rotas, 3 turnos")
    left.set_xlabel("Data da viagem")
    left.set_ylabel("Mediana móvel de 7 dias do atraso (min)")
    left.legend(ncol=2, frameon=False, fontsize=8)
    right.plot(grouped.index, grouped["Demais rotas"], color=GRAY, lw=2.2)
    right.plot(grouped.index, grouped["R03 e R05"], color=CORAL, lw=3.4)
    right.axvline(pd.Timestamp("2026-04-06"), color=YELLOW, lw=2.1, ls="--")
    right.axhline(5, color=TEAL, lw=1.2, ls=":")
    right.text(
        pd.Timestamp("2026-02-04"), 5.6, "limite de pontualidade: 5 min", color=TEAL, fontsize=9
    )
    right.annotate(
        "06/04: início da ruptura",
        xy=(pd.Timestamp("2026-04-06"), 1),
        xytext=(pd.Timestamp("2026-02-20"), 11.5),
        arrowprops={"arrowstyle": "->", "color": INK},
        fontsize=10,
    )
    right.text(
        grouped.index[-1],
        median_after["R03 e R05"] + 1.2,
        f"R03 e R05\n{minutes(median_after['R03 e R05'])}",
        color=CORAL,
        fontweight="bold",
        ha="right",
    )
    right.text(
        grouped.index[-1],
        median_after["Demais rotas"] - 4.2,
        f"Demais rotas\n{minutes(median_after['Demais rotas'])}",
        color="#6F7B7F",
        fontweight="bold",
        ha="right",
    )
    right.set_title(
        "Desde 6 de abril, R03 e R05 chegam com 12 min de atraso\n"
        "nos turnos diurnos; as demais seguem adiantadas",
        fontsize=12.5,
        loc="left",
    )
    right.set_xlabel("Data da viagem")
    right.set_ylabel("Mediana móvel de 7 dias do atraso (min)")
    right.tick_params(labelleft=True)
    for axis in (left, right):
        axis.xaxis.set_major_locator(mdates.MonthLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        axis.grid(axis="x", visible=False)
        sns.despine(ax=axis)
    fig.tight_layout()
    paths.append(_save(fig, "06_exploratorio_explicativo.png"))
    return paths


def export_clean_data(data: pd.DataFrame) -> Path:
    """Export the treated dataset with analysis-ready columns."""
    columns = [
        "data",
        "turno",
        "rota",
        "zona_origem",
        "empresa",
        "horario_previsto",
        "horario_chegada",
        "atraso_min",
        "passageiros",
        "chuva_mm",
        "ocorrencia",
        "pontual",
        "apos_inicio_turno",
    ]
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    output = DATASET_DIR / "dados_tratados_transporte_fretado.csv"
    data[columns].to_csv(output, index=False, date_format="%Y-%m-%d")
    return output


if __name__ == "__main__":
    raw_data = read_raw_data()
    clean, quality_log = clean_data(raw_data)
    export_clean_data(clean)
    create_charts(clean)
    print(summary_metrics(clean))
    print(quality_log.to_string(index=False))
