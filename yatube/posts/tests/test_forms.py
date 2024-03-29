import shutil
import tempfile

from django import forms
from http import HTTPStatus
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User, Comment

USER = 'user'
USER2 = 'another'
INDEX_URL = reverse('posts:index')
CREATE = reverse('posts:post_create')
PROFILE = reverse('posts:profile', args=[USER])
LOGIN_URL = reverse('login')
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='first',
            description='описание',
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username=USER)
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.another = User.objects.create_user(username=USER2)
        cls.another_client = Client()
        cls.another_client.force_login(cls.another)
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.author,
            text='Тестовый текст',
            image=cls.image
        )
        cls.group_2 = Group.objects.create(
            title='Заголовок_2',
            slug='second',
            description='описание_2',
        )
        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.group.id])
        cls.POST_DETAL = reverse('posts:post_detail', args=[cls.post.id])
        cls.COMMET_URL = reverse('posts:add_comment', args=[cls.post.id])
        cls.REDIRECT_COMMENT = f'{LOGIN_URL}?next={cls.COMMET_URL}'
        cls.REDIRECT_EDIT = f'{LOGIN_URL}?next={cls.POST_EDIT}'

    def test_create_post(self):
        """Тест создания новой записи"""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст',
            'group': self.group.id,
            'image': uploaded
        }
        posts = set(Post.objects.all())
        response = self.authorized_client.post(
            CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Post.objects.count(), post_count + 1)
        posts = set(Post.objects.all()) - posts
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(
            post.image.name.split('/')[-1], form_data['image'].name)

    def test_post_create_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        response = [
            CREATE,
            self.POST_EDIT,
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for urls in response:
            response = self.authorized_client.get(urls)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    self.assertIsInstance(
                        response.context['form'].fields[value], expected)

    def test_edit_post(self):
        """Тест изминения id после редактирования"""
        post = self.post
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': self.post.text,
            'group': self.group_2.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            self.POST_EDIT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAL)
        post = response.context['post']
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(
            post.image.name.split('/')[-1], form_data['image'].name)

    def test_add_comment(self):
        """Тест добавления комментария к посту"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'комментарий'
        }
        comments = set(Comment.objects.all())
        response = self.authorized_client.post(
            self.COMMET_URL,
            data=form_data,
            follow=True
        )
        comments = set(Comment.objects.all()) - comments
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, self.POST_DETAL)
        self.assertEqual(self.post.comments.count(), comment_count + 1)
        self.assertEqual(len(comments), 1)
        comment = comments.pop()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(self.post, comment.post)
        self.assertEqual(self.author, comment.author)

    def test_add_comment_not_login_user(self):
        """Тест создания комментария только авторизированным пользователем"""
        Comment.objects.all().delete()
        form_data = {
            'text': 'комментарий'
        }
        response = self.guest_client.post(
            self.COMMET_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.REDIRECT_COMMENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_post_edit_guest_another(self):
        """Тест анонима, не-автора отредактировать пост"""
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        clients = {
            self.guest_client: self.REDIRECT_EDIT,
            self.another_client: self.POST_DETAL,
        }
        form_data = {
            'text': 'Попытка отредактировать',
            'group': self.group.id,
            'image': uploaded
        }
        for client, urls in clients.items():
            with self.subTest(user=client, urls=urls):
                response = client.post(
                    self.POST_EDIT, data=form_data, follow=True
                )
                post = Post.objects.get(id=self.post.id)
                self.assertRedirects(response, urls)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)
