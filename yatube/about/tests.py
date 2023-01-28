from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTest(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_available_pages(self):
        """Доступные страницы приложения about"""
        field_urls = (
            '/about/author/',
            '/about/tech/',
        )
        for address in field_urls:
            with self.subTest():
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """Проверяем, запрос к несуществующей странице."""
        response = self.guest_client.get('/error/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
