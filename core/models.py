from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=30, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    verified = models.BooleanField(default=False)
    address = models.CharField(max_length=500, blank=True)
    about = models.TextField(blank=True)

    def __str__(self):
        return self.display_name or self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Item(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="items")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Holmi"
        verbose_name_plural = "Holmik"

    def __str__(self) -> str:
        return self.title

    @property
    def is_available(self) -> bool:
        return not self.loans.filter(state__in=[
            Loan.State.REQUESTED,
            Loan.State.ACCEPTED,
            Loan.State.HANDED_OVER,
        ]).exists()

    def cover_image(self):
        # first cover if exists
        return self.images.filter(is_cover=True).first()

    def main_image(self):
        # cover else first
        return self.cover_image() or self.images.first()

class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="items/")
    is_cover = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Holmi kép"
        verbose_name_plural = "Holmi képek"

    def __str__(self) -> str:
        return f"Image for {self.item_id}"

class Loan(models.Model):
    class State(models.TextChoices):
        REQUESTED = "REQUESTED", "Igénylve"
        ACCEPTED = "ACCEPTED", "Elfoagdva"
        HANDED_OVER = "HANDED_OVER", "Átadva"
        RETURNED = "RETURNED", "Visszaadva"
        DECLINED = "DECLINED", "Elutasítva"
        CANCELLED = "CANCELLED", "Lemondva"

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="loans")
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    state = models.CharField(max_length=20, choices=State.choices, default=State.REQUESTED)

    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    handed_over_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    expected_return_date = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Loan({self.item.title} -> {self.borrower.username}) [{self.state}]"

    def can_accept(self, user) -> bool:
        return user == self.item.owner and self.state == self.State.REQUESTED

    def can_decline(self, user) -> bool:
        return user == self.item.owner and self.state == self.State.REQUESTED

    def can_cancel(self, user) -> bool:
        return user == self.borrower and self.state in [self.State.REQUESTED, self.State.ACCEPTED]

    def can_hand_over(self, user) -> bool:
        return user == self.item.owner and self.state == self.State.ACCEPTED

    def can_mark_returned(self, user) -> bool:
        return user == self.item.owner and self.state == self.State.HANDED_OVER
