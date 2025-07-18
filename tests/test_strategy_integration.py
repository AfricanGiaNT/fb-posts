import unittest
from implemented.content_strategy_generator import ContentStrategyGenerator
from implemented.strategy_presenter import StrategyPresenter
import os

class TestStrategyIntegration(unittest.TestCase):
    def setUp(self):
        self.generator = ContentStrategyGenerator()
        self.presenter = StrategyPresenter()
        
        # Test file data
        self.test_analysis = {
            "project_theme": "Authentication System Enhancement",
            "source_files": [{
                "file_id": "test-strategy-001",
                "filename": "test-strategy-001.md",
                "file_phase": "implementation",
                "content": open("content/dev_journal/test-strategy-001.md").read(),
                "key_themes": ["security", "performance", "implementation"]
            }]
        }

    def test_strategy_generation(self):
        # Generate strategy
        strategy = self.generator.generate_optimal_strategy(self.test_analysis)
        
        # Verify key components
        self.assertIn("project_theme", strategy)
        self.assertIn("estimated_posts", strategy)
        self.assertIn("recommended_sequence", strategy)
        self.assertIn("cross_references", strategy)
        self.assertIn("audience_split", strategy)
        
        # Verify theme detection
        self.assertIn("security", strategy["theme_strength"])
        self.assertIn("performance", strategy["theme_strength"])
        
        # Verify audience split
        audience_split = strategy["audience_split"]
        self.assertTrue(audience_split["technical"] > 0)
        
        # Test customization
        customization = {
            "excluded_themes": ["performance"],
            "audience_preference": "technical"
        }
        custom_strategy = self.generator.generate_optimal_strategy(
            self.test_analysis,
            customization
        )
        self.assertTrue(custom_strategy["customization_applied"])

if __name__ == "__main__":
    unittest.main() 