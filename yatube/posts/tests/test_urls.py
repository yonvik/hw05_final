from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User

INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_list', args=['slug'])
USER = 'test_user'
PROFILE_URL = reverse('posts:profile', args=[USER])
LOGIN_URL = reverse('login')
REDIRECT_LOGIN = f'{LOGIN_URL}?next={CREATE_URL}'
PROFILE_FOLLOW = reverse('posts:profile_follow', args=[USER])
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', args=[USER])


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
        cls.guest = Client()
        cls.author = Client()
        cls.another = Client()
        cls.another_author = User.objects.create_user(username='test_user2')
        cls.DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.EDIT_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.REDIRECT_EDIT = f'{LOGIN_URL}?next={cls.EDIT_URL}'
        cls.author.force_login(cls.post.author)
        cls.another.force_login(cls.another_author)
        cls.REDIRECT_FOLLOW = f'{LOGIN_URL}?next={PROFILE_FOLLOW}'
        cls.REDIRECT_UNFOLLOW = f'{LOGIN_URL}?next={PROFILE_UNFOLLOW}'
        cls.REDIRECT_LOGIN = f'{LOGIN_URL}?next={FOLLOW_URL}'

    def setUp(self):
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
            [FOLLOW_URL, self.guest, 302],
            [FOLLOW_URL, self.author, 200],
            [PROFILE_FOLLOW, self.guest, 302],
            [PROFILE_FOLLOW, self.author, 302],
            [PROFILE_FOLLOW, self.another, 302],
            [PROFILE_UNFOLLOW, self.guest, 302],
            [PROFILE_UNFOLLOW, self.author, 404],
            [PROFILE_UNFOLLOW, self.another, 302],
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
            FOLLOW_URL: 'posts/follow.html'
        }
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author.get(url), template)

    def test_redirect(self):
        """Тесты перенаправлений"""
        urls = [
            [CREATE_URL, self.client, REDIRECT_LOGIN],
            [self.EDIT_URL, self.client, self.REDIRECT_EDIT],
            [self.EDIT_URL, self.another, self.DETAIL_URL],
            [PROFILE_FOLLOW, self.client, self.REDIRECT_FOLLOW],
            [PROFILE_FOLLOW, self.author, FOLLOW_URL],
            [PROFILE_FOLLOW, self.another, FOLLOW_URL],
            [PROFILE_UNFOLLOW, self.client, self.REDIRECT_UNFOLLOW],
            [PROFILE_UNFOLLOW, self.another, FOLLOW_URL],
            [FOLLOW_URL, self.client, self.REDIRECT_LOGIN]
        ]
        for url, client, reverses in urls:
            with self.subTest(url=url, client=client):
                self.assertRedirects(client.get(url), reverses)
