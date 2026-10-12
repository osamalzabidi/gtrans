#!/usr/bin/python3
# -*- coding: utf-8 -*-

import flet as ft
import asyncio
from googletrans.constants import (
    DEFAULT_CLIENT_SERVICE_URLS,
    DEFAULT_USER_AGENT,
    LANGUAGES,
)


class SettingsDialog:
    """Settings dialog using Flet's client_storage with async support"""

    def __init__(self, page: ft.Page, app_instance=None, save_callback=None):
        self.page = page
        self.app = app_instance
        self.dialog = None
        self._save_settings_callback = save_callback

        # Initialize form fields with empty values (will be populated async)
        self.proxy_field = ft.TextField(
            label="Proxy URL",
            hint_text="http://proxy.example.com:8080",
            value="",
            width=300,
            text_size=14,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
        )

        self.proxy_default_toggle = ft.Checkbox(
            label="Use system default proxy", value=False
        )

        self.request_timeout_field = ft.TextField(
            label="Request Timeout",
            value="30",
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
        )

        self.width_field = ft.TextField(
            label="Window Width",
            value="900",
            width=140,
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
        )

        self.height_field = ft.TextField(
            label="Window Height",
            value="550",
            width=140,
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
        )

        self.service_urls_field = ft.TextField(
            label="Service URLs (comma-separated)",
            hint_text="translate.google.com, translate.google.co.kr",
            value=", ".join(DEFAULT_CLIENT_SERVICE_URLS),
            width=300,
            text_size=14,
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
        )

        self.user_agent_field = ft.TextField(
            label="User Agent",
            value=DEFAULT_USER_AGENT,
            width=300,
            text_size=14,
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
        )

        self.default_source_lang_dropdown = ft.Dropdown(
            label="Default Source Language",
            value="auto",
            options=[
                ft.dropdown.Option("auto", "Auto Detect"),
                *[ft.dropdown.Option(k, v.capitalize()) for k, v in LANGUAGES.items()],
            ],
            width=200,
            content_padding=12,
            text_size=14,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
            enable_search=True,
        )

        self.default_target_lang_dropdown = ft.Dropdown(
            label="Default Target Language",
            value="en",
            options=[
                ft.dropdown.Option(k, v.capitalize()) for k, v in LANGUAGES.items()
            ],
            width=200,
            content_padding=12,
            text_size=14,
            border_radius=8,
            filled=True,
            border_color=ft.Colors.TRANSPARENT,
            enable_search=True,
        )

        # Status message
        self.status_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.GREEN,
            visible=False,
        )

        # Restart required warning
        self.restart_warning = ft.Text(
            "⚠️ Some changes require app restart",
            size=12,
            color=ft.Colors.ORANGE,
            visible=False,
        )

    async def _load_settings_async(self):
        """Load settings asynchronously from client_storage"""
        try:
            # Load all settings using async method
            proxy = await self.app.sp.get("gt.proxy")
            proxy_default = await self.app.sp.get("gt.proxy_default")
            width = await self.app.sp.get("gt.window_width")
            height = await self.app.sp.get("gt.window_height")
            service_urls = await self.app.sp.get("gt.service_urls")
            user_agent = await self.app.sp.get("gt.user_agent")
            default_source_lang = await self.app.sp.get("gt.default_source_lang")
            default_target_lang = await self.app.sp.get("gt.default_target_lang")
            request_timeout = await self.app.sp.get("gt.request_timeout")

            # Update form fields
            if proxy:
                self.proxy_field.value = proxy
            if proxy_default is not None:
                self.proxy_default_toggle.value = proxy_default
            if width:
                self.width_field.value = str(width)
            if height:
                self.height_field.value = str(height)
            if service_urls:
                self.service_urls_field.value = service_urls
            if user_agent:
                self.user_agent_field.value = user_agent
            if default_source_lang:
                self.default_source_lang_dropdown.value = default_source_lang
            if default_target_lang:
                self.default_target_lang_dropdown.value = default_target_lang
            if request_timeout:
                self.request_timeout_field.value = request_timeout

            # Update UI
            self.proxy_field.update()
            self.width_field.update()
            self.height_field.update()
            self.service_urls_field.update()
            self.user_agent_field.update()
            self.default_source_lang_dropdown.update()
            self.default_target_lang_dropdown.update()

        except Exception as e:
            print(f"Error loading settings: {e}")

    async def _show_status(self, message: str, is_error: bool = False):
        """Show status message"""
        self.status_text.value = message
        self.status_text.color = ft.Colors.RED if is_error else ft.Colors.GREEN
        self.status_text.visible = True
        self.status_text.update()

        # Hide after 3 seconds
        async def hide_status():
            await asyncio.sleep(2)
            self.status_text.visible = False
            self.status_text.update()

        # asyncio.create_task(hide_status())
        await hide_status()

    async def _save_settings_async(self, e):
        """Save settings to client_storage asynchronously"""
        try:
            # Save proxy
            proxy = self.proxy_field.value.strip()
            proxy_default = self.proxy_default_toggle.value

            await self.app.sp.set("gt.proxy", proxy)
            await self.app.sp.set("gt.proxy_default", proxy_default)

            # Save window dimensions
            try:
                width = int(self.width_field.value.strip())
                height = int(self.height_field.value.strip())
                if width < 300 or height < 300:
                    raise ValueError
                await self.app.sp.set("gt.window_width", width)
                await self.app.sp.set("gt.window_height", height)
            except (ValueError, AttributeError):
                await self._show_status(
                    "Invalid window dimensions (min: 300x300)", True
                )
                return

            # Save service URLs
            urls = self.service_urls_field.value.strip()
            await self.app.sp.set("gt.service_urls", urls)

            # Save user agent
            user_agent = self.user_agent_field.value.strip()
            await self.app.sp.set("gt.user_agent", user_agent)

            # Save default language
            src_lang = self.default_source_lang_dropdown.value
            dest_lang = self.default_target_lang_dropdown.value

            if src_lang:
                await self.app.sp.set("gt.default_source_lang", src_lang)
            if dest_lang:
                await self.app.sp.set("gt.default_target_lang", dest_lang)

                # Update app if it's running
                # if self.app and hasattr(self.app, 'target_lang'):
                #     self.app.target_lang = lang
                #     if hasattr(self.app, 'target_dropdown'):
                #         self.app.target_dropdown.value = lang
                #         self.app.target_dropdown.update()

            request_timeout = self.request_timeout_field.value
            await self.app.sp.set("gt.request_timeout", int(request_timeout))

            # Show restart warning for some settings
            self.restart_warning.visible = True
            self.restart_warning.update()

            await self._show_status("Settings saved successfully!")

        except Exception as e:
            await self._show_status(f"Error saving settings: {str(e)}", True)

    async def _save_settings(self, e):
        """Wrapper for async save"""
        # asyncio.create_task(self._save_settings_async(e))
        await self._save_settings_async(e)
        if self._save_settings_callback is not None:
            try:
                await self._save_settings_callback()
            except Exception:
                pass

    def _close_dialog(self, page: ft.Page):
        """Close the dialog"""
        page.pop_dialog()

    async def open_dialog(self):
        """Open the settings dialog and load settings"""
        # Create the scrollable content section
        scrollable_content = ft.Container(
            content=ft.Column(
                [
                    # Network settings
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    title=ft.Text(
                                        "Network", weight=ft.FontWeight.W_500
                                    ),
                                    leading=ft.Icon(
                                        ft.Icons.NETWORK_CHECK, color=ft.Colors.BLUE
                                    ),
                                ),
                                ft.Container(
                                    content=ft.Column(
                                        controls=[
                                            self.proxy_field,
                                            self.proxy_default_toggle,
                                            self.request_timeout_field,
                                        ]
                                    ),
                                    padding=ft.Padding.only(
                                        left=16, right=16, bottom=16
                                    ),
                                ),
                            ]
                        ),
                        border_radius=12,
                        border=ft.Border.all(1, ft.Colors.OUTLINE),
                        bgcolor=ft.Colors.SURFACE,
                    ),
                    ft.Divider(height=24, color=ft.Colors.TRANSPARENT),
                    # Window settings
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    title=ft.Text("Window", weight=ft.FontWeight.W_500),
                                    leading=ft.Icon(
                                        ft.Icons.WINDOW, color=ft.Colors.BLUE
                                    ),
                                ),
                                ft.Container(
                                    content=ft.Row(
                                        [
                                            self.width_field,
                                            ft.Text(
                                                "×", size=20, color=ft.Colors.GREY_600
                                            ),
                                            self.height_field,
                                        ],
                                        alignment=ft.MainAxisAlignment.START,
                                        spacing=16,
                                    ),
                                    padding=ft.Padding.only(
                                        left=16, right=16, bottom=16
                                    ),
                                ),
                            ]
                        ),
                        border_radius=12,
                        border=ft.Border.all(1, ft.Colors.OUTLINE),
                        bgcolor=ft.Colors.SURFACE,
                    ),
                    ft.Divider(height=24, color=ft.Colors.TRANSPARENT),
                    # Translation service
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    title=ft.Text(
                                        "Translation Service",
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    leading=ft.Icon(
                                        ft.Icons.TRANSLATE, color=ft.Colors.BLUE
                                    ),
                                ),
                                ft.Container(
                                    content=self.service_urls_field,
                                    padding=ft.Padding.only(
                                        left=16, right=16, bottom=16
                                    ),
                                ),
                                ft.Container(
                                    content=self.user_agent_field,
                                    padding=ft.Padding.only(
                                        left=16, right=16, bottom=16
                                    ),
                                ),
                            ]
                        ),
                        border_radius=12,
                        border=ft.Border.all(1, ft.Colors.OUTLINE),
                        bgcolor=ft.Colors.SURFACE,
                    ),
                    ft.Divider(height=24, color=ft.Colors.TRANSPARENT),
                    # Language settings
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    title=ft.Text(
                                        "Language", weight=ft.FontWeight.W_500
                                    ),
                                    leading=ft.Icon(
                                        ft.Icons.LANGUAGE, color=ft.Colors.BLUE
                                    ),
                                ),
                                ft.Container(
                                    content=self.default_source_lang_dropdown,
                                    padding=ft.Padding.only(
                                        left=16, right=16, bottom=16
                                    ),
                                ),
                                ft.Container(
                                    content=self.default_target_lang_dropdown,
                                    padding=ft.Padding.only(
                                        left=16, right=16, bottom=16
                                    ),
                                ),
                            ]
                        ),
                        border_radius=12,
                        border=ft.Border.all(1, ft.Colors.OUTLINE),
                        bgcolor=ft.Colors.SURFACE,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
            ),
            # height=400,  # Fixed height for scrollable area
            expand=True,
        )

        # Create the main dialog content with non-scrollable header and footer
        self.dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.Icons.SETTINGS, size=28, color=ft.Colors.BLUE),
                    ft.Text(
                        "Settings",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        on_click=lambda e: self._close_dialog(self.page),
                        icon_color=ft.Colors.ON_SURFACE,
                        hover_color="#FF0000",
                    ),
                ]
            ),
            content=scrollable_content,
            actions=[
                ft.Column(
                    [
                        self.restart_warning,
                        self.status_text,
                        # ft.Divider(height=16, color=ft.Colors.TRANSPARENT),
                        ft.Row(
                            [
                                ft.OutlinedButton(
                                    "Reset Defaults",
                                    on_click=self._reset_defaults,
                                    icon=ft.Icons.RESTORE,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                ),
                                ft.Container(expand=True),
                                ft.OutlinedButton(
                                    "Cancel",
                                    on_click=lambda e: self._close_dialog(self.page),
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                ),
                                ft.Container(width=8),
                                ft.FilledButton(
                                    "Save Changes",
                                    on_click=self._save_settings,
                                    icon=ft.Icons.SAVE,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                        padding=ft.Padding.symmetric(
                                            horizontal=24, vertical=12
                                        ),
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=8,
                )
            ],
        )

        # Open dialog first
        self.page.show_dialog(self.dialog)

        # Then load settings asynchronously
        # asyncio.create_task(self._load_settings_async())
        await self._load_settings_async()

    async def _reset_defaults(self, e):
        """Reset all settings to defaults"""
        self.proxy_field.value = ""
        self.proxy_default_toggle.value = False
        self.width_field.value = "900"
        self.height_field.value = "550"
        self.service_urls_field.value = ", ".join(DEFAULT_CLIENT_SERVICE_URLS)
        self.user_agent_field.value = DEFAULT_USER_AGENT
        self.default_source_lang_dropdown.value = "auto"
        self.default_target_lang_dropdown.value = "en"

        self.proxy_field.update()
        self.proxy_default_toggle.update()
        self.width_field.update()
        self.height_field.update()
        self.service_urls_field.update()
        self.user_agent_field.update()
        self.default_source_lang_dropdown.update()
        self.default_target_lang_dropdown.update()

        await self._show_status("Reset to defaults - click Save to apply")
