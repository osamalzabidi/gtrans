#!/usr/bin/python3
# -*- coding: utf-8 -*-


import flet as ft

from src.gtrans.home_page import GoogleTranslateApp


def main():
    app = GoogleTranslateApp()
    ft.run(app.main)


if __name__ == "__main__":
    main()
