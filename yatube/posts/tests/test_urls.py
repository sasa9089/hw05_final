from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User

User = get_user_model()


class UrlsViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.user_author = User.objects.create_user(
            username='author')
        cls.another_user = User.objects.create_user(
            username='user',
        )

        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Текст поста',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.another_user)
        self.authorized_client_author.force_login(self.user_author)
        cache.clear()

    def test_available_pages_for_unauthorized_user(self):
        """Доступные страницы для неавторизованного пользователя"""
        field_urls = (
            '/',
            '/group/test-slug/',
            '/profile/user/',
            f'/posts/{self.post.id}/',
        )
        for address in field_urls:
            with self.subTest():
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_available_pages_for_authorized_user(self):
        """Доступные страницы для авторизованного пользователя"""
        field_urls = (
            '/',
            '/group/test-slug/',
            '/profile/user/',
            f'/posts/{self.post.id}/',
            '/create/',
            f'/posts/{self.post.id}/edit/',
            '/follow/',
        )
        for address in field_urls:
            with self.subTest():
                response = self.authorized_client_author.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
            'posts/profile.html': '/profile/user/',
            'posts/create_post.html': '/create/',
            'posts/follow.html': '/follow/'
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        """Проверяем, запрос к несуществующей странице."""
        response = self.guest_client.get('/error/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_redirect_anonymous_on_admin_login(self):
        """
        Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_edit_redirect_anonymous_user_to_login_page(self):
        """
        Страница /edit/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_authorized_user_does_not_access_post_edit_page(self):
        """Авторизованный пользователь, не автор,не имеет
        доступа к странице редактирования поста."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/')
