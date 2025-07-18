import unittest
from implemented.content_strategy_generator import ContentStrategyGenerator

class TestContentStrategyGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = ContentStrategyGenerator()
        self.sample_project_analysis = {
            "project_theme": "API Development",
            "source_files": [
                {
                    "file_id": "file1",
                    "filename": "planning-phase-001.md",
                    "file_phase": "planning",
                    "key_themes": ["architecture", "planning"],
                    "content": """
                    # Project Planning Phase
                    
                    We need to design a scalable system architecture for our API.
                    The plan includes security considerations and performance optimization.
                    Next steps will involve implementation and testing.
                    """
                },
                {
                    "file_id": "file2",
                    "filename": "implementation-core-001.md",
                    "file_phase": "implementation",
                    "key_themes": ["development", "testing"],
                    "content": """
                    # Implementation Phase
                    
                    Building on our architecture design, we implemented the core API endpoints.
                    The implementation includes unit tests and integration tests.
                    We improved performance through caching and optimization.
                    """
                },
                {
                    "file_id": "file3",
                    "filename": "debugging-session-001.md",
                    "file_phase": "debugging",
                    "key_themes": ["debugging", "problem-solving"],
                    "content": """
                    # Debugging Session
                    
                    Fixed several critical issues in the API implementation.
                    This required extensive debugging and problem-solving.
                    Comparing with our initial implementation, we found better approaches.
                    """
                }
            ]
        }

    def test_generate_optimal_strategy(self):
        strategy = self.generator.generate_optimal_strategy(self.sample_project_analysis)
        
        # Test strategy structure
        self.assertIn("project_theme", strategy)
        self.assertIn("estimated_posts", strategy)
        self.assertIn("narrative_flow", strategy)
        self.assertIn("recommended_sequence", strategy)
        self.assertIn("content_themes", strategy)
        self.assertIn("audience_split", strategy)
        self.assertIn("cross_references", strategy)
        self.assertIn("tone_suggestions", strategy)
        self.assertIn("posting_timeline", strategy)
        self.assertIn("theme_strength", strategy)
        self.assertIn("customization_applied", strategy)
        
        # Test estimated posts
        self.assertEqual(strategy["estimated_posts"], 3)

    def test_suggest_posting_sequence(self):
        sequence = self.generator.suggest_posting_sequence(
            self.sample_project_analysis["source_files"],
            self.sample_project_analysis
        )
        
        # Test sequence length
        self.assertEqual(len(sequence), 3)
        
        # Test sequence order
        self.assertEqual(sequence[0]["file_id"], "file1")  # Planning should be first
        self.assertEqual(sequence[1]["file_id"], "file2")  # Implementation second
        self.assertEqual(sequence[2]["file_id"], "file3")  # Debugging third

    def test_generate_cross_references(self):
        sequence = self.generator.suggest_posting_sequence(
            self.sample_project_analysis["source_files"],
            self.sample_project_analysis
        )
        
        references = self.generator.generate_cross_references(
            self.sample_project_analysis["source_files"],
            sequence
        )
        
        # Test that we have references
        self.assertTrue(len(references) > 0)
        
        # Test reference structure
        for ref in references:
            self.assertIn("from_file", ref)
            self.assertIn("to_file", ref)
            self.assertIn("connection_type", ref)
            self.assertIn("reference_text", ref)
            self.assertIn("strength", ref)  # New field

    def test_analyze_audience_split(self):
        audience_split = self.generator._analyze_audience_split(self.sample_project_analysis)
        
        # Test split structure
        self.assertIn("technical", audience_split)
        self.assertIn("business", audience_split)
        
        # Test counts
        self.assertTrue(audience_split["technical"] > 0)

    def test_determine_tone(self):
        # Test different phases
        planning_file = {"file_phase": "planning"}
        self.assertEqual(
            self.generator._determine_tone(planning_file),
            "Problem → Solution"
        )
        
        debugging_file = {"file_phase": "debugging"}
        self.assertEqual(
            self.generator._determine_tone(debugging_file),
            "What Broke"
        )

    def test_enhanced_theme_extraction(self):
        """Test the enhanced theme extraction functionality."""
        themes = self.generator._extract_content_themes(self.sample_project_analysis)
        
        # Test that we found the major themes
        expected_themes = {"architecture", "implementation", "testing", "debugging"}
        found_themes = set(themes)
        self.assertTrue(expected_themes.issubset(found_themes))
        
        # Test theme order (most frequent first)
        self.assertIn("implementation", themes[:2])  # Should be among top 2

    def test_theme_strength_analysis(self):
        """Test the theme strength analysis functionality."""
        strengths = self.generator._analyze_theme_strength(self.sample_project_analysis)
        
        # Test structure
        self.assertIsInstance(strengths, dict)
        self.assertTrue(len(strengths) > 0)
        
        # Test strength values
        for strength in strengths.values():
            self.assertIsInstance(strength, int)
            self.assertGreaterEqual(strength, 0)
            self.assertLessEqual(strength, 100)
        
        # Test relative strengths
        if "implementation" in strengths and "debugging" in strengths:
            self.assertGreaterEqual(
                strengths["implementation"],
                strengths["debugging"]
            )

    def test_customization(self):
        """Test the customization functionality."""
        customization = {
            "excluded_themes": ["security"],
            "preferred_sequence": ["file2", "file3", "file1"],
            "audience_preference": "technical"
        }
        
        strategy = self.generator.generate_optimal_strategy(
            self.sample_project_analysis,
            customization
        )
        
        # Test customization was applied
        self.assertTrue(strategy["customization_applied"])
        
        # Test sequence customization
        sequence = strategy["recommended_sequence"]
        self.assertEqual(sequence[0]["file_id"], "file2")
        
        # Test theme exclusion
        self.assertNotIn("security", strategy["content_themes"])
        
        # Test audience preference
        self.assertIn("planning", self.generator.audience_types["technical"])

    def test_enhanced_cross_references(self):
        """Test the enhanced cross-reference functionality."""
        sequence = self.generator.suggest_posting_sequence(
            self.sample_project_analysis["source_files"],
            self.sample_project_analysis
        )
        
        references = self.generator.generate_cross_references(
            self.sample_project_analysis["source_files"],
            sequence
        )
        
        # Test connection types
        connection_types = {ref["connection_type"] for ref in references}
        self.assertTrue(len(connection_types) > 1)  # Should find multiple types
        
        # Test connection strength
        for ref in references:
            self.assertIn("strength", ref)
            self.assertGreater(ref["strength"], 0)
        
        # Test reference text templates
        for ref in references:
            self.assertIn(ref["connection_type"], self.generator.connection_patterns)
            template = self.generator.connection_patterns[ref["connection_type"]]["template"]
            self.assertIn(template.split("{")[0], ref["reference_text"])

if __name__ == '__main__':
    unittest.main() 