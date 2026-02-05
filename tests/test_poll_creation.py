import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())
from app import app
import jdatetime

class TestPollCreation(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        app.config['WTF_CSRF_ENABLED'] = False

        # Mock admin login
        with self.app.session_transaction() as sess:
            sess['admin_authenticated'] = True

    @patch('app.poll_manager')
    def test_create_poll_success_hyphen(self, mock_pm):
        """Test creating poll with YYYY-MM-DD dates"""
        mock_pm.create_poll.return_value = (True, "Success", MagicMock())

        data = {
            'title': 'Test Poll',
            'description': 'Description',
            'start_date': '1403-01-01',
            'end_date': '1403-01-10',
            'options[]': ['Op1', 'Op2']
        }
        response = self.app.post('/admin/create-poll', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify call args
        # Expected Gregorian: 1403-01-01 -> 2024-03-20
        # 1403-01-10 -> 2024-03-29

        args, kwargs = mock_pm.create_poll.call_args
        self.assertIn('2024-03-20 00:00:00', kwargs['start_time'])
        self.assertIn('2024-03-29 23:59:59', kwargs['end_time'])

    @patch('app.poll_manager')
    def test_create_poll_success_slash(self, mock_pm):
        """Test creating poll with YYYY/MM/DD dates"""
        mock_pm.create_poll.return_value = (True, "Success", MagicMock())

        data = {
            'title': 'Test Poll Slash',
            'description': 'Description',
            'start_date': '1403/02/01',
            'end_date': '1403/02/10',
            'options[]': ['Op1', 'Op2']
        }
        response = self.app.post('/admin/create-poll', data=data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verify call args
        # 1403/02/01 -> 2024-04-20
        # 1403/02/10 -> 2024-04-29

        args, kwargs = mock_pm.create_poll.call_args
        self.assertIn('2024-04-20 00:00:00', kwargs['start_time'])
        self.assertIn('2024-04-29 23:59:59', kwargs['end_time'])

if __name__ == '__main__':
    unittest.main()
