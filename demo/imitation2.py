import pygame
import random
import threading
import time

# Constants
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 600
DRONE_WIDTH = 50
DRONE_HEIGHT = 50
FLIGHT_SPEED = 2
FLIGHT_ALTITUDE_CHANGE = 2
TERMINAL_WIDTH = 200
IMAGE_SIZE = (50, 50)
NUM_IMAGES = 5
ORIGINAL_POSITION = (50, 500)


class Obstacle:
    def __init__(self, x, y, width, height, image):
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.transform.scale(image, (width, height))

class Drone:
    def __init__(self, image):
        self.x = ORIGINAL_POSITION[0]
        self.y = ORIGINAL_POSITION[1]
        self.altitude = 0
        self.battery_charge = 100
        self.speed = FLIGHT_SPEED
        self.is_flying = False
        self.image = image
        self.original_position = (self.x, self.y)
        self.error_messages = []
        self.success_message = ""
        self.max_altitude = 500
        self.target_x = None
        self.target_y = None
        self.last_update_time = pygame.time.get_ticks()  # To track flight progress
        self.stopped_due_to_collision = False  # Track if stopped due to a collision

    def fly_to(self, target_x, target_y, obstacles):
        self.is_flying = True
        self.current_target_position = (target_x, target_y)
        self.target_x = target_x
        self.target_y = target_y
        self.last_update_time = pygame.time.get_ticks()

    def update_flight(self, obstacles):
        if not self.is_flying:
            return

        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.last_update_time

        if elapsed_time < 100:  # Move the drone every 100ms
            return

        # Update the last update time
        self.last_update_time = current_time

        direction_x = self.target_x - self.x
        direction_y = self.target_y - self.altitude
        distance = (direction_x ** 2 + direction_y ** 2) ** 0.5

        if distance > 0:
            direction_x /= distance
            direction_y /= distance

        new_x = self.x + direction_x * self.speed
        new_altitude = self.altitude + direction_y * FLIGHT_ALTITUDE_CHANGE

        # Keep the drone within the bounds of the window
        new_x = max(0, min(new_x, WINDOW_WIDTH - DRONE_WIDTH))
        new_altitude = max(0, min(new_altitude, WINDOW_HEIGHT))

        drone_rect = pygame.Rect(new_x, new_altitude, DRONE_WIDTH, DRONE_HEIGHT)
        collision = any(drone_rect.colliderect(obstacle.rect) for obstacle in obstacles)

        if collision:
            self.error_messages.append("Collision detected! Attempting to navigate around.")
            self.stopped_due_to_collision = True  # Mark as stopped due to collision
            self.navigate_around_obstacle(obstacles)
            return  # Continue moving after obstacle navigation

        self.x = new_x
        self.altitude = new_altitude

        # Check if we have reached the target
        if abs(self.x - self.target_x) < self.speed and abs(self.altitude - self.target_y) < FLIGHT_ALTITUDE_CHANGE:
            self.x = self.target_x
            self.altitude = self.target_y
            self.success_message = "Drone has reached the target!"
            self.is_flying = False  # Stop flying after reaching the target

    def navigate_around_obstacle(self, obstacles):
        if not self.stopped_due_to_collision:
            return

        direction = 1 if self.x < obstacles[0].rect.centerx else -1  # Determine whether to move left or right

        # Smoothly adjust altitude to clear the obstacle
        while self.altitude < self.max_altitude and not self.is_path_clear(self.x,
                                                                           self.altitude + FLIGHT_ALTITUDE_CHANGE,
                                                                           obstacles):
            self.altitude += FLIGHT_ALTITUDE_CHANGE / 2  # Increment altitude
            pygame.event.pump()
            pygame.time.delay(50)  # Smooth movement delay

        # Smoothly move sideways to find a clear path
        while not self.is_path_clear(self.x + direction * FLIGHT_SPEED, self.altitude, obstacles):
            self.x += direction * FLIGHT_SPEED / 2  # Increment horizontal movement
            self.x = max(0, min(self.x, WINDOW_WIDTH - DRONE_WIDTH))  # Keep within screen bounds
            pygame.event.pump()
            pygame.time.delay(50)

        # Gradually descend to the target altitude after avoiding the obstacle
        while self.altitude > self.target_y and self.is_path_clear(self.x, self.altitude - FLIGHT_ALTITUDE_CHANGE,
                                                                   obstacles):
            self.altitude -= FLIGHT_ALTITUDE_CHANGE / 2  # Decrement altitude smoothly
            pygame.event.pump()
            pygame.time.delay(50)

        self.stopped_due_to_collision = False  # Reset collision flag

    def is_path_clear(self, x, y, obstacles):
        drone_rect = pygame.Rect(x, y, DRONE_WIDTH, DRONE_HEIGHT)
        return not any(drone_rect.colliderect(obstacle.rect) for obstacle in obstacles)

    def is_target_valid(self, target_x, target_y, obstacles):
        # Check if the target coordinates are within any obstacle's range
        target_rect = pygame.Rect(target_x, target_y, DRONE_WIDTH, DRONE_HEIGHT)
        for obstacle in obstacles:
            if target_rect.colliderect(obstacle.rect):
                return False  # Target is inside an obstacle's range
        return True

class DroneSimulatorApp:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Drone Delivery Simulator')

        self.background_image = pygame.image.load('image/map.png')
        self.drone_image = pygame.image.load('image/drone.png').convert_alpha()
        self.drone_image = pygame.transform.scale(self.drone_image, (DRONE_WIDTH, DRONE_HEIGHT))

        self.drone = Drone(self.drone_image)

        obstacle_images = [
            pygame.image.load('image/obstacle1.png').convert_alpha(),
            pygame.image.load('image/obstacle2.png').convert_alpha(),
            pygame.image.load('image/obstacle2.png').convert_alpha(),
        ]

        # Add obstacles with positions, dimensions, and corresponding images
        self.obstacles = [
            Obstacle(300, 250, 50, 100, obstacle_images[0]),
            Obstacle(500, 400, 100, 50, obstacle_images[1]),
            Obstacle(200, 100, 50, 300, obstacle_images[2]),
        ]

        self.image_positions = self.generate_random_positions(NUM_IMAGES)
        self.image = pygame.image.load('image/place.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, IMAGE_SIZE)

        self.running = True
        self.font = pygame.font.SysFont("Arial", 18)

        self.input_box = pygame.Rect(WINDOW_WIDTH - 190, WINDOW_HEIGHT - 80, 140, 32)
        self.color_inactive = pygame.Color('white')
        self.color_active = pygame.Color('dodgerblue')
        self.color = self.color_inactive
        self.text = ''
        self.active = False

        self.send_button = pygame.Rect(WINDOW_WIDTH - 200, WINDOW_HEIGHT - 120, 150, 32)
        self.button_color = pygame.Color('green')
        self.button_hover_color = pygame.Color('lightgreen')

        self.stop_button = pygame.Rect(WINDOW_WIDTH - 200, WINDOW_HEIGHT - 160, 150, 32)
    def generate_random_positions(self, num_images):
        positions = []
        base_rect_y = WINDOW_HEIGHT - 50

        while len(positions) < num_images:
            x = random.randint(0, WINDOW_WIDTH - IMAGE_SIZE[0])
            y = random.randint(0, WINDOW_HEIGHT - IMAGE_SIZE[1])

            if all(not pygame.Rect(x, y, IMAGE_SIZE[0], IMAGE_SIZE[1]).colliderect(obstacle) for obstacle in
                   self.obstacles) and \
                    (y + IMAGE_SIZE[1] <= base_rect_y - 100):
                positions.append((x, y))
        return positions

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.input_box.collidepoint(event.pos):
                    self.active = not self.active
                else:
                    self.active = False

                if self.send_button.collidepoint(event.pos):
                    self.send_flight_task()

                if self.stop_button.collidepoint(event.pos):
                    self.stop_flight()

                self.color = self.color_active if self.active else self.color_inactive

            if event.type == pygame.KEYDOWN:
                if self.active:
                    if event.key == pygame.K_BACKSPACE:
                        self.text = self.text[:-1]
                    else:
                        self.text += event.unicode

    def send_flight_task(self):
        try:
            target_x, target_y = map(int, self.text.split(","))
            # Check if the target coordinates are valid (not inside an obstacle)
            if not self.drone.is_target_valid(target_x, target_y, self.obstacles):
                self.drone.error_messages.append("Flight to this zone is prohibited.")
                self.text = ''
                return
            self.drone.fly_to(target_x, target_y, self.obstacles)
        except ValueError:
            self.drone.error_messages.append("Invalid target coordinates.")

    def stop_flight(self):
        self.drone.is_flying = False  # Cancel the mission
        target_x = 50  # Base x-coordinate
        target_altitude = 0  # Ground level altitude

        # Smoothly move the drone back to the starting position
        while abs(self.drone.x - target_x) > 0.1 or abs(self.drone.altitude - target_altitude) > 0.1:
            # Gradually adjust the x position
            if abs(self.drone.x - target_x) > 0.1:
                self.drone.x += (target_x - self.drone.x) * 0.1  # Move a fraction of the distance
                self.drone.x = max(0, min(self.drone.x, WINDOW_WIDTH - DRONE_WIDTH))  # Ensure within bounds

            # Gradually adjust the altitude
            if abs(self.drone.altitude - target_altitude) > 0.1:
                self.drone.altitude += (target_altitude - self.drone.altitude) * 0.1  # Move a fraction of the distance
                self.drone.altitude = max(0, min(self.drone.altitude, WINDOW_HEIGHT))  # Ensure within bounds

            # Process events and delay for smooth animation
            pygame.event.pump()  # Keep the application responsive
            pygame.time.delay(50)  # Delay for smooth visual transition

    def update(self):
        self.drone.update_flight(self.obstacles)


    def draw_messages(self):
        # Display any error or success messages
        for i, message in enumerate(self.drone.error_messages):
            text_surface = self.font.render(message, True, (255, 0, 0))
            self.screen.blit(text_surface, (10, 10 + i * 20))

        if self.drone.success_message:
            success_text = self.font.render(self.drone.success_message, True, (0, 255, 0))
            self.screen.blit(success_text, (10, 10 + len(self.drone.error_messages) * 20))

        # Draw the input box
        pygame.draw.rect(self.screen, self.color, self.input_box, 2)
        input_surface = self.font.render(self.text, True, self.color)
        self.screen.blit(input_surface, (self.input_box.x + 5, self.input_box.y + 5))

        # Draw buttons
        pygame.draw.rect(self.screen, self.button_color, self.send_button)
        self.screen.blit(self.font.render("Send Flight", True, (0, 0, 0)),
                         (self.send_button.x + 5, self.send_button.y + 5))

        pygame.draw.rect(self.screen, (255, 0, 0), self.stop_button)
        self.screen.blit(self.font.render("Stop Mission", True, (0, 0, 0)),
                         (self.stop_button.x + 5, self.stop_button.y + 5))


    def draw_map(self):
        self.screen.blit(self.background_image, (50, 0))

        # Draw obstacles using their images
        for obstacle in self.obstacles:
            self.screen.blit(obstacle.image, (obstacle.rect.x, obstacle.rect.y))

        # Draw the drone
        self.screen.blit(self.drone.image, (self.drone.x, WINDOW_HEIGHT - self.drone.altitude - DRONE_HEIGHT))

        base_rect_x = 50
        base_rect_y = WINDOW_HEIGHT - 50
        base_rect_width = 150
        base_rect_height = 30

        pygame.draw.rect(self.screen, (128, 128, 128),
                         (base_rect_x, base_rect_y, base_rect_width, base_rect_height))

        base_text = "Base - Instructions"
        text_surface = self.font.render(base_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(
            center=(base_rect_x + base_rect_width // 2, base_rect_y + base_rect_height // 2))
        self.screen.blit(text_surface, text_rect)

        # Draw locations
        for (x, y) in self.image_positions:
            self.screen.blit(self.image, (x, y))
            coords_text = f"({x}, {y})"
            text_surface = self.font.render(coords_text, True, (0, 0, 0))
            self.screen.blit(text_surface, (x, y + IMAGE_SIZE[1]))

    def draw_terminal(self):
        terminal_rect = pygame.Rect(WINDOW_WIDTH - TERMINAL_WIDTH, 0, TERMINAL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, (0, 0, 0), terminal_rect)

        y_offset = 10
        coordinates_text = f"Coordinates: ({self.drone.x}, {self.drone.y - self.drone.altitude})"
        battery_text = f"Battery: {self.drone.battery_charge:.2f}%"
        altitude_text = f"Altitude: {self.drone.altitude} m"
        speed_text = f"Speed: {self.drone.speed} units"

        characteristics_lines = [coordinates_text, battery_text, altitude_text, speed_text]

        for line in characteristics_lines:
            wrapped_lines = self.wrap_text(line, TERMINAL_WIDTH - 10)
            for wrapped_line in wrapped_lines:
                text_surface = self.font.render(wrapped_line, True, (0, 255, 0))
                self.screen.blit(text_surface, (WINDOW_WIDTH - TERMINAL_WIDTH + 5, y_offset))
                y_offset += 30

        y_offset += 10
        error_text = "Errors:"
        self.screen.blit(self.font.render(error_text, True, (255, 0, 0)), (WINDOW_WIDTH - TERMINAL_WIDTH + 5, y_offset))
        y_offset += 30

        for error in self.drone.error_messages:
            wrapped_lines = self.wrap_text(error, TERMINAL_WIDTH - 10)
            for wrapped_line in wrapped_lines:
                text_surface = self.font.render(wrapped_line, True, (255, 0, 0))
                self.screen.blit(text_surface, (WINDOW_WIDTH - TERMINAL_WIDTH + 5, y_offset))
                y_offset += 25

                if y_offset > WINDOW_HEIGHT - 10:
                    break

        if self.drone.success_message:
            self.screen.blit(self.font.render(self.drone.success_message, True, (255, 255, 255)),
                             (WINDOW_WIDTH - TERMINAL_WIDTH + 5, y_offset))
            y_offset += 25

    def wrap_text(self, text, max_width):
        words = text.split(' ')
        wrapped_lines = []
        current_line = ''

        for word in words:
            test_line = current_line + word + ' '
            text_surface = self.font.render(test_line, True, (0, 255, 0))
            if text_surface.get_width() > max_width and current_line:
                wrapped_lines.append(current_line)
                current_line = word + ' '
            else:
                current_line = test_line

        if current_line:
            wrapped_lines.append(current_line)

        return wrapped_lines

    def draw_altitude_ruler(self):
        ruler_x = 0
        pygame.draw.line(self.screen, (255, 255, 255), (ruler_x, 0), (ruler_x, WINDOW_HEIGHT), 2)

        for height in range(0, self.drone.max_altitude + 1, 100):
            y = WINDOW_HEIGHT - height * (WINDOW_HEIGHT / self.drone.max_altitude)
            pygame.draw.line(self.screen, (255, 255, 255), (ruler_x - 5, y), (ruler_x + 5, y), 2)
            height_text = self.font.render(str(height), True, (255, 255, 255))
            self.screen.blit(height_text, (10, y - 10))

    def draw(self):
        self.screen.fill((40, 44, 52))

        self.draw_altitude_ruler()
        self.draw_map()
        self.draw_terminal()

        pygame.draw.rect(self.screen, (70, 70, 70), self.input_box)
        txt_surface = self.font.render(self.text, True, self.color)
        width = max(200, txt_surface.get_width() + 10)
        self.input_box.w = width
        self.screen.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))

        button_color = self.button_hover_color if self.send_button.collidepoint(
            pygame.mouse.get_pos()) else self.button_color
        pygame.draw.rect(self.screen, button_color, self.send_button)
        button_text = self.font.render("Send Mission", True, (0, 0, 0))
        self.screen.blit(button_text, (self.send_button.x + 5, self.send_button.y + 5))

        pygame.draw.rect(self.screen, (255, 0, 0), self.stop_button)
        stop_button_text = self.font.render("Stop Mission", True, (255, 255, 255))
        self.screen.blit(stop_button_text, (self.stop_button.x + 5, self.stop_button.y + 5))

        pygame.display.flip()


if __name__ == "__main__":
    app = DroneSimulatorApp()
    app.run()