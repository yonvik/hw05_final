import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Post, Group, User, Follow
from yatube.settings import PAGE_SIZE

INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
SLUG = 'test_slug_post'
GROUP_SLUG = reverse('posts:group_list', args=[SLUG])
SLUG2 = 'test_slug'
GROUP_SLUG2 = reverse('posts:group_list', args=['test_slug'])
USER = 'test_user'
USER2 = 'test_follower'
PROFILE_URL = reverse('posts:profile', args=[USER])
PROFILE_FOLLOW = reverse('posts:profile_follow', args=[USER2])
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', args=[USER2])
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
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username=USER)
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись',
            group=Group.objects.create(
                title='Заголовок',
                slug=SLUG,
                description='Описание'),
            image=cls.image
        )

        cls.group = Group.objects.create(
            title='Заголовок',
            slug=SLUG2,
            description='Описание'
        )
        cls.DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.post.author)
        cls.follower = User.objects.create(username=USER2)
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.author)
        cls.PROFILE_FOLLOW = reverse('posts:profile_follow',
                                     args=[USER2])

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()

    def test_pages_context(self):
        """Шаблоны сформированы с правильным контекстом"""
        urls = {
            INDEX_URL: 'page_obj',
            GROUP_SLUG: 'page_obj',
            PROFILE_URL: 'page_obj',
            self.DETAIL_URL: 'post',
            FOLLOW_URL: 'page_obj',
        }
        Follow.objects.create(user=self.author, author=self.author)
        for url, context in urls.items():
            posts = self.authorized_client.get(url).context[context]
            with self.subTest(url=url):
                if context == 'page_obj':
                    self.assertEqual(len(posts), 1)
                    post = posts[0]
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.image, self.post.image)

    def test_group_pages_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_SLUG2)
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.id, self.group.id)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(PROFILE_URL)
        profile = response.context['author']
        self.assertEqual(profile, self.author)

    def test_post_not_in_other_group(self):
        """Пост не попал в другую группу"""
        urls = {
            GROUP_SLUG2: 'page_obj',
            FOLLOW_URL: 'page_obj',
        }
        for url, context in urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertNotIn(self.post, response.context[context])

    def test_cache_index_page(self):
        """Проверка работы кэша"""
        post = Post.objects.create(
            text='Тестовый текст',
            author=self.author)
        content_add = self.authorized_client.get(INDEX_URL).content
        post.delete()
        content_delete = self.authorized_client.get(INDEX_URL).content
        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.authorized_client.get(INDEX_URL).content
        self.assertNotEqual(content_add, content_cache_clear)

    def test_first_page_contains_ten_posts(self):
        Post.objects.bulk_create(Post(
            text=f'Тестовый пост {i}',
            author=self.author,
            group=self.group
        ) for i in range(PAGE_SIZE + 3))
        """Тестирование пагинатора"""
        list_urls = [
            [INDEX_URL, PAGE_SIZE],
            [INDEX_URL + '?page=2', 4],
            [GROUP_SLUG2, PAGE_SIZE],
            [GROUP_SLUG2 + '?page=2', 3],
            [PROFILE_URL, PAGE_SIZE],
            [PROFILE_URL + '?page=2', 4],
            [FOLLOW_URL, PAGE_SIZE],
            [FOLLOW_URL + '?page=2', 4]
        ]
        Follow.objects.create(user=self.author, author=self.author)
        for page, urls in list_urls:
            with self.subTest(page=page):
                self.assertEqual(len(
                    self.authorized_client.get(page).context.get(
                        'page_obj').object_list), urls)

    def test_follow_on_authors(self):
        """Тест записей у тех кто подписан."""
        Follow.objects.all().delete()
        self.authorized_client.get(PROFILE_FOLLOW)
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow_on_user(self):
        """Тест отписки от пользователя."""
        Follow.objects.create(
            user=self.author,
            author=self.follower)
        self.authorized_client.get(PROFILE_UNFOLLOW)
        self.assertEqual(Follow.objects.count(), 0)
