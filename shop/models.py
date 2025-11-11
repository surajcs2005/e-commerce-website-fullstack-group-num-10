from django.db import models

class Product(models.Model):
    CATEGORY_CHOICES = [
    ('men', 'Men'),
    ('women', 'Women'),
    ('accessories', 'Accessories'),
    ('kids', 'Kids'),
    ('grocery', 'Grocery'),
    ('electronics', 'Electronics'),
    ('others', 'Others'),
]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='others')

    def __str__(self):
        return self.name