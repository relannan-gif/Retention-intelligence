"""
Phase 3 screenshots — all 6 pages including Data Management.
Uses matplotlib on the real scored dataset (dark gold executive theme).
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np, sys, os

sys.path.insert(0, "/home/user/Retention-intelligence")
os.chdir("/home/user/Retention-intelligence")

from data.sample_data import generate_clients
from utils.helpers import (DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS,
    DEFAULT_PROF_WEIGHTS, DEFAULT_REACT_WEIGHTS, DEFAULT_VIP_WEIGHTS,
    DEFAULT_THRESHOLDS, fmt_currency)
from utils.rules_engine import load_rules
from utils.scoring import score_dataframe, generate_trend_snapshots

rules  = load_rules()
df_raw = generate_clients(300)
scored = score_dataframe(df_raw, DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS,
    DEFAULT_PROF_WEIGHTS, DEFAULT_REACT_WEIGHTS, DEFAULT_VIP_WEIGHTS,
    DEFAULT_THRESHOLDS, rules=rules)
trend  = generate_trend_snapshots(scored)
t      = DEFAULT_THRESHOLDS
hr     = t["high_risk"]; hv = t["high_value"]; hp = t.get("high_profitability", 60)

# ── Theme ─────────────────────────────────────────────────────────────────────
BG    = "#0A0E1A"; CARD  = "#141B2D"; BORDER = "#1E2D4A"
GOLD  = "#F0B429"; RED   = "#EF4444"; GREEN  = "#10B981"
AMBER = "#F59E0B"; BLUE  = "#3B82F6"; PURPLE = "#8B5CF6"
TEXT  = "#E8E8E8"; MUTED = "#94A3B8"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "text.color": TEXT,
    "axes.facecolor": CARD, "axes.edgecolor": BORDER,
    "axes.labelcolor": TEXT, "xtick.color": MUTED,
    "ytick.color": MUTED, "grid.color": BORDER,
})

SAVE_DIR = "/tmp"

def new_fig(h=22):
    fig = plt.figure(figsize=(20, h))
    fig.patch.set_facecolor(BG)
    return fig

def nav_bar(fig, active_page):
    ax = fig.add_axes([0, 0.972, 1, 0.028])
    ax.set_facecolor("#0A0E1A")
    ax.axis("off")
    ax.axhline(0, color=BORDER, linewidth=1)
    ax.text(0.008, 0.5, "OneRoyal  Client Intelligence Platform",
            color=GOLD, fontsize=10, fontweight="bold", va="center")
    pages = ["Executive Dashboard","Client List","Scoring Engine",
             "Action Center","Settings","Data Management"]
    for i, p in enumerate(pages):
        x = 0.31 + i * 0.115
        color = GOLD if p == active_page else MUTED
        weight = "bold" if p == active_page else "normal"
        ax.text(x, 0.5, p, color=color, fontsize=7.8, va="center",
                fontweight=weight, ha="center")
        if p == active_page:
            ax.axhline(-0.05, xmin=x-0.04, xmax=x+0.04,
                       color=GOLD, linewidth=2.5)

def page_title(fig, title, subtitle, y=0.960):
    ax = fig.add_axes([0, y, 1, 0.012])
    ax.set_facecolor(BG); ax.axis("off")
    ax.text(0.012, 0.7, title, color=GOLD, fontsize=14, fontweight="bold", va="top")
    ax.text(0.012, -0.1, subtitle, color=MUTED, fontsize=8.5, va="bottom")

def divider(fig, y):
    ax = fig.add_axes([0, y, 1, 0.002])
    ax.set_facecolor(BORDER); ax.axis("off")

def kpi(ax, val, label, color=GOLD, sub=""):
    ax.set_facecolor(CARD)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER); sp.set_linewidth(1.2)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.5, 0.60, str(val), ha="center", va="center",
            fontsize=19, fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.22, label, ha="center", va="center",
            fontsize=8, color=MUTED, transform=ax.transAxes)
    if sub:
        ax.text(0.5, 0.07, sub, ha="center", va="center",
                fontsize=7.5, color=MUTED, transform=ax.transAxes)

def section_head(ax, text):
    ax.set_facecolor(BG); ax.axis("off")
    ax.text(0, 0.5, text, color=GOLD, fontsize=11, fontweight="bold", va="center")

def save(name):
    path = f"{SAVE_DIR}/{name}"
    plt.savefig(path, dpi=130, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    plt.close()
    print(f"  Saved: {path}")
    return path

# =============================================================================
# PAGE 1 — EXECUTIVE DASHBOARD
# =============================================================================
print("\n── Page 1: Executive Dashboard ──")
fig = new_fig(h=26)
nav_bar(fig, "Executive Dashboard")
page_title(fig, "📊 Executive Dashboard",
           "Portfolio overview · retention risk · commercial value · profitability", y=0.956)

# ── KPI tiles ─────────────────────────────────────────────────────────────────
labels = ["Total Clients","High Risk","High Value","High Profitability",
          "Critical Priority","Avg Health Score"]
values = [
    len(scored),
    int((scored["retention_risk_score"] >= hr).sum()),
    int((scored["commercial_value_score"] >= hv).sum()),
    int((scored["profitability_score"] >= hp).sum()),
    int((scored["priority_score"] >= t["critical_priority"]).sum()),
    f"{scored['client_health_score'].mean():.1f}",
]
colors = [GOLD, RED, BLUE, GREEN, AMBER, GREEN]
subs   = [
    "active clients",
    f"{(scored['retention_risk_score']>=hr).mean():.0%} of portfolio",
    f"{(scored['commercial_value_score']>=hv).mean():.0%} of portfolio",
    f"{(scored['profitability_score']>=hp).mean():.0%} of portfolio",
    f"threshold: {t['critical_priority']}",
    "/ 100 target",
]
for i, (v, l, c, s) in enumerate(zip(values, labels, colors, subs)):
    ax = fig.add_axes([0.01 + i*0.165, 0.895, 0.155, 0.054])
    kpi(ax, v, l, c, s)

divider(fig, 0.890)

# ── Risk distribution ─────────────────────────────────────────────────────────
ax1 = fig.add_axes([0.02, 0.780, 0.29, 0.102])
ax1.set_facecolor(CARD); ax1.tick_params(colors=MUTED, labelsize=7)
for sp in ax1.spines.values(): sp.set_edgecolor(BORDER)
n, bins = np.histogram(scored["retention_risk_score"], bins=20, range=(0,100))
c = [RED if b >= hr else AMBER if b >= hr*0.5 else GREEN for b in bins[:-1]]
ax1.bar(bins[:-1], n, width=(bins[1]-bins[0])*0.85, color=c, alpha=0.85)
ax1.axvline(hr, color=RED, linewidth=1.5, linestyle="--", alpha=0.8)
ax1.set_title("Retention Risk Distribution", color=GOLD, fontsize=8.5, pad=4)
ax1.set_xlabel("Risk Score →", fontsize=7, color=MUTED)

# ── Health distribution ───────────────────────────────────────────────────────
ax2 = fig.add_axes([0.35, 0.780, 0.29, 0.102])
ax2.set_facecolor(CARD); ax2.tick_params(colors=MUTED, labelsize=7)
for sp in ax2.spines.values(): sp.set_edgecolor(BORDER)
n2, bins2 = np.histogram(scored["client_health_score"], bins=20, range=(0,100))
c2 = [GREEN if b >= 60 else AMBER if b >= 40 else RED for b in bins2[:-1]]
ax2.bar(bins2[:-1], n2, width=(bins2[1]-bins2[0])*0.85, color=c2, alpha=0.85)
ax2.set_title("Client Health Distribution", color=GOLD, fontsize=8.5, pad=4)
ax2.set_xlabel("Health Score →", fontsize=7, color=MUTED)

# ── Profitability by book ─────────────────────────────────────────────────────
ax3 = fig.add_axes([0.68, 0.780, 0.30, 0.102])
ax3.set_facecolor(CARD); ax3.tick_params(colors=MUTED, labelsize=8)
for sp in ax3.spines.values(): sp.set_edgecolor(BORDER)
book_pnl = scored.groupby("book_type")["net_company_pnl"].sum() / 1000
bk_colors = {"A-Book": BLUE, "B-Book": RED, "M-Book": PURPLE}
bars = ax3.bar(book_pnl.index, book_pnl.values,
               color=[bk_colors.get(k, GOLD) for k in book_pnl.index], alpha=0.85)
for bar, val in zip(bars, book_pnl.values):
    ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
             f"${val:.0f}K", ha="center", va="bottom", fontsize=7.5, color=TEXT)
ax3.set_title("Monthly PnL by Book Type ($K)", color=GOLD, fontsize=8.5, pad=4)

divider(fig, 0.775)

# ── 3×3 Segmentation heatmap ──────────────────────────────────────────────────
ax_h_title = fig.add_axes([0.02, 0.745, 0.35, 0.024])
section_head(ax_h_title, "Client Segmentation Matrix (Risk × Value)")
ax_heat = fig.add_axes([0.02, 0.590, 0.35, 0.148])
ax_heat.set_facecolor(CARD)
for sp in ax_heat.spines.values(): sp.set_edgecolor(BORDER)

seg_names = {
    "Save Immediately": RED, "Senior Retention Review": "#F97316",
    "Automated Retention": AMBER, "Proactive Nurture": BLUE,
    "Standard Nurture": "#6366F1", "Light Touch": "#8B5CF6",
    "VIP Expansion": GREEN, "Growth Program": "#22C55E", "Monitor": MUTED,
}
risk_tiers  = ["Low Risk", "Medium Risk", "High Risk"]
value_tiers = ["Low Value", "Medium Value", "High Value"]
seg_grid = [
    ["Monitor",         "Light Touch",            "Automated Retention"],
    ["Growth Program",  "Standard Nurture",        "Senior Retention Review"],
    ["VIP Expansion",   "Proactive Nurture",        "Save Immediately"],
]
seg_counts = scored["segment"].value_counts()
for r, row in enumerate(seg_grid):
    for c, seg in enumerate(row):
        cnt = seg_counts.get(seg, 0)
        color = seg_names.get(seg, MUTED)
        rect = mpatches.FancyBboxPatch(
            (c+0.05, r+0.05), 0.88, 0.88,
            boxstyle="round,pad=0.03", linewidth=0,
            facecolor=color, alpha=0.25
        )
        ax_heat.add_patch(rect)
        ax_heat.text(c+0.5, r+0.62, seg, ha="center", va="center",
                     fontsize=6.5, color=TEXT, fontweight="bold")
        ax_heat.text(c+0.5, r+0.28, f"{cnt} clients", ha="center", va="center",
                     fontsize=7.5, color=color, fontweight="bold")
ax_heat.set_xlim(0,3); ax_heat.set_ylim(0,3)
ax_heat.set_xticks([0.5,1.5,2.5]); ax_heat.set_xticklabels(value_tiers, fontsize=7, color=MUTED)
ax_heat.set_yticks([0.5,1.5,2.5]); ax_heat.set_yticklabels(risk_tiers, fontsize=7, color=MUTED)

# ── Trend chart ───────────────────────────────────────────────────────────────
ax_tr_title = fig.add_axes([0.40, 0.745, 0.35, 0.024])
section_head(ax_tr_title, "Platform Trend — Portfolio Health & Risk (6 months)")
ax_tr = fig.add_axes([0.40, 0.590, 0.57, 0.148])
ax_tr.set_facecolor(CARD)
for sp in ax_tr.spines.values(): sp.set_edgecolor(BORDER)
dates = [str(d)[:7] for d in trend["date"]]
ax_tr.plot(dates, trend["avg_health_score"], color=GREEN, marker="o", ms=4,
           linewidth=2, label="Avg Health Score")
ax_tr2 = ax_tr.twinx()
ax_tr2.plot(dates, trend["avg_risk_score"], color=RED, marker="s", ms=4,
            linewidth=2, label="Avg Risk Score", linestyle="--")
ax_tr2.set_facecolor("none")
ax_tr.set_ylabel("Health Score", color=GREEN, fontsize=8)
ax_tr2.set_ylabel("Risk Score", color=RED, fontsize=8)
ax_tr.tick_params(colors=MUTED, labelsize=7, axis="x", rotation=20)
ax_tr.tick_params(colors=MUTED, labelsize=7, axis="y")
ax_tr2.tick_params(colors=MUTED, labelsize=7)
for sp in ax_tr2.spines.values(): sp.set_edgecolor(BORDER)
ax_tr.legend(loc="upper left", fontsize=7, facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT)
ax_tr2.legend(loc="upper right", fontsize=7, facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT)

divider(fig, 0.585)

# ── AM Performance ────────────────────────────────────────────────────────────
ax_am_title = fig.add_axes([0.02, 0.556, 0.55, 0.024])
section_head(ax_am_title, "Account Manager Performance")
am = scored.groupby("account_manager").agg(
    clients=("client_id","count"),
    avg_risk=("retention_risk_score","mean"),
    avg_value=("commercial_value_score","mean"),
    high_risk_count=("retention_risk_score", lambda x: (x>=hr).sum()),
).reset_index().sort_values("avg_risk", ascending=False).head(8)

ax_am = fig.add_axes([0.02, 0.410, 0.55, 0.140])
ax_am.set_facecolor(CARD)
for sp in ax_am.spines.values(): sp.set_edgecolor(BORDER)
y_pos = np.arange(len(am))
bars1 = ax_am.barh(y_pos+0.2, am["avg_risk"].values, 0.35, color=RED, alpha=0.75, label="Avg Risk")
bars2 = ax_am.barh(y_pos-0.2, am["avg_value"].values, 0.35, color=BLUE, alpha=0.75, label="Avg Value")
ax_am.set_yticks(y_pos)
ax_am.set_yticklabels([n.split()[-1] for n in am["account_manager"].values], fontsize=7.5, color=TEXT)
ax_am.set_xlabel("Score (0–100)", fontsize=7, color=MUTED)
ax_am.tick_params(colors=MUTED, labelsize=7)
ax_am.legend(fontsize=7, facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT, loc="lower right")
ax_am.axvline(50, color=BORDER, linewidth=0.8, linestyle=":")

# ── Geographic revenue ────────────────────────────────────────────────────────
ax_geo_title = fig.add_axes([0.60, 0.556, 0.38, 0.024])
section_head(ax_geo_title, "Top 10 Countries by Portfolio Equity")
geo = scored.groupby("country")["current_equity"].sum().nlargest(10)
ax_geo = fig.add_axes([0.60, 0.410, 0.38, 0.140])
ax_geo.set_facecolor(CARD)
for sp in ax_geo.spines.values(): sp.set_edgecolor(BORDER)
bars = ax_geo.barh(range(len(geo)), geo.values/1000, color=GOLD, alpha=0.80)
ax_geo.set_yticks(range(len(geo)))
ax_geo.set_yticklabels(geo.index, fontsize=7.5, color=TEXT)
ax_geo.set_xlabel("Total Equity ($K)", fontsize=7, color=MUTED)
ax_geo.tick_params(colors=MUTED, labelsize=7)
for bar, val in zip(bars, geo.values/1000):
    ax_geo.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
                f"${val:.0f}K", va="center", fontsize=6.5, color=MUTED)

save("p3_page1_executive_dashboard.png")
print("  Page 1 done.")

# =============================================================================
# PAGE 2 — CLIENT LIST
# =============================================================================
print("\n── Page 2: Client List ──")
fig = new_fig(h=22)
nav_bar(fig, "Client List")
page_title(fig, "👥 Client List",
           "All 300 clients · 8 filters · all 6 scores · recommended actions · segment", y=0.956)

# ── Filters strip ─────────────────────────────────────────────────────────────
filter_labels = ["Search client…","Book Type: All","Risk Level: All",
                 "Value Level: All","Owner: All","Segment: All",
                 "Status: All","Priority: All"]
for i, lbl in enumerate(filter_labels[:8]):
    ax = fig.add_axes([0.01 + i*0.123, 0.905, 0.115, 0.032])
    ax.set_facecolor("#141B2D")
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER); sp.set_linewidth(0.8)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.08, 0.5, lbl, color=MUTED, fontsize=6.8, va="center")

divider(fig, 0.900)

# ── Summary metrics ───────────────────────────────────────────────────────────
s_labels = ["Showing","High Risk","High Value","Need Action","Avg Priority"]
s_values = [
    len(scored),
    int((scored["retention_risk_score"]>=hr).sum()),
    int((scored["commercial_value_score"]>=hv).sum()),
    int((scored["recommended_action"] != "Monitor Only").sum()),
    f"{scored['priority_score'].mean():.1f}",
]
s_colors = [TEXT, RED, BLUE, AMBER, GOLD]
for i, (v, l, c) in enumerate(zip(s_values, s_labels, s_colors)):
    ax = fig.add_axes([0.01+i*0.198, 0.858, 0.185, 0.036])
    kpi(ax, v, l, c)

divider(fig, 0.854)

# ── Client table ──────────────────────────────────────────────────────────────
ax_tbl = fig.add_axes([0.01, 0.270, 0.98, 0.578])
ax_tbl.set_facecolor(CARD); ax_tbl.axis("off")

cols = ["Client ID","Client Name","Country","Book","Risk","Value","Profit",
        "Health","Segment","Action","Owner"]
col_x = [0.00, 0.055, 0.145, 0.210, 0.255, 0.300, 0.348,
          0.398, 0.450, 0.565, 0.800]

# Header
for j, (col, x) in enumerate(zip(cols, col_x)):
    ax_tbl.text(x, 0.968, col, color=GOLD, fontsize=7.5, fontweight="bold", va="top")
ax_tbl.axhline(0.960, color=BORDER, linewidth=0.8)

# Rows
disp = scored.sort_values("priority_score", ascending=False).head(25)
for i, (_, row) in enumerate(disp.iterrows()):
    y = 0.930 - i * 0.038
    bg = "#0F1629" if i % 2 == 0 else CARD
    rect = mpatches.FancyBboxPatch((0, y-0.012), 1.0, 0.038,
        boxstyle="square,pad=0", linewidth=0, facecolor=bg)
    ax_tbl.add_patch(rect)

    rr = row["retention_risk_score"]
    vv = row["commercial_value_score"]
    pp = row["profitability_score"]
    risk_c   = RED   if rr >= hr else (AMBER if rr >= hr*0.5 else GREEN)
    value_c  = BLUE  if vv >= hv else (MUTED if vv >= hv*0.5 else MUTED)
    prof_c   = GREEN if pp >= hp else MUTED

    vals = [
        row["client_id"],
        row["client_name"][:18],
        row["country"][:12],
        row["book_type"],
        f"{rr:.0f}",
        f"{vv:.0f}",
        f"{pp:.0f}",
        row["health_label"],
        row["segment"][:22],
        row["recommended_action"][:28],
        row["recommended_owner"],
    ]
    fcolors = [MUTED, TEXT, TEXT, MUTED, risk_c, value_c, prof_c,
               GREEN if row["health_label"]=="Excellent" else AMBER,
               TEXT, GOLD, TEXT]

    for j, (val, x, fc) in enumerate(zip(vals, col_x, fcolors)):
        ax_tbl.text(x, y, str(val), color=fc, fontsize=6.5, va="center")

ax_tbl.set_xlim(0,1); ax_tbl.set_ylim(0,1)
ax_tbl.text(0.5, -0.03, "Showing 25 of 300 clients (sorted by Priority Score descending)",
            ha="center", color=MUTED, fontsize=7.5)

# ── Score column legend ───────────────────────────────────────────────────────
ax_leg = fig.add_axes([0.01, 0.225, 0.98, 0.038])
ax_leg.set_facecolor("#0F1629"); ax_leg.axis("off")
for sp in ax_leg.spines.values(): sp.set_edgecolor(BORDER)
legend_items = [
    (RED, f"Risk ≥{hr}  = High Risk"),
    (AMBER, f"Risk {int(hr*0.5)}–{hr}  = Medium"),
    (GREEN, f"Risk <{int(hr*0.5)}  = Low"),
    (BLUE, f"Value ≥{hv}  = High Value"),
    (GREEN, f"Profit ≥{hp}  = High Profit"),
]
for i, (c, lbl) in enumerate(legend_items):
    ax_leg.add_patch(mpatches.Circle((0.04+i*0.2, 0.5), 0.015, color=c, transform=ax_leg.transAxes))
    ax_leg.text(0.053+i*0.2, 0.5, lbl, color=TEXT, fontsize=7, va="center")

save("p3_page2_client_list.png")
print("  Page 2 done.")

# =============================================================================
# PAGE 3 — SCORING ENGINE  (new: Active Scoring Rules tab)
# =============================================================================
print("\n── Page 3: Scoring Engine ──")
fig = new_fig(h=26)
nav_bar(fig, "Scoring Engine")
page_title(fig, "⚙️ Scoring Engine",
           "Active Scoring Rules · weight sliders · 6-score distributions · Risk vs Profitability scatter",
           y=0.956)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = ["Active Scoring Rules","Risk Weights","Value Weights",
        "Reactivation Weights","VIP Upside Weights","Score Distributions"]
for i, tab in enumerate(tabs):
    x = 0.01 + i * 0.163
    color = GOLD if i == 0 else MUTED
    fig.text(x, 0.945, tab, color=color, fontsize=8.5,
             fontweight="bold" if i==0 else "normal")
if True:
    ax_uline = fig.add_axes([0.01, 0.942, 0.163, 0.002])
    ax_uline.set_facecolor(GOLD); ax_uline.axis("off")

divider(fig, 0.938)

# ── Active Scoring Rules — Retention Risk ─────────────────────────────────────
ax_rr_head = fig.add_axes([0.01, 0.910, 0.50, 0.024])
section_head(ax_rr_head, "Retention Risk Factors — active band rules")

rr_rules = rules["retention_risk"]
rr_rows = []
for fkey, fdata in rr_rules.items():
    for band in fdata["bands"]:
        rr_rows.append([fdata["label"], band["label"], str(band["points"])])

ax_rr = fig.add_axes([0.01, 0.715, 0.49, 0.190])
ax_rr.set_facecolor(CARD); ax_rr.axis("off")
for sp in ax_rr.spines.values(): sp.set_edgecolor(BORDER)

col_heads = ["Factor","Band Condition","Points"]
col_xr = [0.0, 0.30, 0.86]
ax_rr.text(0.00, 0.970, col_heads[0], color=GOLD, fontsize=7.5, fontweight="bold", va="top")
ax_rr.text(0.30, 0.970, col_heads[1], color=GOLD, fontsize=7.5, fontweight="bold", va="top")
ax_rr.text(0.86, 0.970, col_heads[2], color=GOLD, fontsize=7.5, fontweight="bold", va="top")
ax_rr.axhline(0.960, color=BORDER, linewidth=0.8)

for i, row in enumerate(rr_rows):
    y = 0.930 - i * 0.044
    bg = "#0F1629" if i % 2 == 0 else CARD
    rect = mpatches.FancyBboxPatch((0, y-0.018), 1, 0.044,
        boxstyle="square,pad=0", facecolor=bg, linewidth=0)
    ax_rr.add_patch(rect)
    pts = int(row[2])
    pt_color = RED if pts >= 75 else AMBER if pts >= 40 else GREEN
    ax_rr.text(0.00, y, row[0], color=TEXT, fontsize=6.5, va="center")
    ax_rr.text(0.30, y, row[1], color=MUTED, fontsize=6.5, va="center")
    ax_rr.text(0.86, y, row[2], color=pt_color, fontsize=7.5, va="center", fontweight="bold")
ax_rr.set_xlim(0,1); ax_rr.set_ylim(0,1)

# ── Active Scoring Rules — Commercial Value ───────────────────────────────────
ax_cv_head = fig.add_axes([0.52, 0.910, 0.47, 0.024])
section_head(ax_cv_head, "Commercial Value Factors — active band rules")

cv_rules = rules["commercial_value"]
cv_rows = []
for fkey, fdata in cv_rules.items():
    for band in fdata["bands"]:
        cv_rows.append([fdata["label"], band["label"], str(band["points"])])

ax_cv = fig.add_axes([0.52, 0.715, 0.47, 0.190])
ax_cv.set_facecolor(CARD); ax_cv.axis("off")
ax_cv.text(0.00, 0.970, "Factor", color=GOLD, fontsize=7.5, fontweight="bold", va="top")
ax_cv.text(0.33, 0.970, "Band Condition", color=GOLD, fontsize=7.5, fontweight="bold", va="top")
ax_cv.text(0.86, 0.970, "Points", color=GOLD, fontsize=7.5, fontweight="bold", va="top")
ax_cv.axhline(0.960, color=BORDER, linewidth=0.8)
for i, row in enumerate(cv_rows):
    y = 0.930 - i * 0.033
    bg = "#0F1629" if i % 2 == 0 else CARD
    rect = mpatches.FancyBboxPatch((0, y-0.014), 1, 0.033,
        boxstyle="square,pad=0", facecolor=bg, linewidth=0)
    ax_cv.add_patch(rect)
    pts = int(row[2])
    pt_color = GREEN if pts >= 75 else AMBER if pts >= 40 else MUTED
    ax_cv.text(0.00, y, row[0], color=TEXT, fontsize=6.5, va="center")
    ax_cv.text(0.33, y, row[1], color=MUTED, fontsize=6.5, va="center")
    ax_cv.text(0.86, y, row[2], color=pt_color, fontsize=7.5, va="center", fontweight="bold")
ax_cv.set_xlim(0,1); ax_cv.set_ylim(0,1)

divider(fig, 0.710)

# ── Profitability bands ───────────────────────────────────────────────────────
ax_pb_head = fig.add_axes([0.01, 0.682, 0.50, 0.024])
section_head(ax_pb_head, "Profitability Bands (by Book Type)")

pr = rules["profitability"]
for bi, (bkey, bcolor) in enumerate([("a_book",BLUE),("b_book",RED),("m_book",PURPLE)]):
    bdata = pr[bkey]
    left = 0.01 + bi * 0.328
    ax_bh = fig.add_axes([left, 0.656, 0.315, 0.022])
    ax_bh.set_facecolor("#0F1629"); ax_bh.axis("off")
    ax_bh.text(0.02, 0.5, bdata["label"], color=bcolor, fontsize=8, fontweight="bold", va="center")

    ax_b = fig.add_axes([left, 0.530, 0.315, 0.122])
    ax_b.set_facecolor(CARD); ax_b.axis("off")
    for sp in ax_b.spines.values(): sp.set_edgecolor(BORDER)
    ax_b.text(0.02, 0.965, bdata.get("formula_label",""), color=MUTED, fontsize=6.5, va="top", style="italic")
    ax_b.axhline(0.930, color=BORDER, linewidth=0.7)
    for i, band in enumerate(bdata["bands"]):
        y = 0.890 - i * 0.135
        bg = "#0F1629" if i%2==0 else CARD
        rect = mpatches.FancyBboxPatch((0, y-0.060), 1, 0.135,
            boxstyle="square,pad=0", facecolor=bg, linewidth=0)
        ax_b.add_patch(rect)
        pts = int(band["points"])
        pt_c = bcolor if pts >= 70 else (AMBER if pts >= 40 else MUTED)
        ax_b.text(0.02, y, band["label"], color=TEXT, fontsize=6.2, va="center")
        ax_b.text(0.85, y, str(pts), color=pt_c, fontsize=7.5, va="center", fontweight="bold")
    ax_b.set_xlim(0,1); ax_b.set_ylim(0,1)

divider(fig, 0.525)

# ── Score distributions (6 histograms) ───────────────────────────────────────
ax_dist_head = fig.add_axes([0.01, 0.497, 0.50, 0.024])
section_head(ax_dist_head, "Score Distributions — all 6 scores")

score_cols = [("retention_risk_score","Risk",RED),
              ("commercial_value_score","Value",BLUE),
              ("profitability_score","Profitability",GREEN),
              ("reactivation_score","Reactivation",AMBER),
              ("vip_upside_score","VIP Upside",PURPLE),
              ("client_health_score","Health",GOLD)]
for i, (col, lbl, color) in enumerate(score_cols):
    row_idx, col_idx = divmod(i, 3)
    ax_d = fig.add_axes([0.01+col_idx*0.327, 0.355-row_idx*0.125, 0.310, 0.108])
    ax_d.set_facecolor(CARD)
    for sp in ax_d.spines.values(): sp.set_edgecolor(BORDER)
    ax_d.tick_params(colors=MUTED, labelsize=6)
    n, bins = np.histogram(scored[col], bins=20, range=(0,100))
    ax_d.bar(bins[:-1], n, width=(bins[1]-bins[0])*0.85, color=color, alpha=0.75)
    ax_d.set_title(f"{lbl} Score", color=color, fontsize=8, pad=3)
    ax_d.set_xlabel("Score", fontsize=6, color=MUTED)
    avg = scored[col].mean()
    ax_d.axvline(avg, color=TEXT, linewidth=1.2, linestyle="--", alpha=0.7)
    ax_d.text(avg+1, ax_d.get_ylim()[1]*0.85, f"avg {avg:.0f}", fontsize=6, color=TEXT)

save("p3_page3_scoring_engine.png")
print("  Page 3 done.")

# =============================================================================
# PAGE 4 — ACTION CENTER
# =============================================================================
print("\n── Page 4: Action Center ──")
fig = new_fig(h=24)
nav_bar(fig, "Action Center")
page_title(fig, "🎯 Action Center",
           "Priority-sorted retention actions · owner assignment · team workload · deep-dive",
           y=0.956)

# ── KPI tiles ─────────────────────────────────────────────────────────────────
ac_labels = ["Total Actions","Urgent / Critical","High Risk + Value","Reactivations","Monitor Only"]
ac_values = [
    len(scored),
    int((scored["priority_score"] >= t["critical_priority"]).sum()),
    int(((scored["retention_risk_score"]>=hr) & (scored["commercial_value_score"]>=hv)).sum()),
    int((scored["recommended_action"]=="Reactivation Campaign").sum()),
    int((scored["recommended_action"]=="Monitor Only").sum()),
]
ac_colors = [GOLD, RED, AMBER, BLUE, MUTED]
for i, (v, l, c) in enumerate(zip(ac_values, ac_labels, ac_colors)):
    ax = fig.add_axes([0.01 + i*0.197, 0.898, 0.188, 0.048])
    kpi(ax, v, l, c)

divider(fig, 0.893)

# ── Action breakdown bar ──────────────────────────────────────────────────────
ax_act_head = fig.add_axes([0.01, 0.860, 0.44, 0.026])
section_head(ax_act_head, "Actions by Type")
action_counts = scored["recommended_action"].value_counts().head(8)
ax_act = fig.add_axes([0.01, 0.740, 0.44, 0.115])
ax_act.set_facecolor(CARD)
for sp in ax_act.spines.values(): sp.set_edgecolor(BORDER)
ax_act.tick_params(colors=MUTED, labelsize=6.5)
bars = ax_act.barh(range(len(action_counts)), action_counts.values, color=GOLD, alpha=0.75)
ax_act.set_yticks(range(len(action_counts)))
ax_act.set_yticklabels([a[:35] for a in action_counts.index], fontsize=6, color=TEXT)
for bar, val in zip(bars, action_counts.values):
    ax_act.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2,
                str(val), va="center", fontsize=6.5, color=MUTED)

# ── Owner breakdown pie ───────────────────────────────────────────────────────
ax_own_head = fig.add_axes([0.50, 0.860, 0.48, 0.026])
section_head(ax_own_head, "Workload by Recommended Owner")
owner_counts = scored["recommended_owner"].value_counts()
ax_pie = fig.add_axes([0.52, 0.740, 0.45, 0.115])
ax_pie.set_facecolor(CARD)
pie_colors = [GOLD, RED, BLUE, GREEN, PURPLE][:len(owner_counts)]
wedges, texts, autotexts = ax_pie.pie(
    owner_counts.values, labels=owner_counts.index,
    colors=pie_colors, autopct="%1.0f%%",
    textprops={"color": TEXT, "fontsize": 7},
    pctdistance=0.75, startangle=90)
for at in autotexts: at.set_fontsize(6.5); at.set_color(BG)

divider(fig, 0.735)

# ── Priority action table ─────────────────────────────────────────────────────
ax_ptbl_head = fig.add_axes([0.01, 0.707, 0.98, 0.024])
section_head(ax_ptbl_head, "Priority Action Queue — Top 20 clients (sorted by Priority Score)")
ax_ptbl = fig.add_axes([0.01, 0.300, 0.98, 0.402])
ax_ptbl.set_facecolor(CARD); ax_ptbl.axis("off")

tbl_cols = ["Priority","Client","Country","Book","Risk","Value","Profit","Priority Score","Action","Owner"]
tbl_x    = [0.000, 0.040, 0.130, 0.188, 0.228, 0.268, 0.308, 0.358, 0.435, 0.790]
for j, (col, x) in enumerate(zip(tbl_cols, tbl_x)):
    ax_ptbl.text(x, 0.970, col, color=GOLD, fontsize=7.2, fontweight="bold", va="top")
ax_ptbl.axhline(0.958, color=BORDER, linewidth=0.8)

top20 = scored.sort_values("priority_score", ascending=False).head(20)
for i, (_, row) in enumerate(top20.iterrows()):
    y = 0.925 - i * 0.048
    bg = "#0F1629" if i % 2 == 0 else CARD
    ax_ptbl.add_patch(mpatches.FancyBboxPatch((0, y-0.018), 1, 0.048,
        boxstyle="square,pad=0", facecolor=bg, linewidth=0))
    rr = row["retention_risk_score"]; vv = row["commercial_value_score"]
    pp = row["profitability_score"];  ps = row["priority_score"]
    risk_c = RED if rr>=hr else (AMBER if rr>=hr*0.5 else GREEN)
    ps_c   = RED if ps>=t["critical_priority"] else (AMBER if ps>=50 else TEXT)
    row_vals = [f"#{i+1}", row["client_name"][:16], row["country"][:10],
                row["book_type"], f"{rr:.0f}", f"{vv:.0f}", f"{pp:.0f}",
                f"{ps:.0f}", row["recommended_action"][:38], row["recommended_owner"]]
    colors_r = [MUTED, TEXT, MUTED, MUTED, risk_c, BLUE, GREEN, ps_c, GOLD, TEXT]
    for j, (val, x, fc) in enumerate(zip(row_vals, tbl_x, colors_r)):
        ax_ptbl.text(x, y, str(val), color=fc, fontsize=6.2, va="center")
ax_ptbl.set_xlim(0,1); ax_ptbl.set_ylim(0,1)

# ── Team workload ─────────────────────────────────────────────────────────────
ax_tw_head = fig.add_axes([0.01, 0.272, 0.98, 0.024])
section_head(ax_tw_head, "Team Workload Summary")
teams = scored.groupby("recommended_owner").agg(
    clients=("client_id","count"),
    avg_priority=("priority_score","mean"),
    critical=("priority_score", lambda x: (x>=t["critical_priority"]).sum()),
).reset_index()

ax_tw = fig.add_axes([0.01, 0.140, 0.98, 0.124])
ax_tw.set_facecolor(CARD); ax_tw.axis("off")
tw_cols = ["Team / Owner","Clients Assigned","Avg Priority Score","Critical Items"]
tw_x = [0.0, 0.35, 0.58, 0.80]
for j, (col, x) in enumerate(zip(tw_cols, tw_x)):
    ax_tw.text(x, 0.95, col, color=GOLD, fontsize=8, fontweight="bold", va="top")
ax_tw.axhline(0.89, color=BORDER, linewidth=0.8)
for i, (_, row) in enumerate(teams.iterrows()):
    y = 0.75 - i * 0.165
    bg = "#0F1629" if i%2==0 else CARD
    ax_tw.add_patch(mpatches.FancyBboxPatch((0, y-0.065), 1, 0.165,
        boxstyle="square,pad=0", facecolor=bg, linewidth=0))
    crit_c = RED if row["critical"] > 5 else (AMBER if row["critical"] > 2 else GREEN)
    for j, (val, x) in enumerate(zip(
        [row["recommended_owner"], f"{int(row['clients']):,}",
         f"{row['avg_priority']:.1f}", f"{int(row['critical'])}"],
        tw_x
    )):
        col = [TEXT, TEXT, GOLD, crit_c][j]
        ax_tw.text(x, y, str(val), color=col, fontsize=8, va="center")
ax_tw.set_xlim(0,1); ax_tw.set_ylim(0,1)

save("p3_page4_action_center.png")
print("  Page 4 done.")

# =============================================================================
# PAGE 5 — SETTINGS
# =============================================================================
print("\n── Page 5: Settings ──")
fig = new_fig(h=28)
nav_bar(fig, "Settings")
page_title(fig, "⚙️ Settings",
           "Score thresholds · activity settings · Business Rules Engine — all 15 factors",
           y=0.960)

# ── Scoring thresholds ────────────────────────────────────────────────────────
ax_th_head = fig.add_axes([0.01, 0.935, 0.98, 0.020])
section_head(ax_th_head, "Scoring Thresholds")

thresh_items = [
    ("High Risk Threshold", t["high_risk"],   "Clients above this are 'High Risk'",   RED),
    ("High Value Threshold",t["high_value"],   "Clients above this are 'High Value'",  BLUE),
    ("High Profitability",  t["high_profitability"], "High-profit flag threshold",     GREEN),
    ("Critical Priority",   t["critical_priority"],  "Critical alert threshold",       AMBER),
]
for i, (label, val, hint, color) in enumerate(thresh_items):
    ax = fig.add_axes([0.01 + i*0.248, 0.875, 0.235, 0.054])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    ax.set_xticks([]); ax.set_yticks([])
    # Slider bar
    ax.axhline(0.32, xmin=0.06, xmax=0.94, color=BORDER, linewidth=6)
    ax.axhline(0.32, xmin=0.06, xmax=0.06+val/100*0.88, color=color, linewidth=6)
    ax.plot([0.06+val/100*0.88], [0.32], "o", color=color, ms=9, transform=ax.transAxes)
    ax.text(0.5, 0.75, f"{val}", ha="center", fontsize=14, fontweight="bold",
            color=color, transform=ax.transAxes)
    ax.text(0.5, 0.10, label, ha="center", fontsize=7, color=MUTED, transform=ax.transAxes)

divider(fig, 0.870)

# ── Activity thresholds ───────────────────────────────────────────────────────
ax_at_head = fig.add_axes([0.01, 0.843, 0.98, 0.020])
section_head(ax_at_head, "Activity Thresholds")

act_items = [
    ("Login Inactivity (days)",    t["login_inactivity_days"], 7, 180, GOLD),
    ("Large Withdrawal % of equity", int(t["large_withdrawal_pct"]*100), 5, 80, RED),
    ("Dormant Client Threshold (days)", t.get("dormant_days",30), 7, 90,  AMBER),
]
for i, (label, val, mn, mx, color) in enumerate(act_items):
    ax = fig.add_axes([0.02 + i*0.328, 0.792, 0.308, 0.045])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    ax.set_xticks([]); ax.set_yticks([])
    frac = (val - mn) / (mx - mn)
    ax.axhline(0.35, xmin=0.05, xmax=0.95, color=BORDER, linewidth=5)
    ax.axhline(0.35, xmin=0.05, xmax=0.05+frac*0.90, color=color, linewidth=5)
    ax.plot([0.05+frac*0.90], [0.35], "o", color=color, ms=8, transform=ax.transAxes)
    ax.text(0.5, 0.78, f"{val}", ha="center", fontsize=12, fontweight="bold",
            color=color, transform=ax.transAxes)
    ax.text(0.5, 0.10, label, ha="center", fontsize=7, color=MUTED, transform=ax.transAxes)

divider(fig, 0.787)

# ── Business Rules Engine ─────────────────────────────────────────────────────
ax_bre_head = fig.add_axes([0.01, 0.760, 0.98, 0.022])
section_head(ax_bre_head, "Business Rules Engine — Scoring Bands (edit points 0–100 per band)")
fig.text(0.012, 0.754, "Tabs: Retention Risk Factors · Commercial Value Factors · Profitability Bands",
         color=MUTED, fontsize=8)

# ── Tab: Retention Risk ───────────────────────────────────────────────────────
bre_tabs = ["Retention Risk Factors","Commercial Value Factors","Profitability Bands"]
for ti, tab in enumerate(bre_tabs):
    color = GOLD if ti==0 else MUTED
    fig.text(0.01 + ti*0.24, 0.742, tab, color=color, fontsize=8,
             fontweight="bold" if ti==0 else "normal")

# Render RR bands as a clean mini-table
ax_bre = fig.add_axes([0.01, 0.540, 0.97, 0.196])
ax_bre.set_facecolor(CARD); ax_bre.axis("off")
for sp in ax_bre.spines.values(): sp.set_edgecolor(BORDER)

# Two columns of factors
rr_factors = list(rules["retention_risk"].items())
col_width = 0.49
for fi, (fkey, fdata) in enumerate(rr_factors):
    col = fi % 2; row_offset = fi // 2
    left_x = 0.01 + col * col_width
    base_y  = 0.95 - row_offset * 0.33

    ax_bre.text(left_x, base_y, f"▸ {fdata['label']}", color=GOLD, fontsize=7.5,
                fontweight="bold", va="top")
    ax_bre.text(left_x+col_width*0.55, base_y, "Band Condition", color=MUTED, fontsize=6.5, va="top")
    ax_bre.text(left_x+col_width*0.93, base_y, "Pts", color=MUTED, fontsize=6.5, va="top")
    ax_bre.axhline(base_y-0.04, xmin=left_x, xmax=left_x+col_width-0.01, color=BORDER, linewidth=0.6)

    for bi, band in enumerate(fdata["bands"]):
        by = base_y - 0.07 - bi * 0.075
        pts = int(band["points"])
        pt_c = RED if pts>=75 else AMBER if pts>=40 else GREEN
        ax_bre.text(left_x, by, band["label"], color=TEXT, fontsize=6.2, va="center")
        ax_bre.text(left_x+col_width*0.93, by, str(pts), color=pt_c,
                    fontsize=7, va="center", fontweight="bold")

ax_bre.set_xlim(0,1); ax_bre.set_ylim(0,1)

divider(fig, 0.535)

# ── Impact preview ────────────────────────────────────────────────────────────
ax_imp_head = fig.add_axes([0.01, 0.507, 0.98, 0.022])
section_head(ax_imp_head, "Impact of Current Thresholds")
imp_items = [
    ("High Risk Clients",      int((scored["retention_risk_score"]>=hr).sum()),    RED),
    ("High Value Clients",     int((scored["commercial_value_score"]>=hv).sum()),   BLUE),
    ("High Profitability",     int((scored["profitability_score"]>=hp).sum()),      GREEN),
    ("Critical Priority",      int((scored["priority_score"]>=t["critical_priority"]).sum()), RED),
    ("High-Value At Risk",     int(((scored["retention_risk_score"]>=hr)&
                                   (scored["commercial_value_score"]>=hv)).sum()),  AMBER),
]
for i, (label, val, color) in enumerate(imp_items):
    ax = fig.add_axes([0.01 + i*0.197, 0.450, 0.188, 0.050])
    kpi(ax, val, label, color, f"{val/len(scored):.0%} of portfolio" if i<4 else "clients")

divider(fig, 0.445)

# ── Current config display ────────────────────────────────────────────────────
ax_cfg_head = fig.add_axes([0.01, 0.418, 0.98, 0.022])
section_head(ax_cfg_head, "Current Configuration Summary")
ax_cfg = fig.add_axes([0.01, 0.260, 0.97, 0.152])
ax_cfg.set_facecolor(CARD); ax_cfg.axis("off")
cfg_data = [
    ["Setting","Value","Setting","Value"],
    ["High Risk Threshold",     str(t["high_risk"]),      "High Value Threshold",      str(t["high_value"])],
    ["High Profitability",      str(t.get("high_profitability",60)),
     "Critical Priority",        str(t["critical_priority"])],
    ["Login Inactivity",        f"{t['login_inactivity_days']}d",
     "Large Withdrawal",         f"{int(t['large_withdrawal_pct']*100)}% of equity"],
    ["Dormant Threshold",       f"{t.get('dormant_days',30)}d",
     "Risk Weight — Complaints", "9 / 10 (highest)"],
    ["Value Weight — VIP",      "9 / 10 (highest)",
     "Scoring Rules Source",     "config/scoring_rules.json"],
]
col_x2 = [0.0, 0.22, 0.52, 0.74]
for ri, row in enumerate(cfg_data):
    y = 0.96 - ri * 0.165
    bg = "#0F1629" if ri % 2 == 0 else CARD
    ax_cfg.add_patch(mpatches.FancyBboxPatch(
        (0, y-0.080), 1, 0.165, boxstyle="square,pad=0", facecolor=bg, linewidth=0))
    for ci, (cell, x) in enumerate(zip(row, col_x2)):
        color = GOLD if ri==0 else (GOLD if ci%2==0 and ri>0 else TEXT)
        ax_cfg.text(x, y, cell, color=color, fontsize=7.5, va="center",
                    fontweight="bold" if ri==0 or ci%2==0 else "normal")
ax_cfg.set_xlim(0,1); ax_cfg.set_ylim(0,1)

save("p3_page5_settings.png")
print("  Page 5 done.")

# =============================================================================
# PAGE 6 — DATA MANAGEMENT
# =============================================================================
print("\n── Page 6: Data Management ──")
fig = new_fig(h=26)
nav_bar(fig, "Data Management")
page_title(fig, "📂 Data Management",
           "Data source selector · drag-and-drop upload · quality monitoring · refresh schedule",
           y=0.957)

# ── Status tiles ──────────────────────────────────────────────────────────────
status_items = [
    ("Current Source",     "Sample Data\n(Built-in 300 clients)", GOLD),
    ("Last Refresh",       "Just now",                            GREEN),
    ("Records Loaded",     "300",                                 TEXT),
    ("Data Quality",       "100 / 100",                          GREEN),
    ("Next Refresh",       "Manual only",                         MUTED),
]
for i, (label, val, color) in enumerate(status_items):
    ax = fig.add_axes([0.01 + i*0.197, 0.900, 0.188, 0.048])
    kpi(ax, val, label, color)

divider(fig, 0.895)

# ── Source tabs ───────────────────────────────────────────────────────────────
src_tabs = ["📊 Sample Data","📁 Excel / CSV Upload","🔌 CRM API","🤖 Holistics Feed"]
for i, tab in enumerate(src_tabs):
    color = GOLD if i == 1 else MUTED  # highlight Upload tab
    fig.text(0.01 + i*0.248, 0.880, tab, color=color, fontsize=9,
             fontweight="bold" if i==1 else "normal")
ax_uline2 = fig.add_axes([0.01 + 0.248, 0.876, 0.245, 0.002])
ax_uline2.set_facecolor(GOLD); ax_uline2.axis("off")

divider(fig, 0.872)

# ── Upload tab content ────────────────────────────────────────────────────────
ax_ul_head = fig.add_axes([0.01, 0.845, 0.98, 0.024])
section_head(ax_ul_head, "Manual Excel / CSV Upload — Drag and Drop")

# File upload area
ax_drop = fig.add_axes([0.01, 0.770, 0.97, 0.070])
ax_drop.set_facecolor("#0F1629")
for sp in ax_drop.spines.values(): sp.set_edgecolor(GOLD); sp.set_linewidth(1.5); sp.set_linestyle("--")
ax_drop.set_xticks([]); ax_drop.set_yticks([])
ax_drop.text(0.5, 0.65, "📁  Drag and drop your file here, or click to browse",
             ha="center", va="center", color=MUTED, fontsize=10)
ax_drop.text(0.5, 0.30, "Supports:  .xlsx  ·  .csv  |  Single unified client intelligence file",
             ha="center", va="center", color=MUTED, fontsize=8)

# Validation results panel (simulated with example data)
ax_val_head = fig.add_axes([0.01, 0.742, 0.98, 0.024])
section_head(ax_val_head, "Validation Results — client_data_june_2026.xlsx")
vr_items = [
    ("Records Found", "312",  TEXT,  "from file"),
    ("Missing Columns","0",   GREEN, "all required present"),
    ("Duplicate Clients","2", AMBER, "2 duplicate IDs found"),
    ("Quality Score","97/100",GREEN, "Excellent"),
]
for i, (label, val, color, sub) in enumerate(vr_items):
    ax = fig.add_axes([0.01+i*0.248, 0.694, 0.234, 0.042])
    kpi(ax, val, label, color, sub)

# Warnings
ax_warn = fig.add_axes([0.01, 0.658, 0.97, 0.030])
ax_warn.set_facecolor("#1A1505")
for sp in ax_warn.spines.values(): sp.set_edgecolor(AMBER); sp.set_linewidth(0.8)
ax_warn.set_xticks([]); ax_warn.set_yticks([])
ax_warn.text(0.01, 0.55, "⚠️  2 duplicate client_id values found — they will be de-duplicated on activation",
             color=AMBER, fontsize=8, va="center")

# Preview table
ax_prev_head = fig.add_axes([0.01, 0.630, 0.98, 0.024])
section_head(ax_prev_head, "Data Preview — first 100 rows")

ax_prev = fig.add_axes([0.01, 0.495, 0.97, 0.130])
ax_prev.set_facecolor(CARD); ax_prev.axis("off")
preview_cols = ["client_id","client_name","country","book_type","lifetime_deposits",
                "current_equity","trading_volume_30d","last_login_date","vip_status"]
preview_x    = [0.00,0.06,0.16,0.24,0.31,0.41,0.51,0.63,0.78]
for j, (col, x) in enumerate(zip(preview_cols, preview_x)):
    ax_prev.text(x, 0.95, col, color=GOLD, fontsize=6.2, fontweight="bold", va="top")
ax_prev.axhline(0.88, color=BORDER, linewidth=0.8)
sample_preview = [
    ("CR10001","Mohammed Al-Sayed","UAE","B-Book","45,000","38,500","210,000","2026-06-10","False"),
    ("CR10002","Sarah Johnson","UK","A-Book","12,000","9,800","65,000","2026-06-12","True"),
    ("CR10003","David Chen","Singapore","M-Book","87,500","71,200","450,000","2026-05-28","True"),
    ("CR10004","Priya Sharma","India","B-Book","5,500","3,200","28,000","2026-06-01","False"),
    ("CR10005","Ahmed Hassan","Egypt","A-Book","22,000","18,700","125,000","2026-06-08","False"),
]
for ri, row in enumerate(sample_preview):
    y = 0.78 - ri * 0.18
    bg = "#0F1629" if ri%2==0 else CARD
    ax_prev.add_patch(mpatches.FancyBboxPatch(
        (0, y-0.08), 1, 0.18, boxstyle="square,pad=0", facecolor=bg, linewidth=0))
    for j, (val, x) in enumerate(zip(row, preview_x)):
        ax_prev.text(x, y, val, color=TEXT, fontsize=6.2, va="center")
ax_prev.set_xlim(0,1); ax_prev.set_ylim(0,1)

# Activate button area
ax_btn = fig.add_axes([0.01, 0.448, 0.38, 0.040])
ax_btn.set_facecolor(GOLD)
for sp in ax_btn.spines.values(): sp.set_edgecolor(GOLD)
ax_btn.set_xticks([]); ax_btn.set_yticks([])
ax_btn.text(0.5, 0.5, "✅  Activate This Dataset", ha="center", va="center",
            color=BG, fontsize=10, fontweight="bold")

ax_btnnote = fig.add_axes([0.41, 0.448, 0.57, 0.040])
ax_btnnote.set_facecolor("#141B2D")
for sp in ax_btnnote.spines.values(): sp.set_edgecolor(BORDER)
ax_btnnote.set_xticks([]); ax_btnnote.set_yticks([])
ax_btnnote.text(0.03, 0.5,
    "Activating will: map upload columns → internal schema  ·  compute all 6 scores  ·  refresh every dashboard",
    ha="left", va="center", color=MUTED, fontsize=7.5)

divider(fig, 0.443)

# ── Refresh schedule ──────────────────────────────────────────────────────────
ax_ref_head = fig.add_axes([0.01, 0.415, 0.98, 0.024])
section_head(ax_ref_head, "Refresh Schedule")

sch_options = ["Manual Only","Every Hour","Every 6 Hours","Daily (recommended for CRM/Holistics)"]
sch_cols    = [GOLD, MUTED, MUTED, MUTED]
for i, (opt, col) in enumerate(zip(sch_options, sch_cols)):
    ax_r = fig.add_axes([0.01 + i*0.248, 0.375, 0.235, 0.034])
    ax_r.set_facecolor(CARD if i>0 else "#1A1409")
    for sp in ax_r.spines.values(): sp.set_edgecolor(GOLD if i==0 else BORDER)
    ax_r.set_xticks([]); ax_r.set_yticks([])
    ax_r.add_patch(mpatches.Circle((0.06,0.5), 0.10, color=GOLD if i==0 else BORDER,
                                   transform=ax_r.transAxes))
    if i==0:
        ax_r.add_patch(mpatches.Circle((0.06,0.5), 0.055, color=BG,
                                       transform=ax_r.transAxes))
    ax_r.text(0.17, 0.5, opt, va="center", color=GOLD if i==0 else TEXT,
              fontsize=7.5, fontweight="bold" if i==0 else "normal")

divider(fig, 0.370)

# ── Data quality dashboard ────────────────────────────────────────────────────
ax_dq_head = fig.add_axes([0.01, 0.342, 0.98, 0.024])
section_head(ax_dq_head, "Data Quality Dashboard — current dataset")

# Quality score gauge
ax_gauge = fig.add_axes([0.01, 0.215, 0.14, 0.120])
ax_gauge.set_facecolor(CARD)
for sp in ax_gauge.spines.values(): sp.set_edgecolor(GREEN)
ax_gauge.set_xticks([]); ax_gauge.set_yticks([])
ax_gauge.text(0.5, 0.60, "100", ha="center", va="center",
              fontsize=28, fontweight="bold", color=GREEN, transform=ax_gauge.transAxes)
ax_gauge.text(0.5, 0.22, "Quality Score / 100", ha="center", fontsize=7,
              color=MUTED, transform=ax_gauge.transAxes)
ax_gauge.text(0.5, 0.08, "✓  Excellent", ha="center", fontsize=7.5,
              color=GREEN, transform=ax_gauge.transAxes)

# Quality metrics
qm_items = [
    ("Missing Columns",    "0",  GREEN, "all required present"),
    ("Duplicate Clients",  "0",  GREEN, "no duplicates"),
    ("Invalid Book Types", "0",  GREEN, "all valid"),
    ("Negative Values",    "0",  GREEN, "no invalid equity"),
    ("Null Values",        "0",  GREEN, "100% complete"),
]
for i, (label, val, color, sub) in enumerate(qm_items):
    ax = fig.add_axes([0.17 + i*0.165, 0.215, 0.155, 0.120])
    kpi(ax, val, label, color, sub)

ax_dq_info = fig.add_axes([0.01, 0.170, 0.97, 0.040])
ax_dq_info.set_facecolor("#0A130A")
for sp in ax_dq_info.spines.values(): sp.set_edgecolor(GREEN)
ax_dq_info.set_xticks([]); ax_dq_info.set_yticks([])
ax_dq_info.text(0.015, 0.5,
    "✅  No data quality issues detected. 300 clients loaded from Sample Data. "
    "All 6 scores computed successfully using the Business Rules Engine.",
    va="center", color=GREEN, fontsize=8)

# ── Architecture diagram ──────────────────────────────────────────────────────
ax_arch_head = fig.add_axes([0.01, 0.142, 0.98, 0.024])
section_head(ax_arch_head, "Long-Term Target Architecture — Holistics Daily Feed")

ax_arch = fig.add_axes([0.01, 0.030, 0.97, 0.108])
ax_arch.set_facecolor("#0F1629")
for sp in ax_arch.spines.values(): sp.set_edgecolor(BORDER)
ax_arch.set_xticks([]); ax_arch.set_yticks([])

steps = [
    ("Holistics\nDataset", PURPLE),
    ("data_mapper\nmap_upload()", BLUE),
    ("Unified\nInternal Schema", GOLD),
    ("rules_engine\nscore_*()", GREEN),
    ("All 6 Scores\n+ Actions", RED),
    ("All Dashboards\nAuto-Refresh", GOLD),
]
for i, (label, color) in enumerate(steps):
    x = 0.05 + i * 0.155
    rect = mpatches.FancyBboxPatch((x, 0.20), 0.12, 0.60,
        boxstyle="round,pad=0.02", linewidth=1.5, edgecolor=color,
        facecolor=CARD)
    ax_arch.add_patch(rect)
    ax_arch.text(x+0.060, 0.50, label, ha="center", va="center",
                 color=color, fontsize=6.8, fontweight="bold")
    if i < len(steps)-1:
        ax_arch.annotate("", xy=(x+0.135, 0.50), xytext=(x+0.120, 0.50),
                         arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.5))

ax_arch.text(0.5, 0.06, "Daily at 06:00 → Holistics exports unified client dataset → "
             "pipeline runs automatically → scores computed → dashboards refresh",
             ha="center", color=MUTED, fontsize=7)
ax_arch.set_xlim(0,1); ax_arch.set_ylim(0,1)

save("p3_page6_data_management.png")
print("  Page 6 done.")

# =============================================================================
print("\n" + "─"*60)
print("All 6 Phase 3 screenshots generated:")
for i, name in enumerate([
    "p3_page1_executive_dashboard.png",
    "p3_page2_client_list.png",
    "p3_page3_scoring_engine.png",
    "p3_page4_action_center.png",
    "p3_page5_settings.png",
    "p3_page6_data_management.png",
], 1):
    print(f"  Page {i}: /tmp/{name}")
