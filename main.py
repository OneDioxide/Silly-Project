import pygame
import sys
import math
import random
from PIL import Image

# Initialize Pygame
pygame.init()
pygame.font.init()
pygame.mixer.init()  # Initialize the mixer for sound playback

# Define the screen width and height
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Initialize the font (using a default font, size 36)
font = pygame.font.Font(None, 36)

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spaceship Movement")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
RED_TRANSPARENT = (255, 0, 0, 128)  # Red color with transparency

# Load images for player, enemy, missile, and neutrons
player_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\player.png")
player_image = pygame.transform.scale(player_image, (25, 25))

enemy_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Alien1 - popular.png")
enemy_image = pygame.transform.scale(enemy_image, (15, 15))

missile_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Missile.png")
missile_image = pygame.transform.scale(missile_image, (32, 32))

neutrons_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Orb.png")
neutrons_image = pygame.transform.scale(neutrons_image, (32, 32))

tracking_missile_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Missile.png")
tracking_missile_image = pygame.transform.scale(tracking_missile_image, (16, 32))

strafe_enemy_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Strafe.png")
strafe_enemy_image = pygame.transform.scale(strafe_enemy_image, (30, 30))  # Adjust size as necessary

feint_enemy_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Feint.png")
feint_enemy_image = pygame.transform.scale(feint_enemy_image, (30, 30))  # Adjust size as necessary

# Load the Ambush enemy sprite
ambush_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Ambush.png")
ambush_image = pygame.transform.scale(ambush_image, (30, 30))  # Adjust size as necessary

# Load and scale the bullet image once
AMBUSH_BULLET_IMAGE = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\normalbullet.png")
AMBUSH_BULLET_IMAGE = pygame.transform.scale(AMBUSH_BULLET_IMAGE, (32, 32))  # Scale to the desired size

# Load missile sound effect
missile_sound = pygame.mixer.Sound("C:\\Users\\hweeh\\Downloads\\pygame image database\\Audio Database\\Playermissile.wav")

# Load missile explosion sound effect
explosion_sound = pygame.mixer.Sound("C:\\Users\\hweeh\\Downloads\\pygame image database\\Audio Database\\missileexplode.wav")
missile_run_sound = pygame.mixer.Sound("C:\\Users\\hweeh\\Downloads\\pygame image database\\Audio Database\\missilerun.mp3")

# Load sniper shot sound effect
sniper_shot_sound = pygame.mixer.Sound("C:\\Users\\hweeh\\Downloads\\pygame image database\\Audio Database\\Snipershot.wav")

# Load sniper pierce sound effect
sniper_pierce_sound = pygame.mixer.Sound("C:\\Users\\hweeh\\Downloads\\pygame image database\\Audio Database\\sniperpierce.mp3")

# Load gunshot sound effect for Normal and Home weapons
gunshot_sound = pygame.mixer.Sound("C:\\Users\\hweeh\\Downloads\\pygame image database\\Audio Database\\gunshot2.mp3")

# Load trap sound effect
trap_sound = pygame.mixer.Sound("C:\\Users\\hweeh\\Downloads\\pygame image database\\Audio Database\\TrapBeep.wav")

# Sound management variables
MAX_SIMULTANEOUS_EXPLOSIONS = 5
current_explosions = 0

MAX_SIMULTANEOUS_MISSILES = 5
current_missiles = 0

current_missiles = 0
MAX_MISSILES = 35  # Assume a reasonable maximum number of missiles

# Assign sound channels
missile_channel = pygame.mixer.Channel(1)
explosion_channel = pygame.mixer.Channel(0)
missile_run_channel = pygame.mixer.Channel(2)
sniper_shot_channel = pygame.mixer.Channel(3)  # Channel for sniper shot sound
sniper_pierce_channel = pygame.mixer.Channel(4)  # Channel for sniper pierce sound
gunshot_channel = pygame.mixer.Channel(5)  # Channel for gunshot sound
trap_channel = pygame.mixer.Channel(6)  # Channel for trap sound

# Extract frames from the GIF using PIL
gif_path = "C:\\Users\\hweeh\\Downloads\\pygame image database\\Implodes.gif"
gif = Image.open(gif_path)
frames = []
scale_factor = 0.5  # Resize to 50% of the original size
frame_duration = 50  # Set frame duration to be 2x faster

try:
    while True:
        frame = gif.copy()
        frame = frame.resize((int(frame.width * scale_factor), int(frame.height * scale_factor)))
        frames.append(pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode))
        gif.seek(gif.tell() + 1)
except EOFError:
    pass

def update_missile_run_volume():
    global current_missiles

    if current_missiles > 0:
        # Reduce the volume as more missiles are active
        volume = max(0.2, 1.0 - (current_missiles / MAX_MISSILES))
        missile_run_channel.set_volume(volume * 0.5)  # Keep the base volume at 50%
        if not missile_run_channel.get_busy():
            missile_run_channel.play(missile_run_sound, loops=-1, fade_ms=500)
    else:
        missile_run_channel.stop()

class SoundRoom:
    def __init__(self, player, radius=250):
        self.player = player  # The player object
        self.radius = radius  # The radius of the sound room

    def calculate_volume(self, sound_position):
        # Calculate the distance between the player and the sound source
        player_pos = pygame.math.Vector2(self.player.rect.center)
        sound_pos = pygame.math.Vector2(sound_position)

        distance = player_pos.distance_to(sound_pos)

        # Outer region (from outer edge to half the radius)
        outer_radius = self.radius
        inner_radius = self.radius / 2

        if distance > outer_radius:
            return 0  # If the sound is outside the sound room, volume is 0
        elif distance > inner_radius:
            # Outer region (half to outer edge): scale volume from 0 to 0.25
            return 0.25 * (outer_radius - distance) / (outer_radius - inner_radius)
        else:
            # Inner region (center to half): scale volume from 0.25 to 1
            return 0.25 + 0.75 * (inner_radius - distance) / inner_radius

    def is_in_sound_room(self, sound_rect):
        # Convert player position and the closest point on the sound_rect to Vector2
        player_pos = pygame.math.Vector2(self.player.rect.center)
        
        # Get the closest point on the sound_rect to the player_rect
        closest_x = max(sound_rect.left, min(self.player.rect.centerx, sound_rect.right))
        closest_y = max(sound_rect.top, min(self.player.rect.centery, sound_rect.bottom))
        closest_point = pygame.math.Vector2(closest_x, closest_y)

        # Calculate the distance between the player and the closest point on the object's hitbox
        distance = player_pos.distance_to(closest_point)
        
        return distance <= self.radius

    def draw(self, screen):
        # Optional: Draw the sound room circle for visual debugging
        pygame.draw.circle(screen, (255, 0, 0), self.player.rect.center, self.radius, 2)

def apply_sound_room(sound_room, sound, sound_rect, sound_channel):
    # Check if the sound source is in the sound room
    if sound_room.is_in_sound_room(sound_rect):
        # Calculate volume based on distance and room position
        volume = sound_room.calculate_volume(sound_rect.center)
        sound_channel.set_volume(volume)

        # If the sound should be played and the channel isn't busy, play it
        if volume > 0 and not sound_channel.get_busy():
            sound_channel.play(sound, loops=-1)
    else:
        # If the sound is out of the room, stop the sound
        if sound_channel.get_busy():
            sound_channel.stop()

class Spaceship(pygame.sprite.Sprite):
    def __init__(self, all_sprites, explosion_group):
        super().__init__()
        self.image = player_image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.position = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)
        self.drag = 0.95
        self.initial_health = 1023123132133131230  # Adjusted for testing
        self.health = self.initial_health
        self.kill_count = 0
        self.money = 0
        self.charge = 0
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group
        self.image_angle = 0
        self.weapon_type = "Normal"  # Start with Normal weapon
        self.last_shooting_angle = 0
        self.base_shoot_cooldown = 500  # Initial cooldown for machine gun mechanic
        self.min_shoot_cooldown = 100  # Minimum cooldown to reach as firing rate increases
        self.shoot_cooldown = 500  # Default cooldown for Normal weapon

        self.max_charge_radius = 50  # Maximum radius for the charge circle

        # Initialize shooting-related attributes
        self.shooting = False
        self.shooting_start_time = 0
        self.shoot_delay = 500  # Adjusted delay for shooting (for Normal and Home)
        self.sniper_cooldown = 2000  # 2 seconds cooldown for Sniper
        self.last_shot_time = 0

    def update(self):
        # Reduce velocity with drag
        self.velocity *= self.drag

        # Update spaceship position
        new_position = self.position + self.velocity
        new_rect = self.rect.copy()
        new_rect.center = new_position

        # Check boundaries to keep spaceship on screen
        if new_rect.left >= 0 and new_rect.right <= WIDTH and new_rect.top >= 0 and new_rect.bottom <= HEIGHT:
            self.position = new_position
            self.rect = new_rect
        else:
            if new_rect.left < 0:
                self.rect.left = 0
            elif new_rect.right > WIDTH:
                self.rect.right = WIDTH
            if new_rect.top < 0:
                self.rect.top = 0
            elif new_rect.bottom > HEIGHT:
                self.rect.bottom = HEIGHT

        # Set rotation angle based on velocity direction
        if self.velocity.length_squared() > 0:
            self.image_angle = math.degrees(math.atan2(-self.velocity.x, -self.velocity.y))
            self.image = pygame.transform.rotate(player_image, self.image_angle)
            self.rect = self.image.get_rect(center=self.rect.center)

        # Handle shooting mechanics
        if self.shooting:
            current_time = pygame.time.get_ticks()
            if self.weapon_type != "Sniper":
                # Gradually reduce the cooldown as the player keeps shooting
                elapsed_time = current_time - self.shooting_start_time
                self.shoot_cooldown = max(self.min_shoot_cooldown, self.base_shoot_cooldown - elapsed_time // 10)

                if current_time - self.last_shot_time >= self.shoot_cooldown:
                    self.shoot_bullet()
                    self.last_shot_time = current_time
            else:
                if current_time - self.last_shot_time >= self.sniper_cooldown:
                    self.shoot_bullet()
                    self.last_shot_time = current_time

    def start_shooting(self):
        if self.weapon_type != "Sniper":
            self.shooting = True
            self.shooting_start_time = pygame.time.get_ticks()
            self.shoot_bullet()
        else:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shot_time >= self.sniper_cooldown:
                self.shoot_bullet()
                self.last_shot_time = current_time

    def stop_shooting(self):
        if self.weapon_type != "Sniper":
            self.shooting = False
            self.shoot_cooldown = self.base_shoot_cooldown  # Reset cooldown when shooting stops

    def shoot_bullet(self):
        if self.velocity.length_squared() > 0:
            self.last_shooting_angle = self.image_angle

        bullet = None

        if self.weapon_type == "Normal":
            bullet = NormalBullet(self.rect.center, self.last_shooting_angle, self)
            gunshot_channel.play(gunshot_sound)  # Play the gunshot sound for Normal bullets
        elif self.weapon_type == "Sniper":
            bullet = SniperBullet(self.rect.center, self.last_shooting_angle, self)
            self.apply_recoil(self.last_shooting_angle)  # Apply recoil when shooting a sniper bullet
            self.reduce_speed_and_change_angle()  # Reduce speed and change angle when shooting while moving
        elif self.weapon_type == "Home":
            bullet = HomeBullet(self.rect.center, self.last_shooting_angle, self)
            gunshot_channel.play(gunshot_sound)  # Play the gunshot sound for Home bullets

        if bullet:
            self.all_sprites.add(bullet)
            bullets.add(bullet)

    def apply_recoil(self, angle):
        # Recoil force and direction
        recoil_force = 5  # Adjust this value to control the strength of the recoil
        angle_radians = math.radians(angle)

        # Calculate the recoil vector in the opposite direction of the shot
        recoil_vector = pygame.math.Vector2(
            math.sin(angle_radians) * recoil_force,
            -math.cos(angle_radians) * recoil_force
        )

        # Apply the recoil to the player's velocity
        self.velocity -= recoil_vector

    def reduce_speed_and_change_angle(self):
        # Speed reduction factor
        speed_reduction_factor = 0.7  # Reduce speed by 30%

        # Reduce the player's speed
        self.velocity *= speed_reduction_factor

        # Change in angle (in degrees)
        angle_change = 5  # Adjust this value for how much the angle should change

        # Apply a slight angle deviation based on current movement direction
        if self.velocity.length_squared() > 0:
            current_angle = math.degrees(math.atan2(-self.velocity.y, -self.velocity.x))
            new_angle = current_angle + random.uniform(-angle_change, angle_change)
            angle_radians = math.radians(new_angle)

            # Recalculate the velocity vector based on the new angle and current speed
            speed = self.velocity.length()
            self.velocity = pygame.math.Vector2(
                math.sin(angle_radians) * speed,
                -math.cos(angle_radians) * speed
            )
            
    def draw_charge_circle(self):
        # Calculate the position for the charge circle in front of the spaceship
        direction_vector = pygame.math.Vector2(-math.sin(math.radians(self.image_angle)), -math.cos(math.radians(self.image_angle)))
        charge_circle_position = self.rect.center + direction_vector * 30  # Distance from the spaceship's center
        charge_circle_radius = min(self.charge * 5, self.max_charge_radius)  # Scale the radius based on the charge level, with a maximum limit
        pygame.draw.circle(screen, RED_TRANSPARENT, charge_circle_position, charge_circle_radius, 2)

    def charge_laser(self):
        # Increase the charge level
        self.charge += 1

    def release_laser(self):
        # Shoot the laser beam with the current charge level
        laser_beam = LaserBeam(self.rect.center, self.charge)
        self.all_sprites.add(laser_beam)
        laser_beams.add(laser_beam)
        self.charge = 0  # Reset the charge level

    def shoot_missile(self):
        # Play the missile sound
        missile_sound.play()
        
        # Create a new missile and add it to the sprite groups
        missile = Missile(self.rect.center, self)
        self.all_sprites.add(missile)
        enemy_missiles.add(missile)

    def shoot_tracking_missile(self):
        # Play the missile sound
        missile_sound.play()
        
        # Find the closest enemy
        closest_enemy = self.find_closest_enemy()
        if closest_enemy:
            # Create a new tracking missile and add it to the sprite groups
            tracking_missile = TrackingMissile(self.rect.center, closest_enemy, self.velocity, self.all_sprites, self.explosion_group)
            self.all_sprites.add(tracking_missile)
            enemy_missiles.add(tracking_missile)
        else:
            # Create a new tracking missile that flies straight
            tracking_missile = TrackingMissile(self.rect.center, None, self.velocity, self.all_sprites, self.explosion_group)
            self.all_sprites.add(tracking_missile)
            enemy_missiles.add(tracking_missile)


    def find_closest_enemy(self):
        closest_enemy = None
        closest_distance = float('inf')
        for enemy in enemies_group:
            distance = self.position.distance_to(enemy.position)
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
        return closest_enemy

# Class for the laser beam
class LaserBeam(pygame.sprite.Sprite):
    def __init__(self, start_pos, charge):
        super().__init__()
        self.image = pygame.Surface((charge * 10, 5))
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=start_pos)
        self.duration = 600  # Duration in milliseconds (10 seconds)
        self.creation_time = pygame.time.get_ticks()

    def update(self):
        # Check if the laser beam has reached its maximum duration
        if pygame.time.get_ticks() - self.creation_time >= self.duration:
            self.kill()  # Kill the laser beam if it exceeds the duration
            
class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_pos, angle, speed, damage, spaceship):
        super().__init__()
        
        # Load and scale the bullet image
        bullet_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\normalbullet.png")
        bullet_image = pygame.transform.scale(bullet_image, (32, 32))  # Adjust size if necessary
        
        # Rotate the bullet image based on the player's angle
        self.image = pygame.transform.rotate(bullet_image, angle)
        self.rect = self.image.get_rect(center=start_pos)
        
        # Convert angle to radians
        self.angle = math.radians(angle)
        
        # Calculate velocity based on angle
        self.velocity = pygame.math.Vector2(
            -math.sin(self.angle) * speed,  # Horizontal component (sine)
            -math.cos(self.angle) * speed   # Vertical component (cosine)
        )
        
        self.damage = damage  # Damage dealt by each bullet
        self.spaceship = spaceship  # Reference to the spaceship object

    def update(self):
        self.rect.move_ip(self.velocity)  # Move the bullet according to its velocity
        if self.rect.left < 0 or self.rect.right > WIDTH or self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.kill()  # Remove the bullet if it goes off screen

        # Check for collisions with enemies
        for enemy in enemies_group:
            if pygame.sprite.collide_rect(self, enemy):
                enemy.health -= self.damage
                self.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    # Increment kill count for spaceship
                    self.spaceship.kill_count += 1

class HomeBullet(Bullet):
    def __init__(self, start_pos, angle, spaceship):
        super().__init__(start_pos, angle, speed=5, damage=10, spaceship=spaceship)
        self.max_speed = 5  # Constant speed of the homing bullet
        self.turn_rate = 0.1  # Increase turn rate for more aggressive homing

        # Load and scale down the bullet image to the same size as other bullets
        self.original_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\homingbullet.png")
        self.image = pygame.transform.scale(self.original_image, (32, 32))  # Match the size to other bullets
        self.rect = self.image.get_rect(center=start_pos)

        # Initialize position as a vector
        self.position = pygame.math.Vector2(start_pos)

        self.target = None
        self.lifetime = 2500  # Lifetime in milliseconds
        self.creation_time = pygame.time.get_ticks()

    def update(self):
        # Check if the bullet has exceeded its lifetime
        if pygame.time.get_ticks() - self.creation_time > self.lifetime:
            self.kill()
            return

        # Find the closest enemy if no target or target is dead
        if not self.target or not self.target.alive():
            self.target = self.find_closest_enemy()

        if self.target:
            # Calculate the direction vector to the target
            to_target_vector = self.target.position - self.position
            distance_to_target = to_target_vector.length()

            # Predict the target's position when the bullet is 100 units away from it
            if distance_to_target > 100:
                predicted_position = self.target.position + self.target.velocity.normalize() * 100 if self.target.velocity.length_squared() > 0 else self.target.position
            else:
                predicted_position = self.target.position

            # Calculate the desired direction towards the predicted position
            target_vector = predicted_position - self.position

            if target_vector.length_squared() > 0:  # Ensure the vector is not zero before normalizing
                target_vector = target_vector.normalize()

            # Slightly adjust the bullet's velocity towards the predicted position
            self.velocity = self.velocity + (target_vector * self.turn_rate)
            if self.velocity.length() > self.max_speed:
                self.velocity = self.velocity.normalize() * self.max_speed

            # Ensure the bullet always moves forward without braking
            self.velocity = self.velocity.normalize() * self.max_speed

            # Rotate the bullet image to match the new direction
            angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
            self.image = pygame.transform.rotate(pygame.transform.scale(self.original_image, (32, 32)), angle)
            self.rect = self.image.get_rect(center=self.position)

        # Update position based on the velocity
        self.position += self.velocity
        self.rect.center = self.position

        # The bullet is not affected by screen borders, so it keeps moving forward even off-screen

        # Check for collisions with enemies
        self.check_collision()

    def find_closest_enemy(self):
        closest_enemy = None
        closest_distance = float('inf')
        for enemy in enemies_group:
            distance = pygame.math.Vector2(self.rect.center).distance_to(enemy.position)
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
        return closest_enemy

    def check_collision(self):
        # Check for collisions with enemies
        for enemy in enemies_group:
            if pygame.sprite.collide_rect(self, enemy):
                enemy.health -= self.damage
                self.kill()
                if enemy.health <= 0:
                    enemy.kill()
                    # Increment kill count for spaceship
                    self.spaceship.kill_count += 1

class NormalBullet(Bullet):
    def __init__(self, start_pos, angle, spaceship):
        super().__init__(start_pos, angle, speed=10, damage=20, spaceship=spaceship)  # Standard speed and damage

class SniperBullet(Bullet):
    def __init__(self, start_pos, angle, spaceship):
        super().__init__(start_pos, angle, speed=20, damage=60, spaceship=spaceship)  # Fast speed and high damage
        self.pierced_count = 0  # Number of enemies pierced
        self.max_pierce = 5  # Maximum number of enemies the bullet can pierce

        # Play the sniper shot sound
        sniper_shot_channel.play(sniper_shot_sound)

    def update(self):
        self.rect.move_ip(self.velocity)  # Move the bullet according to its velocity
        if self.rect.left < 0 or self.rect.right > WIDTH or self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.kill()  # Remove the bullet if it goes off screen

        # List to keep track of enemies hit in this frame
        enemies_hit = []

        # Check for collisions with enemies
        for enemy in enemies_group:
            if pygame.sprite.collide_rect(self, enemy):
                if enemy.alive() and enemy not in enemies_hit:
                    enemy.health -= self.damage
                    self.pierced_count += 1
                    enemies_hit.append(enemy)

                    # Play the sniper pierce sound every time the bullet pierces an enemy
                    sniper_pierce_channel.play(sniper_pierce_sound)

                    if enemy.health <= 0:
                        enemy.kill()
                        # Increment kill count for spaceship
                        self.spaceship.kill_count += 1

                    # Check if the bullet has reached the max number of pierces
                    if self.pierced_count >= self.max_pierce:
                        self.kill()
                        return  # Exit early to prevent further processing

        # Kill the bullet if it has pierced the maximum number of enemies
        if self.pierced_count >= self.max_pierce:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, target):
        super().__init__()
        self.image = enemy_image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH)
        self.rect.y = random.randint(0, HEIGHT)
        self.velocity = pygame.math.Vector2(0, 0)
        self.target = target
        self.position = pygame.math.Vector2(self.rect.center)  # Adding position attribute
        self.health = 30  # Add health attribute

    def update(self):
        # Move towards the target (spaceship)
        direction = (self.target.position - pygame.math.Vector2(self.rect.center)).normalize()
        self.velocity = direction * 2  # Adjust speed as necessary
        self.rect.move_ip(self.velocity)
        self.position = pygame.math.Vector2(self.rect.center)  # Update position

        # Kill if off screen
        if self.rect.right < 0:
            self.rect.left = WIDTH
        elif self.rect.left > WIDTH:
            self.rect.right = 0
        if self.rect.bottom < 0:
            self.rect.top = HEIGHT
        elif self.rect.top > HEIGHT:
            self.rect.bottom = 0

class FeintEnemy(pygame.sprite.Sprite):
    def __init__(self, target, all_sprites, explosion_group, sound_room):
        super().__init__()
        self.image = feint_enemy_image
        self.rect = self.image.get_rect()
        self.position = pygame.math.Vector2(random.randint(0, WIDTH), random.randint(0, HEIGHT))
        self.velocity = pygame.math.Vector2(0, 0)
        self.acceleration = pygame.math.Vector2(0, 0)
        self.target = target
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group
        self.health = 30
        self.min_distance = 200  # Minimum distance to avoid the player
        self.max_distance = 400  # Maximum distance to stay from the player
        self.max_speed = 4  # Maximum speed
        self.turn_speed = 0.1  # Speed at which the enemy turns
        self.drag = 0.95  # Drag to slow down the enemy over time
        self.deploy_trap_cooldown = 5000  # Deploy trap every 5 seconds
        self.last_trap_time = pygame.time.get_ticks()
        self.trap_success = False  # Flag to track if the trap was successful
        self.momentum = 0.9  # Momentum factor to smooth out changes in direction
        self.sound_room = sound_room  # Store the sound room


    def update(self):
        # Calculate direction towards the target (spaceship)
        direction = self.target.position - self.position
        distance = direction.length()

        # Adjust Feint's movement based on distance to player
        if distance > self.max_distance:
            # Move closer to the player
            desired_acceleration = direction.normalize() * self.max_speed
        elif distance < self.min_distance:
            # Move away from the player if too close
            desired_acceleration = -direction.normalize() * self.max_speed
        else:
            # Move around the player at a mid-range distance
            perp_direction = pygame.math.Vector2(-direction.y, direction.x).normalize()
            desired_acceleration = perp_direction * self.max_speed

        # Apply momentum to smooth the acceleration changes
        self.acceleration = (self.acceleration * self.momentum) + (desired_acceleration * (1 - self.momentum))

        # Update velocity with acceleration
        self.velocity += self.acceleration

        # Apply drag
        self.velocity *= self.drag

        # Clamp the velocity to the maximum speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        # Update position
        self.position += self.velocity
        self.rect.center = self.position

        # Rotate the enemy image to match the direction of movement
        if self.velocity.length_squared() > 0:
            angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
            self.image = pygame.transform.rotate(feint_enemy_image, angle)
            self.rect = self.image.get_rect(center=self.position)

        # Deploy traps if cooldown has passed
        current_time = pygame.time.get_ticks()
        if current_time - self.last_trap_time >= self.deploy_trap_cooldown:
            self.deploy_trap()
            self.last_trap_time = current_time

        # Kill if off screen
        if self.rect.right < 0:
            self.rect.left = WIDTH
        elif self.rect.left > WIDTH:
            self.rect.right = 0
        if self.rect.bottom < 0:
            self.rect.top = HEIGHT
        elif self.rect.top > HEIGHT:
            self.rect.bottom = 0

    def deploy_trap(self):
        # Predict the player's next movement path
        prediction_time = 1000  # Predict 1 second ahead
        if self.target.velocity.length_squared() > 0:
            predicted_position = self.target.position + self.target.velocity.normalize() * 100
        else:
            # If the player's velocity is zero, use a default direction
            predicted_position = self.target.position + pygame.math.Vector2(0, -100)

        # Calculate a random offset around the player
        offset_distance = 50 + random.randint(0, 100)  # Random distance between 50 and 150 pixels
        offset_angle = random.uniform(0, 2 * math.pi)  # Random angle in radians
        offset_vector = pygame.math.Vector2(math.cos(offset_angle), math.sin(offset_angle)) * offset_distance

        # Place the trap at the predicted position with the offset
        trap_position = predicted_position + offset_vector

        # Now, pass the sound_room when creating the trap
        trap = Trap(trap_position, self.all_sprites, self.explosion_group, self.sound_room)
        self.all_sprites.add(trap)
        traps.add(trap)

        # If the previous trap was successful, deploy more traps
        if self.trap_success:
            for _ in range(2):
                additional_offset_distance = 50 + random.randint(0, 100)
                additional_offset_angle = random.uniform(0, 2 * math.pi)
                additional_offset_vector = pygame.math.Vector2(math.cos(additional_offset_angle), math.sin(additional_offset_angle)) * additional_offset_distance
                additional_trap_position = predicted_position + additional_offset_vector
                additional_trap = Trap(additional_trap_position, self.all_sprites, self.explosion_group)
                self.all_sprites.add(additional_trap)
                traps.add(additional_trap)
            self.trap_success = False

    def on_trap_success(self):
        # This method will be called when the player is trapped
        self.trap_success = True

        # Reduce the player's movement speed by 50%
        self.target.velocity *= 0.5
        
class Trap(pygame.sprite.Sprite):
    def __init__(self, position, all_sprites, explosion_group, sound_room):
        super().__init__()
        self.position = pygame.math.Vector2(position)
        self.frames = frames
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=self.position)
        self.animation_speed = frame_duration  # Set frame duration to be 2x faster
        self.last_update_time = pygame.time.get_ticks()
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group
        self.hitbox = pygame.Rect(self.position[0] - 20, self.position[1] - 20, 40, 40)
        self.damage = 250
        self.creation_time = pygame.time.get_ticks()  # Track the time when the trap was created
        self.sound_room = sound_room  # Reference to the sound room

        # Each trap has its own sound channel for independent playback
        self.sound_channel = pygame.mixer.find_channel()  # Find an available channel directly

    def update(self):
        # Animate the trap
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.rect = self.image.get_rect(center=self.position)
            self.last_update_time = current_time

        # Apply sound room logic to control the sound volume based on the trap's distance to the player
        if self.sound_channel:  # Ensure a channel is available
            apply_sound_room(self.sound_room, trap_sound, self.rect, self.sound_channel)

        # Check if the trap has reached its maximum duration (10 seconds)
        if current_time - self.creation_time >= 10000:
            self.create_explosion()
            self.kill()

        # Check collision with the player
        for sprite in self.all_sprites:
            if isinstance(sprite, Spaceship) and self.hitbox.colliderect(sprite.rect):
                sprite.health -= self.damage
                self.create_explosion()
                self.kill()

        # Check collision with the player
        for sprite in self.all_sprites:
            if isinstance(sprite, Spaceship) and self.hitbox.colliderect(sprite.rect):
                sprite.health -= self.damage
                self.create_explosion()
                self.kill()
                
    def create_explosion(self):
        explosion = Explosion(self.rect.center, self.all_sprites, self.explosion_group)
        self.all_sprites.add(explosion)
        self.explosion_group.add(explosion)

class Missile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target):
        super().__init__()
        self.image = missile_image
        self.rect = self.image.get_rect(center=start_pos)
        self.target = target

    def update(self):
        # Move towards the target (spaceship)
        direction = (self.target.position - pygame.math.Vector2(self.rect.center)).normalize()
        self.rect.move_ip(direction * 5)  # Adjust speed as necessary

        # Kill if it hits the target
        if pygame.sprite.collide_rect(self, self.target):
            self.kill()

class TrackingMissile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target, initial_velocity, all_sprites, explosion_group):
        super().__init__()
        self.image = tracking_missile_image
        self.rect = self.image.get_rect(center=start_pos)
        self.target = target
        self.position = pygame.math.Vector2(start_pos)
        self.velocity = initial_velocity.normalize() * 5 if initial_velocity.length() != 0 else pygame.math.Vector2(0, -5)
        self.max_speed = 5
        self.turn_speed = 0.1  # Control how sharp the missile can turn
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group
        self.lifetime = 5000  # Lifetime in milliseconds
        self.creation_time = pygame.time.get_ticks()

        global current_missiles

        # Play missile launch sound and manage the volume
        missile_channel.set_volume(1.0)  # Full volume for the missile sound
        missile_channel.play(missile_sound)
        
        current_missiles += 1
        update_missile_run_volume()

    def update(self):
        global current_missiles

        current_time = pygame.time.get_ticks()

        # Check if the missile exceeded its lifetime
        if current_time - self.creation_time > self.lifetime:
            self.create_explosion()
            self.kill()
            return

        # If the target is None or not alive, find a new closest target
        if self.target is None or not self.target.alive():
            self.target = self.find_closest_enemy()

        if self.target:
            # Calculate the desired direction towards the target
            target_vector = self.target.position - self.position
            target_vector = target_vector.normalize()

            # Adjust the missile's velocity towards the target
            self.velocity = self.velocity + (target_vector * self.turn_speed)
            if self.velocity.length() > self.max_speed:
                self.velocity = self.velocity.normalize() * self.max_speed

        # Update the missile's position
        self.position += self.velocity
        self.rect.center = self.position

        # Rotate the missile image to match the direction
        angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
        self.image = pygame.transform.rotate(tracking_missile_image, angle)
        self.rect = self.image.get_rect(center=self.position)

        # Check for collision with any enemy
        hit_enemy = pygame.sprite.spritecollideany(self, enemies_group)
        if hit_enemy:
            hit_enemy.health -= 50  # Adjust the damage value as needed
            self.create_explosion()

            if hit_enemy.health <= 0:
                hit_enemy.kill()
                # Increment kill count for spaceship
                for sprite in self.all_sprites:
                    if isinstance(sprite, Spaceship):
                        sprite.kill_count += 1

            self.kill()

    def create_explosion(self):
        explosion = Explosion(self.rect.center, self.all_sprites, self.explosion_group)
        self.all_sprites.add(explosion)
        self.explosion_group.add(explosion)

    def find_closest_enemy(self):
        closest_enemy = None
        closest_distance = float('inf')
        for enemy in enemies_group:
            distance = self.position.distance_to(enemy.position)
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
        return closest_enemy

    def kill(self):
        # Decrement missile count and update volume
        global current_missiles
        current_missiles = max(0, current_missiles - 1)
        update_missile_run_volume()
        super().kill()

class Neutrons(pygame.sprite.Sprite):
    def __init__(self, start_pos, target, all_sprites):
        super().__init__()
        self.image = neutrons_image
        self.rect = self.image.get_rect(center=start_pos)
        self.target = target
        self.all_sprites = all_sprites

    def update(self):
        # Move towards the target (spaceship)
        direction = (self.target.position - pygame.math.Vector2(self.rect.center)).normalize()
        self.rect.move_ip(direction * 5)  # Adjust speed as necessary

        # Kill if it hits the target
        if pygame.sprite.collide_rect(self, self.target):
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, all_sprites, explosion_group):
        super().__init__()
        self.center = center
        self.radius = 10
        self.max_radius = 50
        self.alpha = 255
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group

        # Create a surface for the explosion
        self.image = pygame.Surface((self.max_radius * 2, self.max_radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.center)

        global current_explosions

        # Play explosion sound and manage the volume
        if current_explosions < MAX_SIMULTANEOUS_EXPLOSIONS:
            explosion_channel.set_volume(1.0)  # Set to full volume
        else:
            explosion_channel.set_volume(0.5)  # Lower the volume if too many explosions

        explosion_channel.play(explosion_sound)
        current_explosions += 1

    def update(self):
        global current_explosions

        if self.radius < self.max_radius:
            self.radius += 2
        if self.alpha > 0:
            self.alpha = max(0, 255 - int((self.radius / self.max_radius) * 255))
        else:
            self.kill()
            current_explosions = max(0, current_explosions - 1)  # Decrement the explosion count

        # Update the image with the new explosion size and transparency
        self.image.fill((0, 0, 0, 0))  # Clear the surface with transparency
        pygame.draw.circle(self.image, (255, 0, 0, self.alpha), (self.max_radius, self.max_radius), self.radius)

        # Update the rect to keep it centered
        self.rect = self.image.get_rect(center=self.center)

class StrafingEnemy(pygame.sprite.Sprite):
    def __init__(self, target, all_sprites, enemy_missiles, explosion_group):
        super().__init__()
        self.original_image = pygame.transform.scale(strafe_enemy_image, (int(strafe_enemy_image.get_width() * 1.25), int(strafe_enemy_image.get_height() * 1.25)))
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, WIDTH)
        self.rect.y = random.randint(0, HEIGHT)
        self.position = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)
        self.target = target
        self.all_sprites = all_sprites
        self.enemy_missiles = enemy_missiles
        self.shoot_cooldown = 3000  # Cooldown in milliseconds (3 seconds)
        self.last_shot_time = pygame.time.get_ticks()
        self.health = 5000  # Large health pool
        self.min_distance = 200  # Minimum distance from the player
        self.max_speed = 6  # Maximum speed
        self.acceleration = 0.1  # Acceleration rate
        self.deceleration = 0.02  # Deceleration rate
        self.circling_direction = pygame.math.Vector2(1, 0)  # Direction to circle the player
        self.explosion_group = explosion_group
        self.missile_shoot_times = []  # Times when each missile should be shot

    def update(self):
        # Calculate direction towards the target (spaceship)
        direction = self.target.position - self.position
        distance = direction.length()

        if distance > self.min_distance:
            # Move towards the player if too far
            direction = direction.normalize()
            self.velocity += direction * self.acceleration  # Accelerate towards the player
            self.circling_direction = pygame.math.Vector2(-direction.y, direction.x).normalize()
        else:
            # Move in a circular path around the player
            self.velocity += self.circling_direction * self.acceleration

            # Adjust the circling direction based on the player's position
            perpendicular_direction = pygame.math.Vector2(-direction.y, direction.x).normalize()
            self.circling_direction = perpendicular_direction

        # Apply deceleration if no input
        if self.velocity.length() > 0:
            self.velocity -= self.velocity.normalize() * self.deceleration

        # Clamp the velocity to the maximum speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        # Update position
        self.position += self.velocity
        self.rect.center = self.position

        # Rotate the enemy image to match the direction of movement
        if self.velocity.length_squared() > 0:
            angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)

        # Shoot missiles if it's time
        current_time = pygame.time.get_ticks()
        if (current_time - self.last_shot_time) >= self.shoot_cooldown:
            self.missile_shoot_times = [current_time, current_time + 250, current_time + 500]
            self.last_shot_time = current_time + 750  # Set the next cooldown time after the last missile

        for shoot_time in self.missile_shoot_times:
            if current_time >= shoot_time:
                self.shoot_missile()
                self.missile_shoot_times.remove(shoot_time)

        # Kill if off screen
        if self.rect.right < 0:
            self.rect.left = WIDTH
        elif self.rect.left > WIDTH:
            self.rect.right = 0
        if self.rect.bottom < 0:
            self.rect.top = HEIGHT
        elif self.rect.top > HEIGHT:
            self.rect.bottom = 0

    def shoot_missile(self):
        missile = StrafeMissile(self.rect.center, self.target, self.all_sprites, self.explosion_group)
        self.all_sprites.add(missile)
        self.enemy_missiles.add(missile)

class StrafeMissile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target, all_sprites, explosion_group):
        super().__init__()
        self.original_image = pygame.transform.scale(missile_image, (12, 24))  # Narrower missile
        self.image = self.original_image
        self.rect = self.image.get_rect(center=start_pos)
        self.target = target
        self.position = pygame.math.Vector2(start_pos)
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 5  # Adjust speed as necessary
        self.turn_rate = 10  # Sharpness of turns
        self.damage = 300
        self.lifetime = 3000  # Lifetime in milliseconds
        self.creation_time = pygame.time.get_ticks()
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group

        global current_missiles

        # Play missile launch sound and manage the volume
        missile_channel.set_volume(1.0)  # Full volume for the missile sound
        missile_channel.play(missile_sound)
        
        current_missiles += 1
        update_missile_run_volume()

    def update(self):
        global current_missiles

        # Check if missile has exceeded its lifetime
        if pygame.time.get_ticks() - self.creation_time > self.lifetime:
            self.create_explosion()
            self.kill()
            return

        # Move towards the target (the player's spaceship)
        direction = (self.target.position - self.position).normalize()
        self.velocity = self.velocity + (direction * self.turn_rate)
        if self.velocity.length() > self.speed:
            self.velocity = self.velocity.normalize() * self.speed

        self.position += self.velocity
        self.rect.center = self.position

        # Rotate the missile image to match the direction
        angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Check collision with the player
        if pygame.sprite.collide_rect(self, self.target):
            self.target.health -= self.damage
            self.create_explosion()
            self.kill()
            if self.target.health <= 0:
                self.target.kill()
                global running
                running = False

    def create_explosion(self):
        explosion = Explosion(self.rect.center, self.all_sprites, self.explosion_group)
        self.all_sprites.add(explosion)
        self.explosion_group.add(explosion)

    def kill(self):
        # Decrement missile count and update volume
        global current_missiles
        current_missiles = max(0, current_missiles - 1)
        update_missile_run_volume()
        super().kill()
        
class AmbushEnemy(pygame.sprite.Sprite):
    def __init__(self, target, all_sprites, enemy_missiles, explosion_group):
        super().__init__()
        self.original_image = ambush_image  # Use the provided ambush image
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.position = pygame.math.Vector2(random.randint(0, WIDTH), random.randint(0, HEIGHT))
        self.rect.center = self.position
        self.velocity = pygame.math.Vector2(0, 0)
        self.target = target
        self.all_sprites = all_sprites
        self.enemy_missiles = enemy_missiles
        self.explosion_group = explosion_group
        self.health = 100  # Health points for Ambush
        self.min_distance = 340  # Minimum distance from the player
        self.max_speed = 8  # Maximum speed (faster than strafing enemy)
        self.acceleration = 0.2  # Acceleration rate
        self.deceleration = 0.02  # Deceleration rate
        self.shoot_cooldown = 2000  # Cooldown in milliseconds (2 seconds)
        self.last_shot_time = pygame.time.get_ticks()

        # Step back by 10 units from the initial position
        self.step_back_distance = 10  # Units to step back upon spawn
        self.has_stepped_back = False  # Track if the enemy has already stepped back

    def update(self):
        if not self.has_stepped_back:
            self.step_back_from_player()
        else:
            self.perform_normal_behavior()

    def step_back_from_player(self):
        # Calculate the direction away from the player
        direction = self.position - self.target.position
        if direction.length_squared() > 0:
            direction = direction.normalize()
        
        # Step back by 10 units
        self.position += direction * self.step_back_distance
        self.rect.center = self.position
        self.has_stepped_back = True

    def perform_normal_behavior(self):
        direction = self.target.position - self.position
        distance = direction.length()

        # Ensure the enemy maintains the minimum distance before moving closer
        if distance > self.min_distance or self.velocity.length_squared() == 0:
            direction = direction.normalize()
            self.velocity += direction * self.acceleration
        else:
            # Maintain momentum and avoid deceleration
            self.velocity *= 1.05

        # Clamp the velocity to the maximum speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        # Update position
        self.position += self.velocity
        self.rect.center = self.position

        # Rotate the enemy image to match the direction of movement (always towards the player)
        if self.velocity.length_squared() > 0:
            angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.position)

        # Shoot bullets towards the player's predicted position or directly at the player if they are not moving
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_cooldown:
            self.shoot_at_player_or_prediction()
            self.last_shot_time = current_time

        # If health is below 5%, move towards the player for a suicide attack
        if self.health < 5:
            self.suicide_attack()

        # Kill if off screen
        if self.rect.right < 0:
            self.rect.left = WIDTH
        elif self.rect.left > WIDTH:
            self.rect.right = 0
        if self.rect.bottom < 0:
            self.rect.top = HEIGHT
        elif self.rect.top > HEIGHT:
            self.rect.bottom = 0

    def shoot_at_player_or_prediction(self):
        # Remove the angle calculation and directly instantiate AmbushBullet
        ambush_bullet = AmbushBullet(self.rect.center, self.target)
        self.all_sprites.add(ambush_bullet)
        bullets.add(ambush_bullet)

    def suicide_attack(self):
        # Fly directly towards the player at maximum speed
        direction = self.target.position - self.position
        if direction.length_squared() > 0:
            direction = direction.normalize()
        self.velocity = direction * (self.max_speed * 2)  # Double speed for suicide attack

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.kill()

class AmbushBullet(Bullet):
    def __init__(self, start_pos, target):
        # Initialize with speed 3x and damage 5x the normal bullet
        speed = 30
        damage = 100
        super().__init__(start_pos, 0, speed=speed, damage=damage, spaceship=target)  # Angle will be calculated

        # Set the bullet image using the preloaded and scaled image
        self.image = AMBUSH_BULLET_IMAGE
        self.rect = self.image.get_rect(center=start_pos)
        self.target = target  # The target is the player's spaceship

        # Play the sniper shot sound (reused for Ambush's shot)
        sniper_shot_channel.play(sniper_shot_sound)

    def update(self):
        # Predict the future position of the player based on their velocity and distance to target
        to_target_vector = self.target.position - pygame.math.Vector2(self.rect.center)
        distance_to_target = to_target_vector.length()

        # Predict the time it would take to reach the target
        if self.velocity.length() > 0:
            time_to_target = distance_to_target / self.velocity.length()
        else:
            time_to_target = 0

        # Predict where the player will be in that time
        future_position = self.target.position + self.target.velocity * time_to_target

        # Adjust the bullet's trajectory to point towards the predicted future position
        direction_vector = (future_position - pygame.math.Vector2(self.rect.center)).normalize()
        self.velocity = direction_vector * self.velocity.length()

        # Rotate the bullet image to match the new direction
        angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
        self.image = pygame.transform.rotate(AMBUSH_BULLET_IMAGE, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Move the bullet according to its velocity
        self.rect.move_ip(self.velocity)

        # Kill the bullet if it goes off-screen
        if self.rect.left < 0 or self.rect.right > WIDTH or self.rect.top < 0 or self.rect.bottom > HEIGHT:
            self.kill()

        # Check for collisions with the player's spaceship
        if pygame.sprite.collide_rect(self, self.target):
            self.target.health -= self.damage
            if self.target.health <= 0:
                global running
                running = False
            self.kill()  # Destroy the bullet after it hits the player

class BossMissile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target, all_sprites, explosion_group):
        super().__init__()
        self.original_image = pygame.transform.scale(missile_image, (12, 24))  # Narrower missile
        self.image = self.original_image
        self.rect = self.image.get_rect(center=start_pos)
        self.target = target
        self.position = pygame.math.Vector2(start_pos)
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 10  # Adjust speed as necessary
        self.turn_rate = 10  # Sharpness of turns
        self.damage = 450
        self.lifetime = 2500  # Lifetime in milliseconds
        self.creation_time = pygame.time.get_ticks()
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group

        global current_missiles

        # Play missile launch sound and manage the volume
        missile_channel.set_volume(1.0)  # Full volume for the missile sound
        missile_channel.play(missile_sound)
        
        current_missiles += 1
        update_missile_run_volume()

    def update(self):
        global current_missiles

        # Check if missile has exceeded its lifetime
        if pygame.time.get_ticks() - self.creation_time > self.lifetime:
            self.create_explosion()
            self.kill()
            return

        # Move towards the target (the player's spaceship)
        direction = (self.target.position - self.position).normalize()
        self.velocity = self.velocity + (direction * self.turn_rate)
        if self.velocity.length() > self.speed:
            self.velocity = self.velocity.normalize() * self.speed

        self.position += self.velocity
        self.rect.center = self.position

        # Rotate the missile image to match the direction
        angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

        # Check collision with the player
        if pygame.sprite.collide_rect(self, self.target):
            self.target.health -= self.damage
            self.create_explosion()
            self.kill()
            if self.target.health <= 0:
                self.target.kill()
                global running
                running = False

    def create_explosion(self):
        explosion = Explosion(self.rect.center, self.all_sprites, self.explosion_group)
        self.all_sprites.add(explosion)
        self.explosion_group.add(explosion)

    def kill(self):
        # Decrement missile count and update volume
        global current_missiles
        current_missiles = max(0, current_missiles - 1)
        update_missile_run_volume()
        super().kill()

# BossTrap class
class BossTrap(pygame.sprite.Sprite):
    def __init__(self, position, all_sprites, explosion_group):
        super().__init__()
        self.position = position
        self.frames = frames
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=self.position)
        self.animation_speed = frame_duration  # Set frame duration to be 2x faster
        self.last_update_time = pygame.time.get_ticks()
        self.all_sprites = all_sprites
        self.explosion_group = explosion_group
        self.hitbox = pygame.Rect(self.position[0] - 20, self.position[1] - 20, 40, 40)
        self.damage = 600
        self.creation_time = pygame.time.get_ticks()  # Track the time when the trap was created

        if not trap_channel.get_busy():
            trap_channel.play(trap_sound)

    def update(self):
        # Animate the trap
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.rect = self.image.get_rect(center=self.position)
            self.last_update_time = current_time

        # Check if the trap has reached its maximum duration (10 seconds)
        if current_time - self.creation_time >= 10000:
            self.create_explosion()
            self.kill()

        # Check collision with the player
        for sprite in self.all_sprites:
            if isinstance(sprite, Spaceship) and self.hitbox.colliderect(sprite.rect):
                sprite.health -= self.damage
                self.create_explosion()
                self.kill()

    def create_explosion(self):
        explosion = Explosion(self.rect.center, self.all_sprites, self.explosion_group)
        self.all_sprites.add(explosion)
        self.explosion_group.add(explosion)

class BossAura(pygame.sprite.Sprite):
    def __init__(self, boss, player, damage_interval=50, damage_percentage=90):
        super().__init__()
        self.boss = boss
        self.player = player
        self.radius = 150  # Set the radius of the aura as desired
        self.damage_interval = damage_interval  # Time between damage applications in milliseconds
        self.damage_percentage = damage_percentage  # Percentage of player's health to be deducted
        self.last_damage_time = pygame.time.get_ticks()  # Track the last time damage was applied

        # Create a surface for the aura
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.boss.rect.center)

        # Fading properties
        self.alpha = 0  # Current alpha value
        self.fade_speed = 5  # How quickly the aura fades in/out
        self.fade_direction = 1  # 1 for fade in, -1 for fade out

        self.active = True  # Flag to control aura activation

    def update(self):
        if not self.active:
            self.image.fill((0, 0, 0, 0))  # Clear the image when inactive
            return

        # Update the position of the aura to match the boss's position
        self.rect.center = self.boss.rect.center

        # Update the aura's alpha for a fade effect
        self.alpha += self.fade_speed * self.fade_direction

        # Reverse fade direction if necessary
        if self.alpha >= 255:
            self.alpha = 255
            self.fade_direction = -1  # Start fading out
        elif self.alpha <= 0:
            self.alpha = 0
            self.fade_direction = 1  # Start fading in

        # Clear the image before drawing the new aura
        self.image.fill((0, 0, 0, 0))  # Fill with transparent color

        # Draw a red circle with the current alpha
        pygame.draw.circle(self.image, (255, 0, 0, self.alpha), (self.radius, self.radius), self.radius)

        # Check collision with the player's spaceship
        if self.rect.colliderect(self.player.rect):
            # Calculate the distance between the player's center and the aura's center
            distance = pygame.math.Vector2(self.player.rect.center).distance_to(self.rect.center)
            if distance < self.radius:
                current_time = pygame.time.get_ticks()
                if current_time - self.last_damage_time >= self.damage_interval:
                    self.apply_damage()
                    self.last_damage_time = current_time

    def apply_damage(self):
        # Calculate damage based on the player's current health
        damage = self.player.health * self.damage_percentage
        self.player.health -= damage
        if self.player.health <= 0:
            global running
            running = False

    def set_active(self, is_active):
        self.active = is_active  # Enable or disable the aura

class Boss(pygame.sprite.Sprite):
    def __init__(self, target, all_sprites, enemy_missiles, explosion_group):
        super().__init__()
        self.original_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Stratos.png")
        self.original_image = pygame.transform.scale(self.original_image, (int(self.original_image.get_width() * 1.25), int(self.original_image.get_height() * 1.25)))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.position = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)
        self.target = target
        self.all_sprites = all_sprites
        self.enemy_missiles = enemy_missiles
        self.explosion_group = explosion_group
        self.health = 1000  # Large health pool for the boss
        self.max_health = self.health
        self.min_distance = 400  # Initial minimum distance from the player
        self.max_speed = 3  # Maximum speed (2x slower than strafing enemy)
        self.acceleration = 0.05  # Acceleration rate
        self.deceleration = 0.01  # Deceleration rate
        self.circling_direction = pygame.math.Vector2(1, 0)  # Direction to circle the player

        # Phase control
        self.phase = "missile"  # Initial phase
        self.phase_duration = {"missile": 25000, "trap": 30000}  # Duration of each phase in milliseconds
        self.last_phase_change_time = pygame.time.get_ticks()
        self.transparency = 255  # Initial transparency
        self.fading = False  # Flag to indicate if the boss is fading
        self.fade_duration = 2000  # Duration of fade in milliseconds

        self.shoot_cooldown = 150  # Cooldown in milliseconds (0.15 seconds)
        self.last_shot_time = pygame.time.get_ticks()
        self.trap_cooldown = 5000  # Deploy trap every 5 seconds
        self.last_trap_time = pygame.time.get_ticks()

        # Aura radius for visual effect
        self.aura_radius = 100  # Set the radius of the aura as desired

        # Hitbox radius for collision detection
        self.hitbox_radius = 50

        # Create a boss aura that damages the player
        self.aura = BossAura(self, self.target)
        self.all_sprites.add(self.aura)

        # Adjust the rect size to match the hitbox radius
        self.rect = pygame.Rect(0, 0, self.hitbox_radius * 2, self.hitbox_radius * 2)
        self.rect.center = self.position

        # Define the rotor positions relative to the center of the boss
        self.rotor_offsets = [
            pygame.math.Vector2(-30, -40),  # Top-left rotor
            pygame.math.Vector2(30, -40),   # Top-right rotor
            pygame.math.Vector2(-30, 40),   # Bottom-left rotor
            pygame.math.Vector2(30, 40)     # Bottom-right rotor
        ]

    def update(self):
        current_time = pygame.time.get_ticks()

        # Phase switching logic
        if current_time - self.last_phase_change_time >= self.phase_duration[self.phase]:
            self.last_phase_change_time = current_time
            self.fading = True
            self.fade_start_time = current_time

        # Handle fading effect
        if self.fading:
            fade_progress = (current_time - self.fade_start_time) / self.fade_duration
            if fade_progress >= 1:
                self.fading = False
                self.phase = "trap" if self.phase == "missile" else "missile"
                self.transparency = 0 if self.phase == "trap" else 255
                # Enable or disable the aura based on the current phase
                self.aura.set_active(self.phase == "missile")
                # Adjust min_distance based on phase
                self.min_distance = 200 if self.phase == "trap" else 400
            else:
                self.transparency = int(255 * (1 - fade_progress)) if self.phase == "missile" else int(255 * fade_progress)
            self.image = self.original_image.copy()
            self.image.set_alpha(self.transparency)

        # Missile phase logic
        if self.phase == "missile" and not self.fading:
            if current_time - self.last_shot_time >= self.shoot_cooldown:
                self.shoot_rotor_missiles()
                self.last_shot_time = current_time

        # Trap phase logic
        if self.phase == "trap" and not self.fading:
            if current_time - self.last_trap_time >= self.trap_cooldown:
                self.deploy_trap()
                self.last_trap_time = current_time

        # Calculate direction towards the target (spaceship)
        direction = self.target.position - self.position
        distance = direction.length()

        if distance > self.min_distance:
            # Move towards the player if too far
            if direction.length_squared() > 0:
                direction = direction.normalize()
            self.velocity += direction * self.acceleration  # Accelerate towards the player
            self.circling_direction = pygame.math.Vector2(-direction.y, direction.x).normalize() if direction.length_squared() > 0 else self.circling_direction
        else:
            # Move in a circular path around the player
            if direction.length_squared() > 0:
                perpendicular_direction = pygame.math.Vector2(-direction.y, direction.x).normalize()
                self.circling_direction = perpendicular_direction

            self.velocity += self.circling_direction * self.acceleration

        # Apply deceleration if no input
        if self.velocity.length() > 0:
            self.velocity -= self.velocity.normalize() * self.deceleration

        # Clamp the velocity to the maximum speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        # Update position
        self.position += self.velocity
        self.rect.center = self.position

        # Update the hitbox to match the hitbox radius
        self.hitbox = pygame.Rect(0, 0, self.hitbox_radius * 2, self.hitbox_radius * 2)
        self.hitbox.center = self.position

        # Rotate the boss image to match the direction of movement
        if self.velocity.length_squared() > 0:
            angle = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) - 90
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.image.set_alpha(self.transparency)
            self.rect = self.image.get_rect(center=self.rect.center)

        # Kill if off screen
        if self.rect.right < 0:
            self.rect.left = WIDTH
        elif self.rect.left > WIDTH:
            self.rect.right = 0
        if self.rect.bottom < 0:
            self.rect.top = HEIGHT
        elif self.rect.top > HEIGHT:
            self.rect.bottom = 0

    def shoot_rotor_missiles(self):
        for offset in self.rotor_offsets:
            missile_position = self.position + offset
            missile = BossMissile(missile_position, self.target, self.all_sprites, self.explosion_group)
            self.all_sprites.add(missile)
            self.enemy_missiles.add(missile)

    def deploy_trap(self):
        trap = BossTrap(self.rect.center, self.all_sprites, self.explosion_group)
        trap.damage = 6000  # Set trap damage to 6000
        self.all_sprites.add(trap)
        traps.add(trap)

    def draw_health_bar(self, screen):
        # Calculate health bar dimensions and position
        bar_length = 100
        bar_height = 10
        bar_x = self.rect.centerx - bar_length // 2
        bar_y = self.rect.bottom + 10

        # Draw background bar
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_length, bar_height))

        # Draw current health bar
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_length * health_ratio, bar_height))

    def kill(self):
        self.aura.kill()  # Remove the aura when the boss is killed
        super().kill()  # Call the parent class's kill method

class BossSpawnIndicator(pygame.sprite.Sprite):
    def __init__(self, position, duration, fade_duration, blink_interval=500):
        super().__init__()
        self.position = position
        self.radius = 150
        self.alpha = 0
        self.creation_time = pygame.time.get_ticks()
        self.duration = duration
        self.fade_duration = fade_duration
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.position)
        self.blink_interval = blink_interval
        self.last_blink_time = pygame.time.get_ticks()
        self.blinking = True

    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.creation_time

        # Handle blinking effect with fade transition
        blink_phase = (elapsed_time // self.blink_interval) % 2
        if blink_phase == 0:
            fade_progress = (elapsed_time % self.blink_interval) / self.blink_interval
            self.alpha = int(fade_progress * 255)
        else:
            fade_progress = (elapsed_time % self.blink_interval) / self.blink_interval
            self.alpha = int((1 - fade_progress) * 255)

        # Update the alpha for fade in/out effect
        if elapsed_time < self.fade_duration:
            overall_fade_progress = elapsed_time / self.fade_duration
            self.alpha = int(overall_fade_progress * self.alpha)
        elif elapsed_time > self.duration - self.fade_duration:
            overall_fade_progress = (self.duration - elapsed_time) / self.fade_duration
            self.alpha = int(overall_fade_progress * self.alpha)

        # Clear the image before drawing the new circle
        self.image.fill((0, 0, 0, 0))  # Fill with transparent color

        # Draw a red circle with the current alpha
        pygame.draw.circle(self.image, (255, 0, 0, self.alpha), (self.radius, self.radius), self.radius)
        
class SnareBoss(pygame.sprite.Sprite):
    def __init__(self, target, all_sprites, enemy_missiles, explosion_group):
        super().__init__()
        self.original_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\Snare.png")
        self.original_image = pygame.transform.scale(self.original_image, (int(self.original_image.get_width() * 1.25), int(self.original_image.get_height() * 1.25)))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.position = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(0, 0)
        self.target = target
        self.all_sprites = all_sprites
        self.enemy_missiles = enemy_missiles
        self.explosion_group = explosion_group
        self.health = 800  # Snare's health pool
        self.max_health = self.health
        self.min_distance = 300  # Minimum distance from the player
        self.max_speed = 6  # Fast speed
        self.acceleration = 0.15  # Acceleration rate
        self.deceleration = 0.05  # Deceleration rate
        self.last_damage_time = pygame.time.get_ticks()  # Track last time of damage for healing

        # Weapons and behavior timers
        self.behavior_timer = pygame.time.get_ticks()
        self.behavior_switch_interval = 5000  # Switch behavior every 5 seconds
        self.is_shooting_ambush = True  # Start with ambush bullets
        self.shoot_cooldown = 150  # Ambush shooting cooldown in milliseconds
        self.last_shot_time = pygame.time.get_ticks()
        self.heal_per_second = 200  # Heal 200 HP per second after 3 seconds of no damage
        self.undamaged_duration = 3000  # Must be undamaged for 3 seconds to start healing
        self.step_back = False

    def update(self):
        current_time = pygame.time.get_ticks()

        # Check if it's time to switch between ambush bullets and traps
        if current_time - self.behavior_timer >= self.behavior_switch_interval:
            self.behavior_timer = current_time
            self.is_shooting_ambush = not self.is_shooting_ambush
            self.step_back = True  # Step back from the player

        # Step back from the player before returning to normal behavior
        if self.step_back:
            self.step_back_from_player()
        else:
            self.perform_normal_behavior()

        # Shooting ambush bullets or deploying traps based on the behavior
        if self.is_shooting_ambush and not self.step_back:
            self.shoot_ambush_bullets(current_time)
        elif not self.is_shooting_ambush and not self.step_back:
            self.deploy_trap()

        # Handle healing logic
        self.handle_healing(current_time)

    def step_back_from_player(self):
        # Calculate the direction away from the player
        direction = self.position - self.target.position
        if direction.length_squared() > 0:
            direction = direction.normalize()
        
        # Step back
        self.position += direction * 10  # Step back by 10 units
        self.rect.center = self.position
        self.step_back = False

    def perform_normal_behavior(self):
        # Feint-like behavior: keep a certain distance from the player
        direction = self.target.position - self.position
        distance = direction.length()

        if distance > self.min_distance:
            direction = direction.normalize()
            self.velocity += direction * self.acceleration
        else:
            self.velocity *= 0.95  # Slow down when at minimum distance

        # Apply deceleration if no input
        if self.velocity.length() > 0:
            self.velocity -= self.velocity.normalize() * self.deceleration

        # Clamp the velocity to the maximum speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        # Update position
        self.position += self.velocity
        self.rect.center = self.position

    def shoot_ambush_bullets(self, current_time):
        if current_time - self.last_shot_time >= self.shoot_cooldown:
            ambush_bullet = AmbushBullet(self.rect.center, self.target)
            self.all_sprites.add(ambush_bullet)
            bullets.add(ambush_bullet)
            self.last_shot_time = current_time

    def deploy_trap(self):
        trap = Trap(self.rect.center, self.all_sprites, self.explosion_group)
        self.all_sprites.add(trap)
        traps.add(trap)

    def handle_healing(self, current_time):
        # Heal only if not damaged in the last 3 seconds
        if current_time - self.last_damage_time >= self.undamaged_duration:
            self.health = min(self.max_health, self.health + self.heal_per_second / 60)  # Heal at 60 FPS

    def take_damage(self, damage):
        self.health -= damage
        self.last_damage_time = pygame.time.get_ticks()  # Reset the damage timer
        if self.health <= 0:
            self.kill()

    def draw_health_bar(self, screen):
        # Same as previous boss, draw the health bar
        bar_length = 100
        bar_height = 10
        bar_x = self.rect.centerx - bar_length // 2
        bar_y = self.rect.bottom + 10
        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_length, bar_height))  # Background
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_length * health_ratio, bar_height))  # Health

    def kill(self):
        super().kill()

class AutoTurret(pygame.sprite.Sprite):
    def __init__(self, position, all_sprites, enemies_group):
        super().__init__()
        # Load the setup GIF frames
        setup_gif_path = "C:\\Users\\hweeh\\Downloads\\pygame image database\\autoturret setting up.gif"
        gif = Image.open(setup_gif_path)
        self.frames = []
        self.load_gif_frames(gif)
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(center=position)
        self.all_sprites = all_sprites
        self.enemies_group = enemies_group
        self.setup_duration = 5000  # 5 seconds setup time
        self.setup_start_time = pygame.time.get_ticks()
        self.is_setup = False
        self.is_assigned = False
        self.weapon_type = None
        self.health = 200
        self.max_health = 200
        self.rotation_speed = 2  # Default rotation speed
        self.shoot_cooldown = 1000  # Default shooting cooldown
        self.last_shot_time = 0

        self.original_position = pygame.math.Vector2(position)

        self.setup_complete_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\autoturret unassigned.png")
        self.active_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\autoturret active.png")
        self.broken_image = pygame.image.load("C:\\Users\\hweeh\\Downloads\\pygame image database\\autoturret active broken.png")

    def load_gif_frames(self, gif):
        scale_factor = 1.0  # Scale as needed
        try:
            while True:
                frame = gif.copy()
                frame = frame.resize((int(frame.width * scale_factor), int(frame.height * scale_factor)))
                self.frames.append(pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode))
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass

    def update(self):
        current_time = pygame.time.get_ticks()

        if not self.is_setup:
            self.handle_setup_phase(current_time)
        elif not self.is_assigned:
            self.handle_assignment_phase(current_time)
        else:
            self.handle_active_phase(current_time)

    def handle_setup_phase(self, current_time):
        if current_time - self.setup_start_time >= self.setup_duration:
            self.is_setup = True
            self.image = self.setup_complete_image
        else:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]

    def handle_assignment_phase(self, current_time):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]:
            player_pos = pygame.math.Vector2(self.all_sprites.sprites()[0].rect.center)
            distance = player_pos.distance_to(self.original_position)
            if distance <= 50:
                self.assign_weapon()

    def handle_active_phase(self, current_time):
        if self.health <= 0:
            self.kill()
            return

        if self.health <= self.max_health * 0.2:
            self.image = self.broken_image
            self.rotation_speed = 1.2  # 40% reduced speed
            self.shoot_cooldown = int(self.shoot_cooldown * 1.3)  # 30% increased cooldown

        closest_enemy = self.find_closest_enemy()
        if closest_enemy:
            self.rotate_towards(closest_enemy)
            if current_time - self.last_shot_time >= self.shoot_cooldown:
                self.shoot(closest_enemy)
                self.last_shot_time = current_time

    def find_closest_enemy(self):
        closest_enemy = None
        closest_distance = float('inf')
        for enemy in self.enemies_group:
            distance = pygame.math.Vector2(self.rect.center).distance_to(enemy.position)
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
        return closest_enemy

    def rotate_towards(self, enemy):
        direction = enemy.position - self.original_position
        angle = math.degrees(math.atan2(-direction.y, direction.x)) - 90
        self.image = pygame.transform.rotate(self.active_image, angle)
        self.rect = self.image.get_rect(center=self.original_position)

    def shoot(self, enemy):
        if self.weapon_type == "Normal":
            bullet = NormalBullet(self.rect.center, self.angle_to_enemy(enemy), self.all_sprites.sprites()[0])
        elif self.weapon_type == "Sniper":
            bullet = SniperBullet(self.rect.center, self.angle_to_enemy(enemy), self.all_sprites.sprites()[0])
        elif self.weapon_type == "Home":
            bullet = HomeBullet(self.rect.center, self.angle_to_enemy(enemy), self.all_sprites.sprites()[0])
        
        if bullet:
            self.all_sprites.add(bullet)
            bullets.add(bullet)

    def angle_to_enemy(self, enemy):
        direction = enemy.position - self.original_position
        return math.degrees(math.atan2(-direction.y, direction.x))

    def assign_weapon(self):
        # Implement a menu to choose between Normal, Sniper, and Home weapons
        weapon_choices = ["Normal", "Sniper", "Home"]
        chosen_weapon = random.choice(weapon_choices)  # Replace with actual menu logic
        self.weapon_type = chosen_weapon
        self.image = self.active_image
        self.is_assigned = True

    def draw_health_bar(self, screen):
        bar_length = 50
        bar_height = 5
        bar_x = self.rect.centerx - bar_length // 2
        bar_y = self.rect.bottom + 10

        pygame.draw.rect(screen, (255, 0, 0), (bar_x, bar_y, bar_length, bar_height))
        health_ratio = self.health / self.max_health
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_length * health_ratio, bar_height))

def draw_hud(screen, spaceship):
    # Draw health bar at the bottom
    health_ratio = spaceship.health / spaceship.initial_health
    pygame.draw.rect(screen, (255, 0, 0), (10, HEIGHT - 30, WIDTH - 20, 20))  # Background
    pygame.draw.rect(screen, (0, 255, 0), (10, HEIGHT - 30, (WIDTH - 20) * health_ratio, 20))  # Health

    # Display kill count at the bottom-right corner
    font = pygame.font.Font(None, 36)
    kill_count_text = f"Kill Count: {spaceship.kill_count}"
    kill_count_surface = font.render(kill_count_text, True, (255, 0, 0))
    kill_count_rect = kill_count_surface.get_rect(bottomright=(WIDTH - 10, HEIGHT - 35 ))
    screen.blit(kill_count_surface, kill_count_rect)

    # Display current weapon above the kill count
    weapon_text = f"Weapon: {spaceship.weapon_type}"
    weapon_surface = font.render(weapon_text, True, (255, 0, 0))
    weapon_rect = weapon_surface.get_rect(bottomright=(WIDTH - 10, HEIGHT - 55))
    screen.blit(weapon_surface, weapon_rect)

def fade_out_text(screen, message, font, duration, color, width, height, all_sprites, explosion_group, spaceship, boss_spawned, stratos):
    text_surface = font.render(message, True, color)
    text_rect = text_surface.get_rect(center=(width // 2, height // 2))
    
    for alpha in range(255, -1, -5):
        text_surface.set_alpha(alpha)
        
        # Clear the screen with the background color
        screen.fill(WHITE)
        
        # Draw all sprites
        all_sprites.draw(screen)
        
        # Draw the HUD (health bar, kill count, weapon type)
        draw_hud(screen, spaceship)
        
        # Draw the boss health bar if the boss is spawned
        if boss_spawned:
            stratos.draw_health_bar(screen)
        
        # Draw the fade-out text on top of everything
        screen.blit(text_surface, text_rect)
        
        # Update the display
        pygame.display.flip()
        
        # Delay to control the fade-out speed
        pygame.time.delay(int(duration / 51))  # Adjust delay to match the fade-out duration

    def update(self):
        current_time = pygame.time.get_ticks()

        # Handle blinking effect
        if current_time - self.last_blink_time >= self.blink_interval:
            self.blinking = not self.blinking
            self.last_blink_time = current_time

        # Update the alpha for fade effect
        elapsed_time = current_time - self.creation_time
        if elapsed_time >= self.duration:
            self.alpha = max(0, 255 - int((elapsed_time - self.duration) / self.duration * 255))

        # Clear the image before drawing the new circle
        self.image.fill((0, 0, 0, 0))  # Fill with transparent color

        if self.blinking:
            # Draw a red circle with the current alpha
            pygame.draw.circle(self.image, (255, 0, 0, self.alpha), (self.radius, self.radius), self.radius)

def main():
    # Initialize sprite groups
    all_sprites = pygame.sprite.Group()
    explosion_group = pygame.sprite.Group()

    spaceship = Spaceship(all_sprites, explosion_group)
    all_sprites.add(spaceship)

    global enemies_group
    enemies_group = pygame.sprite.Group()

    global traps
    traps = pygame.sprite.Group()

    global enemy_missiles
    enemy_missiles = pygame.sprite.Group()

    global laser_beams
    laser_beams = pygame.sprite.Group()

    global bullets
    bullets = pygame.sprite.Group()

    # Initialize Sound Room for the player
    sound_room = SoundRoom(spaceship, radius=250)

    clock = pygame.time.Clock()
    global running
    running = True
    
    # Timing and state variables
    last_strafe_spawn_time = pygame.time.get_ticks()
    last_feint_spawn_time = pygame.time.get_ticks()
    boss_spawned = False
    boss_defeated = False
    stop_spawning = False
    stage_cleared = False
    stage_clear_time = 0
    increased_spawn_rate = 1

    boss_spawn_indicator = None

    # Counter for AmbushEnemy spawning after the boss is defeated
    post_boss_kill_counter = 0

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:  # Switch to Sniper
                    spaceship.weapon_type = "Sniper"
                elif event.key == pygame.K_2:  # Switch to Home
                    spaceship.weapon_type = "Home"
                elif event.key == pygame.K_3:  # Switch to Normal
                    spaceship.weapon_type = "Normal"
                elif event.key == pygame.K_SPACE:
                    spaceship.shoot_missile()
                elif event.key == pygame.K_LALT:
                    if enemies_group:
                        neutron = Neutrons(spaceship.rect.center, spaceship, all_sprites)
                        all_sprites.add(neutron)
                elif event.key == pygame.K_LSHIFT:
                    spaceship.shoot_tracking_missile()
                elif event.key == pygame.K_e:
                    turret = AutoTurret(spaceship.rect.center, all_sprites, enemies_group)
                    all_sprites.add(turret)
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_e:
                    spaceship.release_laser()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    spaceship.start_shooting()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    spaceship.stop_shooting()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            spaceship.velocity.y -= 0.5
        if keys[pygame.K_s]:
            spaceship.velocity.y += 0.5
        if keys[pygame.K_a]:
            spaceship.velocity.x -= 0.5
        if keys[pygame.K_d]:
            spaceship.velocity.x += 0.5

        # Stop spawning normal enemies if kill count reaches a certain number and the boss is not defeated yet
        if spaceship.kill_count >= 1 and not boss_defeated:
            stop_spawning = True
            
        # In the main loop
        if spaceship.kill_count >= 20 and not boss_spawned and not boss_defeated:
            snare = SnareBoss(spaceship, all_sprites, enemy_missiles, explosion_group)
            all_sprites.add(snare)
            enemies_group.add(snare)
            boss_spawned = True  # Set boss_spawned flag to prevent multiple spawns

        # Spawn normal enemies before the boss appears
        if not boss_spawned and not boss_defeated and not stop_spawning:
            if random.randint(0, 100) < 2 * increased_spawn_rate:
                enemy = Enemy(spaceship)
                all_sprites.add(enemy)
                enemies_group.add(enemy)

        # Check if all normal enemies are defeated before spawning the boss
        if stop_spawning and len(enemies_group) == 0 and not boss_spawned and not boss_defeated:
            if boss_spawn_indicator is None:
                boss_spawn_indicator = BossSpawnIndicator((WIDTH // 2, HEIGHT // 2), duration=3000, fade_duration=1500)
                all_sprites.add(boss_spawn_indicator)
            else:
                if pygame.time.get_ticks() - boss_spawn_indicator.creation_time >= boss_spawn_indicator.duration:
                    stratos = Boss(spaceship, all_sprites, enemy_missiles, explosion_group)
                    all_sprites.add(stratos)
                    enemies_group.add(stratos)
                    boss_spawned = True
                    boss_spawn_indicator.kill()
                    boss_spawn_indicator = None

        # Spawn special enemies after the boss is defeated
        if boss_defeated and not stage_cleared:
            current_time = pygame.time.get_ticks()

            # Spawn strafing enemy every 5 seconds
            if current_time - last_strafe_spawn_time >= 5000:
                strafing_enemy = StrafingEnemy(spaceship, all_sprites, enemy_missiles, explosion_group)
                all_sprites.add(strafing_enemy)
                enemies_group.add(strafing_enemy)
                last_strafe_spawn_time = current_time

            # Spawn feint enemy every 7 seconds
            if current_time - last_feint_spawn_time >= 7000:
                feint_enemy = FeintEnemy(spaceship, all_sprites, explosion_group, sound_room)
                all_sprites.add(feint_enemy)
                enemies_group.add(feint_enemy)
                last_feint_spawn_time = current_time

        # Ambush enemy spawning logic after boss defeat
        if boss_defeated:
            if post_boss_kill_counter >= 3:
                ambush_enemy = AmbushEnemy(spaceship, all_sprites, enemy_missiles, explosion_group)
                all_sprites.add(ambush_enemy)
                enemies_group.add(ambush_enemy)
                post_boss_kill_counter = 0  # Reset the counter

        # Collision detection between player and enemy
        player_hit = pygame.sprite.spritecollideany(spaceship, enemies_group)
        if player_hit:
            if isinstance(player_hit, Boss):
                direction = player_hit.position - spaceship.position
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                else:
                    direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize()

                player_hit.velocity += direction * 5
            else:
                damage_to_player = max(5, player_hit.health // 10)
                spaceship.health -= damage_to_player
                player_hit.kill()
                spaceship.kill_count += 1
                post_boss_kill_counter += 1  # Increment the counter for AmbushEnemy spawn
                if spaceship.health <= 0:
                    running = False

        # Check if the boss is defeated
        if boss_spawned and not stratos.alive():
            boss_spawned = False
            stop_spawning = True
            stage_cleared = True
            stage_clear_time = pygame.time.get_ticks()
            boss_defeated = True
            increased_spawn_rate *= 1.5

        # Handle stage clear message and resetting the game state
        if stage_cleared:
            elapsed_time = pygame.time.get_ticks() - stage_clear_time
            if elapsed_time < 5000:
                message = "You've reached Stage 2"
                fade_out_text(screen, message, pygame.font.Font(None, 36), 5000, (0, 255, 0), WIDTH, HEIGHT, all_sprites, explosion_group, spaceship, boss_spawned, stratos)
            else:
                stage_cleared = False

        # Update all sprite groups
        all_sprites.update()
        explosion_group.update()
        traps.update()

        # Clear screen
        screen.fill(WHITE)

        # Draw all sprites
        all_sprites.draw(screen)

        # Draw the HUD (weapon type and kill count)
        draw_hud(screen, spaceship)

        # Draw boss health bar if the boss is spawned
        if boss_spawned:
            stratos.draw_health_bar(screen)

        # Draw the sound room around the player for testing/debugging
        sound_room.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
