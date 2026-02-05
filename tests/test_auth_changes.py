import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app import app
from utils.auth import VoterDatabase

class TestAuthChanges(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Disable CSRF for testing
        app.config['WTF_CSRF_ENABLED'] = False

        self.voter_db = VoterDatabase('data/voters.csv')

    def test_verify_stage1_success(self):
        """Test verify_stage1 with valid data (Mobile + National Code + Birth Date + Serial)"""
        national_code = "0012345678"
        birth_date = "1370-05-15"
        mobile = "09123456789"
        serial = "123456789A"

        success, message, voter = self.voter_db.verify_stage1(national_code, birth_date, mobile, serial)
        self.assertTrue(success)
        self.assertEqual(voter['full_name'], "علی احمدی")

    def test_verify_stage1_failure_mobile(self):
        """Test verify_stage1 with wrong mobile"""
        national_code = "0012345678"
        birth_date = "1370-05-15"
        mobile = "09000000000" # Wrong
        serial = "123456789A"

        success, message, voter = self.voter_db.verify_stage1(national_code, birth_date, mobile, serial)
        self.assertFalse(success)
        self.assertIn("شماره موبایل", message)

    def test_api_auth_stage1(self):
        """Test API endpoint for Stage 1"""
        payload = {
            "national_code": "0012345678",
            "birth_date": "1370-05-15",
            "mobile": "09123456789",
            "serial_number": "123456789A"
        }

        response = self.app.post('/api/voter/auth/stage1',
                               json=payload,
                               content_type='application/json')

        if response.status_code != 200:
            print(f"API Error: {response.data}")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['mobile'], "09123456789")

    @patch('app.call_videomatch_api')
    def test_biometric_success(self, mock_api):
        """Test Biometric flow (Stage 3)"""
        mock_api.return_value = True
        pass

if __name__ == '__main__':
    unittest.main()
