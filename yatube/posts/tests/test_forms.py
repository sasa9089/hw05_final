import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client_author = Client()
        cls.author = User.objects.create_user(username='author')
        cls.authorized_client_author.force_login(cls.author)
        cls.no_author = User.objects.create_user(username='auth')
        cls.authorized_client.force_login(cls.no_author)

        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.comment = Comment.objects.create(
            author=cls.author,
            post=cls.post,
            text='Комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_form_create_post(self):
        """При отправке формы, создается запись в базе."""
        post_numb = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Это текст нового поста',
            'group': self.group.id,
            'author': self.no_author,
            'image': uploaded,
        }
        self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_numb + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            author=self.author,
            image='posts/small.gif'
        ).exists())

    def test_posts_forms_edit_post(self):
        """Проверка, редактируется ли пост."""
        form_data = {
            'text': 'Измененный пост',
            'group': self.group.id,
            'author': self.no_author,
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            author=self.post.author,
            pub_date=self.post.pub_date,
            id=self.post.id
        ).exists())

    def test_unauthorized_user_cannot_edit_post(self):
        """
        Проверка : неавторизованный пользователь не может
        отредактировать пост. Корректно происходит перенаправление.
         """
        form_data = {'text': 'Измененный текст'}
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')
        self.assertTrue(Post.objects.filter(
            text=self.post.text,
            group=self.group.id,
            author=self.post.author,
            pub_date=self.post.pub_date,
            id=self.post.id
        ).exists())

    def test_unauthorized_user_cannot_create_post(self):
        """
        Проверка : неавторизованный пользователь не может
         создать пост. Корректно происходит перенаправление.
         """
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response,
                             '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(),
                         post_count)

    def test_authorized_user_cannot_edit_post(self):
        """
        Проверка : авторизованный пользователь, не автор, не может
        отредактировать пост. Корректно происходит перенаправление.
        """
        form_data = {
            'text': 'Измененный пост',
            'group': self.group.id,
            'author': self.author,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertTrue(Post.objects.filter(
            text=self.post.text,
            group=self.post.group,
            author=self.post.author,
            pub_date=self.post.pub_date,
            id=self.post.id
        ).exists())

    def test_group_can_be_omitted(self):
        """
        Проверка : при создании поста группу
        можно не указывать.
        """
        post_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста для проверки',
        }
        response = self.authorized_client_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=None,
            author=self.author
        ).exists())

    def test_authorized_user_can_write_comment(self):
        """
        Проверка : авторизованный пользователь может оставить
        комментарий. Корректно происходит перенаправление.
        """
        comment_count = Comment.objects.count()
        form_data = {
            'text': self.comment.text
        }
        response = self.authorized_client_author.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count+1)
        self.assertTrue(Comment.objects.filter(
            post=self.post,
            author=self.author,
            text=self.comment.text,
        ).exists())

    def test_unauthorized_user_cannot_write_comment(self):
        """
        Проверка: неавторизованный пользователь не может оставить
        комментарий.
        """
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Проверочный комментарий',
        }
        self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        response = self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), comment_count)
