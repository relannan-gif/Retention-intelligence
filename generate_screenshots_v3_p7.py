"""
Generate a static screenshot for Page 7 — Model Validation (Prediction Accuracy tab).
Saves to: /tmp/p3_page7_model_validation.png
"""

import sys
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.gridspec as gridspec

# ── Try to import project data; fall back to built-in defaults ─────────────────
sys.path.insert(0, os.path.dirname(__file__))

try:
    from data.sample_data import get_sample_data
    raw_df = get_sample_data()
    HAVE_SAMPLE = True
except Exception:
    HAVE_SAMPLE = False
    raw_df = None

try:
    from utils.helpers import GOLD, RED, GREEN, AMBER, BLUE, PURPLE, MUTED, BG, CARD
except Exception:
    GOLD   = "#F0B429"
    RED    = "#EF4444"
    GREEN  = "#10B981"
    AMBER  = "#F59E0B"
    BLUE   = "#3B82F6"
    PURPLE = "#8B5CF6"
    MUTED  = "#94A3B8"
    BG     = "#0A0E1A"
    CARD   = "#141B2D"

BORDER = "#1E2D4A"

# ── Layout constants ────────────────────────────────────────────────────────────
BAND_LABELS   = ["0–20\n(Very Low)", "21–40\n(Low)", "41–60\n(Medium)", "61–80\n(High)", "81–100\n(Very High)"]
CHURN_RATES   = [0.02, 0.05, 0.13, 0.28, 0.52]
WD_RATES      = [0.03, 0.08, 0.18, 0.35, 0.61]
KPI_CHURN     = 78.0
KPI_WD        = 84.0
KPI_REACTIV   = 71.0

# Risk factor breakdown for a sample "High Risk" client
RISK_FACTORS = {
    "Login inactivity":    72,
    "Recent withdrawals":  58,
    "Volume decline":      45,
    "Complaints filed":    30,
    "Open tickets":        20,
}
VALUE_FACTORS = {
    "Current equity":      65,
    "Lifetime deposits":   48,
    "Trading volume":      35,
    "Client tenure":       22,
}

# ── If we have real data, compute band client counts ───────────────────────────
BAND_CLIENTS = [0, 0, 0, 0, 0]
if HAVE_SAMPLE and raw_df is not None:
    try:
        score_col = "retention_risk_score"
        if score_col not in raw_df.columns:
            # try to find any risk column
            candidates = [c for c in raw_df.columns if "risk" in c.lower()]
            score_col = candidates[0] if candidates else None
        if score_col:
            bounds = [(0, 20), (21, 40), (41, 60), (61, 80), (81, 100)]
            for i, (lo, hi) in enumerate(bounds):
                BAND_CLIENTS[i] = int(((raw_df[score_col] >= lo) & (raw_df[score_col] <= hi)).sum())
    except Exception:
        pass

if all(c == 0 for c in BAND_CLIENTS):
    BAND_CLIENTS = [120, 95, 78, 52, 31]

# ── Figure setup ───────────────────────────────────────────────────────────────
FIG_W, FIG_H = 20, 26
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG)

# Custom GridSpec: rows for title, KPIs, table, bar chart, factor breakdown
gs = gridspec.GridSpec(
    6, 1,
    figure=fig,
    height_ratios=[0.8, 1.2, 2.2, 3.5, 3.5, 0.3],
    hspace=0.4,
    left=0.04, right=0.96, top=0.97, bottom=0.02,
)

# ── Helper: draw a rounded card background ─────────────────────────────────────
def card_bg(ax, facecolor=CARD, edgecolor=BORDER, alpha=1.0):
    ax.set_facecolor(facecolor)
    for spine in ax.spines.values():
        spine.set_edgecolor(edgecolor)
        spine.set_linewidth(1.2)
    ax.patch.set_alpha(alpha)

def off_ax(ax):
    """Hide axes ticks and spines cleanly."""
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 0 — Title bar
# ══════════════════════════════════════════════════════════════════════════════
ax_title = fig.add_subplot(gs[0])
ax_title.set_facecolor("#0D1527")
off_ax(ax_title)
ax_title.text(
    0.5, 0.55,
    "📈  Model Validation — Is the scoring model actually predictive?",
    transform=ax_title.transAxes,
    ha="center", va="center",
    fontsize=18, fontweight="bold", color=GOLD,
)
ax_title.text(
    0.5, 0.15,
    "Prediction Accuracy  •  Score Factor Breakdown  •  Retention Effectiveness  •  Score Trends  •  Data Snapshots",
    transform=ax_title.transAxes,
    ha="center", va="center",
    fontsize=10, color=MUTED,
)
for spine in ax_title.spines.values():
    spine.set_visible(True)
    spine.set_edgecolor(GOLD)
    spine.set_linewidth(1.5)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 1 — KPI tiles (3 big metrics)
# ══════════════════════════════════════════════════════════════════════════════
ax_kpis = fig.add_subplot(gs[1])
ax_kpis.set_facecolor(BG)
off_ax(ax_kpis)

KPI_DATA = [
    ("Churn Prediction\nAccuracy",        f"{KPI_CHURN:.0f}%",  GREEN,  "AUC vs 60-day churn events"),
    ("Withdrawal Prediction\nAccuracy",   f"{KPI_WD:.0f}%",     GREEN,  "AUC vs 60-day withdrawal events"),
    ("Reactivation Prediction\nAccuracy", f"{KPI_REACTIV:.0f}%", AMBER,  "AUC vs returning-client events"),
]

tile_w = 0.28
tile_gap = (1.0 - 3 * tile_w) / 4
for i, (label, value, color, note) in enumerate(KPI_DATA):
    x0 = tile_gap + i * (tile_w + tile_gap)
    rect = FancyBboxPatch(
        (x0, 0.08), tile_w, 0.84,
        boxstyle="round,pad=0.01",
        transform=ax_kpis.transAxes,
        linewidth=1.5, edgecolor=BORDER,
        facecolor=CARD,
    )
    ax_kpis.add_patch(rect)
    ax_kpis.text(x0 + tile_w / 2, 0.78, label,
                 transform=ax_kpis.transAxes,
                 ha="center", va="center",
                 fontsize=9.5, color=MUTED, fontweight="normal",
                 multialignment="center")
    ax_kpis.text(x0 + tile_w / 2, 0.45, value,
                 transform=ax_kpis.transAxes,
                 ha="center", va="center",
                 fontsize=26, color=color, fontweight="bold")
    ax_kpis.text(x0 + tile_w / 2, 0.15, note,
                 transform=ax_kpis.transAxes,
                 ha="center", va="center",
                 fontsize=7.5, color=MUTED, style="italic")

# Simulated-data notice
ax_kpis.text(1.0, 0.0, "ℹ  Generating simulated validation data — no historical outcomes recorded yet",
             transform=ax_kpis.transAxes,
             ha="right", va="bottom",
             fontsize=7.5, color=BLUE, style="italic")

# ══════════════════════════════════════════════════════════════════════════════
# ROW 2 — Risk Band table
# ══════════════════════════════════════════════════════════════════════════════
ax_table = fig.add_subplot(gs[2])
ax_table.set_facecolor(BG)
off_ax(ax_table)

ax_table.text(0.0, 0.97, "Risk Band vs Observed Outcomes",
              transform=ax_table.transAxes,
              ha="left", va="top",
              fontsize=13, fontweight="bold", color="#E8E8E8")

# Build table data
col_headers = ["Risk Band", "Clients", "Churned", "Churn Rate", "Withdrawal Events", "Withdrawal Rate"]
raw_bands = [
    ("0–20  (Very Low)",    BAND_CLIENTS[0], int(BAND_CLIENTS[0]*0.02), "2%",  int(BAND_CLIENTS[0]*0.03), "3%"),
    ("21–40  (Low)",        BAND_CLIENTS[1], int(BAND_CLIENTS[1]*0.05), "5%",  int(BAND_CLIENTS[1]*0.08), "8%"),
    ("41–60  (Medium)",     BAND_CLIENTS[2], int(BAND_CLIENTS[2]*0.13), "13%", int(BAND_CLIENTS[2]*0.18), "18%"),
    ("61–80  (High)",       BAND_CLIENTS[3], int(BAND_CLIENTS[3]*0.28), "28%", int(BAND_CLIENTS[3]*0.35), "35%"),
    ("81–100  (Very High)", BAND_CLIENTS[4], int(BAND_CLIENTS[4]*0.52), "52%", int(BAND_CLIENTS[4]*0.61), "61%"),
]

CHURN_RATE_COLORS = [GREEN, GREEN, AMBER, RED, RED]

n_rows = len(raw_bands)
n_cols = len(col_headers)
col_x = [0.0, 0.22, 0.34, 0.46, 0.60, 0.78]
col_align = ["left", "center", "center", "center", "center", "center"]
row_h = 0.13
header_y = 0.86

# Header background
rect_hdr = FancyBboxPatch(
    (-0.01, header_y - 0.005), 1.02, row_h + 0.01,
    boxstyle="round,pad=0.005",
    transform=ax_table.transAxes,
    facecolor="#1E2D4A", edgecolor=BORDER, linewidth=1,
)
ax_table.add_patch(rect_hdr)

for j, (hdr, x, align) in enumerate(zip(col_headers, col_x, col_align)):
    ax_table.text(x, header_y + row_h * 0.45, hdr,
                  transform=ax_table.transAxes,
                  ha=align, va="center",
                  fontsize=8.5, color=GOLD, fontweight="bold")

for i, (band, clients, churned, churn_r, wd_events, wd_r) in enumerate(raw_bands):
    y = header_y - (i + 1) * (row_h + 0.008)
    row_bg = CARD if i % 2 == 0 else "#101828"
    rect_row = FancyBboxPatch(
        (-0.01, y - 0.004), 1.02, row_h,
        boxstyle="round,pad=0.003",
        transform=ax_table.transAxes,
        facecolor=row_bg, edgecolor=BORDER, linewidth=0.5,
    )
    ax_table.add_patch(rect_row)

    row_vals = [band, str(clients), str(churned), churn_r, str(wd_events), wd_r]
    row_colors = ["#E8E8E8", "#E8E8E8", MUTED, CHURN_RATE_COLORS[i], MUTED, AMBER]
    for j, (val, x, align, color) in enumerate(zip(row_vals, col_x, col_align, row_colors)):
        ax_table.text(x, y + row_h * 0.4, val,
                      transform=ax_table.transAxes,
                      ha=align, va="center",
                      fontsize=8.5, color=color,
                      fontweight="bold" if j in (3, 5) else "normal")

# ══════════════════════════════════════════════════════════════════════════════
# ROW 3 — Grouped bar chart
# ══════════════════════════════════════════════════════════════════════════════
ax_bar = fig.add_subplot(gs[3])
card_bg(ax_bar)

x = np.arange(5)
width = 0.35

bars1 = ax_bar.bar(x - width / 2, [r * 100 for r in CHURN_RATES], width,
                   label="Churn Rate", color=RED, alpha=0.88, zorder=3)
bars2 = ax_bar.bar(x + width / 2, [r * 100 for r in WD_RATES], width,
                   label="Withdrawal Rate", color=AMBER, alpha=0.88, zorder=3)

for bar in bars1:
    h = bar.get_height()
    ax_bar.text(bar.get_x() + bar.get_width() / 2, h + 0.8,
                f"{h:.0f}%", ha="center", va="bottom",
                fontsize=8, color=RED, fontweight="bold")
for bar in bars2:
    h = bar.get_height()
    ax_bar.text(bar.get_x() + bar.get_width() / 2, h + 0.8,
                f"{h:.0f}%", ha="center", va="bottom",
                fontsize=8, color=AMBER, fontweight="bold")

ax_bar.set_xticks(x)
ax_bar.set_xticklabels(BAND_LABELS, color="#E8E8E8", fontsize=9)
ax_bar.set_ylabel("Rate (%)", color=MUTED, fontsize=9)
ax_bar.set_yticks(range(0, 75, 10))
ax_bar.set_yticklabels([f"{v}%" for v in range(0, 75, 10)], color=MUTED, fontsize=8)
ax_bar.set_ylim(0, 72)
ax_bar.set_title("Churn & Withdrawal Rate by Risk Band", color="#E8E8E8",
                  fontsize=12, fontweight="bold", pad=8)
ax_bar.legend(
    handles=[
        mpatches.Patch(color=RED, label="Churn Rate"),
        mpatches.Patch(color=AMBER, label="Withdrawal Rate"),
    ],
    loc="upper left", facecolor=CARD, edgecolor=BORDER,
    labelcolor="#E8E8E8", fontsize=8.5,
)
ax_bar.grid(axis="y", color="#1E2D4A", linewidth=0.7, linestyle="--", zorder=0)
ax_bar.tick_params(colors=MUTED)
ax_bar.text(
    0.5, -0.13,
    "A well-calibrated model should show churn rates increasing monotonically with risk score.",
    transform=ax_bar.transAxes, ha="center", va="top",
    fontsize=8, color=MUTED, style="italic",
)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 4 — Score Factor Breakdown (horizontal bars, side by side)
# ══════════════════════════════════════════════════════════════════════════════
gs_inner = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[4], wspace=0.35)
ax_risk_factors  = fig.add_subplot(gs_inner[0])
ax_value_factors = fig.add_subplot(gs_inner[1])

def draw_factor_chart(ax, factors, color, title, subtitle=""):
    card_bg(ax)
    labels = list(factors.keys())
    vals   = list(factors.values())
    y_pos  = np.arange(len(labels))

    bars = ax.barh(y_pos, vals, color=color, alpha=0.85, height=0.55, zorder=3)
    for bar, v in zip(bars, vals):
        ax.text(v + 1.5, bar.get_y() + bar.get_height() / 2,
                str(v), va="center", ha="left",
                fontsize=8, color=color, fontweight="bold")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color="#E8E8E8", fontsize=8.5)
    ax.set_xlim(0, 110)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0", "25", "50", "75", "100"], color=MUTED, fontsize=7.5)
    ax.set_xlabel("Score (0–100 scale)", color=MUTED, fontsize=8)
    ax.set_title(title, color="#E8E8E8", fontsize=10, fontweight="bold", pad=6)
    ax.grid(axis="x", color="#1E2D4A", linewidth=0.7, linestyle="--", zorder=0)
    ax.tick_params(colors=MUTED)
    if subtitle:
        ax.text(0.5, -0.12, subtitle, transform=ax.transAxes,
                ha="center", fontsize=7.5, color=MUTED, style="italic")

# Determine sample client name
sample_client = "CLIENT-0042"
if HAVE_SAMPLE and raw_df is not None:
    try:
        top_risk = raw_df.sort_values("retention_risk_score", ascending=False).iloc[0]
        cid = str(top_risk.get("client_id", "?"))
        cname = str(top_risk.get("client_name", "Unknown"))[:20]
        risk_val = int(top_risk.get("retention_risk_score", 0))
        sample_client = f"{cid} — {cname} — Risk: {risk_val}"
    except Exception:
        pass

draw_factor_chart(
    ax_risk_factors, RISK_FACTORS, RED,
    f"Risk Factors — {sample_client}",
    subtitle="Higher score = stronger churn signal",
)
draw_factor_chart(
    ax_value_factors, VALUE_FACTORS, BLUE,
    "Commercial Value Factors",
    subtitle="Higher score = greater revenue contribution",
)

# ══════════════════════════════════════════════════════════════════════════════
# ROW 5 — Footer caption
# ══════════════════════════════════════════════════════════════════════════════
ax_footer = fig.add_subplot(gs[5])
ax_footer.set_facecolor(BG)
off_ax(ax_footer)
ax_footer.text(
    0.5, 0.5,
    "Factor scores are on 0–100 scale. Higher = stronger signal. "
    "Final score is a weighted combination of all factors.  |  "
    "Simulated data shown — connect snapshot_db for live validation.",
    transform=ax_footer.transAxes,
    ha="center", va="center",
    fontsize=7.5, color=MUTED, style="italic",
)

# ── Save ───────────────────────────────────────────────────────────────────────
OUTPUT_PATH = "/tmp/p3_page7_model_validation.png"
fig.savefig(OUTPUT_PATH, dpi=140, bbox_inches="tight", facecolor=BG)
plt.close(fig)
print(f"Saved: {OUTPUT_PATH}")
print("DONE")
