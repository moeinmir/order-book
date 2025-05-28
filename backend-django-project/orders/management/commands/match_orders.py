from django.core.management.base import BaseCommand
import time
from orders.services.schedule_finding_matched_orders import ScheduleFindingMatchedOrders 
class Command(BaseCommand):
    help = 'Continuously matches and executes orders'

    def handle(self, *args, **options):
        while True:
            try:
                ScheduleFindingMatchedOrders.find_matched_orders_parallel()
                time.sleep(2)
            except Exception as e:
                self.stdout.write(f"Error: {str(e)}")
                time.sleep(2)


                