from django.core.management.base import BaseCommand
import time
from orders.services import MatchOrdersService

class Command(BaseCommand):
    help = 'Continuously matches and executes orders'

    def handle(self, *args, **options):
        while True:
            try:
                MatchOrdersService.find_and_execute_matches()
                time.sleep(2) 
            except Exception as e:
                self.stdout.write(f"Error: {str(e)}")
                time.sleep(2)