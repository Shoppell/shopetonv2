from django.forms import modelformset_factory, formset_factory
from django.shortcuts import render, redirect
from blog.forms import ShopComment, CommentForm
from shop.forms import Updateshop, ShopCreateForm, ProductCreateForm, Updateproduct, Wishlist, wishliststatus, postform, choice_product
from .models import myshop, Product, wishlist, postinfo, Product_Choice
from blog.models import SupCategory, Category, Comment, Comment_shop
from user_auth.models import User
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from shop.decorators import just_owner, not_owner
import math
from PIL import Image
from persian_tools import digits
from user_auth.sms import shop_registered, status_changing
from django.http import HttpResponseRedirect
from django.urls import reverse


def all_views_navbar_utils(request):
    wish_op = digits.convert_to_fa(0)
    login = False

    same_context = {
        'wish': wish_op,
        'login': login,
        'scategory': SupCategory.objects.all(),
    }

    if request.user.is_authenticated:
        login = True
        if wishlist.objects.filter(buyer=request.user).filter(paid=False).exists():
            wish_op = wishlist.objects.filter(buyer=request.user).filter(paid=False).__len__()
        else:
            wish_op = 0
        same_context['login'] = login
        wish_op = digits.convert_to_fa(wish_op)
        same_context['wish'] = wish_op

        if request.user.owner:
            owner = True
            me = User.objects.get(mobile=request.user.mobile)
            my_shop = me.shop
            same_context['my_shop'] = my_shop
            same_context['owner'] = owner

    return same_context


def help_video(request):
    context = all_views_navbar_utils(request)
    return render(request, 'blog/help.html', context)

@login_required(login_url='register')
@just_owner
def my_statistics(request):
    my_shop = request.user.shop
    products = my_shop.products.all()
    context = {
        'products': products,
        'shop': my_shop,
    }
    context_same = all_views_navbar_utils(request)
    context.update(context_same)
    return render(request, 'shop/my_statistics.html', context)


@login_required(login_url='register')
@just_owner
def my_products(request):
    my_shop = request.user.shop
    products = my_shop.products.all()
    if request.method == 'POST':
        if 'update' in request.POST:
            pk = request.POST['update']
            return redirect('update_product', pk)
        elif 'delete' in request.POST:
            my_shop = request.user.shop
            pk = request.POST['delete']
            my_shop.products.get(pk=pk).delete()
            return redirect('shop', my_shop.slug)
        elif 'add' in request.POST:
            pk = request.POST['add']
            return redirect('add_product_choice', my_shop.slug, pk)

    context = {
        'products': products,
        'shop': my_shop,
    }
    context_same = all_views_navbar_utils(request)
    context.update(context_same)
    return render(request, 'shop/my_products.html', context)


def all_products(request, slug):
    shop = myshop.objects.get(slug=slug)
    products = shop.products.all()
    context = {
        'shop': shop,
        'products': products,
    }
    context_same = all_views_navbar_utils(request)
    context.update(context_same)

    return render(request, 'shop/all_products.html', context)


def shop(request, slug):
    shop = myshop.objects.get(slug=slug)
    comments = Comment_shop.objects.filter(shop=shop).order_by('-date_posted')
    score = 0
    for i in range(0, len(comments)):
        score += int(comments[i].grade)
    if len(comments) != 0:
        final_score = score/len(comments)
    else:
        final_score = 0
    shop.grade = final_score
    final_score = math.ceil(final_score)
    shop.stars = final_score*'1'
    shop.stars_left = (5-final_score) * '1'
    shop.save()
    products_shop = shop.products.filter().order_by('-date')[0:8]
    rare = shop.products.filter(rare=True)[0:3]
    off = shop.products.filter(most_off=True)[0:3]
    hot = shop.products.filter(hot=True)[0:3]
    shop_m = [shop]
    if request.method == 'POST':
        form = ShopComment(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.feedbacker = request.user
            obj.save()
            obj.shop.set(shop_m)
            obj.save()
            obj.stars = obj.grade * '1'
            obj.save()
            obj.stars_left = (5 - obj.grade) * '1'
            obj.save()
            return redirect('shop',shop.slug)
    else:
        form = ShopComment()

    if request.user.is_anonymous:

        add_comment = False
    else:
        comments_me = comments.filter(feedbacker=request.user)
        j = 0
        for i in comments_me:
            j += 1

        if j > 3:
            add_comment = False
        else:
            add_comment = True
    comments = comments[0:10]
    blogs = shop.blogs.all()[0:8]

    ip_address = request.user.ip_address
    if ip_address not in shop.hits.all():
        shop.hits.add(ip_address)

    context = {
        'products': products_shop,
        'add_comment': add_comment,
        'comments': comments,
        'shop': shop,
        'form': form,
        'rare': rare,
        'hot': hot,
        'blog': blogs,
        'off': off,
    }
    if request.user.is_authenticated:
        if request.user.shop == shop:
            context['own_shop'] = True
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'shop/shop.html', context)


@login_required(login_url='register')
@just_owner
def update_shop(request):
    me = User.objects.get(mobile=request.user.mobile)
    my_shop = me.shop
    shop = my_shop
    if request.method == 'POST':
        form = Updateshop(request.POST, request.FILES, instance=shop)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            return redirect('shop', shop.slug)
    else:
        form = Updateshop(instance=shop)
    context = {
            'my_shop': my_shop,
            'shop': shop,
            'form': form,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'shop/update_shop.html', context)


@login_required(login_url='register')
@not_owner
def add_shop(request):
    if request.method == 'POST':
        form1 = ShopCreateForm(request.POST, request.FILES)
        user = request.user
        if form1.is_valid():
            obj = form1.save(commit=False)
            shop_slug = obj.slug
            obj.save()
            shop_o = myshop.objects.get(slug=shop_slug)
            user.shop = shop_o
            user.owner = True
            user.save()
            shop_registered(request.user.mobile, 'shopeton.ir/update_shop/', 'shopeton.ir/addproduct/')
            return redirect('home')
    else:
        form1 = ShopCreateForm()
    context = {
        'form': form1,
    }
    context_same = all_views_navbar_utils(request)
    context.update(context_same)
    return render(request, 'shop/add_shop.html', context)


@login_required(login_url='register')
@just_owner
def update_product(request, pk):
    me = User.objects.get(mobile=request.user.mobile)
    my_shop = me.shop
    shop = my_shop
    products = shop.products.all()
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return HttpResponseRedirect(reverse('add_product'))
    if request.method == 'POST':
        form = Updateproduct(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product-details', shop.slug, pk)
    else:
        form = Updateproduct(instance=product)

    context = {
            'shop': shop,
            'form': form,
            'products': products,
            'my_shop': my_shop,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'shop/update_product.html', context)


@login_required(login_url='register')
@just_owner
def add_product(request):
    if request.method == 'POST':
        form = ProductCreateForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            request.user.shop.products.add(obj)
            return redirect('shop', request.user.shop.slug)
    else:
        form = ProductCreateForm()
    context = {
        'form': form,
        'shop': request.user.shop,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'shop/add_product.html', context)


@login_required(login_url='register')
@just_owner
def add_product_choice(request, slug, pk):
    product = Product.objects.get(pk=pk)
    if product in request.user.shop.products.all():
        pass
    else:
        return HttpResponseRedirect(reverse('add_product'))

    if request.method == 'POST':
        form = choice_product(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            Product.objects.get(pk=pk).product_choice.add(obj)
            return redirect('product-details', slug, pk)
    else:
        form = choice_product()
    context = {
        'form': form,
        'shop': request.user.shop,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'shop/add_choice_product.html', context)


def product_details(request, slug, pk):
    shop = myshop.objects.get(slug=slug)
    own = False
    if request.user.is_authenticated:
        if shop == request.user.shop:
            own = True
    product_details = shop.products.get(pk=pk)
    comments = Comment.objects.filter(products=product_details).order_by('-date_posted')
    score =0
    for i in range(0, len(comments)):
        score += int(comments[i].grade)
    if len(comments) != 0:
        final_score = score/len(comments)
    else:
        final_score = 0
    form2 = Wishlist()
    product_one = Product.objects.get(pk=pk)
    product_details.star_rate = final_score
    final_score = math.ceil(final_score)
    product_details.stars = final_score*'1'
    product_details.stars_left = (5-final_score) * '1'
    product_details.save()
    products = [product_details]
    if request.method == 'POST':
        if request.POST['action'] == 'comment':
            form1 = CommentForm(request.POST)
            form2 = form_base(request.POST, queryset=product_one.product_choice.all)

            print(form2)
            print(Product.objects.get(pk=pk).product_choice.all)
            if form1.is_valid():
                obj = form1.save(commit=False)
                obj.feedbacker = request.user
                obj.save()
                obj.products.set(products)
                obj.save()
                obj.stars = obj.grade*'1'
                obj.save()
                obj.stars_left = (5-obj.grade) * '1'
                obj.save()
                return redirect('product-details', slug, pk)
        elif request.POST['action'] == 'add_cart':
            form2 = modelformset_factory(wishlist, extra=-len(wishlist.objects.all()), fields=('product_choice',))
            form2.form.base_fields['product_choice'].queryset = product_one.product_choice.exclude(count=0)
            if 'form-0-product_choice' in request.POST and request.POST['form-0-product_choice'] != '':
                index_object = Product_Choice.objects.get(pk=int(request.POST['form-0-product_choice']))
                user_wish = wishlist(shop=shop, buyer=request.user, paid=False, product=product_one, product_choice=index_object)
                user_wish.save()
            form1 = CommentForm()

        elif request.POST['action'] == 'change':
            return redirect('update_product', pk)
        elif request.POST['action'] == 'delete':
            my_shop = request.user.shop
            form1 = CommentForm()
            form2 = modelformset_factory(wishlist, extra=-len(wishlist.objects.all()) + 1, fields=('product_choice',))
            form2.form.base_fields['product_choice'].queryset = product_one.product_choice.exclude(count=0)
            if my_shop.pk == shop.pk:
                my_shop.products.get(pk=pk).delete()
                return redirect('shop', slug)
        elif request.POST['action'] == 'add':
            return redirect('add_product_choice', shop.slug, pk)
    else:
        form2 = modelformset_factory(wishlist, extra=-len(wishlist.objects.all())+1, fields=('product_choice',))
        form2.form.base_fields['product_choice'].queryset = product_one.product_choice.exclude(count=0)
        form1 = CommentForm()

    if len(product_one.product_choice.exclude(count=0))==0:
        danger_sale = True
    else:
        danger_sale = False

    score_list = [None] * math.ceil(final_score)
    left_list = [None] * (5-math.ceil(final_score))
    final_score = math.ceil(final_score)
    ctg = Category.objects.get(name=product_details.category)
    related_products = Product.objects.filter(category=ctg)[0:4]

    if request.user.is_anonymous:

        add_comment = False
    else:
        comments_me = comments.filter(feedbacker=request.user)
        j=0
        for i in comments_me:
            j+=1

        if j>3:
            add_comment = False
        else:
            add_comment = True
    num_photos = 0
    if product_details.photo_3:
        num_photos += 1
    if product_details.photo_4:
        num_photos += 1
    if product_details.photo_5:
        num_photos += 1
    if product_details.photo_6:
        num_photos += 1
    any = True

    ip_address = request.user.ip_address
    if ip_address not in product_details.hits.all():
        product_details.hits.add(ip_address)

    context = {
                'danger_sale': danger_sale,
                'own': own,
                'any': any,
                'now': timezone.now,
                'num_photos': num_photos,
                'product': product_details,
                'related_products': related_products,
                'comments': comments,
                'form': form1,
                'form2': form2,
                'final_score': final_score,
                'score_list': score_list,
                'left_list': left_list,
                'shop': shop,
                'add_comment': add_comment,
        
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)

    return render(request, 'shop/product-details.html', context)


@login_required(login_url='register')
def cart(request):
    wishlist_p = 0
    shop = myshop.objects.all()
    if request.method == "POST":
        pk = request.POST['action']
        wishlist_o = wishlist.objects.filter(pk=pk)
        wishlist_o.delete()
    if request.user.is_anonymous:
        context = {
        }
    else:
        wishlist_all = wishlist.objects.filter(buyer=request.user).filter(paid=False)
        all, off, op = 0, 0, 0
        for i in wishlist_all:
            wishlist_p += 1
            off += i.product.price * i.product.off/100
            op += i.product.price
  
        off = int(off)
        all_all = op-off
     
        context = {
            'off': f"{off:,}",
            'all_all': f"{all_all:,}",
            'all_price': f"{op:,}",
            'wish_list': wishlist_p,
            'wish_all': wishlist_all,
        }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'blog/cart.html', context)


@login_required(login_url='register')
def bought(request):
    wishlist_all = wishlist.objects.filter(buyer=request.user).filter(paid=True).order_by('-created')
    context = {
        'buy': wishlist_all,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'blog/bought.html', context)
    
    
@login_required(login_url='register')
@just_owner
def sold(request):
    my_shop = request.user.shop
    wish_sold = wishlist.objects.filter(shop=my_shop).filter(paid=True).order_by('-created')
    context = {
        'sold': wish_sold,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'blog/sold.html', context)


@login_required(login_url='register')
@just_owner
def sold_detail(request, pk):
    my_shop = request.user.shop
    wish_sold = wishlist.objects.filter(shop=my_shop)
    wish_sold = wish_sold.get(pk=pk)
    if request.method == 'POST':
        form = wishliststatus(request.POST, instance=wish_sold)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            status_changing(request.user.mobile, obj.status)
            return redirect('sold-detail', pk)
    else:
        form = wishliststatus(instance=wish_sold)
    context = {
        'sold': wish_sold,
        'form': form,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'blog/sold_detail.html', context)
    
    
@login_required(login_url='register')
def post_info(request):
    wish_me = wishlist.objects.filter(buyer=request.user).filter(paid=False)
    post_m = postinfo.objects.filter(user=request.user).order_by('-time_add').first()
    if request.method == 'POST':
        form = postform(request.POST, instance=post_m)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            for x in wish_me:
                x.post_info = obj
                x.save()
            return redirect('go-to-shop')
    else:
        form = postform(instance=post_m)
    context = {
        'form': form,
    }
    context_sample = all_views_navbar_utils(request)
    context.update(context_sample)
    return render(request, 'blog/post_info.html', context)


def page_404(request, exception):
    return render(request, '404.html', status=404)


def page_403(request, exception):
    return render(request, '403.html', status=403)


def page_500(request, exception):
    return render(request, '500.html', status=500)


def page_400(request, exception):
    return render(request, '400.html', status=400)