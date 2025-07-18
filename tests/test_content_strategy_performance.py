import unittest
import time
from typing import List, Dict
from implemented.content_strategy_generator import ContentStrategyGenerator

class TestContentStrategyPerformance(unittest.TestCase):
    def setUp(self):
        self.generator = ContentStrategyGenerator()
        
    def _generate_test_files(self, count: int) -> List[Dict]:
        """Generate test files with varying content."""
        files = []
        phases = ["planning", "implementation", "debugging", "results"]
        themes = ["architecture", "development", "testing", "security"]
        
        for i in range(count):
            phase_idx = i % len(phases)
            theme_idx = i % len(themes)
            
            content = f"""
            # Project Phase {i + 1}
            
            This is a {phases[phase_idx]} document focusing on {themes[theme_idx]}.
            We need to implement several features and ensure proper testing.
            The architecture should be scalable and secure.
            
            ## Key Points
            - Feature implementation
            - Performance optimization
            - Security considerations
            - Testing requirements
            
            ## Technical Details
            We'll use various technologies and frameworks to achieve our goals.
            The system needs to handle high loads and maintain security.
            """
            
            files.append({
                "file_id": f"file{i + 1}",
                "filename": f"{phases[phase_idx]}-phase-{i + 1:03d}.md",
                "file_phase": phases[phase_idx],
                "key_themes": [themes[theme_idx]],
                "content": content
            })
        
        return files

    def test_strategy_generation_performance(self):
        """Test strategy generation performance with different file counts."""
        file_counts = [2, 4, 8]  # Test with different numbers of files
        times = {}
        
        for count in file_counts:
            files = self._generate_test_files(count)
            project_analysis = {
                "project_theme": "Performance Test Project",
                "source_files": files
            }
            
            start_time = time.time()
            strategy = self.generator.generate_optimal_strategy(project_analysis)
            end_time = time.time()
            
            generation_time = end_time - start_time
            times[count] = generation_time
            
            # Performance assertions
            self.assertLess(
                generation_time, 
                1.0,  # Should process in under 1 second
                f"Strategy generation for {count} files took too long: {generation_time:.2f}s"
            )
            
            # Debug output
            print(f"\nTesting {count} files:")
            print(f"Generated sequence length: {len(strategy['recommended_sequence'])}")
            print(f"Generated themes: {strategy['content_themes']}")
            print(f"Generated references: {len(strategy['cross_references'])}")
            print("References:", strategy['cross_references'])
            
            # Quality assertions
            self.assertEqual(len(strategy["recommended_sequence"]), count)
            self.assertTrue(len(strategy["content_themes"]) > 0)
            self.assertTrue(
                len(strategy["cross_references"]) >= count - 1,
                f"Expected at least {count - 1} references, got {len(strategy['cross_references'])}"
            )
        
        # Print performance results
        print("\nStrategy Generation Performance:")
        for count, duration in times.items():
            print(f"{count} files: {duration:.3f} seconds")

    def test_theme_extraction_performance(self):
        """Test theme extraction performance with large content."""
        files = self._generate_test_files(4)  # Use 4 files
        
        # Add more content to test theme extraction
        for file in files:
            file["content"] *= 5  # Multiply content to make it larger
        
        project_analysis = {
            "project_theme": "Theme Extraction Test",
            "source_files": files
        }
        
        start_time = time.time()
        themes = self.generator._extract_content_themes(project_analysis)
        end_time = time.time()
        
        extraction_time = end_time - start_time
        
        # Performance assertions
        self.assertLess(
            extraction_time,
            0.5,  # Should extract themes in under 0.5 seconds
            f"Theme extraction took too long: {extraction_time:.2f}s"
        )
        
        # Quality assertions
        self.assertTrue(len(themes) > 0)
        self.assertTrue(all(isinstance(theme, str) for theme in themes))

    def test_cross_reference_generation_performance(self):
        """Test cross-reference generation performance with many files."""
        files = self._generate_test_files(8)  # Test with 8 files
        sequence = [
            {
                "file_id": f["file_id"],
                "position": i + 1,
                "theme": f["key_themes"][0]
            }
            for i, f in enumerate(files)
        ]
        
        start_time = time.time()
        references = self.generator.generate_cross_references(files, sequence)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Performance assertions
        self.assertLess(
            generation_time,
            0.5,  # Should generate references in under 0.5 seconds
            f"Cross-reference generation took too long: {generation_time:.2f}s"
        )
        
        # Quality assertions
        self.assertTrue(len(references) > 0)
        self.assertTrue(all(
            isinstance(ref["strength"], (int, float))
            for ref in references
        ))

    def test_customization_performance(self):
        """Test strategy customization performance."""
        files = self._generate_test_files(6)  # Test with 6 files
        project_analysis = {
            "project_theme": "Customization Test",
            "source_files": files
        }
        
        customization = {
            "excluded_themes": ["security"],
            "preferred_sequence": [f"file{i}" for i in range(1, 7)],
            "audience_preference": "technical"
        }
        
        start_time = time.time()
        strategy = self.generator.generate_optimal_strategy(
            project_analysis,
            customization
        )
        end_time = time.time()
        
        customization_time = end_time - start_time
        
        # Performance assertions
        self.assertLess(
            customization_time,
            1.0,  # Should customize in under 1 second
            f"Strategy customization took too long: {customization_time:.2f}s"
        )
        
        # Quality assertions
        self.assertTrue(strategy["customization_applied"])
        self.assertNotIn("security", strategy["content_themes"])
        self.assertEqual(
            strategy["recommended_sequence"][0]["file_id"],
            "file1"
        )

if __name__ == '__main__':
    unittest.main() 