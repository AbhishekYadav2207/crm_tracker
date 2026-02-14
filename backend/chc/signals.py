from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from machines.models import Machine
from .models import CHC

@receiver(post_save, sender=Machine)
def update_machine_count_on_save(sender, instance, created, **kwargs):
    if instance.chc:
        instance.chc.total_machines = instance.chc.machines.count()
        instance.chc.save()

@receiver(post_delete, sender=Machine)
def update_machine_count_on_delete(sender, instance, **kwargs):
    if instance.chc:
        instance.chc.total_machines = instance.chc.machines.count()
        instance.chc.save()
