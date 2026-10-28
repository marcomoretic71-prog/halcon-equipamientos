# Generated migration for venta manual + descuento
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('equipamientos', '0014_remove_producto_es_activo'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='descuento_monto',
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2, verbose_name='Monto descontado'),
        ),
        migrations.AddField(
            model_name='venta',
            name='descuento_porcentaje',
            field=models.DecimalField(default=0, max_digits=5, decimal_places=2, verbose_name='Descuento % sobre productos'),
        ),
        migrations.AddField(
            model_name='venta',
            name='subtotal_productos',
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2, verbose_name='Subtotal productos sin descuento'),
        ),
        migrations.AddField(
            model_name='venta',
            name='total_original',
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2, verbose_name='Total original sin descuento'),
        ),
        migrations.AddField(
            model_name='itemventa',
            name='es_manual',
            field=models.BooleanField(default=False, verbose_name='Es producto manual sin stock'),
        ),
        migrations.AddField(
            model_name='itemventa',
            name='nombre_manual',
            field=models.CharField(blank=True, default='', max_length=250, verbose_name='Nombre manual'),
        ),
        migrations.AlterField(
            model_name='itemventa',
            name='producto',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='items_venta', to='equipamientos.producto'),
        ),
    ]
