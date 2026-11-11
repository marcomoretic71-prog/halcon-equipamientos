from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('equipamientos', '[STRIPPED 65 bytes]'),
    ]

    operations = [
        migrations.AddField(
            model_name='venta',
            name='vendedor',
            field=models.CharField(blank=True, choices=[('HALCON', 'Halcon Equipamientos'), ('DIAZ', 'Electromecánica Diaz')], help_text='Quién hizo la venta - Halcon Equipamientos o Electromecánica Diaz', max_length=20, null=True),
        ),
    ]