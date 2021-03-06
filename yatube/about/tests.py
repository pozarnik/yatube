from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse


class AboutURLViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_available_all_users(self):
        """Страницы приложения about доступны по данным URL-адресам."""
        pages = (
            '/about/author/',
            '/about/tech/',
        )
        for page in pages:
            with self.subTest(url=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_views_reverse_name_uses_correct_template(self):
        """View функции приложения about используются соответствующий шаблон."""
        templates_url_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
