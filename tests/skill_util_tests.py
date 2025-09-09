# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2025 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import unittest
import tempfile
import shutil
import subprocess


class SkillUtilTests(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures, downloading the test skill repository"""
        cls.test_dir = tempfile.mkdtemp(prefix="skill_util_tests_")

        # Set up setuptools test repository
        cls.setuptools_repo_url = "https://github.com/NeonGeckoCom/skill-caffeinewiz.git"
        cls.setuptools_skill_branch = "0.3.1"
        cls.setuptools_skill_repo_path = os.path.join(cls.test_dir, "skill-caffeinewiz")
        subprocess.run([
            "git", "clone", "--branch", cls.setuptools_skill_branch, "--depth", "1",
            cls.setuptools_repo_url, cls.setuptools_skill_repo_path
        ], check=True, capture_output=True, text=True, timeout=30)
        cls.setup_py_path = os.path.join(cls.setuptools_skill_repo_path, "setup.py")
        
        # Set up poetry test repository
        cls.poetry_repo_url = "https://github.com/OscillateLabsLLC/skill-homeassistant.git"
        cls.poetry_skill_branch = "v0.5.1"
        cls.poetry_skill_repo_path = os.path.join(cls.test_dir, "skill-homeassistant")
        subprocess.run([
            "git", "clone", "--branch", cls.poetry_skill_branch, "--depth", "1",
            cls.poetry_repo_url, cls.poetry_skill_repo_path
        ], check=True, capture_output=True, text=True, timeout=30)
        cls.pyproject_toml_path = os.path.join(cls.poetry_skill_repo_path, "pyproject.toml")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test fixtures"""
        if hasattr(cls, 'test_dir') and os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
    
    def test_get_skill_data_poetry(self):
        """Test extracting skill metadata from pyproject.toml files"""
        from neon_utils.skill_utils import _get_skill_data_poetry
        
        # Test with real skill-homeassistant pyproject.toml file
        self.assertTrue(os.path.exists(self.pyproject_toml_path), 
                       f"pyproject.toml not found at {self.pyproject_toml_path}")
        
        skill_metadata = _get_skill_data_poetry(self.pyproject_toml_path)
        self.assertIsInstance(skill_metadata, dict)
        self.assertEqual(skill_metadata.get("name"), "skill-homeassistant")
        self.assertEqual(skill_metadata.get("package_name"), "skill-homeassistant")
        self.assertEqual(skill_metadata.get("pip_spec"), "skill-homeassistant")
        self.assertEqual(skill_metadata.get("version"), "0.5.1")
        self.assertEqual(skill_metadata.get("license"), "Apache-2.0")
        self.assertIn("Mike Gray", skill_metadata.get("author")[0])
        self.assertEqual(skill_metadata.get("title"), "skill-homeassistant")
        self.assertIsInstance(skill_metadata.get("tags"), list)
        self.assertIn("neon", skill_metadata.get("tags"))
        self.assertIsInstance(skill_metadata.get("requirements", {}).get("python"), list)
        self.assertGreaterEqual(len(skill_metadata['requirements']['python']), 1)
        
        # Test FileNotFoundError for non-existent file
        with self.assertRaises(FileNotFoundError):
            _get_skill_data_poetry("non_existent_file.toml")

    def test_get_skill_data_setuptools(self):
        from neon_utils.skill_utils import _get_skill_data_setuptools
        # Test with real skill-caffeinewiz setup.py file
        self.assertTrue(os.path.exists(self.setup_py_path), 
                       f"setup.py not found at {self.setup_py_path}")
        
        skill_metadata = _get_skill_data_setuptools(self.setup_py_path)
        self.assertIsInstance(skill_metadata, dict)
        self.assertEqual(skill_metadata.get("authorname"), "NeonGeckoCom")
        self.assertEqual(skill_metadata.get("skillname"), "skill-caffeinewiz")
        self.assertEqual(skill_metadata['package_name'], 'neon-skill-caffeinewiz')
        self.assertEqual(skill_metadata['pip_spec'], 'neon-skill-caffeinewiz')
        self.assertIn("BSD-3", skill_metadata['license'])
        self.assertIsInstance(skill_metadata['author'], str)
        self.assertEqual(skill_metadata['version'], '0.3.1')
        self.assertIsInstance(skill_metadata['url'], str)
        self.assertEqual(skill_metadata['name'], 'neon-skill-caffeinewiz')
        self.assertEqual(skill_metadata['title'], 'neon-skill-caffeinewiz')
        self.assertIn('Neongecko', skill_metadata['credits'])
        self.assertIsInstance(skill_metadata['requirements']['python'], list)
        self.assertGreaterEqual(len(skill_metadata['requirements']['python']), 1)
        
        # Test FileNotFoundError for non-existent file
        with self.assertRaises(FileNotFoundError):
            _get_skill_data_setuptools("non_existent_setup.py")

    def test_get_skill_data_readme(self):
        """Test extracting skill metadata from README.md files"""
        # TODO: Implement test for valid README.md file
        pass
        
        # TODO: Test FileNotFoundError for non-existent file
        # with self.assertRaises(FileNotFoundError):
        #     _get_skill_data_readme("non_existent_readme.md")
        
        # TODO: Test parsing of markdown headers and content
        # TODO: Test extraction of skill description and examples
        # TODO: Test handling of various README formats


if __name__ == '__main__':
    unittest.main()
