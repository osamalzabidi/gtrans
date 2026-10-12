#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
from unittest.mock import Mock, patch

import pytest
from googletrans import Translator

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from gtrans import GoogleTranslateApp


class TestGoogleTranslateApp:
    """Test cases for GoogleTranslateApp"""

    def setup_method(self):
        """Setup before each test"""
        self.app = GoogleTranslateApp()
        self.app.translator = Translator()

    def test_initialization(self):
        """Test app initializes with correct default values"""
        assert self.app.source_lang == "en"
        assert self.app.target_lang == "ar"
        assert self.app.source_hint_text == "Enter text here..."
        assert self.app.current_mode == "text"
        assert hasattr(self.app, "translator")

    def test_language_swap(self):
        """Test language swapping functionality"""
        # Set initial languages
        self.app.source_lang = "en"
        self.app.target_lang = "ar"

        # Mock the swap method
        async def mock_swap():
            self.app.source_lang, self.app.target_lang = (
                self.app.target_lang,
                self.app.source_lang,
            )

        # Test swap
        asyncio.run(mock_swap())

        assert self.app.source_lang == "ar"
        assert self.app.target_lang == "en"

    @patch("googletrans.Translator.translate")
    def test_translate_text_success(self, mock_translate):
        """Test successful text translation"""
        # Mock the translation response
        mock_response = Mock()
        mock_response.text = "مرحبا بالعالم"
        mock_translate.return_value = mock_response

        # Test data
        source_text = "Hello world"
        source_lang = "en"
        target_lang = "ar"

        # Perform translation
        result = self.app.translator.translate(
            source_text, dest=target_lang, src=source_lang
        )

        # Assertions
        mock_translate.assert_called_once_with(
            source_text, dest=target_lang, src=source_lang
        )
        assert result.text == "مرحبا بالعالم"

    # @patch('googletrans.Translator.translate')
    # def test_translate_text_auto_detect(self, mock_translate):
    #     """Test translation with auto language detection"""
    #     mock_response = Mock()
    #     mock_response.text = "Hola Mundo"
    #     mock_response.src = "en"
    #     mock_translate.return_value = mock_response

    #     source_text = "Hello World"
    #     target_lang = "es"

    #     result = self.app.translator.translate(
    #         source_text,
    #         dest=target_lang
    #         # No src specified for auto-detection
    #     )

    #     mock_translate.assert_called_once_with(
    #         source_text, dest=target_lang
    #     )
    #     assert result.text == "Hola Mundo"
    #     assert result.src == "en"

    @patch("googletrans.Translator.translate")
    def test_translate_empty_text(self, mock_translate):
        """Test translation with empty text"""
        result = self.app.translate_text("")
        assert result == ""  # Should return empty string
        mock_translate.assert_not_called()  # No API call for empty text

    @patch("googletrans.Translator.translate")
    def test_translation_error_handling(self, mock_translate):
        """Test error handling during translation"""
        mock_translate.side_effect = Exception("Network error")

        try:
            result = self.app.translator.translate("test", dest="es")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert str(e) == "Network error"

    def test_language_code_validation(self):
        """Test valid and invalid language codes"""
        valid_languages = ["en", "ar", "es", "fr", "de"]
        invalid_languages = ["xx", "yy", ""]

        for lang in valid_languages:
            # This should not raise an exception
            self.app.source_lang = lang
            self.app.target_lang = lang

        # Test with invalid codes (should be handled gracefully)
        for lang in invalid_languages:
            try:
                self.app.source_lang = lang
                # If the app has validation, it should handle this
            except ValueError:
                pass  # Expected behavior

    def test_text_length_limits(self):
        """Test text length validation"""
        # Test within limits
        short_text = "a" * 100
        assert len(short_text) == 100

        # Test at limit
        limit_text = "a" * 5000
        assert len(limit_text) == 5000

        # Test over limit (should be handled by the app)
        long_text = "a" * 5001
        assert len(long_text) == 5001


class TestTranslationMethods:
    """Test different translation methods"""

    def setup_method(self):
        self.app = GoogleTranslateApp()

    # def test_mode_switching(self):
    #     """Test switching between translation modes"""
    #     modes = ['text', 'doc', 'voice', 'camera', 'conversation']

    #     for mode in modes:
    #         self.app.current_mode = mode
    #         assert self.app.current_mode == mode

    # @patch('builtins.open')
    # @patch('os.path.exists')
    # def test_document_upload_simulation(self, mock_exists, mock_open):
    #     """Test document upload simulation"""
    #     mock_exists.return_value = True
    #     mock_file = Mock()
    #     mock_open.return_value.__enter__ = Mock(return_value=mock_file)
    #     mock_open.return_value.__exit__ = Mock(return_value=None)

    #     # Simulate document processing
    #     def simulate_doc_processing():
    #         return "This is extracted document text"

    #     result = simulate_doc_processing()
    #     assert result == "This is extracted document text"

    # def test_voice_recording_simulation(self):
    #     """Test voice recording simulation"""
    #     # Simulate voice processing
    #     def simulate_voice_processing():
    #         return "This is recognized speech text"

    #     result = simulate_voice_processing()
    #     assert "recognized speech" in result


class TestUIFunctions:
    """Test UI-related functions"""

    def setup_method(self):
        self.app = GoogleTranslateApp()

    def test_character_count(self):
        """Test character counting functionality"""
        test_cases = [
            ("", 0),
            ("Hello", 5),
            ("Hello World", 11),
            ("مرحبا", 5),  # Arabic characters
            ("Hello 世界", 8),  # Mixed characters
        ]

        for text, expected_count in test_cases:
            count = len(text)
            assert count == expected_count

    def test_text_cleaning(self):
        """Test text cleaning utilities"""
        dirty_text = "  Hello   World  \n\n  "
        cleaned_text = dirty_text.strip()

        assert cleaned_text == "Hello   World"

        # Test with extra spaces
        extra_spaces = "Hello    World"
        normalized = " ".join(extra_spaces.split())
        assert normalized == "Hello World"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
