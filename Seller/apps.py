from django.apps import AppConfig

class SellerConfig(AppConfig):
    name = 'Seller'

    def ready(self):
        import Seller.signals
        # Seller.signals.post_save_related.connect(Seller.signals.generate_pdf)
        super(SellerConfig, self).ready()
