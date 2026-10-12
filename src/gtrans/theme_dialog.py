#!/usr/bin/python3
# -*- coding: utf-8 -*-

import flet as ft


class ThemeToggleDialog:
    # card_color, text_color, icon_color
    THEME_COLORS = {
        "system": ("#f8f9fa", "#000000", "#e8f0fe"),
        "light": ("#ffffff", "#000000", "#fce8e6"),
        "dark": ("#1f1f1f", "#ffffff", "#3c4043"),
    }

    def __init__(self, current_theme: str | None = None):
        self.current_theme = current_theme or "system"
        self.theme_changed_callback = None

    def set_theme_changed_callback(self, callback):
        self.theme_changed_callback = callback

    def create_theme_card(self, theme_name, icon, is_selected=False):
        """Create a beautiful theme selection card"""
        card_color, text_color, icon_color = self.THEME_COLORS[theme_name or "system"]

        border_color = "#1a73e8" if is_selected else "#dadce0"
        border_width = 2 if is_selected else 1

        # Create card content
        card_content = ft.Container(
            content=ft.Column(
                [
                    # Icon container
                    ft.Container(
                        content=ft.Icon(
                            icon,
                            size=32,
                            color=text_color,
                        ),
                        width=60,
                        height=60,
                        border_radius=12,
                        bgcolor=icon_color,
                        alignment=ft.Alignment.CENTER,
                    ),
                    # Theme label
                    ft.Container(height=8),
                    ft.Text(
                        theme_name.capitalize(),
                        size=14,
                        weight=ft.FontWeight.W_500,
                        color=text_color,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    # Selection indicator
                    ft.Container(height=4),
                    ft.Container(
                        width=20,
                        height=20,
                        border_radius=10,
                        border=ft.Border.all(2, border_color),
                        bgcolor="#1a73e8" if is_selected else "transparent",
                        alignment=ft.Alignment.CENTER,
                        content=(
                            ft.Icon(
                                ft.Icons.CHECK,
                                size=12,
                                color="#ffffff" if is_selected else "transparent",
                            )
                            if is_selected
                            else None
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            width=120,
            height=140,
            border_radius=16,
            border=ft.Border.all(border_width, border_color),
            bgcolor=card_color,
            padding=16,
            on_click=lambda e, theme=theme_name: self._on_theme_selected(e, theme),
            data=theme_name,
        )
        return card_content

    def _on_theme_selected(self, e, theme_name):
        """Handle theme selection"""
        self.current_theme = theme_name
        if self.theme_changed_callback:
            self.theme_changed_callback(theme_name)

        # e.page.client_storage.set("gt.theme_mode", theme_name)
        # e.page.close(self.dialog)

    def open_dialog(self, page: ft.Page):
        """Open the theme selection dialog"""
        # Create theme cards
        self.current_theme = page.theme_mode.value
        system_card = self.create_theme_card(
            "system", ft.Icons.BRIGHTNESS_AUTO, self.current_theme == "system"
        )
        light_card = self.create_theme_card(
            "light", ft.Icons.LIGHT_MODE, self.current_theme == "light"
        )
        dark_card = self.create_theme_card(
            "dark", ft.Icons.DARK_MODE, self.current_theme == "dark"
        )

        # Create dialog content
        content = ft.Column(
            [
                # Header
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Choose Theme",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.ON_SURFACE,
                            ),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                on_click=lambda _: page.pop_dialog(),
                                icon_color=ft.Colors.ON_SURFACE,
                                hover_color="#FF0000",
                            ),
                        ]
                    ),
                    padding=ft.Padding.only(bottom=20),
                ),
                # Theme cards
                ft.Container(
                    content=ft.Row(
                        [system_card, light_card, dark_card],
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        spacing=10,
                    ),
                    padding=ft.Padding.symmetric(vertical=10),
                ),
                # Description
                ft.Container(
                    content=ft.Text(
                        self._get_theme_description(),
                        size=12,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    padding=ft.Padding.only(top=20),
                ),
            ],
            width=400,
            tight=True,
        )

        # Create dialog
        self.dialog = ft.AlertDialog(
            content=content,
            shape=ft.RoundedRectangleBorder(radius=20),
            content_padding=24,
        )

        page.show_dialog(self.dialog)

    def _get_theme_description(self):
        """Get description for current theme selection"""
        descriptions = {
            "system": "Uses your system's theme setting",
            "light": "Always use light theme",
            "dark": "Always use dark theme",
        }
        return descriptions.get(self.current_theme, "Select your preferred theme")
