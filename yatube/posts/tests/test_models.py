from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Comment, Follow, Group, Post

User = get_user_model()

FIRST_CHARACTERS = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text=('Погода в Вологде сошла с ума'
                  'то неделю -35, то сейчас +5'
                  'и это я на севере живу'),
        )

    def test_post_have_correct_object_name(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        expected_post_str = post.text[:FIRST_CHARACTERS]
        self.assertEqual(expected_post_str, str(post))

    def test_verbose_name_post(self):
        """Проверяем совпадение verbose_name"""
        post = PostModelTest.post
        field_verboses = {
            'author': 'Автор',
            'group': 'Группа',
            'pub_date': 'Дата публикации',
            'text': 'Текст поста',

        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """Проверяем совпадение help_text"""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_group_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = GroupModelTest.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))

    def test_verbose_name_group(self):
        """Проверяем совпадение verbose_name"""
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Название',
            'slug': 'Адрес',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Погода в Вологде сошла с ума'
                  'то неделю -35, то сейчас +5'
                  'и это я на севере живу'),
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text=('Погода в Вологде нормализовалась'
                  'сейчас в среднем -10, -15'
                  'но могло быть и лучше'),
        )

    def test_comment_have_correct_object_names(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        comment = CommentModelTest.comment
        expected_comment_str = comment.text[:FIRST_CHARACTERS]
        self.assertEqual(expected_comment_str, str(comment))

    def test_verbose_name_comment(self):
        """Проверяем совпадение verbose_name"""
        comment = CommentModelTest.comment
        field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Текст комментария',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='author')
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )

    def test_follow_have_correct_object_names(self):
        """Проверяем, что у модели Follow корректно работает __str__."""
        follow = FollowModelTest.follow
        expected_follow_str = f'{self.user} подписан на {self.author}'
        self.assertEqual(expected_follow_str, str(follow))

    def test_verbose_name_follow(self):
        """Проверяем совпадение verbose_name"""
        follow = FollowModelTest.follow
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).verbose_name, expected)
