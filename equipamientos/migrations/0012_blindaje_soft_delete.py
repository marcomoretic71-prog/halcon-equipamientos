# Generated - Blindaje Soft Delete
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('equipamientos', '0011_alter_itempresupuesto_precio_unitario_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditoriaAccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('usuario', models.CharField(default='sistema', max_length=150)),
                ('accion', models.CharField(choices=[('DESACTIVAR_PRODUCTO', 'Desactivar Producto'), ('REACTIVAR_PRODUCTO', 'Reactivar Producto'), ('INTENTO_BORRAR_BLOQUEADO', 'Intento Bloqueado Borrar Producto con Ventas'), ('LIMPIAR_DUPLICADOS', 'Limpiar Duplicados'), ('CREAR_VENTA', 'Crear Venta'), ('ELIMINAR_VENTA', 'Eliminar Venta'), ('OTRO', 'Otro')], max_length=30)),
                ('modelo', models.CharField(max_length=50)),
                ('objeto_id', models.CharField(max_length=50)),
                ('detalle', models.TextField(blank=True)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-fecha'],
                'verbose_name_plural': 'Auditorias',
            },
        ),
        migrations.AddField(
            model_name='producto',
            name='es_activo',
            field=models.BooleanField(default=True, db_index=True, help_text='False = desactivado, no se borra nunca'),
        ),
        migrations.AddField(
            model_name='producto',
            name='eliminado_en',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='producto',
            name='eliminado_por',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
