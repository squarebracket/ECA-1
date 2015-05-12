from django.apps import AppConfig

class QBConfig(AppConfig):
    name = 'QB'

    def ready(self):
        import QB.signals
        # Seller.signals.post_save_related.connect(Seller.signals.generate_pdf)
        super(QBConfig, self).ready()