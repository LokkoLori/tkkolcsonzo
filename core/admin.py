from django.contrib import admin
from .models import Item, ItemImage, Loan, UserProfile

class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 0

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "category")
    search_fields = ("title", "description", "category")
    inlines = [ItemImageInline]

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "borrower", "state", "requested_at")
    list_filter = ("state",)
    search_fields = ("item__title", "borrower__username")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "phone", "verified")
    search_fields = ("user__username", "display_name", "phone")
    readonly_fields = ("user", "display_name", "phone")

    fields = ("user", "display_name", "phone", "avatar", "verified")

    def has_change_permission(self, request, obj=None):
        return request.user.is_staff

    def has_add_permission(self, request):
        return False