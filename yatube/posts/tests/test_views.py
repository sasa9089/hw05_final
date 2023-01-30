import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm
from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.user_author = User.objects.create_user(
            username='author')
        cls.another_user = User.objects.create_user(
            username='user',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='text_post',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.another_user)
        self.authorized_client_author.force_login(self.user_author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        test_index = response.context['page_obj'][0]
        self.assertEqual(test_index, self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}))
        test_group_obj = response.context['page_obj'][0]
        test_group = response.context['group']
        self.assertEqual(test_group, self.group)
        self.assertEqual(test_group_obj, self.post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.post.author}))
        test_profile = response.context['author']
        test_profile_obj = response.context['page_obj'][0]
        self.assertEqual(test_profile, self.user_author)
        self.assertEqual(test_profile_obj, self.post)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        context_post = response.context['post']
        self.assertEqual(context_post, self.post)
        self.assertIn('comments', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_post_create_page_show_correct_context(self):
        """
        Шаблон создания поста post_create сформирован
        с правильным контекстом.
        """
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        is_edit = response.context.get('is_edit')
        self.assertFalse(is_edit)

    def test_create_post_edit_show_correct_context(self):
        """
        Шаблон редактирования поста create_post сформирован
        с правильным контекстом.
        """
        response = self.authorized_client_author.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        is_edit = response.context.get('is_edit')
        self.assertTrue(is_edit)

    def test_checking_creation_post(self):
        """
        Созданный пост отображется на
        страницах index, group_list, profile.
        """
        field_urls = {
            reverse('posts:index'): self.post,
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                self.post,
            reverse('posts:profile', kwargs={'username': self.post.author}):
                self.post,
        }
        for value, expected in field_urls.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_post_another_group(self):
        """
        Пост не попал в группу, для которой
        не был предназначен
        """
        field_urls = {
            reverse(
                "posts:group_list", kwargs={'slug': self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in field_urls.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)


class PaginatorViewsTest(TestCase):

    NUMB_OF_POSTS = 13
    NUMB_POST_FIRST_PAGE = 10
    NUMB_POST_SECOND_PAGE = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.user = User.objects.create_user(username='user')
        cls.authorized_client.force_login(cls.user)
        cache.clear()

        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        for post in range(PaginatorViewsTest.NUMB_OF_POSTS):
            cls.post = Post.objects.create(
                text=f'Текст поста {post}',
                author=cls.author,
                group=cls.group
            )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        urls_paginations = {
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author}),
            reverse('posts:follow_index'),
        }
        for url in urls_paginations:
            with self.subTest(url=url):
                first_page = self.authorized_client.get(url)
                self.assertEqual(len(first_page.context["page_obj"]),
                                 PaginatorViewsTest.NUMB_POST_FIRST_PAGE)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        urls_paginations = {
            reverse('posts:index') + '?page=2',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2',
            reverse('posts:profile',
                    kwargs={'username': self.author}) + '?page=2',
            reverse('posts:follow_index') + '?page=2',
        }
        for url in urls_paginations:
            with self.subTest(url=url):
                second_page = self.authorized_client.get(url)
                self.assertEqual(len(second_page.context["page_obj"]),
                                 PaginatorViewsTest.NUMB_POST_SECOND_PAGE)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='user',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='text_post',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_caching_the_index_page(self):
        """Проверка кэширования главной страницы."""
        post = self.post
        response = self.authorized_client.get(reverse('posts:index'))
        post.delete()
        response_two = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_two.content)
        cache.clear()
        response_three = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, response_three.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='user',
        )
        cls.user_author = User.objects.create_user(
            username='author')

        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Проверочный пост подписки',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)

    def test_authorized_user_subscribe_other_users(self):
        """
        Проверка: авторизованный пользователь может подписываться на
        других пользователей.
        """
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user_author}
        ))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            author__username=self.user_author,
            user__username=self.user,
        ).exists())

    def test_authorized_user_unsubscribe_from_users_he_subscribed(self):
        """
            Проверка: авторизованный пользователь может отписываться от
            пользователей,на которых был подписан.
        """
        Follow.objects.create(author=self.user_author, user=self.user)
        follow_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user_author}
        ))
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(Follow.objects.filter(
            author__username=self.user_author
        ).exists())

    def test_author_new_post_appears_in_feed_those_users_subscribe_to_it(self):
        """
        Проверка: новый пост автора появляется в ленте тех пользователей,
        кто на него подписан.
        """
        post = self.post
        Follow.objects.create(user=self.user, author=self.user_author)
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'])

    def test_new_post_does_not_appear_in_user_feed_not_subscribed_to_it(self):
        """
        Проверка : новый пост автора не появляется в ленте тех
        пользователей, кто на него не подписан.
        """
        post = self.post
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'])
