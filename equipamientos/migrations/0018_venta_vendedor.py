from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('equipamientos', '0017_producto_fecha_creacion_producto_fecha_modificacion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='vendedor',
            field=models.CharField(blank=True, choices=[('HALCON', 'Halcon Equipamientos'), ('DIAZ', 'Electromecánica Diaz')], help_text='Quién hizo la venta - Halcon Equipamientos o Electromecánica Diaz', max_length=20, null=True),
        ),
    ]