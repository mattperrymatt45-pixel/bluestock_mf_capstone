"""
Shared styling helpers for the Bluestock MF dashboard mockup pages.
Mimics a Power BI page layout (dark header, KPI cards, chart panels,
slicer pills) using matplotlib, since Power BI Desktop itself isn't
available in this environment.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.font_manager as fm

NAVY = "#1F3864"
NAVY_DARK = "#152847"
ACCENT_GOLD = "#D4A017"
GREY_BG = "#F4F5F7"
GREY_TEXT = "#595959"
GREEN = "#2E7D32"
RED = "#C0392B"
CARD_BORDER = "#E0E2E6"
PALETTE = ["#1F3864", "#4472C4", "#8FAADC", "#D4A017", "#2E7D32", "#C0392B", "#7B5EA7", "#2E9E9E"]

PAGE_W, PAGE_H = 16, 9


def new_page(title, page_label):
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=150)
    fig.patch.set_facecolor("white")

    # Header bar
    header = fig.add_axes([0, 0.93, 1, 0.07])
    header.set_xlim(0, 1)
    header.set_ylim(0, 1)
    header.axis("off")
    header.add_patch(mpatches.Rectangle((0, 0), 1, 1, facecolor=NAVY, zorder=0))
    header.text(0.012, 0.52, "BLUESTOCK FINTECH", color="white", fontsize=13, fontweight="bold",
                va="center", ha="left", family="sans-serif")
    header.text(0.012, 0.15, "Mutual Fund Analytics Dashboard", color="#B7C3DC", fontsize=8.5,
                va="center", ha="left")
    header.text(0.5, 0.5, title, color="white", fontsize=15, fontweight="bold", va="center", ha="center")
    header.text(0.988, 0.5, page_label, color="#B7C3DC", fontsize=9, va="center", ha="right")
    # small logo mark
    header.add_patch(mpatches.Circle((0.975, 0.5), 0.012, transform=header.transAxes, clip_on=False, visible=False))

    fig.text(0.99, 0.008, "Bluestock Fintech | Educational project - not investment advice", fontsize=6.5,
              color="#9AA0A6", ha="right")
    return fig


def panel(fig, rect, title=None):
    """Add a card-style panel axes at rect=[left,bottom,width,height] in figure coords."""
    ax = fig.add_axes(rect)
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(CARD_BORDER)
        spine.set_linewidth(1.1)
    if title:
        ax.set_title(title, fontsize=10.5, fontweight="bold", color=NAVY, loc="left", pad=8)
    return ax


def kpi_card(fig, rect, value, label, color=NAVY, delta=None):
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.02, 0.06), 0.96, 0.88, boxstyle="round,pad=0.02,rounding_size=0.04",
                                 facecolor="white", edgecolor=CARD_BORDER, linewidth=1.1, transform=ax.transAxes))
    ax.add_patch(mpatches.Rectangle((0.02, 0.88), 0.96, 0.06, facecolor=color, transform=ax.transAxes, zorder=3))
    ax.text(0.5, 0.52, value, fontsize=22, fontweight="bold", color=color, ha="center", va="center")
    ax.text(0.5, 0.22, label, fontsize=9.5, color=GREY_TEXT, ha="center", va="center")
    if delta:
        dcolor = GREEN if delta.startswith("+") else RED
        ax.text(0.5, 0.36, delta, fontsize=8.5, color=dcolor, ha="center", va="center", fontweight="bold")
    return ax


def slicer_strip(fig, rect, labels):
    ax = fig.add_axes(rect)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    n = len(labels)
    gap = 0.02
    w = (1 - gap * (n - 1)) / n
    for i, label in enumerate(labels):
        x0 = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x0, 0.1), w, 0.8, boxstyle="round,pad=0.01,rounding_size=0.35",
                                     facecolor=GREY_BG, edgecolor=CARD_BORDER, linewidth=1, transform=ax.transAxes))
        ax.text(x0 + w * 0.42, 0.5, label, fontsize=8.5, color=NAVY_DARK, ha="center", va="center", fontweight="bold")
        ax.text(x0 + w * 0.92, 0.5, "\u25be", fontsize=9, color=GREY_TEXT, ha="center", va="center")
    return ax


def footer_note(fig, text):
    fig.text(0.01, 0.008, text, fontsize=6.5, color="#9AA0A6", ha="left")
