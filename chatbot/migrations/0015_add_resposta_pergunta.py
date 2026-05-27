from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0014_alter_documento_data_modificacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='resposta',
            name='pergunta',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='resposta',
                to='chatbot.pergunta'
            ),
        ),
    ]
