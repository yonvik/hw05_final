from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='Тестовый слаг',
            description='Описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
        )

    def test_post_verbose_name(self):
        field_verboses = {
            'text': 'текст',
            'pub_date': 'дата',
            'author': 'автор',
            'group': 'группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_group_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'Имя страницы',
            'description': 'описание'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text,
                    expected_value)

    def test_models_have_correct_object_names(self):
        """__str__  task - это строчка с содержимым group.title."""
        self.assertEqual(self.group.title, str(self.group))

    def test_models_have_correct_object_names(self):
        """__str__  task - это строчка с содержимым post.text."""
        self.assertEqual(self.post.text[:15], str(self.post))
