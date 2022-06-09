from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User

INDEX_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_list', args=['slug'])
PAGE_404 = reverse('posts:error_404')
PAGE_403 = reverse('posts:error_403')
PAGE_500 = reverse('posts:error_500')
USER = 'test_user'
PROFILE_URL = reverse('posts:profile', args=[USER])
LOGIN_URL = reverse('login')
REDIRECT_LOGIN = f'{LOGIN_URL}?next={CREATE_URL}'


class StaticURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username=USER),
            text='Тестовая запись',
        )
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='slug',
            description='Описание'
        )
        cls.another_author = User.objects.create_user(username='test_user2')
        cls.DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.REDIRECT_EDIT = f'{LOGIN_URL}?next={cls.EDIT_URL}'

    def setUp(self):
        self.guest = Client()
        self.author = Client()
        self.author.force_login(self.post.author)
        self.another = Client()
        self.another.force_login(self.another_author)
        cache.clear()

    def test_pages_for_guests(self):
        """Тест страниц доступных всем"""
        urls = [
            [INDEX_URL, self.guest, 200],
            [GROUP_URL, self.guest, 200],
            [CREATE_URL, self.guest, 302],
            [CREATE_URL, self.author, 200],
            [PROFILE_URL, self.client, 200],
            [self.DETAIL_URL, self.guest, 200],
            [self.EDIT_URL, self.guest, 302],
            [self.EDIT_URL, self.author, 200],
            [self.EDIT_URL, self.another, 302],
            [PAGE_404, self.guest, 404],
            [PAGE_500, self.guest, 500]
        ]
        for url, client, status in urls:
            with self.subTest(url=url, client=client):
                self.assertEqual((client).get(url).status_code, status)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            INDEX_URL: 'posts/index.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.DETAIL_URL: 'posts/post_detail.html',
            self.EDIT_URL: 'posts/create_post.html',
            CREATE_URL: 'posts/create_post.html',
            PAGE_404: 'core/404.html',
            PAGE_403: 'core/403csrf.html',
            PAGE_500: 'core/500.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertTemplateUsed(
                    self.author.get(reverse_name), template)

    def test_redirect(self):
        """Тесты перенаправлений"""
        urls = [
            [CREATE_URL, self.client, REDIRECT_LOGIN],
            [self.EDIT_URL, self.client, self.REDIRECT_EDIT],
            [self.EDIT_URL, self.another, self.DETAIL_URL]
        ]
        for url, client, reverses in urls:
            with self.subTest(url=url, client=client):
                self.assertRedirects(client.get(url), reverses)
