#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import os
import re
import time
from typing import Callable, Optional

import flet as ft

# NOTE: move this logic to other file
from googletrans import LANGUAGES, Translator
from googletrans.client import Translated
from googletrans.constants import DEFAULT_CLIENT_SERVICE_URLS, DEFAULT_USER_AGENT

from .settings_dialog import SettingsDialog
from .theme_dialog import ThemeToggleDialog


class AsyncTranslationDebouncer:
    """
    Async version for better integration with Flet's async architecture.
    """

    def __init__(self, delay_seconds: float = 1.0):
        self.delay = delay_seconds
        self.task: Optional[asyncio.Task] = None
        # self.last_text = ""
        self.last_change_time = 0

    async def on_text_change(self, translate_callback: Callable):
        """
        Call this whenever text changes.

        Args:
            text: Current text
            translate_callback: Async function that takes text and returns translation
        """
        # self.last_text = text
        self.last_change_time = time.time()

        # Cancel previous task if running
        if self.task and not self.task.done():
            self.task.cancel()

        # Schedule new translation task
        self.task = asyncio.create_task(self._schedule_translation(translate_callback))

    async def _schedule_translation(self, translate_callback: Callable):
        """Wait for delay, then translate if no new changes"""
        try:
            await asyncio.sleep(self.delay)

            # Only translate if no new changes occurred during wait
            if time.time() - self.last_change_time >= self.delay:
                await translate_callback()
        except asyncio.CancelledError:
            pass  # New keystroke occurred, translation cancelled


class GoogleTranslateApp:
    def __init__(self):
        self.debouncer = AsyncTranslationDebouncer(delay_seconds=1.5)
        self.translator = Translator()
        self.source_lang = "auto"
        self.target_lang = "en"
        self.settings_dialog = None

    async def main(self, page: ft.Page):
        self.page = page

        self.sp = ft.SharedPreferences()
        page.services.append(self.sp)

        # Page setup with Theme
        page.title = "GTrans"
        # page.theme_mode = ft.ThemeMode.SYSTEM
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary="#1a73e8",
                on_primary="#ffffff",
                surface="#ffffff",
                on_surface="#202124",
                # background="#ffffff",
                # on_background="#202124",
                outline="#dadce0",
                surface_container="#f8f9fa",
            )
        )
        page.dark_theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary="#8ab4f8",
                on_primary="#000000",
                surface="#1f1f1f",
                on_surface="#e8eaed",
                # background="#1f1f1f",
                # on_background="#e8eaed",
                outline="#5f6368",
                surface_container="#2d2d2d",
            )
        )
        page.padding = 0
        page.bgcolor = ft.Colors.SURFACE

        # Set page dimensions for better mobile experience
        page.window.width = 900
        page.window.height = 550
        await page.window.center()

        self.theme_toggle_dialog = ThemeToggleDialog(
            current_theme=page.theme_mode.value
        )
        self.theme_toggle_dialog.set_theme_changed_callback(self.toggle_theme)

        # Initialize UI components
        self.source_text = ft.TextField(
            multiline=True,
            min_lines=8,
            max_lines=12,
            border_color="transparent",
            bgcolor=ft.Colors.SURFACE,
            content_padding=12,
            text_size=16,
            hint_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE)
            ),
            on_change=self.on_source_text_change,
            expand=True,
            cursor_color=ft.Colors.PRIMARY,
            color=ft.Colors.ON_SURFACE,
            text_style=ft.TextStyle(font_family="Google Sans"),
            rtl=self.source_lang == "ar",
            hint_text=self.get_source_hint_text(),
        )

        self.target_text = ft.TextField(
            multiline=True,
            min_lines=8,
            max_lines=12,
            read_only=True,
            border_color="transparent",
            bgcolor=ft.Colors.SURFACE,
            content_padding=12,
            text_size=16,
            hint_text="...",
            hint_style=ft.TextStyle(
                color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE)
            ),
            expand=True,
            color=ft.Colors.ON_SURFACE,
            text_style=ft.TextStyle(font_family="Google Sans"),
            rtl=self.target_lang == "ar",
        )

        # Theme switch button
        self.theme_button = ft.FilledButton(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PALETTE),
                    ft.Text("Choose Theme", size=16),
                ]
            ),
            on_click=lambda e: self.theme_toggle_dialog.open_dialog(page),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=20,
            ),
        )

        # Settings button
        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            on_click=self._open_settings,
            tooltip="Settings",
        )

        # Language dropdowns with better styling
        self.source_dropdown = ft.Dropdown(
            value=self.source_lang,
            options=[
                ft.dropdown.Option("auto", "Auto Detect"),
                *[ft.dropdown.Option(k, v.capitalize()) for k, v in LANGUAGES.items()],
            ],
            width=160,
            content_padding=12,
            text_size=14,
            on_select=self.on_language_change,
            bgcolor=ft.Colors.SURFACE,
            color=ft.Colors.ON_SURFACE,
            border_color=ft.Colors.OUTLINE,
            border_radius=8,
            text_style=ft.TextStyle(font_family="Google Sans"),
            enable_search=True,
        )

        self.target_dropdown = ft.Dropdown(
            value=self.target_lang,
            options=[
                ft.dropdown.Option(k, v.capitalize()) for k, v in LANGUAGES.items()
            ],
            width=160,
            content_padding=12,
            text_size=14,
            on_select=self.on_language_change,
            bgcolor=ft.Colors.SURFACE,
            color=ft.Colors.ON_SURFACE,
            border_color=ft.Colors.OUTLINE,
            border_radius=8,
            text_style=ft.TextStyle(font_family="Google Sans"),
            enable_search=True,
        )

        # Action buttons with better styling
        self.copy_button = ft.IconButton(
            icon=ft.Icons.CONTENT_COPY_OUTLINED,
            icon_color=ft.Colors.PRIMARY,
            tooltip="Copy translation",
            on_click=self.copy_translation,
            style=ft.ButtonStyle(shape=ft.CircleBorder()),
            icon_size=20,
        )

        self.clear_button = ft.IconButton(
            icon=ft.Icons.CLEAR_ALL_OUTLINED,
            icon_color=ft.Colors.PRIMARY,
            tooltip="Clear translation",
            on_click=lambda e: self.clear_translation(),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(color=ft.Colors.OUTLINE, width=1),
            ),
        )

        self.menu_button = ft.IconButton(
            icon=ft.Icons.FUNCTIONS,
            icon_color=ft.Colors.PRIMARY,
            tooltip="Clear underscores/dots",
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(color=ft.Colors.OUTLINE, width=1),
            ),
            on_click=self.clear_untranslate_text,
            # items=[
            #     ft.PopupMenuItem(
            #         text="Clear Underscores",
            #         on_click=lambda e: self.text_functions.clear_underscore(self.source_text)
            #     ),
            #     ft.PopupMenuItem(
            #         text="Clear Dashs",
            #         on_click=lambda e: self.text_functions.clear_dashs(self.source_text)
            #     ),
            #     ft.PopupMenuItem(
            #         text="Clear Dots",
            #         on_click=lambda e: self.text_functions.clear_dots(self.source_text)
            #     )
            # ]
        )

        self.swap_button = ft.IconButton(
            icon=ft.Icons.SWAP_HORIZ_ROUNDED,
            icon_color=ft.Colors.PRIMARY,
            tooltip="Swap Languages",
            on_click=self.on_swap_languages,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                side=ft.BorderSide(color=ft.Colors.OUTLINE, width=1),
            ),
            disabled=self.source_lang == "auto",
        )

        # Loading indicator
        self.loading_indicator = ft.ProgressRing(
            visible=False, width=24, height=24, color=ft.Colors.PRIMARY, stroke_width=2
        )

        # Character count
        self.char_count = ft.Text(
            "0/5000", size=12, color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE)
        )

        # Feature buttons
        self.mic_button = ft.IconButton(
            icon=ft.Icons.MIC_NONE_OUTLINED,
            icon_color=ft.Colors.ON_SURFACE,
            icon_size=20,
            tooltip="Voice input",
            style=ft.ButtonStyle(shape=ft.CircleBorder()),
            disabled=True,
        )

        self.camera_button = ft.IconButton(
            icon=ft.Icons.CAMERA_ALT_OUTLINED,
            icon_color=ft.Colors.ON_SURFACE,
            icon_size=20,
            tooltip="Camera translation",
            style=ft.ButtonStyle(shape=ft.CircleBorder()),
            disabled=True,
        )

        self.volume_button = ft.IconButton(
            icon=ft.Icons.VOLUME_UP_OUTLINED,
            icon_color=ft.Colors.ON_SURFACE,
            icon_size=20,
            on_click=self.speak_translation,
            tooltip="Listen to translation",
            style=ft.ButtonStyle(shape=ft.CircleBorder()),
            disabled=True,
        )

        # Build the UI layout
        await self.build_ui(page)

    def get_source_hint_text(self) -> str:
        return "Typing..." if self.source_lang != "ar" else "أكتب..."

    async def clear_untranslate_text(self, e=None, *, replace: str = " ") -> None:
        text: str = self.source_text.value
        self.source_text.value = re.sub(r"(-|_|\.)", replace, text)
        self.source_text.update()
        try:
            await self.on_source_text_change()
        except Exception:
            pass

    def clear_translation(self):
        self.source_text.value = ""
        self.target_text.value = ""
        self.char_count.value = "0/5000"

        self.source_text.update()
        self.target_text.update()
        self.char_count.update()

    def toggle_theme(self, theme_name):
        self.page.theme_mode = ft.ThemeMode(theme_name)
        self.page.update()

        # Update the theme button text
        self.theme_button.content = f"Current Theme: {theme_name.title()}"
        self.theme_button.update()

    async def _open_settings(self, e):
        if not self.settings_dialog:
            self.settings_dialog = SettingsDialog(
                self.page, self, self.load_app_settings
            )
        await self.settings_dialog.open_dialog()

    async def load_app_settings(self):
        """Load app settings from client_storage and apply to UI controls"""
        try:

            # Load settings from client_storage
            proxy = await self.sp.get("gt.proxy")
            proxy_default = await self.sp.get("gt.proxy_default")
            width = await self.sp.get("gt.window_width")
            height = await self.sp.get("gt.window_height")
            default_source_lang = await self.sp.get("gt.default_source_lang")
            default_target_lang = await self.sp.get("gt.default_target_lang")
            request_timeout = await self.sp.get("gt.request_timeout")

            # Apply window dimensions if they exist
            if width and height:
                # Set window dimensions
                self.page.window.width = int(width)
                self.page.window.height = int(height)

                # Center the window
                await self.page.window.center()

                # Update window
                # self.page.update()

            # Apply default source/target language if it exists
            if default_source_lang:
                self.source_lang = default_source_lang
                # Update source dropdown if it exists
                if hasattr(self, "source_dropdown") and self.source_dropdown:
                    self.source_dropdown.value = default_source_lang
                    self.source_text.rtl = default_source_lang == "ar"

            if default_target_lang:
                self.target_lang = default_target_lang
                # Update target dropdown if it exists
                if hasattr(self, "target_dropdown") and self.target_dropdown:
                    self.target_dropdown.value = default_target_lang
                    self.target_text.rtl = default_target_lang == "ar"

            self.swap_button.disabled = self.source_lang == "auto"

            # Get user agent
            user_agent = str(
                await self.sp.get("gt.user_agent")
                or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

            # Parse service URLs if available
            service_urls = str(await self.sp.get("gt.service_urls"))
            urls_list: list[str] = []
            if service_urls:
                urls_list = [
                    url.strip() for url in service_urls.split(",") if url.strip()
                ]

            # Recreate translator with new settings
            self.translator = Translator(
                proxy=os.getenv("http_proxy") if proxy_default else proxy or None,
                service_urls=urls_list if urls_list else DEFAULT_CLIENT_SERVICE_URLS,
                user_agent=user_agent if user_agent else DEFAULT_USER_AGENT,
                timeout=request_timeout or 30,
            )

            if hasattr(self, "page") and self.page is not None:
                self.page.update()

            print("Settings loaded and applied successfully")

            return True

        except Exception as e:
            print(f"Error loading app settings: {e}")
            return False

    async def build_ui(self, page):
        await self.load_app_settings()
        page.theme_mode = ft.ThemeMode(await self.sp.get("gt.theme_mode") or "system")

        def new_span(text: str, color: str) -> ft.TextSpan:
            return ft.TextSpan(
                text=text,
                style=ft.TextStyle(size=28, weight=ft.FontWeight.BOLD, color=color),
            )

        # Header (Google-style with better design)
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        spans=[
                            new_span("G", "#4285f4"),
                            new_span(" o", "#ea4335"),
                            new_span(" o", "#fbbc04"),
                            new_span(" g", "#4285f4"),
                            new_span(" l", "#34a853"),
                            new_span(" e", "#ea4335"),
                            ft.TextSpan(
                                text=" Translate",
                                style=ft.TextStyle(
                                    size=24,
                                    color=ft.Colors.ON_SURFACE,
                                    weight=ft.FontWeight.NORMAL,
                                ),
                            ),
                        ]
                    ),
                    ft.Container(expand=True),  # Spacer
                    self.theme_button,
                    self.settings_button,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.only(
                bottom=ft.BorderSide(color=ft.Colors.OUTLINE, width=1)
            ),
        )

        # Language selection row with better design
        lang_row = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "From",
                                size=12,
                                color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE),
                            ),
                            self.source_dropdown,
                        ]
                    ),
                    ft.Container(
                        content=ft.Column(
                            [self.swap_button],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding.only(top=20),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "To",
                                size=12,
                                color=ft.Colors.with_opacity(0.7, ft.Colors.ON_SURFACE),
                            ),
                            self.target_dropdown,
                        ]
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=30,
            ),
            padding=ft.Padding.symmetric(vertical=20, horizontal=24),
            bgcolor=ft.Colors.SURFACE,
        )

        # Translation area with enhanced design
        translation_area = ft.Container(
            content=ft.Row(
                [
                    # Source column
                    ft.Column(
                        expand=True,
                        controls=[
                            ft.Container(
                                content=ft.Stack(
                                    controls=[
                                        ft.Column(
                                            [
                                                ft.Text(
                                                    "Source Text",
                                                    size=14,
                                                    color=ft.Colors.ON_SURFACE,
                                                    weight=ft.FontWeight.W_500,
                                                ),
                                                self.source_text,
                                            ]
                                        ),
                                        ft.Row(
                                            controls=[
                                                self.clear_button,
                                                self.menu_button,
                                            ],
                                            alignment=ft.MainAxisAlignment.END,
                                        ),
                                    ]
                                ),
                                border_radius=12,
                                border=ft.Border.all(1.5, ft.Colors.OUTLINE),
                                padding=16,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        self.char_count,
                                        ft.Container(expand=True),
                                        self.mic_button,
                                        self.camera_button,
                                    ]
                                ),
                                padding=ft.Padding.only(top=12, left=8, right=8),
                            ),
                        ],
                        spacing=0,
                    ),
                    # Spacer
                    ft.Container(width=20),
                    # Target column
                    ft.Column(
                        expand=True,
                        controls=[
                            ft.Container(
                                content=ft.Stack(
                                    [
                                        ft.Column(
                                            [
                                                ft.Text(
                                                    "Translation",
                                                    size=14,
                                                    color=ft.Colors.ON_SURFACE,
                                                    weight=ft.FontWeight.W_500,
                                                ),
                                                self.target_text,
                                            ]
                                        ),
                                        ft.Container(
                                            content=self.loading_indicator,
                                            right=16,
                                        ),
                                    ]
                                ),
                                border_radius=12,
                                border=ft.Border.all(1.5, ft.Colors.OUTLINE),
                                padding=16,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Container(expand=True),
                                        self.copy_button,
                                        self.volume_button,
                                    ]
                                ),
                                padding=ft.Padding.only(top=12, left=8, right=8),
                            ),
                        ],
                        spacing=0,
                    ),
                ][::-1],
                spacing=0,
            ),
            padding=24,
            expand=True,
            bgcolor=ft.Colors.SURFACE,
        )

        # Footer with attribution
        footer = ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        spans=[
                            ft.TextSpan(text="Made with "),
                            ft.TextSpan("♥️ ", style=ft.TextStyle(color="#FF0000")),
                            ft.TextSpan("by "),
                            ft.TextSpan(
                                "@osamalzabidi", url="https://github.com/osamalzabidi"
                            ),
                        ],
                        size=12,
                        color=ft.Colors.with_opacity(0.6, ft.Colors.ON_SURFACE),
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=16,
            bgcolor=ft.Colors.SURFACE,
            border=ft.Border.only(top=ft.BorderSide(color=ft.Colors.OUTLINE, width=1)),
        )

        # Main content
        main_content = ft.Column(
            [
                header,
                lang_row,
                translation_area,
                footer,
            ],
            expand=True,
            spacing=0,
        )

        # Set page content
        page.add(main_content)

    async def on_source_text_change(self, e=None):
        # Update character count
        text = self.source_text.value or ""
        self.char_count.value = f"{len(text)}/5000"
        self.char_count.update()

        # Auto-translate if text is not empty
        if not text.strip():
            self.target_text.value = ""
            self.target_text.update()
            return

        # await self.translate_text()

        # Debounce translation
        await self.debouncer.on_text_change(self.translate_text)

    async def on_language_change(self, e):
        self.source_lang = self.source_dropdown.value
        self.target_lang = self.target_dropdown.value

        # Update text direction
        self.source_text.rtl = self.source_lang == "ar"
        self.target_text.rtl = self.target_lang == "ar"
        self.swap_button.disabled = self.source_lang == "auto"
        self.source_text.hint_text = self.get_source_hint_text()

        self.source_text.update()
        self.target_text.update()
        self.swap_button.update()

        # Re-translate if there's text
        if self.source_text.value and self.source_text.value.strip():
            await self.translate_text()

    async def translate_text(self):
        text = self.source_text.value.strip()
        if not text:
            return

        # Show loading
        self.loading_indicator.visible = True
        self.loading_indicator.update()

        try:
            # Perform translation using asyncio executor to avoid blocking
            translation: Translated = await self.translator.translate(
                text, self.target_lang, self.source_lang
            )

            self.target_text.value = translation.text
            self.target_text.update()

        except Exception as e:
            self.target_text.value = f"Translation error: {str(e)}"
            self.target_text.update()

        finally:
            # Hide loading
            self.loading_indicator.visible = False
            self.loading_indicator.update()

    async def on_swap_languages(self, e):
        # Swap language values
        current_source = self.source_lang
        current_target = self.target_lang

        self.source_lang = current_target
        self.target_lang = current_source

        # Update dropdowns
        self.source_dropdown.value = self.source_lang
        self.target_dropdown.value = self.target_lang

        # Update text direction
        self.source_text.rtl = self.source_lang == "ar"
        self.target_text.rtl = self.target_lang == "ar"

        # Swap text content if both fields have text
        if self.source_text.value and self.target_text.value:
            source_text = self.source_text.value

            self.source_text.value = self.target_text.value
            self.target_text.value = source_text

            # Update character count
            text = self.source_text.value or ""
            self.char_count.value = f"{len(text)}/5000"

        self.source_text.hint_text = self.get_source_hint_text()

        self.source_dropdown.update()
        self.target_dropdown.update()
        self.source_text.update()
        self.char_count.update()

        # Re-translate if there's text
        if self.source_text.value and self.source_text.value.strip():
            await self.translate_text()

    async def copy_translation(self, e):
        if self.target_text.value:
            # pyperclip.copy(self.target_text.value)
            clipboard = ft.Clipboard()
            await clipboard.set(self.target_text.value)

            # Show temporary feedback
            self.copy_button.icon = ft.Icons.CHECK
            self.copy_button.icon_color = "#34a853"  # Google green
            self.copy_button.update()

            # Reset after delay
            await asyncio.sleep(2)
            self.copy_button.icon = ft.Icons.CONTENT_COPY_OUTLINED
            self.copy_button.icon_color = ft.Colors.PRIMARY
            self.copy_button.update()

    async def speak_translation(self, e):
        # This would integrate with text-to-speech
        # For now, just show a snackbar
        if self.target_text.value:
            snackbar = ft.SnackBar(
                content=ft.Text(
                    "🔊 Text-to-speech would play audio here",
                    color=ft.Colors.ON_SURFACE,
                ),
                bgcolor=ft.Colors.SURFACE,
                show_close_icon=True,
            )
            e.page.show_snack_bar(snackbar)
