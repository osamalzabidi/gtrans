#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from gtrans import GoogleTranslateApp


class TestAppConfiguration:
    """Test application configuration and settings"""

    def test_default_settings(self):
        """Test default application settings"""
        app = GoogleTranslateApp()

        # Test default values
        assert app.source_lang == "en"
        assert app.target_lang == "ar"
        assert app.current_mode == "text"

        # Test that required attributes exist
        assert hasattr(app, "translator")
        assert hasattr(app, "source_text")
        assert hasattr(app, "target_text")

    def test_language_persistence(self):
        """Test that language settings persist"""
        app = GoogleTranslateApp()

        # Change languages
        app.source_lang = "fr"
        app.target_lang = "de"

        # Verify persistence
        assert app.source_lang == "fr"
        assert app.target_lang == "de"

        # Change back
        app.source_lang = "en"
        app.target_lang = "ar"
        assert app.source_lang == "en"
        assert app.target_lang == "ar"

    # def test_mode_management(self):
    #     """Test translation mode management"""
    #     app = GoogleTranslateApp()

    #     modes = ['text', 'doc', 'voice', 'camera', 'conversation']

    #     for mode in modes:
    #         app.current_mode = mode
    #         assert app.current_mode == mode

    #     # Verify default mode is restored
    #     app.current_mode = 'text'
    #     assert app.current_mode == 'text'


class TestIntegrationScenarios:
    """Test integration scenarios"""

    def test_complete_translation_flow(self):
        """Test complete translation workflow"""
        app = GoogleTranslateApp()

        # Setup
        app.source_lang = "en"
        app.target_lang = "es"
        app.current_mode = "text"

        # Verify initial state
        assert app.source_lang == "en"
        assert app.target_lang == "es"
        assert app.current_mode == "text"

        # Simulate user interaction
        app.source_lang = "fr"  # User changes source
        app.target_lang = "de"  # User changes target

        assert app.source_lang == "fr"
        assert app.target_lang == "de"

        # Switch mode
        # app.current_mode = "voice"
        # assert app.current_mode == "voice"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
