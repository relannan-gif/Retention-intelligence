# config/theme.py — Centralized theme definitions for OneRoyal Client Intelligence Platform

THEMES = {
    "dark": {
        "name":         "OneRoyal Dark",
        "bg":           "#0A0E1A",
        "card":         "#141B2D",
        "secondary_bg": "#0F1629",
        "sidebar_bg":   "#0F1629",
        "plot_bg":      "#0F1629",
        "text":         "#E8E8E8",
        "muted":        "#94A3B8",
        "border":       "#1E2D4A",
        "input_bg":     "#141B2D",
    },
    "light": {
        "name":         "OneRoyal Light",
        "bg":           "#F4F6FC",
        "card":         "#FFFFFF",
        "secondary_bg": "#EEF1F8",
        "sidebar_bg":   "#E4EAF5",
        "plot_bg":      "#F0F4FA",
        "text":         "#1A1F36",
        "muted":        "#5B6380",
        "border":       "#D1D9E6",
        "input_bg":     "#FFFFFF",
    },
}

# Semantic colors — identical across both themes
GOLD   = "#F0B429"
RED    = "#EF4444"
GREEN  = "#10B981"
AMBER  = "#F59E0B"
BLUE   = "#3B82F6"
PURPLE = "#8B5CF6"

DEFAULT_THEME = "dark"
