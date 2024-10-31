# drone.py
import time

class Drone:
    def __init__(self):
        self.is_flying = False

    def take_off(self):
        if not self.is_flying:
            print("Drone is taking off...")
            time.sleep(2)  # Simulate time taken for takeoff
            self.is_flying = True
            print("Drone has taken off successfully!")
        else:
            print("Drone is already flying.")

    def land(self):
        if self.is_flying:
            print("Drone is landing...")
            time.sleep(2)  # Simulate time taken for landing
            self.is_flying = False
            print("Drone has landed successfully!")
        else:
            print("Drone is already on the ground.")