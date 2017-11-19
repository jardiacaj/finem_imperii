from django.db import models


class InventoryItem(models.Model):
    GRAIN = 'grain'
    CART = 'cart'
    TYPE_CHOICES = (
        (GRAIN, 'grain bushels'),
        (CART, 'transport carts'),
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    owner_character = models.ForeignKey('character.Character',
                                        blank=True, null=True)
    location = models.ForeignKey('world.Building', blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.quantity, self.get_type_display())

    def get_weight(self):
        if self.type == InventoryItem.CART:
            return -100
        return 1