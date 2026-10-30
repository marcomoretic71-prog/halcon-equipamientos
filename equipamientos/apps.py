from django.apps import AppConfig

class EquipamientosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'equipamientos'

    def ready(self):
        try:
            import equipamientos.signals_seguro
        except Exception as e:
            print(f"Signals no cargados aun (normal en migracion): {e}")
