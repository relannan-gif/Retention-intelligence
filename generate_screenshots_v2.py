"""Phase 2 screenshots — dark gold executive theme, all 5 pages."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np, sys, os

sys.path.insert(0, "/home/user/Retention-intelligence")
os.chdir("/home/user/Retention-intelligence")

from data.sample_data import generate_clients
from utils.helpers import (DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS,
    DEFAULT_PROF_WEIGHTS, DEFAULT_REACT_WEIGHTS, DEFAULT_VIP_WEIGHTS,
    DEFAULT_THRESHOLDS, fmt_currency)
from utils.scoring import score_dataframe, generate_trend_snapshots

df = generate_clients(300)
scored = score_dataframe(df, DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS,
    DEFAULT_PROF_WEIGHTS, DEFAULT_REACT_WEIGHTS, DEFAULT_VIP_WEIGHTS, DEFAULT_THRESHOLDS)
trend = generate_trend_snapshots(scored)
t = DEFAULT_THRESHOLDS
hr = t["high_risk"]; hv = t["high_value"]; cp = t["critical_priority"]

# ── Dark gold theme constants ──────────────────────────────────────────────────
BG    = "#0A0E1A"
CARD  = "#141B2D"
BORDER= "#1E2D4A"
GOLD  = "#F0B429"
RED   = "#EF4444"
GREEN = "#10B981"
AMBER = "#F59E0B"
BLUE  = "#3B82F6"
PURPLE= "#8B5CF6"
TEXT  = "#E8E8E8"
MUTED = "#94A3B8"

def new_fig(h=20):
    fig = plt.figure(figsize=(18, h))
    fig.patch.set_facecolor(BG)
    return fig

def header_bar(fig, page_title):
    ax = fig.add_axes([0, 0.968, 1, 0.032])
    ax.set_facecolor("#0F1629")
    ax.axis("off")
    ax.axhline(0, color=GOLD, linewidth=1.5)
    ax.text(0.01, 0.5, "OneRoyal Client Intelligence Platform",
            color=GOLD, fontsize=10, fontweight="bold", va="center")
    ax.text(0.99, 0.5, page_title, color=TEXT, fontsize=9,
            va="center", ha="right")

def kpi_box(ax, value, label, color=GOLD, sub=""):
    ax.set_facecolor(CARD)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER); sp.set_linewidth(1.2)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.5, 0.60, str(value), ha="center", va="center",
            fontsize=20, fontweight="bold", color=color, transform=ax.transAxes)
    ax.text(0.5, 0.28, label, ha="center", va="center",
            fontsize=7.5, color=MUTED, transform=ax.transAxes)
    if sub:
        ax.text(0.5, 0.10, sub, ha="center", va="center",
                fontsize=6.5, color=MUTED, transform=ax.transAxes)

def section(fig, y, title):
    ax = fig.add_axes([0.01, y, 0.98, 0.018])
    ax.axis("off")
    ax.set_facecolor(BG)
    ax.text(0, 0.5, title, color=GOLD, fontsize=10.5, fontweight="bold", va="center")

def dark_ax(fig, rect):
    ax = fig.add_axes(rect)
    ax.set_facecolor(CARD)
    for sp in ax.spines.values():
        sp.set_edgecolor(BORDER); sp.set_linewidth(0.8)
    ax.tick_params(colors=TEXT, labelsize=7)
    ax.xaxis.label.set_color(TEXT); ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(GOLD)
    return ax

def dark_title(ax, title, fs=9):
    ax.set_title(title, color=GOLD, fontsize=fs, pad=4)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTIVE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
fig = new_fig(24)
header_bar(fig, "Executive Dashboard")

at_risk = scored["retention_risk_score"] >= hr
equity_at_risk = scored.loc[at_risk, "current_equity"].sum()
hv_at_risk = int((at_risk & (scored["commercial_value_score"] >= hv)).sum())
rev_at_risk = (scored.loc[at_risk, ["spread_commission_revenue","commission_revenue","swap_revenue"]]
               .sum().sum() * 12)
pnl_at_risk = scored.loc[at_risk, "net_company_pnl"].sum() * 12

kpi_data = [
    (300, "Total Clients", TEXT),
    (int(at_risk.sum()), "Clients At Risk", RED),
    (hv_at_risk, "High-Value At Risk", RED),
    (fmt_currency(equity_at_risk), "Equity At Risk", AMBER),
    (fmt_currency(rev_at_risk), "Annual Revenue\nAt Risk", AMBER),
    (fmt_currency(pnl_at_risk), "Annual Profit\nAt Risk", AMBER),
]
for i, (val, lbl, col) in enumerate(kpi_data):
    ax = fig.add_axes([0.01 + i*0.165, 0.905, 0.155, 0.055])
    kpi_box(ax, val, lbl, col)

section(fig, 0.887, "Risk & Health Overview")

# Risk histogram
ax1 = dark_ax(fig, [0.01, 0.755, 0.465, 0.125])
counts, bins = np.histogram(scored["retention_risk_score"], bins=25)
ax1.bar(bins[:-1], counts, width=(bins[1]-bins[0])*0.9, color=RED, alpha=0.85)
ax1.axvline(hr, color=GOLD, linestyle="--", linewidth=1.5,
            label=f"High Risk ({hr})")
dark_title(ax1, "Retention Risk Distribution")
ax1.set_facecolor("#0F1629"); ax1.legend(fontsize=7, facecolor=CARD, labelcolor=TEXT)

# Health bar
health_order = ["Critical","At Risk","Watchlist","Healthy","Excellent"]
health_colors_m = {"Critical":RED,"At Risk":"#F97316","Watchlist":AMBER,"Healthy":"#22C55E","Excellent":GREEN}
ax2 = dark_ax(fig, [0.53, 0.755, 0.465, 0.125])
vc = scored["health_label"].value_counts().reindex(health_order, fill_value=0)
bars = ax2.bar(vc.index, vc.values, color=[health_colors_m[h] for h in vc.index], alpha=0.9)
for bar, v in zip(bars, vc.values):
    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, str(v),
             ha="center", va="bottom", fontsize=8, color=TEXT, fontweight="bold")
dark_title(ax2, "Client Health Distribution")
ax2.set_facecolor("#0F1629")

section(fig, 0.737, "Profitability by Book Type")

# Profitability histogram
ax3 = dark_ax(fig, [0.01, 0.605, 0.465, 0.125])
counts2, bins2 = np.histogram(scored["profitability_score"], bins=25)
ax3.bar(bins2[:-1], counts2, width=(bins2[1]-bins2[0])*0.9, color=GREEN, alpha=0.85)
dark_title(ax3, "Profitability Score Distribution")
ax3.set_facecolor("#0F1629")

# Book type profitability bars
ax4 = dark_ax(fig, [0.53, 0.605, 0.465, 0.125])
book_prof = scored.groupby("book_type")["profitability_score"].mean()
book_colors = {"A-Book":BLUE,"B-Book":RED,"M-Book":PURPLE}
for bt, val in book_prof.items():
    ax4.bar(bt, val, color=book_colors[bt], alpha=0.9, width=0.5)
    ax4.text(["A-Book","B-Book","M-Book"].index(bt), val+0.3, f"{val:.1f}",
             ha="center", va="bottom", fontsize=9, color=TEXT, fontweight="bold")
dark_title(ax4, "Avg Profitability Score by Book Type")
ax4.set_facecolor("#0F1629")

section(fig, 0.587, "Geographic Revenue & Profitability At Risk")

ar_df = scored[at_risk].copy()
ar_df["annual_rev"] = (ar_df["spread_commission_revenue"]+ar_df["commission_revenue"]+ar_df["swap_revenue"])*12
ar_df["annual_pnl"] = ar_df["net_company_pnl"]*12

country_rev = ar_df.groupby("country")["annual_rev"].sum().sort_values(ascending=False).head(8)
ax5 = dark_ax(fig, [0.01, 0.438, 0.465, 0.14])
colors_bar = [RED if i < 2 else AMBER if i < 5 else BLUE for i in range(len(country_rev))]
ax5.barh(country_rev.index[::-1], country_rev.values[::-1], color=colors_bar[::-1], alpha=0.9)
dark_title(ax5, "Annual Revenue At Risk by Country (Top 8)")
ax5.set_facecolor("#0F1629")

country_pnl = ar_df.groupby("country")["annual_pnl"].sum().sort_values(ascending=False).head(8)
ax6 = dark_ax(fig, [0.53, 0.438, 0.465, 0.14])
ax6.barh(country_pnl.index[::-1], country_pnl.values[::-1], color=GREEN, alpha=0.85)
dark_title(ax6, "Annual Profitability At Risk by Country (Top 8)")
ax6.set_facecolor("#0F1629")

section(fig, 0.42, "Management Segmentation Matrix (3x3)")

rows_order = ["High Risk","Medium Risk","Low Risk"]
cols_order = ["High Value","Medium Value","Low Value"]
risk_map  = {"High Risk":"High","Medium Risk":"Medium","Low Risk":"Low"}
value_map = {"High Value":"High","Medium Value":"Medium","Low Value":"Low"}

ax7 = dark_ax(fig, [0.08, 0.275, 0.84, 0.135])
ax7.set_facecolor("#0F1629")
seg_labels_map = {
    ("High","High"):"Save\nImmediately",    ("High","Medium"):"Senior\nRetention",
    ("High","Low"):"Automated\nRetention",  ("Medium","High"):"Proactive\nNurture",
    ("Medium","Medium"):"Standard\nNurture",("Medium","Low"):"Light\nTouch",
    ("Low","High"):"VIP\nExpansion",        ("Low","Medium"):"Growth\nProgram",
    ("Low","Low"):"Monitor",
}
cell_colors = {
    ("High","High"):RED,  ("High","Medium"):"#F97316", ("High","Low"):AMBER,
    ("Medium","High"):BLUE,("Medium","Medium"):"#60A5FA",("Medium","Low"):MUTED,
    ("Low","High"):GREEN, ("Low","Medium"):"#34D399",  ("Low","Low"):"#4B5563",
}
for ci, col in enumerate(cols_order):
    for ri, row in enumerate(rows_order):
        rv = risk_map[row]; cv = value_map[col]
        mask = (scored["risk_level"]==rv) & (scored["value_level"]==cv)
        cnt = int(mask.sum())
        seg = scored.loc[mask,"segment"].mode()
        seg_name = seg.iloc[0] if len(seg)>0 else "Monitor"
        x, y = ci/3, 1-(ri+1)/3
        rect = FancyBboxPatch((x+0.005, y+0.01), 0.32, 0.30,
                               boxstyle="round,pad=0.01",
                               facecolor=cell_colors.get((rv,cv), CARD),
                               edgecolor=BORDER, alpha=0.4,
                               transform=ax7.transAxes)
        ax7.add_patch(rect)
        ax7.text(x+0.165, y+0.21, str(cnt), ha="center", va="center",
                 fontsize=16, fontweight="bold", color=TEXT, transform=ax7.transAxes)
        ax7.text(x+0.165, y+0.11, seg_name, ha="center", va="center",
                 fontsize=7, color=MUTED, transform=ax7.transAxes)
for ci, col in enumerate(cols_order):
    ax7.text((ci+0.5)/3, 1.06, col, ha="center", va="center",
             fontsize=9, fontweight="bold", color=GOLD, transform=ax7.transAxes)
for ri, row in enumerate(rows_order):
    ax7.text(-0.01, 1-(ri+0.5)/3, row, ha="right", va="center",
             fontsize=9, fontweight="bold", color=GOLD, transform=ax7.transAxes)
ax7.axis("off")
dark_title(ax7, "Client Segmentation Matrix")

section(fig, 0.258, "Platform Trend Analytics (6-Month)")
ax8 = dark_ax(fig, [0.01, 0.12, 0.465, 0.128])
ax8.plot(range(len(trend)), trend["avg_risk_score"], color=RED, marker="o", linewidth=2.5, markersize=5)
ax8.fill_between(range(len(trend)), trend["avg_risk_score"], alpha=0.15, color=RED)
ax8.set_xticks(range(len(trend))); ax8.set_xticklabels([str(d)[-5:] for d in trend["date"]], rotation=20, fontsize=6)
dark_title(ax8, "Avg Retention Risk Score — 6 Month Trend")
ax8.set_facecolor("#0F1629")

ax9 = dark_ax(fig, [0.53, 0.12, 0.465, 0.128])
ax9.plot(range(len(trend)), trend["avg_health_score"], color=GREEN, marker="o", linewidth=2.5, markersize=5)
ax9.fill_between(range(len(trend)), trend["avg_health_score"], alpha=0.15, color=GREEN)
ax9.set_xticks(range(len(trend))); ax9.set_xticklabels([str(d)[-5:] for d in trend["date"]], rotation=20, fontsize=6)
dark_title(ax9, "Avg Client Health Score — 6 Month Trend")
ax9.set_facecolor("#0F1629")

plt.savefig("/tmp/p2_page1_dashboard.png", dpi=130, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Page 1 saved.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CLIENT LIST
# ══════════════════════════════════════════════════════════════════════════════
fig = new_fig(18)
header_bar(fig, "Client List")

# Filter bar mockup
ax_f = fig.add_axes([0.01, 0.885, 0.98, 0.065])
ax_f.set_facecolor(CARD)
for sp in ax_f.spines.values(): sp.set_edgecolor(BORDER)
ax_f.set_xticks([]); ax_f.set_yticks([])
ax_f.text(0.008, 0.80, "Filters", color=GOLD, fontsize=9, fontweight="bold",
          transform=ax_f.transAxes, va="top")
filter_names = ["Search name/ID","Country: All","Account Manager: All",
                "Book Type: All","Risk Level: All","Health: All","Sort: Priority"]
for i, fn in enumerate(filter_names):
    x = 0.008 + i*0.141
    r = FancyBboxPatch((x, 0.12), 0.134, 0.50, boxstyle="round,pad=0.01",
                        facecolor="#0F1629", edgecolor=BORDER, transform=ax_f.transAxes)
    ax_f.add_patch(r)
    ax_f.text(x+0.067, 0.38, fn, fontsize=6.5, color=MUTED,
              transform=ax_f.transAxes, ha="center", va="center")

# Summary stats
ax_sm = fig.add_axes([0.01, 0.840, 0.98, 0.040])
ax_sm.axis("off"); ax_sm.set_facecolor(BG)
top = scored.sort_values("priority_score", ascending=False)
avg_risk = scored["retention_risk_score"].mean()
ax_sm.text(0, 0.5, f"300 clients  ·  Avg Risk: {avg_risk:.1f}  ·  "
           f"VIP Clients: {scored['vip_status'].sum()}  ·  Sort: Priority Score",
           color=MUTED, fontsize=8.5, va="center")

# Client table
display = top.head(20)
cols_show = ["client_id","client_name","country","book_type","account_status",
             "retention_risk_score","commercial_value_score","profitability_score",
             "client_health_score","priority_score","health_label","segment","recommended_action"]

ax_t = fig.add_axes([0.01, 0.04, 0.98, 0.795])
ax_t.axis("off")
col_labels = ["Client ID","Name","Country","Book","Status",
              "Risk","Value","Profit","Health","Priority","Health Label","Segment","Action"]
cell_data = []
for _, row in display.iterrows():
    cell_data.append([
        row["client_id"], row["client_name"][:15], row["country"],
        row["book_type"], row["account_status"],
        f"{row['retention_risk_score']:.0f}", f"{row['commercial_value_score']:.0f}",
        f"{row['profitability_score']:.0f}", f"{row['client_health_score']:.0f}",
        f"{row['priority_score']:.0f}", row["health_label"],
        row["segment"][:14], row["recommended_action"][:22],
    ])
tbl = ax_t.table(cellText=cell_data, colLabels=col_labels,
                 loc="upper center", cellLoc="left")
tbl.auto_set_font_size(False); tbl.set_fontsize(6.8); tbl.scale(1, 1.58)
for (r,c), cell in tbl.get_celld().items():
    cell.set_edgecolor(BORDER)
    if r == 0:
        cell.set_facecolor("#0F1629")
        cell.set_text_props(color=GOLD, fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#0F1629")
    else:
        cell.set_facecolor(CARD)
    if r > 0 and c == 5:
        v = float(cell_data[r-1][5])
        cell.set_facecolor("#3D0000" if v>=hr else "#2D2000" if v>=hr*0.5 else "#002D0E")
    if r > 0 and c == 10:
        hl = cell_data[r-1][10]
        fc = {"Critical":"#3D0000","At Risk":"#2D1000","Watchlist":"#2D2000",
              "Healthy":"#002D0E","Excellent":"#002D14"}.get(hl, CARD)
        cell.set_facecolor(fc)

plt.savefig("/tmp/p2_page2_client_list.png", dpi=130, bbox_inches="tight",
            facecolor=BG, edgecolor="none")
plt.close()
print("Page 2 saved.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════
fig = new_fig(22)
header_bar(fig, "Scoring Engine")

# Title
ax_title = fig.add_axes([0.01, 0.945, 0.98, 0.02])
ax_title.axis("off")
ax_title.text(0, 0.5, "Scoring Engine  —  6 book-aware scores · adjust weights · live scatter analysis",
              color=GOLD, fontsize=11, fontweight="bold", va="center")

# Score cards (6 scores explained)
score_info = [
    ("Retention Risk", RED,    "Withdrawal · Volume drop · Login · Deposits · Complaints · Equity erosion"),
    ("Commercial Value", BLUE, "Lifetime deposits · Net dep · Equity · Volume · Redeposits · Tenure · VIP"),
    ("Profitability",  GREEN,  "A-Book: spread+commission+swap\nB-Book: captured losses+spread\nM-Book: 0.6×losses+spread+comm+swap"),
    ("Reactivation",  AMBER,   "Login window (30-180d) · Historical deposits · Past volume · Redeposits"),
    ("VIP Upside",    PURPLE,  "Equity size · Net deposits · Volume trend · Redeposits · NOT yet VIP"),
    ("Client Health",  GOLD,   "(100-Risk)×50% + Value×30% + Profitability×20%\nExcellent/Healthy/Watchlist/At Risk/Critical"),
]
for i, (name, color, desc) in enumerate(score_info):
    x = 0.01 + (i % 3) * 0.33
    y = 0.85 if i < 3 else 0.73
    ax = fig.add_axes([x, y, 0.30, 0.085])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_edgecolor(color); sp.set_linewidth(1.5)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.03, 0.82, name, fontsize=9, fontweight="bold", color=color,
            transform=ax.transAxes, va="top")
    ax.text(0.03, 0.52, desc, fontsize=6.5, color=MUTED,
            transform=ax.transAxes, va="center")
    ax.text(0.92, 0.15, "0–100", fontsize=8, color=MUTED,
            transform=ax.transAxes, va="center", ha="center")
    ax.add_patch(FancyBboxPatch((0.82,0.05),0.15,0.20,boxstyle="round,pad=0.01",
                                facecolor=color,alpha=0.15,edgecolor=color,
                                transform=ax.transAxes))

# Risk weight sliders
ax_rw = fig.add_axes([0.01, 0.595, 0.47, 0.118])
ax_rw.set_facecolor(CARD)
for sp in ax_rw.spines.values(): sp.set_edgecolor(BORDER)
ax_rw.set_xticks([]); ax_rw.set_yticks([])
ax_rw.text(0.02, 0.92, "Retention Risk Weights", color=GOLD, fontsize=9,
           fontweight="bold", transform=ax_rw.transAxes, va="top")
rw_items = [("Withdrawal pressure",8),("Volume drop",7),("Login inactivity",6),
            ("Deposit staleness",5),("Complaints + tickets",9),
            ("Equity erosion",5),("Equity trend (30d)",6)]
for i,(lbl,val) in enumerate(rw_items):
    y = 0.78 - i*0.115
    ax_rw.text(0.02,y,lbl,fontsize=6.5,color=MUTED,transform=ax_rw.transAxes,va="center")
    r = FancyBboxPatch((0.40,y-0.038),0.50,0.072,boxstyle="round,pad=0.005",
                        facecolor="#0F1629",edgecolor=BORDER,transform=ax_rw.transAxes)
    ax_rw.add_patch(r)
    f = FancyBboxPatch((0.40,y-0.038),0.50*(val/10),0.072,boxstyle="round,pad=0.005",
                        facecolor=RED,edgecolor="none",alpha=0.80,transform=ax_rw.transAxes)
    ax_rw.add_patch(f)
    ax_rw.text(0.95,y,str(val),fontsize=7.5,fontweight="bold",color=TEXT,
               transform=ax_rw.transAxes,va="center",ha="center")

# Value weight sliders
ax_vw = fig.add_axes([0.52, 0.595, 0.47, 0.118])
ax_vw.set_facecolor(CARD)
for sp in ax_vw.spines.values(): sp.set_edgecolor(BORDER)
ax_vw.set_xticks([]); ax_vw.set_yticks([])
ax_vw.text(0.02, 0.92, "Commercial Value Weights", color=GOLD, fontsize=9,
           fontweight="bold", transform=ax_vw.transAxes, va="top")
vw_items = [("Lifetime deposits",8),("Net deposits",7),("Current equity",8),
            ("VIP status",9),("Trading volume",6),("Redeposit count",5),("Client tenure",4)]
for i,(lbl,val) in enumerate(vw_items):
    y = 0.78 - i*0.115
    ax_vw.text(0.02,y,lbl,fontsize=6.5,color=MUTED,transform=ax_vw.transAxes,va="center")
    r = FancyBboxPatch((0.40,y-0.038),0.50,0.072,boxstyle="round,pad=0.005",
                        facecolor="#0F1629",edgecolor=BORDER,transform=ax_vw.transAxes)
    ax_vw.add_patch(r)
    f = FancyBboxPatch((0.40,y-0.038),0.50*(val/10),0.072,boxstyle="round,pad=0.005",
                        facecolor=BLUE,edgecolor="none",alpha=0.80,transform=ax_vw.transAxes)
    ax_vw.add_patch(f)
    ax_vw.text(0.95,y,str(val),fontsize=7.5,fontweight="bold",color=TEXT,
               transform=ax_vw.transAxes,va="center",ha="center")

# Apply button
ax_btn = fig.add_axes([0.35, 0.553, 0.30, 0.033])
ax_btn.set_facecolor(GOLD); ax_btn.set_xticks([]); ax_btn.set_yticks([])
for sp in ax_btn.spines.values(): sp.set_edgecolor(GOLD)
ax_btn.text(0.5,0.5,"Apply Weights & Rescore All 300 Clients",
            fontsize=9,fontweight="bold",color=BG,transform=ax_btn.transAxes,
            va="center",ha="center")

section(fig, 0.534, "Score Distributions")

score_pairs = [
    ("retention_risk_score",RED),   ("commercial_value_score",BLUE),
    ("profitability_score",GREEN),  ("reactivation_score",AMBER),
    ("vip_upside_score",PURPLE),    ("client_health_score",GOLD),
]
for i,(col,color) in enumerate(score_pairs):
    x = 0.01 + (i%3)*0.33; y = 0.39 if i<3 else 0.22
    ax = dark_ax(fig,[x,y,0.30,0.135])
    cnts,bns = np.histogram(scored[col],bins=16)
    ax.bar(bns[:-1],cnts,width=(bns[1]-bns[0])*0.9,color=color,alpha=0.85)
    ax.set_facecolor("#0F1629")
    dark_title(ax,col.replace("_score","").replace("_"," ").title(),fs=8)

section(fig, 0.203, "Risk vs Profitability (by Book Type)")
ax_sc = dark_ax(fig,[0.01,0.05,0.98,0.145])
book_colors_m = {"A-Book":BLUE,"B-Book":RED,"M-Book":PURPLE}
samp = scored.sample(min(200,len(scored)),random_state=1)
for bt,bc in book_colors_m.items():
    sub = samp[samp["book_type"]==bt]
    ax_sc.scatter(sub["profitability_score"],sub["retention_risk_score"],
                  color=bc,alpha=0.65,s=20,label=bt)
ax_sc.axhline(hr,color=GOLD,linestyle="--",linewidth=1.2)
ax_sc.axvline(t.get("high_profitability",60),color=GREEN,linestyle="--",linewidth=1.2)
ax_sc.set_xlabel("Profitability Score",color=TEXT,fontsize=8)
ax_sc.set_ylabel("Retention Risk Score",color=TEXT,fontsize=8)
ax_sc.legend(facecolor=CARD,labelcolor=TEXT,fontsize=7)
ax_sc.set_facecolor("#0F1629")
dark_title(ax_sc,"Risk vs Profitability Scatter (top-right = protect immediately)")

plt.savefig("/tmp/p2_page3_scoring.png",dpi=130,bbox_inches="tight",facecolor=BG,edgecolor="none")
plt.close()
print("Page 3 saved.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — ACTION CENTER
# ══════════════════════════════════════════════════════════════════════════════
fig = new_fig(21)
header_bar(fig, "Action Center")

ax_t2 = fig.add_axes([0.01, 0.942, 0.98, 0.020])
ax_t2.axis("off")
ax_t2.text(0, 0.5, "Action Center  —  Profitability-first · Protect the most revenue today",
           color=GOLD, fontsize=11, fontweight="bold", va="center")

action_df = scored[scored["recommended_action"]!="Monitor Only"].sort_values(
    ["profitability_score","commercial_value_score","retention_risk_score"],
    ascending=[False,False,False])

kpi2 = [
    (len(action_df), "Clients Needing\nAction", RED),
    (f"{action_df['priority_score'].mean():.1f}", "Avg Priority\nScore", AMBER),
    (fmt_currency((action_df["spread_commission_revenue"]+
                   action_df["commission_revenue"]+
                   action_df["swap_revenue"]).sum()*12), "Annual Revenue\nat Stake", AMBER),
    (fmt_currency(action_df["net_company_pnl"].sum()*12), "Annual Profitability\nat Stake", GREEN),
]
for i,(val,lbl,col) in enumerate(kpi2):
    ax = fig.add_axes([0.01+i*0.248, 0.88, 0.235, 0.055])
    kpi_box(ax, val, lbl, col)

section(fig, 0.862, "Action & Owner Distribution")
ax_a1 = dark_ax(fig, [0.01, 0.725, 0.46, 0.130])
ac = action_df["recommended_action"].value_counts()
action_colors_m = {
    "URGENT: VIP Retention — Escalate to Management": "#FF0000",
    "Immediate Retention Call": RED,
    "Resolve Complaints + Retention Review": "#F97316",
    "Retention Call: Withdrawal Alert": AMBER,
    "Retention Follow-Up": "#FCD34D",
    "VIP Expansion Offer": GREEN,
    "VIP Upsell Opportunity": "#34D399",
    "Reactivation Campaign": BLUE,
    "Re-engagement: Trading Incentive": "#60A5FA",
    "Complaint Resolution": PURPLE,
    "Account Manager Follow-Up": MUTED,
}
bar_colors2 = [action_colors_m.get(a, MUTED) for a in ac.index[::-1]]
ax_a1.barh(range(len(ac)), ac.values[::-1], color=bar_colors2, alpha=0.9)
ax_a1.set_yticks(range(len(ac)))
ax_a1.set_yticklabels([a[:32] for a in ac.index[::-1]], fontsize=6.5, color=TEXT)
for i,v in enumerate(ac.values[::-1]):
    ax_a1.text(v+0.2,i,str(v),va="center",fontsize=7,color=TEXT,fontweight="bold")
dark_title(ax_a1, "Clients by Recommended Action")
ax_a1.set_facecolor("#0F1629")

ax_a2 = dark_ax(fig, [0.53, 0.725, 0.46, 0.130])
ow = action_df["recommended_owner"].value_counts()
owner_colors = [GOLD,RED,GREEN,BLUE,PURPLE]
wedges,texts,autotexts = ax_a2.pie(ow.values,labels=ow.index,colors=owner_colors[:len(ow)],
                                    autopct="%1.0f%%",startangle=90,pctdistance=0.75,
                                    textprops={"color":TEXT,"fontsize":7.5})
dark_title(ax_a2, "Distribution by Recommended Owner")

section(fig, 0.708, "Action List — Sorted: Profitability → Value → Risk")
top_action = action_df.head(18)
acols = ["client_id","client_name","book_type","profitability_score","retention_risk_score",
         "commercial_value_score","client_health_score","priority_score",
         "health_label","recommended_action","recommended_owner","action_reason"]
acol_labels = ["Client ID","Name","Book","Profit","Risk","Value","Health","Priority",
               "Health Lbl","Action","Owner","Reason"]
cell_data2 = []
for _, row in top_action.iterrows():
    cell_data2.append([
        row["client_id"], row["client_name"][:13], row["book_type"],
        f"{row['profitability_score']:.0f}", f"{row['retention_risk_score']:.0f}",
        f"{row['commercial_value_score']:.0f}", f"{row['client_health_score']:.0f}",
        f"{row['priority_score']:.0f}", row["health_label"],
        row["recommended_action"][:25], row["recommended_owner"],
        row["action_reason"][:28],
    ])

ax_t3 = fig.add_axes([0.01, 0.06, 0.98, 0.635])
ax_t3.axis("off")
tbl2 = ax_t3.table(cellText=cell_data2, colLabels=acol_labels,
                   loc="upper center", cellLoc="left")
tbl2.auto_set_font_size(False); tbl2.set_fontsize(6.5); tbl2.scale(1,1.60)
for (r,c), cell in tbl2.get_celld().items():
    cell.set_edgecolor(BORDER)
    if r == 0:
        cell.set_facecolor("#0F1629"); cell.set_text_props(color=GOLD, fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#0F1629")
    else:
        cell.set_facecolor(CARD)
    if r > 0:
        if c == 3:
            v = float(cell_data2[r-1][3])
            cell.set_facecolor("#002D0E" if v>=60 else "#1A1A00" if v>=30 else CARD)
        if c == 4:
            v = float(cell_data2[r-1][4])
            cell.set_facecolor("#3D0000" if v>=hr else "#2D1800" if v>=hr*0.5 else CARD)

plt.savefig("/tmp/p2_page4_action.png",dpi=130,bbox_inches="tight",facecolor=BG,edgecolor="none")
plt.close()
print("Page 4 saved.")

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
fig = new_fig(17)
header_bar(fig, "Settings")

ax_s = fig.add_axes([0.01, 0.945, 0.98, 0.018])
ax_s.axis("off")
ax_s.text(0, 0.5, "Settings  —  Configure scoring thresholds · save changes · preview impact",
          color=GOLD, fontsize=11, fontweight="bold", va="center")

section(fig, 0.895, "Scoring Thresholds")

thresh_defs = [
    ("High Risk threshold",          60, RED,    "Clients with risk score above this → 'High Risk'"),
    ("High Value threshold",         60, BLUE,   "Clients with value score above this → 'High Value'"),
    ("High Profitability threshold", 60, GREEN,  "Triggers higher-priority commercial actions"),
    ("Critical Priority threshold",  65, AMBER,  "Clients with priority score above this → 'Critical'"),
]
for i,(name,val,col,hint) in enumerate(thresh_defs):
    ax = fig.add_axes([0.01+i*0.248, 0.808, 0.235, 0.078])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_edgecolor(col); sp.set_linewidth(1.2)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.03, 0.88, name, fontsize=8, fontweight="bold", color=col,
            transform=ax.transAxes, va="top")
    ax.text(0.03, 0.45, hint, fontsize=6.5, color=MUTED, transform=ax.transAxes, va="center")
    r = FancyBboxPatch((0.03,0.12),0.82,0.18,boxstyle="round,pad=0.005",
                        facecolor="#0F1629",edgecolor=BORDER,transform=ax.transAxes)
    ax.add_patch(r)
    f = FancyBboxPatch((0.03,0.12),0.82*(val/100),0.18,boxstyle="round,pad=0.005",
                        facecolor=col,edgecolor="none",alpha=0.85,transform=ax.transAxes)
    ax.add_patch(f)
    ax.text(0.92,0.21,str(val),fontsize=9,fontweight="bold",color=TEXT,
            transform=ax.transAxes,va="center")

section(fig, 0.790, "Activity Thresholds")

act_thresh = [
    ("Login inactivity (days)",   30, "#30d",BLUE,   "Client marked inactive after this many days"),
    ("Large withdrawal (% equity)",30,"30%", AMBER,  "Withdrawal alert trigger threshold"),
    ("Dormant client (days)",     30, "30d", PURPLE, "Clients in Dormant vs Inactive boundary"),
]
for i,(name,val,dv,col,hint) in enumerate(act_thresh):
    ax = fig.add_axes([0.01+i*0.33, 0.705, 0.30, 0.078])
    ax.set_facecolor(CARD)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER); sp.set_linewidth(0.8)
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.03, 0.88, name, fontsize=8, fontweight="bold", color=col,
            transform=ax.transAxes, va="top")
    ax.text(0.03, 0.45, hint, fontsize=6.5, color=MUTED, transform=ax.transAxes, va="center")
    r = FancyBboxPatch((0.03,0.12),0.78,0.18,boxstyle="round,pad=0.005",
                        facecolor="#0F1629",edgecolor=BORDER,transform=ax.transAxes)
    ax.add_patch(r)
    f = FancyBboxPatch((0.03,0.12),0.78*0.33,0.18,boxstyle="round,pad=0.005",
                        facecolor=col,edgecolor="none",alpha=0.85,transform=ax.transAxes)
    ax.add_patch(f)
    ax.text(0.90,0.21,dv,fontsize=9,fontweight="bold",color=TEXT,transform=ax.transAxes,va="center")

# Buttons
ax_save = fig.add_axes([0.01, 0.644, 0.35, 0.045])
ax_save.set_facecolor(GOLD); ax_save.set_xticks([]); ax_save.set_yticks([])
for sp in ax_save.spines.values(): sp.set_edgecolor(GOLD)
ax_save.text(0.5,0.5,"Save Settings & Rescore All Clients",fontsize=9,
             fontweight="bold",color=BG,transform=ax_save.transAxes,va="center",ha="center")

ax_rst = fig.add_axes([0.38, 0.644, 0.22, 0.045])
ax_rst.set_facecolor(CARD); ax_rst.set_xticks([]); ax_rst.set_yticks([])
for sp in ax_rst.spines.values(): sp.set_edgecolor(BORDER)
ax_rst.text(0.5,0.5,"Reset All to Defaults",fontsize=8.5,color=MUTED,
            transform=ax_rst.transAxes,va="center",ha="center")

section(fig, 0.628, "Impact of Current Thresholds")

impact_data = [
    ("High Risk Clients", int((scored["retention_risk_score"]>=hr).sum()),
     f"{(scored['retention_risk_score']>=hr).mean():.0%} of portfolio", RED),
    ("High Value Clients", int((scored["commercial_value_score"]>=hv).sum()),
     f"{(scored['commercial_value_score']>=hv).mean():.0%} of portfolio", BLUE),
    ("High Profitability", int((scored["profitability_score"]>=60).sum()),
     f"{(scored['profitability_score']>=60).mean():.0%} of portfolio", GREEN),
    ("Critical Priority", int((scored["priority_score"]>=cp).sum()),
     f"{(scored['priority_score']>=cp).mean():.0%} of portfolio", AMBER),
    ("High-Value At Risk", int(((scored["retention_risk_score"]>=hr)&
                                 (scored["commercial_value_score"]>=hv)).sum()),
     "Immediate action needed", RED),
]
for i,(lbl,val,sub,col) in enumerate(impact_data):
    ax = fig.add_axes([0.01+i*0.198, 0.510, 0.186, 0.105])
    kpi_box(ax, val, lbl, col, sub)

ax_info = fig.add_axes([0.01, 0.460, 0.98, 0.040])
ax_info.set_facecolor("#0F1A2D"); ax_info.set_xticks([]); ax_info.set_yticks([])
for sp in ax_info.spines.values(): sp.set_edgecolor("#1E3A5F")
ax_info.text(0.01, 0.5, "Tip:  If High Risk count is too high, raise the threshold.  "
             "Focus your retention team on clients where intervention matters most.",
             fontsize=8.5, color="#93C5FD", transform=ax_info.transAxes, va="center")

section(fig, 0.443, "Current Configuration")

ax_cfg = fig.add_axes([0.01, 0.12, 0.45, 0.315])
ax_cfg.axis("off")
cfg_data = [
    ["High Risk threshold",      "60"],
    ["High Value threshold",     "60"],
    ["High Profitability",       "60"],
    ["Critical Priority",        "65"],
    ["Login inactivity",         "30 days"],
    ["Large withdrawal",         "30% of equity"],
    ["Dormant threshold",        "30 days"],
    ["Risk/Value/Profit blend",  "30% / 25% / 30% / 15%"],
]
tbl3 = ax_cfg.table(cellText=cfg_data, colLabels=["Setting","Value"],
                    loc="upper left", cellLoc="left")
tbl3.auto_set_font_size(False); tbl3.set_fontsize(8.5); tbl3.scale(1,1.75)
for (r,c), cell in tbl3.get_celld().items():
    cell.set_edgecolor(BORDER)
    if r == 0:
        cell.set_facecolor("#0F1629"); cell.set_text_props(color=GOLD, fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#0F1629")
    else:
        cell.set_facecolor(CARD)
    cell.set_text_props(color=TEXT if r>0 else GOLD)

ax_wt = fig.add_axes([0.52, 0.12, 0.47, 0.315])
ax_wt.axis("off")
wt_data = [
    ["Withdrawal pressure",     "8"],  ["Volume drop",          "7"],
    ["Login inactivity",        "6"],  ["Deposit staleness",    "5"],
    ["Complaints + tickets",    "9"],  ["Equity erosion",       "5"],
    ["Equity trend (30d)",      "6"],  ["VIP status (value wt)","9"],
]
tbl4 = ax_wt.table(cellText=wt_data, colLabels=["Weight Factor","Score (0-10)"],
                   loc="upper left", cellLoc="left")
tbl4.auto_set_font_size(False); tbl4.set_fontsize(8.5); tbl4.scale(1,1.75)
for (r,c), cell in tbl4.get_celld().items():
    cell.set_edgecolor(BORDER)
    if r == 0:
        cell.set_facecolor("#0F1629"); cell.set_text_props(color=GOLD, fontweight="bold")
    elif r % 2 == 0:
        cell.set_facecolor("#0F1629")
    else:
        cell.set_facecolor(CARD)
    cell.set_text_props(color=TEXT if r>0 else GOLD)

plt.savefig("/tmp/p2_page5_settings.png",dpi=130,bbox_inches="tight",facecolor=BG,edgecolor="none")
plt.close()
print("Page 5 saved.")
print("\nAll 5 Phase 2 screenshots generated successfully.")
