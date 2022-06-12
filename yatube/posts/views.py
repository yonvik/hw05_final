from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import PAGE_SIZE
from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def page_paginator(queryset, request):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get('page'))


@cache_page(60 * 20)
def index(request):
    page_obj = page_paginator(Post.objects.all(), request)
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': page_paginator(group.posts.all(), request),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and request.user != author and (
        Follow.objects.filter(user=request.user, author=author))
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': page_paginator(author.posts.all(), request),
        'following': following
    })


def post_detail(request, post_id):
    return render(request, 'posts/post_detail.html', {
        'post': get_object_or_404(Post, pk=post_id),
        'form': CommentForm(request.POST or None),
    })


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect(
            'posts:post_detail',
            post_id
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        post = form.save()
        return redirect(
            'posts:post_detail',
            post_id
        )
    return render(
        request,
        'posts/create_post.html',
        {'form': form,
         'is_edit': True
         }
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following = Post.objects.filter(author__following__user=request.user)
    return render(request, 'posts/follow.html',
                  {'page_obj': page_paginator(following, request)})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    ).delete()
    return redirect('posts:follow_index')
