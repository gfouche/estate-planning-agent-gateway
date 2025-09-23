"""
Unit test to verify environment variable requirements in .env file
"""
import os
import unittest
from pathlib import Path

from settings import Settings

class TestEnvironmentVariables(unittest.TestCase):
    """Test case for .env file validation"""
    
    def test_env_file_has_required_parameters(self):
        """Test to ensure .env file contains all required parameters"""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / '.env'
        
        # Check if .env file exists
        self.assertTrue(env_path.exists(), f".env file not found at {env_path}")
        
        # List of required environment variables
        required_vars = [
            "AWS_REGION",
            "COGNITO_USER_POOL_ID",
            "COGNITO_CLIENT_ID", 
            "COGNITO_CLIENT_SECRET",
            "GATEWAY_URL",
            "M2M_PROVIDER_NAME"
        ]
        
        # Read the .env file
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Check for each required variable
        missing_vars = []
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
        
        self.assertEqual(len(missing_vars), 0, 
                        f"Missing required variables in .env file: {', '.join(missing_vars)}")


if __name__ == '__main__':
    unittest.main()