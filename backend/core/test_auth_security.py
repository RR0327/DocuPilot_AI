from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APIClient
from .models import Document, AuthenticationFailure
import json

class SessionSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="session-owner", password="LongSecureTestPassword2026!")
        self.other = get_user_model().objects.create_user(username="session-other", password="LongSecureTestPassword2026!")
        self.document = Document.objects.create(owner=self.user, title="private")

    def _csrf_client(self):
        client=Client(enforce_csrf_checks=True)
        client.get('/api/auth/csrf/')
        return client

    def _login(self,client,username='session-owner',password='LongSecureTestPassword2026!'):
        token=client.cookies['csrftoken'].value
        return client.post('/api/auth/login/',data=json.dumps({'username':username,'password':password}),content_type='application/json',HTTP_X_CSRFTOKEN=token)

    def test_csrf_login_logout_and_owner_scope(self):
        client=self._csrf_client()
        denied=client.post('/api/auth/login/', data='{}', content_type='application/json')
        self.assertEqual(denied.status_code,403)
        self.assertEqual(self._login(client).status_code,200)
        self.assertEqual(client.get('/api/auth/me/').status_code,200)
        self.assertEqual(client.get(f'/api/documents/{self.document.id}/').status_code,200)
        self.assertEqual(client.post('/api/auth/logout/',HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value).status_code,200)
        self.assertIn(client.get(f'/api/documents/{self.document.id}/').status_code,(401,403))

    def test_cross_user_resource_access_is_hidden(self):
        c=self._csrf_client()
        self.assertEqual(self._login(c,username='session-other').status_code,200)
        self.assertEqual(c.get(f'/api/documents/{self.document.id}/').status_code,404)
        self.assertEqual(c.get(f'/api/documents/{self.document.id}/private-pdf/').status_code,404)
        self.assertEqual(c.get(f'/api/documents/{self.document.id}/classification-review/').status_code,404)

    @override_settings(DOCUPILOT_LOGIN_FAILURE_LIMIT=3,DOCUPILOT_LOGIN_WINDOW_SECONDS=900)
    def test_invalid_login_is_rate_limited(self):
        c=self._csrf_client()
        for _ in range(3):
            self.assertEqual(self._login(c,password='badpassword').status_code,401)
        last=self._login(c,password='LongSecureTestPassword2026!')
        self.assertEqual(last.status_code,429)
        self.assertIn('Retry-After',last)
        self.assertTrue(AuthenticationFailure.objects.exists())

    def test_no_basic_in_default_configuration(self):
        self.assertNotIn('rest_framework.authentication.BasicAuthentication',settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'])

    @override_settings(DOCUPILOT_SESSION_IDLE_SECONDS=60)
    def test_idle_session_invalidates_private_api_access(self):
        c=self._csrf_client()
        self.assertEqual(self._login(c).status_code,200)
        import time
        session = c.session
        session['docupilot_last_seen'] = int(time.time()) - 180
        session.save()
        self.assertIn(c.get(f'/api/documents/{self.document.id}/').status_code,(401,403))
