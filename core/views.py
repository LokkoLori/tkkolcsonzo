from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Q
from django.template.loader import render_to_string
from django.middleware.csrf import get_token
from django.http import HttpResponseBadRequest, HttpResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Item, ItemImage, Loan
from .forms import ItemForm, ItemImageForm, RegisterForm, UserProfileForm

# Items

def item_list(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    items_qs = Item.objects.all().order_by("-created_at")
    if q:
        items_qs = items_qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category:
        items_qs = items_qs.filter(category__iexact=category)

    # items = [i for i in items_qs if i.is_available]
    items = items_qs
    return render(request, "items/list.html", {"items": items, "q": q, "category": category})

@login_required
def my_items(request):
    items = Item.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "items/my_items.html", {"items": items})

@login_required
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            messages.success(request, "Holmi létrehozva.")
            return redirect("core:item_detail", pk=item.pk)
    else:
        form = ItemForm()
    return render(request, "items/form.html", {"form": form})

def _owner_or_403(request, item):
    if request.user != item.owner:
        messages.error(request, "Nincs jogosultság.")
        return False
    return True

@login_required
def item_delete(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        messages.error(request, "Csak a tulajdonos törölheti ezt a holmit.")
        return redirect("core:item_detail", pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Holmi törölve.")
        return redirect("core:my_items")
    return render(request, "items/confirm_delete.html", {"item": item})


def item_detail(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    main_image = item.main_image()
    gallery = item.images.order_by('-is_cover', 'id')  # borító elöl

    # ... a mostani HTMX ág maradhat, de adjuk át ezeket is, ha a galériát rendereljük
    if request.headers.get("HX-Request"):
        frag = request.GET.get("frag")
        if frag == "gallery":
            html = render_to_string("items/_gallery.html", {"item": item}, request=request)
            return HttpResponse(html)
        if frag == "edit":
            form = ItemForm(instance=item)
            html = render_to_string("items/_edit_form.html", {"item": item, "form": form}, request=request)
            return HttpResponse(html)

    form = ItemForm(instance=item) if request.user == item.owner else None
    img_form = ItemImageForm() if request.user == item.owner else None
    return render(request, "items/detail.html", {
        "item": item,
        "form": form,
        "img_form": img_form,
        "main_image": main_image,
        "gallery": gallery,
    })

@login_required
@require_POST
def item_edit_inline(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    if not _owner_or_403(request, item): return redirect("core:item_detail", pk=pk)
    form = ItemForm(request.POST, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Holmi frissítve.")
        resp = HttpResponse(status=204)  # No Content
        resp["HX-Redirect"] = reverse("core:item_detail", kwargs={"pk": item.pk})
        return resp
    # return the form with errors
    html = render_to_string("items/_edit_form.html", {"item": item, "form": form}, request= request)
    return HttpResponseBadRequest(html)

@login_required
@require_POST
def item_image_add_hx(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    if not _owner_or_403(request, item): return redirect("core:item_detail", pk=pk)
    form = ItemImageForm(request.POST, request.FILES)
    if form.is_valid():
        img = form.save(commit=False)
        img.item = item
        if img.is_cover:
            item.images.update(is_cover=False)
        img.save()
        messages.success(request, "Kép feltöltve.")
        html = render_to_string("items/_gallery.html", {"item": item}, request=request)
        return HttpResponse(html)
    html = render_to_string("items/_image_form.html", {"item": item, "form": form}, request=request)
    return HttpResponseBadRequest(html)

@login_required
@require_POST
def item_image_set_cover_hx(request, pk: int, image_id: int):
    item = get_object_or_404(Item, pk=pk)
    if not _owner_or_403(request, item): return redirect("core:item_detail", pk=pk)
    img = get_object_or_404(ItemImage, pk=image_id, item=item)
    item.images.update(is_cover=False)
    img.is_cover = True
    img.save(update_fields=["is_cover"])
    html = render_to_string("items/_gallery.html", {"item": item}, request=request)
    return HttpResponse(html)

@login_required
@require_POST
def item_image_delete_hx(request, pk: int, image_id: int):
    item = get_object_or_404(Item, pk=pk)
    if not _owner_or_403(request, item): return redirect("core:item_detail", pk=pk)
    img = get_object_or_404(ItemImage, pk=image_id, item=item)
    img.delete()
    html = render_to_string("items/_gallery.html", {"item": item}, request=request)
    return HttpResponse(html)

# Loans

@login_required
def my_loans(request):
    loans_as_borrower = Loan.objects.filter(borrower=request.user).order_by("-requested_at")
    loans_as_owner = Loan.objects.filter(item__owner=request.user).order_by("-requested_at")
    return render(request, "loans/my_loans.html", {
        "loans_as_borrower": loans_as_borrower,
        "loans_as_owner": loans_as_owner,
    })

@login_required
def loan_request(request, item_id: int):
    item = get_object_or_404(Item, pk=item_id)
    if item.owner == request.user:
        messages.error(request, "Saját holmit nem kérhetsz kölcsön.")
        return redirect("core:item_detail", pk=item.pk)
    if not item.is_available:
        messages.error(request, "A holmi nem elérhető.")
        return redirect("core:item_detail", pk=item.pk)
    Loan.objects.create(item=item, borrower=request.user)
    messages.success(request, "Kölcsönkérés elküldve.")
    return redirect("core:my_loans")

@login_required
def loan_accept(request, loan_id: int):
    loan = get_object_or_404(Loan, pk=loan_id)
    if not loan.can_accept(request.user):
        messages.error(request, "Nincs jogosultság.")
        return redirect("core:my_loans")
    loan.state = Loan.State.ACCEPTED
    loan.accepted_at = timezone.now()
    loan.save()
    messages.success(request, "Kölcsönkérés elfogadva.")
    return redirect("core:my_loans")

@login_required
def loan_decline(request, loan_id: int):
    loan = get_object_or_404(Loan, pk=loan_id)
    if not loan.can_decline(request.user):
        messages.error(request, "Nincs jogosultság.")
        return redirect("core:my_loans")
    loan.state = Loan.State.DECLINED
    loan.save()
    messages.success(request, "Kölcsönkérés elutasítva.")
    return redirect("core:my_loans")

@login_required
def loan_cancel(request, loan_id: int):
    loan = get_object_or_404(Loan, pk=loan_id)
    if not loan.can_cancel(request.user):
        messages.error(request, "Nincs jogosultság.")
        return redirect("core:my_loans")
    loan.state = Loan.State.CANCELLED
    loan.cancelled_at = timezone.now()
    loan.save()
    messages.success(request, "Kölcsönkérés lemondva.")
    return redirect("core:my_loans")

@login_required
def loan_hand_over(request, loan_id: int):
    loan = get_object_or_404(Loan, pk=loan_id)
    if not loan.can_hand_over(request.user):
        messages.error(request, "Nincs jogosultság.")
        return redirect("core:my_loans")
    loan.state = Loan.State.HANDED_OVER
    loan.handed_over_at = timezone.now()
    loan.save()
    messages.success(request, "Átadás rögzítve.")
    return redirect("core:my_loans")

@login_required
def loan_mark_returned(request, loan_id: int):
    loan = get_object_or_404(Loan, pk=loan_id)
    if not loan.can_mark_returned(request.user):
        messages.error(request, "Nincs jogosultság.")
        return redirect("core:my_loans")
    loan.state = Loan.State.RETURNED
    loan.returned_at = timezone.now()
    loan.save()
    messages.success(request, "Visszahozatal rögzítve.")
    return redirect("core:my_loans")

# Registration

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Sikeres regisztráció!")
            return redirect("core:item_list")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile_edit(request):
    # Ensure profile exists
    profile = getattr(request.user, "profile", None)
    if profile is None:
        from .models import Profile
        profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil frissítve.")
            return redirect("core:profile_edit")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "account/profile.html", {"form": form})



def _require_verified(request):
    # Simple gate: only verified can view others' profiles
    if not request.user.is_authenticated or not request.user.profile.verified:
        messages.error(request, "Ez a funkció csak hitelesített felhasználóknak érhető el.")
        return False
    return True

User = get_user_model()

def profile_detail(request, username: str):
    if not _require_verified(request):
        return redirect("core:item_list")
    owner = get_object_or_404(User, username=username)
    # ensure profile exists
    _ = getattr(owner, "profile", None) or None

    return render(request, "account/profile_details.html", {
        "owner": owner,
    })

def owner_items(request, username: str):
    if not _require_verified(request):
        return redirect("core:item_list")
    owner = get_object_or_404(User, username=username)
    items_qs = Item.objects.filter(owner=owner).order_by("-created_at").prefetch_related("images")

    return render(request, "items/owner_items.html", {
        "owner": owner,
        "items": items_qs,
    })