from django.core.management.base import BaseCommand
import time
from orders.services.schedule_execute_matched_orders import ScheduleExecuteMatchedOrders 

class Command(BaseCommand):
    help = 'Continuously matches and executes orders'
    def handle(self, *args, **options):
        while True:
            try:
                ScheduleExecuteMatchedOrders.execute_batches_parallel()
                time.sleep(5)
            except Exception as e:
                self.stdout.write(f"Error: {str(e)}")
                time.sleep(5)


                