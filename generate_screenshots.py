"""
Generate visual previews of every app page as PNG images.
Runs the same data + scoring pipeline the app uses.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import numpy as np
import sys, os

sys.path.insert(0, "/home/user/Retention-intelligence")
os.chdir("/home/user/Retention-intelligence")

from data.sample_data import generate_clients
from utils.helpers import DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS, DEFAULT_THRESHOLDS, fmt_currency
from utils.scoring import score_dataframe

# ── Load data once ─────────────────────────────────────────────────────────
df = generate_clients(300)
scored = score_dataframe(df, DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS, DEFAULT_THRESHOLDS, 0.6)
thresholds = DEFAULT_THRESHOLDS
hr = thresholds["high_risk"]
hv = thresholds["high_value"]
cp = thresholds["critical_priority"]

BRAND   = "#1A2B4A"   # dark navy
ACCENT  = "#E8B84B"   # gold
RED     = "#E74C3C"
AMBER   = "#F39C12"
GREEN   = "#27AE60"
BLUE    = "#3498DB"
BG      = "#F7F9FC"
CARD_BG = "#FFFFFF"


def header_bar(fig, title, subtitle=""):
    fig.patch.set_facecolor(BG)
    ax_h = fig.add_axes([0, 0.965, 1, 0.035])
    ax_h.set_facecolor(BRAND)
    ax_h.axis("off")
    ax_h.text(0.012, 0.5, "📊 OneRoyal Client Intelligence Platform",
              color="white", fontsize=9, fontweight="bold", va="center")
    ax_h.text(0.98, 0.5, title, color=ACCENT, fontsize=9,
              fontweight="bold", va="center", ha="right")


def kpi_card(ax, value, label, color=BRAND, delta=None):
    ax.set_facecolor(CARD_BG)
    for spine in ax.spines.values():
        spine.set_edgecolor("#E0E0E0")
        spine.set_linewidth(1.2)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.5, 0.62, str(value), ha="center", va="center",
            fontsize=22, fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.28, label, ha="center", va="center",
            fontsize=7.5, color="#555", transform=ax.transAxes)
    if delta:
        ax.text(0.5, 0.08, delta, ha="center", va="center",
                fontsize=6.5, color=RED, transform=ax.transAxes)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 20))
fig.patch.set_facecolor(BG)
header_bar(fig, "Executive Dashboard")

# KPI row
kpi_labels = ["Total Clients","High Risk","High-Value\nat Risk","Equity at Risk","Withdrawals\n30d","Revenue at Risk"]
kpi_vals   = [
    300,
    int((scored["retention_risk_score"] >= hr).sum()),
    int(((scored["retention_risk_score"] >= hr) & (scored["client_value_score"] >= hv)).sum()),
    fmt_currency(scored.loc[scored["retention_risk_score"]>=hr,"current_equity"].sum()),
    fmt_currency(scored["withdrawal_amount_last_30d"].sum()),
    fmt_currency(scored.loc[scored["retention_risk_score"]>=hr,"spread_commission_revenue"].sum()),
]
kpi_colors = [BRAND, RED, RED, AMBER, AMBER, AMBER]

for i, (val, lbl, col) in enumerate(zip(kpi_vals, kpi_labels, kpi_colors)):
    ax = fig.add_axes([0.01 + i*0.165, 0.875, 0.155, 0.075])
    kpi_card(ax, val, lbl, color=col)

# Section label
fig.text(0.01, 0.865, "Risk & Value Distribution", fontsize=11, fontweight="bold", color=BRAND)

# Risk histogram
ax1 = fig.add_axes([0.01, 0.72, 0.46, 0.135])
ax1.set_facecolor(CARD_BG)
ax1.hist(scored["retention_risk_score"], bins=20, color=RED, alpha=0.85, edgecolor="white")
ax1.axvline(hr, color=BRAND, linestyle="--", linewidth=1.5, label=f"High risk threshold ({hr})")
ax1.set_title("Retention Risk Distribution", fontsize=9, color=BRAND, pad=4)
ax1.set_xlabel("Risk Score (0–100)", fontsize=8); ax1.set_ylabel("# Clients", fontsize=8)
ax1.tick_params(labelsize=7); ax1.legend(fontsize=7)
ax1.set_facecolor(CARD_BG)
for sp in ax1.spines.values(): sp.set_edgecolor("#E0E0E0")

# Value histogram
ax2 = fig.add_axes([0.53, 0.72, 0.46, 0.135])
ax2.hist(scored["client_value_score"], bins=20, color=GREEN, alpha=0.85, edgecolor="white")
ax2.axvline(hv, color=BRAND, linestyle="--", linewidth=1.5, label=f"High value threshold ({hv})")
ax2.set_title("Client Value Distribution", fontsize=9, color=BRAND, pad=4)
ax2.set_xlabel("Value Score (0–100)", fontsize=8); ax2.set_ylabel("# Clients", fontsize=8)
ax2.tick_params(labelsize=7); ax2.legend(fontsize=7)
ax2.set_facecolor(CARD_BG)
for sp in ax2.spines.values(): sp.set_edgecolor("#E0E0E0")

# Priority by country
fig.text(0.01, 0.71, "Priority Analysis", fontsize=11, fontweight="bold", color=BRAND)
country_p = scored.groupby("country")["priority_score"].mean().sort_values(ascending=False).head(10)
ax3 = fig.add_axes([0.01, 0.555, 0.46, 0.145])
colors_bar = [RED if v >= cp else AMBER if v >= cp*0.6 else BLUE for v in country_p.values]
bars = ax3.barh(country_p.index[::-1], country_p.values[::-1], color=colors_bar[::-1], edgecolor="white")
ax3.set_title("Avg Priority Score by Country (Top 10)", fontsize=9, color=BRAND, pad=4)
ax3.set_xlabel("Avg Priority Score", fontsize=8); ax3.tick_params(labelsize=7)
ax3.set_facecolor(CARD_BG)
for sp in ax3.spines.values(): sp.set_edgecolor("#E0E0E0")

# Priority by account manager
am_p = scored.groupby("account_manager")["priority_score"].mean().sort_values(ascending=False)
ax4 = fig.add_axes([0.53, 0.555, 0.46, 0.145])
ax4.barh(am_p.index[::-1], am_p.values[::-1], color=BLUE, alpha=0.85, edgecolor="white")
ax4.set_title("Avg Priority Score by Account Manager", fontsize=9, color=BRAND, pad=4)
ax4.set_xlabel("Avg Priority Score", fontsize=8); ax4.tick_params(labelsize=7)
ax4.set_facecolor(CARD_BG)
for sp in ax4.spines.values(): sp.set_edgecolor("#E0E0E0")

# Book type pie
book_counts = scored["book_type"].value_counts()
ax5 = fig.add_axes([0.01, 0.37, 0.35, 0.17])
wedge_colors = [BLUE, AMBER, "#9B59B6"]
wedges, texts, autotexts = ax5.pie(
    book_counts.values, labels=book_counts.index,
    colors=wedge_colors, autopct="%1.0f%%",
    startangle=90, pctdistance=0.7,
    textprops={"fontsize": 8}
)
ax5.set_title("Clients by Book Type", fontsize=9, color=BRAND, pad=4)

# Risk level pie
risk_counts = scored["risk_level"].value_counts().reindex(["Low","Medium","High"])
ax6 = fig.add_axes([0.38, 0.37, 0.28, 0.17])
ax6.pie(risk_counts.values, labels=risk_counts.index,
        colors=[GREEN, AMBER, RED], autopct="%1.0f%%",
        startangle=90, pctdistance=0.7,
        textprops={"fontsize": 8})
ax6.set_title("Clients by Risk Level", fontsize=9, color=BRAND, pad=4)

# Top 5 tables
fig.text(0.01, 0.365, "Top Retention Opportunities", fontsize=11, fontweight="bold", color=BRAND)

top_c = scored.groupby("country").agg(
    avg_risk=("retention_risk_score","mean"),
    clients=("client_id","count"),
    equity=("current_equity","sum")
).sort_values("avg_risk",ascending=False).head(5).reset_index()

ax7 = fig.add_axes([0.01, 0.185, 0.46, 0.165])
ax7.axis("off")
ax7.set_title("Top 5 Countries by Avg Risk", fontsize=9, color=BRAND, pad=4, loc="left")
table_data = [[r["country"], f"{r['avg_risk']:.1f}", str(r["clients"]), fmt_currency(r["equity"])]
              for _, r in top_c.iterrows()]
tbl = ax7.table(
    cellText=table_data,
    colLabels=["Country","Avg Risk","Clients","Equity at Risk"],
    loc="center", cellLoc="left"
)
tbl.auto_set_font_size(False); tbl.set_fontsize(8)
tbl.scale(1, 1.6)
for (row,col), cell in tbl.get_celld().items():
    cell.set_edgecolor("#E0E0E0")
    if row == 0:
        cell.set_facecolor(BRAND); cell.set_text_props(color="white", fontweight="bold")
    elif row % 2 == 0:
        cell.set_facecolor("#F0F4FA")

top_am = scored.groupby("account_manager").agg(
    high_risk=("retention_risk_score", lambda x: (x>=hr).sum()),
    avg_prio=("priority_score","mean"),
    equity=("current_equity","sum")
).sort_values("high_risk",ascending=False).head(5).reset_index()

ax8 = fig.add_axes([0.53, 0.185, 0.46, 0.165])
ax8.axis("off")
ax8.set_title("Top 5 Account Managers by Retention Opportunity", fontsize=9, color=BRAND, pad=4, loc="left")
table_data2 = [[r["account_manager"].split()[-1], str(r["high_risk"]), f"{r['avg_prio']:.1f}", fmt_currency(r["equity"])]
               for _, r in top_am.iterrows()]
tbl2 = ax8.table(
    cellText=table_data2,
    colLabels=["Manager","High Risk","Avg Priority","Equity Managed"],
    loc="center", cellLoc="left"
)
tbl2.auto_set_font_size(False); tbl2.set_fontsize(8)
tbl2.scale(1, 1.6)
for (row,col), cell in tbl2.get_celld().items():
    cell.set_edgecolor("#E0E0E0")
    if row == 0:
        cell.set_facecolor(BRAND); cell.set_text_props(color="white", fontweight="bold")
    elif row % 2 == 0:
        cell.set_facecolor("#F0F4FA")

plt.savefig("/tmp/page1_executive_dashboard.png", dpi=130, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Page 1 saved.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 2 — CLIENT LIST
# ═══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 18))
fig.patch.set_facecolor(BG)
header_bar(fig, "Client List")

# Filter panel mockup
ax_filter = fig.add_axes([0.01, 0.88, 0.98, 0.075])
ax_filter.set_facecolor(CARD_BG)
for sp in ax_filter.spines.values(): sp.set_edgecolor("#D0D0D0")
ax_filter.set_xticks([]); ax_filter.set_yticks([])
ax_filter.text(0.01, 0.88, "🔍  Filters", fontsize=9, fontweight="bold", color=BRAND,
               transform=ax_filter.transAxes, va="top")
filter_fields = ["Search name/ID", "Country: All", "Account Manager: All",
                 "IB: All", "Book Type: All", "Account Type: All", "Risk Level: All"]
for i, f in enumerate(filter_fields):
    x = 0.01 + i * 0.14
    rect = FancyBboxPatch((x, 0.12), 0.13, 0.55, boxstyle="round,pad=0.01",
                           facecolor="#F0F4FA", edgecolor="#C0C8D8",
                           transform=ax_filter.transAxes)
    ax_filter.add_patch(rect)
    ax_filter.text(x+0.065, 0.40, f, fontsize=6.5, color="#444",
                   transform=ax_filter.transAxes, ha="center", va="center")

# Summary stat
fig.text(0.01, 0.875, "300 clients  ·  Sort by: Priority Score ↓", fontsize=8.5, color="#666")

# Client table (top 18 rows)
display = scored.sort_values("priority_score", ascending=False).head(18)[
    ["client_id","client_name","country","account_manager",
     "retention_risk_score","client_value_score","priority_score",
     "risk_level","priority_level","recommended_action"]
].reset_index(drop=True)

ax_tbl = fig.add_axes([0.01, 0.08, 0.98, 0.79])
ax_tbl.axis("off")
col_labels = ["Client ID","Name","Country","Acct Manager",
              "Risk","Value","Priority","Risk Lvl","Prio Lvl","Recommended Action"]
cell_data = []
for _, row in display.iterrows():
    cell_data.append([
        row["client_id"],
        row["client_name"][:18],
        row["country"],
        row["account_manager"].split()[0],
        f"{row['retention_risk_score']:.0f}",
        f"{row['client_value_score']:.0f}",
        f"{row['priority_score']:.0f}",
        str(row["risk_level"]),
        str(row["priority_level"]),
        row["recommended_action"][:30],
    ])

tbl = ax_tbl.table(cellText=cell_data, colLabels=col_labels,
                   loc="upper center", cellLoc="left")
tbl.auto_set_font_size(False); tbl.set_fontsize(7.2)
tbl.scale(1, 1.55)
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("#E8E8E8")
    if r == 0:
        cell.set_facecolor(BRAND)
        cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#F7F9FC")
    # Colour risk column
    if r > 0 and c == 4:
        val = float(cell_data[r-1][4])
        cell.set_facecolor("#FDECEA" if val >= hr else "#FEF9E7" if val >= hr*0.5 else "#EAF7EF")
    if r > 0 and c == 8:
        lvl = cell_data[r-1][8]
        cell.set_facecolor("#FDECEA" if lvl=="Critical" else "#FEF9E7" if lvl=="Elevated" else "#EAF7EF")

plt.savefig("/tmp/page2_client_list.png", dpi=130, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Page 2 saved.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 3 — SCORING ENGINE
# ═══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 20))
fig.patch.set_facecolor(BG)
header_bar(fig, "Scoring Engine")

fig.text(0.01, 0.955, "⚙️  Scoring Engine — Adjust weights and understand how clients are scored",
         fontsize=12, fontweight="bold", color=BRAND)
fig.text(0.01, 0.942, "Drag sliders to change scoring · Click Apply to rescore all 300 clients",
         fontsize=8.5, color="#666")

# --- Risk weight sliders panel ---
ax_rw = fig.add_axes([0.01, 0.80, 0.47, 0.135])
ax_rw.set_facecolor(CARD_BG)
for sp in ax_rw.spines.values(): sp.set_edgecolor("#D0D0D0")
ax_rw.set_xticks([]); ax_rw.set_yticks([])
ax_rw.text(0.02, 0.92, "Retention Risk Weights", fontsize=9, fontweight="bold", color=BRAND,
           transform=ax_rw.transAxes, va="top")

risk_w = DEFAULT_RISK_WEIGHTS
slider_labels_r = ["💸 Withdrawal pressure","📉 Volume drop","🔒 Login inactivity",
                   "🏦 Deposit staleness","⚠️ Complaints / tickets","📊 Equity erosion"]
slider_vals_r   = [risk_w["w_withdrawal"], risk_w["w_volume_drop"], risk_w["w_login"],
                   risk_w["w_deposit_stale"], risk_w["w_complaints"], risk_w["w_equity_erosion"]]
for i, (lbl, val) in enumerate(zip(slider_labels_r, slider_vals_r)):
    y = 0.79 - i * 0.115
    ax_rw.text(0.02, y, lbl, fontsize=7, color="#444", transform=ax_rw.transAxes, va="center")
    bar_width = val / 10 * 0.55
    rect = FancyBboxPatch((0.38, y-0.04), 0.55, 0.07,
                          boxstyle="round,pad=0.005",
                          facecolor="#E8ECF0", edgecolor="#C8CDD2",
                          transform=ax_rw.transAxes)
    ax_rw.add_patch(rect)
    fill = FancyBboxPatch((0.38, y-0.04), bar_width, 0.07,
                          boxstyle="round,pad=0.005",
                          facecolor=RED, edgecolor="none",
                          transform=ax_rw.transAxes)
    ax_rw.add_patch(fill)
    ax_rw.text(0.945, y, str(val), fontsize=7.5, fontweight="bold", color=BRAND,
               transform=ax_rw.transAxes, va="center", ha="center")

# --- Value weight sliders panel ---
ax_vw = fig.add_axes([0.52, 0.80, 0.47, 0.135])
ax_vw.set_facecolor(CARD_BG)
for sp in ax_vw.spines.values(): sp.set_edgecolor("#D0D0D0")
ax_vw.set_xticks([]); ax_vw.set_yticks([])
ax_vw.text(0.02, 0.92, "Client Value Weights", fontsize=9, fontweight="bold", color=BRAND,
           transform=ax_vw.transAxes, va="top")

val_w = DEFAULT_VALUE_WEIGHTS
slider_labels_v = ["💰 Lifetime deposits","🏧 Net deposits","📈 Trading volume",
                   "🔄 Redeposits","🏢 Company PnL","💹 Spread/commission"]
slider_vals_v   = [val_w["v_lifetime_dep"], val_w["v_net_dep"], val_w["v_volume"],
                   val_w["v_redeposits"], val_w["v_pnl"], val_w["v_spread_rev"]]
for i, (lbl, val) in enumerate(zip(slider_labels_v, slider_vals_v)):
    y = 0.79 - i * 0.115
    ax_vw.text(0.02, y, lbl, fontsize=7, color="#444", transform=ax_vw.transAxes, va="center")
    bar_width = val / 10 * 0.55
    rect = FancyBboxPatch((0.38, y-0.04), 0.55, 0.07,
                          boxstyle="round,pad=0.005",
                          facecolor="#E8ECF0", edgecolor="#C8CDD2",
                          transform=ax_vw.transAxes)
    ax_vw.add_patch(rect)
    fill = FancyBboxPatch((0.38, y-0.04), bar_width, 0.07,
                          boxstyle="round,pad=0.005",
                          facecolor=GREEN, edgecolor="none",
                          transform=ax_vw.transAxes)
    ax_vw.add_patch(fill)
    ax_vw.text(0.945, y, str(val), fontsize=7.5, fontweight="bold", color=BRAND,
               transform=ax_vw.transAxes, va="center", ha="center")

# Priority blend bar
ax_blend = fig.add_axes([0.01, 0.745, 0.98, 0.045])
ax_blend.set_facecolor(CARD_BG)
for sp in ax_blend.spines.values(): sp.set_edgecolor("#D0D0D0")
ax_blend.set_xticks([]); ax_blend.set_yticks([])
ax_blend.text(0.005, 0.5, "Priority Score Blend:  Risk weight 60%  ←slider→  Value weight 40%",
              fontsize=8.5, color="#444", transform=ax_blend.transAxes, va="center")
blend_rect = FancyBboxPatch((0.45, 0.2), 0.42, 0.6, boxstyle="round,pad=0.01",
                             facecolor="#E8ECF0", edgecolor="#C8CDD2",
                             transform=ax_blend.transAxes)
ax_blend.add_patch(blend_rect)
fill_rect = FancyBboxPatch((0.45, 0.2), 0.252, 0.6, boxstyle="round,pad=0.01",
                            facecolor=ACCENT, edgecolor="none",
                            transform=ax_blend.transAxes)
ax_blend.add_patch(fill_rect)
ax_blend.text(0.92, 0.5, "0.60", fontsize=8, fontweight="bold", color=BRAND,
              transform=ax_blend.transAxes, va="center")

# Apply button mockup
ax_btn = fig.add_axes([0.35, 0.695, 0.30, 0.04])
ax_btn.set_facecolor(BRAND)
for sp in ax_btn.spines.values(): sp.set_edgecolor(BRAND)
ax_btn.set_xticks([]); ax_btn.set_yticks([])
ax_btn.text(0.5, 0.5, "✅  Apply new weights and rescore all clients",
            fontsize=8.5, fontweight="bold", color="white",
            transform=ax_btn.transAxes, va="center", ha="center")

# Three score histograms
fig.text(0.01, 0.685, "Current Score Distribution", fontsize=11, fontweight="bold", color=BRAND)

ax_h1 = fig.add_axes([0.01, 0.54, 0.31, 0.135])
ax_h1.hist(scored["retention_risk_score"], bins=15, color=RED, alpha=0.85, edgecolor="white")
ax_h1.set_title("Risk Score", fontsize=9, color=BRAND); ax_h1.tick_params(labelsize=7)
ax_h1.set_facecolor(CARD_BG); [sp.set_edgecolor("#E0E0E0") for sp in ax_h1.spines.values()]

ax_h2 = fig.add_axes([0.35, 0.54, 0.31, 0.135])
ax_h2.hist(scored["client_value_score"], bins=15, color=GREEN, alpha=0.85, edgecolor="white")
ax_h2.set_title("Value Score", fontsize=9, color=BRAND); ax_h2.tick_params(labelsize=7)
ax_h2.set_facecolor(CARD_BG); [sp.set_edgecolor("#E0E0E0") for sp in ax_h2.spines.values()]

ax_h3 = fig.add_axes([0.69, 0.54, 0.31, 0.135])
ax_h3.hist(scored["priority_score"], bins=15, color=BLUE, alpha=0.85, edgecolor="white")
ax_h3.set_title("Priority Score", fontsize=9, color=BRAND); ax_h3.tick_params(labelsize=7)
ax_h3.set_facecolor(CARD_BG); [sp.set_edgecolor("#E0E0E0") for sp in ax_h3.spines.values()]

# Scatter plot
fig.text(0.01, 0.53, "Risk vs Value Scatter  (bubble size = equity)", fontsize=11, fontweight="bold", color=BRAND)
ax_sc = fig.add_axes([0.01, 0.06, 0.98, 0.455])
ax_sc.set_facecolor(CARD_BG)
sample = scored.sample(min(200, len(scored)), random_state=1)
sizes = (sample["current_equity"] / sample["current_equity"].max() * 200 + 20).clip(10, 220)
sc = ax_sc.scatter(
    sample["client_value_score"], sample["retention_risk_score"],
    c=sample["priority_score"], s=sizes,
    cmap="RdYlGn_r", alpha=0.7, edgecolors="white", linewidths=0.4
)
ax_sc.axhline(hr, color=RED,   linestyle="--", linewidth=1.2, label=f"High Risk threshold ({hr})")
ax_sc.axvline(hv, color=GREEN, linestyle="--", linewidth=1.2, label=f"High Value threshold ({hv})")
ax_sc.set_xlabel("Client Value Score →", fontsize=9, color="#444")
ax_sc.set_ylabel("↑ Retention Risk Score", fontsize=9, color="#444")
ax_sc.set_title("Top-right quadrant = highest priority (high value + high risk)", fontsize=9, color=BRAND)
ax_sc.tick_params(labelsize=7)
ax_sc.legend(fontsize=7, loc="lower right")
plt.colorbar(sc, ax=ax_sc, label="Priority Score", shrink=0.8)
# Quadrant labels
ax_sc.text(hv*0.5, hr+(100-hr)*0.7, "High Risk\nLow Value", fontsize=7, color=RED, ha="center", alpha=0.6)
ax_sc.text(hv+(100-hv)*0.5, hr+(100-hr)*0.7, "★ TOP PRIORITY\nHigh Risk + High Value",
           fontsize=8, color=BRAND, ha="center", fontweight="bold", alpha=0.8)
ax_sc.text(hv+(100-hv)*0.5, hr*0.35, "VIP Upsell\nHigh Value Low Risk",
           fontsize=7, color=GREEN, ha="center", alpha=0.6)
[sp.set_edgecolor("#E0E0E0") for sp in ax_sc.spines.values()]

plt.savefig("/tmp/page3_scoring_engine.png", dpi=130, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Page 3 saved.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 4 — ACTION CENTER
# ═══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 19))
fig.patch.set_facecolor(BG)
header_bar(fig, "Action Center")

fig.text(0.01, 0.955, "🚨  Action Center — Clients requiring immediate retention or commercial action",
         fontsize=12, fontweight="bold", color=BRAND)

action_df = scored[scored["recommended_action"] != "Watch only"].sort_values("priority_score", ascending=False)

# KPIs
kpi_data = [
    (len(action_df), "Clients\nNeeding Action", RED),
    (f"{action_df['priority_score'].mean():.1f}", "Avg Priority\nScore", AMBER),
    (fmt_currency(action_df["current_equity"].sum()), "Equity\nat Stake", AMBER),
    (fmt_currency(action_df["spread_commission_revenue"].sum()), "Revenue\nat Stake", GREEN),
]
for i, (val, lbl, col) in enumerate(kpi_data):
    ax = fig.add_axes([0.01 + i*0.248, 0.88, 0.235, 0.065])
    kpi_card(ax, val, lbl, color=col)

# Action bar chart
action_counts = action_df["recommended_action"].value_counts()
ax_bar = fig.add_axes([0.01, 0.70, 0.98, 0.165])
colors_actions = {
    "Senior retention call today":                  RED,
    "Investigate complaints before commercial offer": AMBER,
    "Account manager follow-up":                    BLUE,
    "Cashback/bonus review":                        "#9B59B6",
    "VIP upsell opportunity":                       GREEN,
    "Do not offer bonus":                           "#E67E22",
    "Nurture campaign":                             "#1ABC9C",
}
bar_colors = [colors_actions.get(a, BLUE) for a in action_counts.index]
bars = ax_bar.barh(action_counts.index[::-1], action_counts.values[::-1],
                   color=bar_colors[::-1], edgecolor="white", height=0.65)
for bar, val in zip(bars, action_counts.values[::-1]):
    ax_bar.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                str(val), va="center", fontsize=8, fontweight="bold", color=BRAND)
ax_bar.set_title("Clients by Recommended Action", fontsize=10, color=BRAND, pad=6)
ax_bar.set_xlabel("Number of Clients", fontsize=8)
ax_bar.tick_params(labelsize=7.5)
ax_bar.set_facecolor(CARD_BG)
[sp.set_edgecolor("#E0E0E0") for sp in ax_bar.spines.values()]

# Action table (top 20 by priority)
fig.text(0.01, 0.695, "Action List — Top Priority Clients", fontsize=11, fontweight="bold", color=BRAND)
top20 = action_df.head(20)[
    ["client_id","client_name","country","account_manager",
     "priority_score","retention_risk_score","priority_level",
     "recommended_action","action_reason"]
].reset_index(drop=True)

ax_tbl = fig.add_axes([0.01, 0.07, 0.98, 0.615])
ax_tbl.axis("off")
cell_data = []
for _, row in top20.iterrows():
    cell_data.append([
        row["client_id"],
        row["client_name"][:16],
        row["country"],
        row["account_manager"].split()[0],
        f"{row['priority_score']:.0f}",
        f"{row['retention_risk_score']:.0f}",
        str(row["priority_level"]),
        row["recommended_action"][:28],
        row["action_reason"][:32],
    ])

tbl = ax_tbl.table(
    cellText=cell_data,
    colLabels=["Client ID","Name","Country","AM","Priority","Risk","Level","Action","Reason"],
    loc="upper center", cellLoc="left"
)
tbl.auto_set_font_size(False); tbl.set_fontsize(6.8)
tbl.scale(1, 1.62)
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("#E8E8E8")
    if r == 0:
        cell.set_facecolor(BRAND); cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#F7F9FC")
    if r > 0 and c == 6:
        lvl = cell_data[r-1][6]
        cell.set_facecolor("#FDECEA" if lvl=="Critical" else "#FEF9E7" if lvl=="Elevated" else "#EAF7EF")

plt.savefig("/tmp/page4_action_center.png", dpi=130, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Page 4 saved.")


# ═══════════════════════════════════════════════════════════════════════════
# PAGE 5 — SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 16))
fig.patch.set_facecolor(BG)
header_bar(fig, "Settings")

fig.text(0.01, 0.955, "🔧  Settings — Configure thresholds and platform behaviour",
         fontsize=12, fontweight="bold", color=BRAND)

# Threshold sliders
fig.text(0.01, 0.925, "Scoring Thresholds", fontsize=10, fontweight="bold", color=BRAND)
fig.text(0.01, 0.910, "These thresholds determine when a client is labelled High Risk, High Value, or Critical Priority.",
         fontsize=8, color="#666")

thresh_items = [
    ("High Risk threshold",         thresholds["high_risk"],      100, RED,   "Clients above this score are labelled 'High Risk'"),
    ("High Value threshold",        thresholds["high_value"],     100, GREEN, "Clients above this score are labelled 'High Value'"),
    ("Critical Priority threshold", thresholds["critical_priority"], 100, AMBER, "Clients above this score are labelled 'Critical'"),
]
for i, (name, val, maxv, col, hint) in enumerate(thresh_items):
    y_top = 0.895 - i * 0.085
    ax_t = fig.add_axes([0.01 + i*0.33, y_top - 0.062, 0.31, 0.058])
    ax_t.set_facecolor(CARD_BG)
    for sp in ax_t.spines.values(): sp.set_edgecolor("#D0D0D0")
    ax_t.set_xticks([]); ax_t.set_yticks([])
    ax_t.text(0.02, 0.85, name, fontsize=8, fontweight="bold", color=BRAND,
              transform=ax_t.transAxes, va="top")
    ax_t.text(0.02, 0.38, hint, fontsize=6.5, color="#888",
              transform=ax_t.transAxes, va="center")
    # slider bar
    track = FancyBboxPatch((0.02, 0.08), 0.82, 0.18, boxstyle="round,pad=0.01",
                            facecolor="#E8ECF0", edgecolor="#C8CDD2",
                            transform=ax_t.transAxes)
    ax_t.add_patch(track)
    fill = FancyBboxPatch((0.02, 0.08), 0.82*(val/maxv), 0.18, boxstyle="round,pad=0.01",
                           facecolor=col, edgecolor="none", alpha=0.85,
                           transform=ax_t.transAxes)
    ax_t.add_patch(fill)
    ax_t.text(0.88, 0.17, str(val), fontsize=9, fontweight="bold", color=BRAND,
              transform=ax_t.transAxes, va="center")

# Activity thresholds
fig.text(0.01, 0.723, "Activity Thresholds", fontsize=10, fontweight="bold", color=BRAND)
for i, (name, val, maxv, col, hint) in enumerate([
    ("Login inactivity (days)",     thresholds["login_inactivity_days"], 180, BLUE,  "Client is inactive if no login for this many days"),
    ("Large withdrawal % of equity",int(thresholds["large_withdrawal_pct"]*100), 80, AMBER,"Withdrawal is 'large' when > this % of equity"),
]):
    ax_a = fig.add_axes([0.01 + i*0.50, 0.635, 0.47, 0.075])
    ax_a.set_facecolor(CARD_BG)
    for sp in ax_a.spines.values(): sp.set_edgecolor("#D0D0D0")
    ax_a.set_xticks([]); ax_a.set_yticks([])
    ax_a.text(0.015, 0.85, name, fontsize=8.5, fontweight="bold", color=BRAND,
              transform=ax_a.transAxes, va="top")
    ax_a.text(0.015, 0.40, hint, fontsize=7, color="#888",
              transform=ax_a.transAxes, va="center")
    track = FancyBboxPatch((0.015, 0.10), 0.85, 0.20, boxstyle="round,pad=0.01",
                            facecolor="#E8ECF0", edgecolor="#C8CDD2", transform=ax_a.transAxes)
    ax_a.add_patch(track)
    fill = FancyBboxPatch((0.015, 0.10), 0.85*(val/maxv), 0.20, boxstyle="round,pad=0.01",
                           facecolor=col, edgecolor="none", alpha=0.85, transform=ax_a.transAxes)
    ax_a.add_patch(fill)
    display_val = f"{val}d" if "days" in name else f"{val}%"
    ax_a.text(0.92, 0.20, display_val, fontsize=9, fontweight="bold", color=BRAND,
              transform=ax_a.transAxes, va="center")

# Buttons
ax_save = fig.add_axes([0.01, 0.572, 0.30, 0.048])
ax_save.set_facecolor(BRAND); ax_save.set_xticks([]); ax_save.set_yticks([])
for sp in ax_save.spines.values(): sp.set_edgecolor(BRAND)
ax_save.text(0.5, 0.5, "✅  Save settings and rescore", fontsize=9, fontweight="bold",
             color="white", transform=ax_save.transAxes, va="center", ha="center")

ax_rst = fig.add_axes([0.35, 0.572, 0.20, 0.048])
ax_rst.set_facecolor("#EEF2F7"); ax_rst.set_xticks([]); ax_rst.set_yticks([])
for sp in ax_rst.spines.values(): sp.set_edgecolor("#C0C8D8")
ax_rst.text(0.5, 0.5, "🔄  Reset to defaults", fontsize=8.5, color=BRAND,
            transform=ax_rst.transAxes, va="center", ha="center")

# Impact preview
fig.text(0.01, 0.555, "Impact of Current Thresholds", fontsize=10, fontweight="bold", color=BRAND)

impact_data = [
    ("High Risk Clients",    int((scored["retention_risk_score"]>=hr).sum()),
     f"{(scored['retention_risk_score']>=hr).mean():.0%} of total", RED),
    ("High Value Clients",   int((scored["client_value_score"]>=hv).sum()),
     f"{(scored['client_value_score']>=hv).mean():.0%} of total", GREEN),
    ("Critical Priority",    int((scored["priority_score"]>=cp).sum()),
     f"{(scored['priority_score']>=cp).mean():.0%} of total", AMBER),
    ("High-Value at Risk",   int(((scored["retention_risk_score"]>=hr)&(scored["client_value_score"]>=hv)).sum()),
     "Immediate attention needed", RED),
]
for i, (lbl, val, delta, col) in enumerate(impact_data):
    ax = fig.add_axes([0.01 + i*0.248, 0.45, 0.235, 0.095])
    kpi_card(ax, val, lbl, color=col, delta=delta)

# Info box
ax_info = fig.add_axes([0.01, 0.39, 0.98, 0.048])
ax_info.set_facecolor("#EBF5FB")
for sp in ax_info.spines.values(): sp.set_edgecolor("#AED6F1")
ax_info.set_xticks([]); ax_info.set_yticks([])
ax_info.text(0.012, 0.5,
             "💡  Tip: If High Risk count is too high, raise the threshold. "
             "If too low, lower it. The goal is to focus your team on the most important clients.",
             fontsize=8, color="#1A5276", transform=ax_info.transAxes, va="center")

# Config summary table
fig.text(0.01, 0.375, "Current Configuration Summary", fontsize=10, fontweight="bold", color=BRAND)
ax_cfg = fig.add_axes([0.01, 0.08, 0.45, 0.285])
ax_cfg.axis("off")
cfg_data = [
    ["High Risk threshold",      str(thresholds["high_risk"])],
    ["High Value threshold",     str(thresholds["high_value"])],
    ["Critical Priority",        str(thresholds["critical_priority"])],
    ["Login inactivity (days)",  str(thresholds["login_inactivity_days"])],
    ["Large withdrawal %",       f"{int(thresholds['large_withdrawal_pct']*100)}%"],
    ["Risk/Value blend",         "60% risk · 40% value"],
]
tbl = ax_cfg.table(cellText=cfg_data, colLabels=["Setting","Value"],
                   loc="upper left", cellLoc="left")
tbl.auto_set_font_size(False); tbl.set_fontsize(8.5)
tbl.scale(1, 1.8)
for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor("#E0E0E0")
    if r == 0:
        cell.set_facecolor(BRAND); cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#F0F4FA")

# Risk weight summary
ax_wt = fig.add_axes([0.52, 0.08, 0.47, 0.285])
ax_wt.axis("off")
all_weights = [
    ["Withdrawal pressure",    str(DEFAULT_RISK_WEIGHTS["w_withdrawal"])],
    ["Volume drop",            str(DEFAULT_RISK_WEIGHTS["w_volume_drop"])],
    ["Login inactivity",       str(DEFAULT_RISK_WEIGHTS["w_login"])],
    ["Deposit staleness",      str(DEFAULT_RISK_WEIGHTS["w_deposit_stale"])],
    ["Complaints / tickets",   str(DEFAULT_RISK_WEIGHTS["w_complaints"])],
    ["Equity erosion",         str(DEFAULT_RISK_WEIGHTS["w_equity_erosion"])],
]
tbl2 = ax_wt.table(cellText=all_weights, colLabels=["Risk Weight Factor","Score (0–10)"],
                   loc="upper left", cellLoc="left")
tbl2.auto_set_font_size(False); tbl2.set_fontsize(8.5)
tbl2.scale(1, 1.8)
for (r, c), cell in tbl2.get_celld().items():
    cell.set_edgecolor("#E0E0E0")
    if r == 0:
        cell.set_facecolor(BRAND); cell.set_text_props(color="white", fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#F0F4FA")

plt.savefig("/tmp/page5_settings.png", dpi=130, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Page 5 saved.")
print("\nAll 5 screenshots generated successfully.")
