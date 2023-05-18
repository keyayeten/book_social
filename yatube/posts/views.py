from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page
from .models import Post, Group, User, Follow
from django.shortcuts import get_object_or_404
from .forms import PostForm, CommentForm
from .utils import create_pagination
from django.contrib.auth.decorators import login_required

NUM_OF_POSTS = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.all()
    page_obj = create_pagination(request, posts, NUM_OF_POSTS)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):

    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()

    page_obj = create_pagination(request, posts, NUM_OF_POSTS)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    user_id = user.id
    posts = Post.objects.filter(author=user_id)

    page_obj = create_pagination(request, posts, NUM_OF_POSTS)
    follow = True
    if request.user.is_authenticated and request.user.id != user_id:
        follow = Follow.objects.filter(user=request.user.id,
                                       author=user_id).exists()
    context = {
        'author': user,
        'name': username,
        'page_obj': page_obj,
        'post_count': len(posts),
        'id': user_id,
        'following': follow,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    username = Post.objects.get(pk=post_id).author
    post = get_object_or_404(Post,
                             pk=post_id,
                             author__username=username
                             )
    user = post.author
    user_posts = user.posts.all()

    form = CommentForm(request.POST or None)
    comments = post.comments.all()

    context = {
        'post': post,
        'count': user_posts.count(),
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    username = get_object_or_404(User, pk=request.user.id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect(f'/profile/{username}/')

    return render(request, 'posts/create_post.html', {'form': form,
                                                      'author': username,
                                                      'is_edit': False
                                                      })


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    if request.user.id != post.author.id:
        return redirect(f'/posts/{post_id}/')
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    username = post.author.get_full_name()
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect(f'/posts/{post_id}/')

    return render(request, 'posts/create_post.html', {'form': form,
                                                      'author': username,
                                                      'is_edit': True
                                                      })


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
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = create_pagination(request, post_list, NUM_OF_POSTS)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author and not (Follow.
                                       objects.
                                       filter(
            user=request.user.id,
            author=author.id).exists()):
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
