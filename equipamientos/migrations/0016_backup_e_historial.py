# Generated manually for anti-perdida
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('equipamientos', '0015_venta_manual_descuento'),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupAutomatico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('tipo', models.CharField(default='AUTO', max_length=20)),
                ('archivo_nombre', models.CharField(max_length=255)),
                ('archivo_json', models.TextField(blank=True)),
                ('cantidad_productos', models.IntegerField(default=0)),
                ('cantidad_ventas', models.IntegerField(default=0)),
                ('cantidad_clientes', models.IntegerField(default=0)),
                ('tamano_kb', models.FloatField(default=0)),
                ('estado', models.CharField(default='OK', max_length=20)),
                ('nota', models.TextField(blank=True, default='')),
            ],
            options={
                'ordering': ['-fecha'],
            },
        ),
        migrations.CreateModel(
            name='ProductoHistorial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=100)),
                ('nombre', models.CharField(blank=True, max_length=300)),
                ('campo', models.CharField(max_length=20)),
                ('valor_viejo', models.CharField(blank=True, max_length=100)),
                ('valor_nuevo', models.CharField(max_length=100)),
                ('usuario', models.CharField(default='cliente', max_length=100)),
                ('fecha', models.DateTimeField(default=django.utils.timezone.now)),
                ('ip', models.CharField(blank=True, max_length=50)),
                ('producto', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='historial', to='equipamientos.producto')),
            ],
            options={
                'ordering': ['-fecha'],
            },
        ),
    ]
