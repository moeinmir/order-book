from django.db import migrations

def add_initial_tokens(apps, schema_editor):
    Token = apps.get_model('tokensbalances', 'Token')
    Token.objects.create(
        address='0x216cb9acB601474b2b27ee0BbaFc94c1C7148577',
        type='ERC20',
        is_active=True,
        decimals=6
    )
    Token.objects.create(
        address='0xA559F61AB112aD6Fe9162f82d45576C1411501aD',
        type='ERC20',
        is_active=True,
        decimals=18
    )

class Migration(migrations.Migration):

    dependencies = [
        ('tokensbalances', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_initial_tokens),
    ]
