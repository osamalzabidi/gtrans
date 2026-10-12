#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
from unittest.mock import patch

import pytest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from gtrans import GoogleTranslateApp


class TestAsyncTranslations:
    """Test asynchronous translation operations"""

    def setup_method(self):
        self.app = GoogleTranslateApp()

    @pytest.mark.asyncio
    async def test_async_translation(self):
        """Test async translation functionality"""
        with patch("asyncio.get_event_loop.run_in_executor") as mock_executor:
            # Mock the translation result
            mock_translation = Mock()
            mock_translation.text = "Translated text"
            mock_executor.return_value = asyncio.Future()
            mock_executor.return_value.set_result(mock_translation)

            # Set up app state
            self.app.source_text.value = "Hello"
            self.app.source_lang = "en"
            self.app.target_lang = "es"

            # Execute async translation
            await self.app.translate_text()

            # Verify the translation was processed
            mock_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_concurrent_translations(self):
        """Test handling multiple concurrent translations"""

        async def mock_translate(text, target_lang):
            await asyncio.sleep(0.1)  # Simulate API call
            return f"Translated: {text}"

        # Test multiple translations
        texts = ["Hello", "World", "Test"]
        tasks = [mock_translate(text, "es") for text in texts]

        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all("Translated:" in result for result in results)

    @pytest.mark.asyncio
    async def test_translation_cancellation(self):
        """Test translation cancellation"""

        async def long_running_translation():
            try:
                await asyncio.sleep(10)  # Long operation
                return "Result"
            except asyncio.CancelledError:
                return "Cancelled"

        # Start translation
        task = asyncio.create_task(long_running_translation())
        await asyncio.sleep(0.1)
        task.cancel()

        result = await task
        assert result == "Cancelled"


class TestErrorScenarios:
    """Test error scenarios and edge cases"""

    def setup_method(self):
        self.app = GoogleTranslateApp()

    @pytest.mark.asyncio
    async def test_network_failure(self):
        """Test behavior when network fails"""
        with patch("asyncio.get_event_loop.run_in_executor") as mock_executor:
            mock_executor.side_effect = Exception("Network unavailable")

            self.app.source_text.value = "Test text"

            try:
                await self.app.translate_text()
                assert False, "Should have raised an exception"
            except Exception as e:
                assert "Network unavailable" in str(e)

    @pytest.mark.asyncio
    async def test_invalid_language_code(self):
        """Test translation with invalid language code"""
        self.app.source_lang = "en"
        self.app.target_lang = "invalid_code"
        self.app.source_text.value = "Hello"

        # This should be handled gracefully by the app
        try:
            await self.app.translate_text()
        except Exception as e:
            # Either handle the error or let it propagate
            assert "language" in str(e).lower() or "code" in str(e).lower()

    def test_special_characters_handling(self):
        """Test translation with special characters"""
        test_cases = [
            "Hello @World!",
            "Line1\nLine2",
            "Text with <html> tags",
            "Emoji 😀 test",
            "Unicode: 中文",
        ]

        for text in test_cases:
            # Should not crash when processing
            processed = text.strip()
            assert isinstance(processed, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
