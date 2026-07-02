import unittest
from loop_wizard.commands.picker import get_subsequence_score, match_pattern

class TestPicker(unittest.TestCase):
    
    def test_subsequence_score(self):
        # Exact match
        self.assertEqual(get_subsequence_score("scan", "scan"), 20.0)
        
        # Substring match vs Subsequence match
        substring_score = get_subsequence_score("scan", "security-scan")
        subseq_score = get_subsequence_score("scan", "stale-branch-janitor")
        
        self.assertGreater(substring_score, 0.0)
        self.assertGreater(subseq_score, 0.0)
        self.assertGreater(substring_score, subseq_score) # Substring should score higher
        
        # No match
        self.assertEqual(get_subsequence_score("scan", "backend-api"), 0.0)
        
        # Empty query
        self.assertEqual(get_subsequence_score("", "anything"), 1.0)
        
    def test_match_pattern(self):
        known_domains = ["backend", "frontend", "general"]
        
        pattern1 = {"name": "security-scan", "description": "Scan deps", "domain": "backend"}
        pattern2 = {"name": "ui-test-sweeper", "description": "Fix broken selectors", "domain": "frontend"}
        pattern3 = {"name": "stale-branch-janitor", "description": "clean stale branches", "domain": "general"}
        
        # Name match should be > 100
        score_name = match_pattern(pattern1, "scan", known_domains)
        self.assertGreater(score_name, 100.0)
        
        # Description only match
        score_desc = match_pattern(pattern1, "deps", known_domains)
        self.assertGreater(score_desc, 0.0)
        self.assertLess(score_desc, 100.0)
        
        # Domain filtering: match
        score_domain_match = match_pattern(pattern1, "backend/scan", known_domains)
        self.assertGreater(score_domain_match, 0.0)
        
        # Domain filtering: mismatch
        score_domain_mismatch = match_pattern(pattern1, "frontend/scan", known_domains)
        self.assertEqual(score_domain_mismatch, 0.0)
        
        # Non-known domain prefix should be treated as part of query
        score_unknown_prefix = match_pattern(pattern1, "unknown/scan", known_domains)
        self.assertEqual(score_unknown_prefix, 0.0) # because 'unknown/scan' is not in 'security-scan' or its desc

if __name__ == '__main__':
    unittest.main()
