from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipamientos', '0012_producto_es_activo_alter_configsistema_version_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='fecha_ultimo_cambio_precio',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Último cambio precio'),
        ),
        migrations.AddField(
            model_name='producto',
            name='fecha_ultimo_cambio_stock',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Último cambio stock'),
        ),
    ]
