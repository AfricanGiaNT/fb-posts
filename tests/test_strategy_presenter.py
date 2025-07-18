import unittest
from unittest.mock import MagicMock, patch
from implemented.strategy_presenter import StrategyPresenter

class TestStrategyPresenter(unittest.TestCase):
    def setUp(self):
        self.presenter = StrategyPresenter()
        self.sample_strategy = {
            "project_theme": "Test Project",
            "estimated_posts": 3,
            "narrative_flow": "Complete project journey",
            "recommended_sequence": [
                {
                    "position": 1,
                    "file_id": "file1",
                    "filename": "planning.md",
                    "theme": "architecture",
                    "recommended_tone": "Problem → Solution",
                    "target_audience": "technical"
                },
                {
                    "position": 2,
                    "file_id": "file2",
                    "filename": "implementation.md",
                    "theme": "development",
                    "recommended_tone": "Behind-the-Build",
                    "target_audience": "technical"
                }
            ],
            "content_themes": ["architecture", "development"],
            "theme_strength": {
                "architecture": 80,
                "development": 60
            },
            "audience_split": {
                "technical": 2,
                "business": 1
            },
            "cross_references": [
                {
                    "from_file": "file1",
                    "to_file": "file2",
                    "connection_type": "continuation",
                    "reference_text": "Building on the architecture from earlier...",
                    "strength": 5
                }
            ],
            "posting_timeline": {
                "frequency": "2-3 posts per week",
                "duration": "1 weeks",
                "best_times": ["Tuesday 10am", "Thursday 2pm"]
            }
        }

    @patch('rich.console.Console.print')
    def test_present_strategy(self, mock_print):
        """Test that present_strategy calls all print methods."""
        self.presenter.present_strategy(self.sample_strategy)
        # Should call print multiple times for different sections
        self.assertTrue(mock_print.call_count > 5)

    @patch('rich.console.Console.print')
    @patch('rich.console.Console.input')
    def test_edit_sequence(self, mock_input, mock_print):
        """Test sequence editing functionality."""
        # Simulate moving a post
        mock_input.side_effect = ["1", "1", "2", "3"]
        
        result = self.presenter.edit_sequence(self.sample_strategy)
        
        # Check that sequence was modified
        self.assertEqual(
            result["recommended_sequence"][0]["file_id"],
            "file2"
        )
        self.assertEqual(
            result["recommended_sequence"][1]["file_id"],
            "file1"
        )

    @patch('rich.console.Console.print')
    @patch('rich.console.Console.input')
    def test_customize_themes(self, mock_input, mock_print):
        """Test theme customization functionality."""
        # Simulate excluding a theme
        mock_input.side_effect = ["architecture", "done"]
        
        result = self.presenter.customize_themes(self.sample_strategy)
        
        # Check that theme was excluded
        self.assertIn("customization", result)
        self.assertIn("excluded_themes", result["customization"])
        self.assertIn("architecture", result["customization"]["excluded_themes"])

    @patch('rich.console.Console.print')
    @patch('rich.console.Console.input')
    def test_set_audience_preference(self, mock_input, mock_print):
        """Test audience preference setting."""
        # Simulate selecting technical focus
        mock_input.return_value = "1"
        
        result = self.presenter.set_audience_preference(self.sample_strategy)
        
        # Check that preference was set
        self.assertIn("customization", result)
        self.assertIn("audience_preference", result["customization"])
        self.assertEqual(
            result["customization"]["audience_preference"],
            "technical"
        )

    @patch('rich.console.Console.print')
    def test_print_themes(self, mock_print):
        """Test theme printing functionality."""
        self.presenter._print_themes(self.sample_strategy)
        # Should print theme table
        self.assertTrue(mock_print.called)

    @patch('rich.console.Console.print')
    def test_print_sequence(self, mock_print):
        """Test sequence printing functionality."""
        self.presenter._print_sequence(self.sample_strategy)
        # Should print sequence table
        self.assertTrue(mock_print.called)

    @patch('rich.console.Console.print')
    def test_print_cross_references(self, mock_print):
        """Test cross-reference printing functionality."""
        self.presenter._print_cross_references(self.sample_strategy)
        # Should print reference tree
        self.assertTrue(mock_print.called)

    @patch('rich.console.Console.print')
    def test_print_audience_split(self, mock_print):
        """Test audience split printing functionality."""
        self.presenter._print_audience_split(self.sample_strategy)
        # Should print split table
        self.assertTrue(mock_print.called)

if __name__ == '__main__':
    unittest.main() 