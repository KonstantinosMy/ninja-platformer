import pygame
from pygame import mixer
import os
import random
import csv

from pygame.display import update
import button

mixer.init()
pygame.init()


SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Irene^2_game')

#οριζουμε framerate
clock = pygame.time.Clock()
FPS = 60

#οριζουμε μεταβλητες
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False


#οριζουμε μεταβλητες παικτη
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False


#φορτωνουμε μουσικη και ηχους
pygame.mixer.music.load('audio/music2.mp3')
pygame.mixer.music.set_volume(0.03)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.05)
shot_fx = pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.05)
grenade_fx = pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.05)


#φορτωνουμε εικονες
#φορτωνουμε εικονες κουμπια
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()
#φοντο
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()
#αποθηκευουμε τα tiles σε μια λιστα
img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'img/Tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)
#αστερι
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
#βομβα
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
#κουτια ανεφοδιασμου
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
	'Health'	: health_box_img,
	'Ammo'		: ammo_box_img,
	'Grenade'	: grenade_box_img
}


#οριζουμε χρωματα
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

#οριζουμε γραμματοσειρα
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

#φτιαχνουμε ενα parallax εφε με ξεχωριστες εικονες που κινουνται σε διαφορετικο χρονο
def draw_bg():
	screen.fill(BG)
	width = sky_img.get_width()
	for x in range(5):
		screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
		screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
		screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
		screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))


#function για επαναφορα επιπεδου
def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	#δημιουργια λιστας για τα tiles
	data = []
	for row in range(ROWS):
		r = [-1] * COLS
		data.append(r)

	return data



#κλαση του παικτη μας
class ninja(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False
		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0
		
		#φορτωμα εικονων για την κινηση του παικτη
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			#επαναφορα λιστας
			temp_list = []
			#μετρημα αρχειων στον φακελο
			num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()


	def update(self):
		self.update_animation()
		self.check_alive()
		#ανανεωση cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown -= 1


	def move(self, moving_left, moving_right):
		#επαναφορα μεταβλητων κινησης
		screen_scroll = 0
		dx = 0
		dy = 0

		#αναθετω μεταβλητες για δεξια η αριστερα
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		#πηδημα
		if self.jump == True and self.in_air == False:
			self.vel_y = -14
			self.jump = False
			self.in_air = True

		#εφαρμογη βαρυτητας
		self.vel_y += GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy += self.vel_y

		#ελεγχος για επαφη( collision)
		for tile in world.obstacle_list:
			#ελεγχος για επαφη( collision) στον Χ
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
				#εαν ο εχθρος χτυπησει τοιχο τοτε να αλλαξει πορεια
				if self.char_type == 'enemy':
					self.direction *= -1
					self.move_counter = 0
			#ελεγχος για επαφη( collision) στον Υ 
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#ελεγχος εαν ειναι κατω απο το εδαφος
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#ελεγχος εαν ειναι πανω απο το εδαφος
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom


		#ελεγχος για επαφη με νερο, αρα θανατος
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health = 0

		#ελεγχος για επαφη με το τελος του επιπεδου
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True


		# for platform in platform_group:
		# 	if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
		# 		dx = 0
		# 	if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
		# 		if abs((self.rect.top + dy) - platform.rect.bottom) < 20:
		# 			self.vel_y = 0
		# 			dy = platform.rect.bottom - self.rect.top
		# 		elif abs((self.rect.bottom + dy) - platform.rect.top) < 20:
		# 			self.rect.bottom = platform.rect.top - 1
		# 			self.in_air = False
		# 			dy = 0
		# 		if platform.move_x != 0:
		# 			self.rect.x += platform.move_direction

				

		#ελεγχος για εαν πεσαμε κατω απο την πιστα, αρα θανατος
		if self.rect.bottom > SCREEN_HEIGHT:
			self.health = 0


		#ελεγχος για εαν ο παικτης παει στην ακρη της πιστας
		if self.char_type == 'player':
			if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
				dx = 0

		#ανανεωση rect
		self.rect.x += dx
		self.rect.y += dy

		#μετακινηση "καμερας" βαση του που βρισκεται ο παικτης
		if self.char_type == 'player':
			if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
				or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
				self.rect.x -= dx
				screen_scroll = -dx

		return screen_scroll, level_complete



	def shoot(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			#αφαιρουμε αστερι ανα βολη
			self.ammo -= 1
			shot_fx.play()


	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and random.randint(1, 200) == 1:
				self.update_action(0)#0: idle
				self.idling = True
				self.idling_counter = 50
			#ελεγχος για το εαν ο εχθρος ειναι κοντα στον παικτη
			if self.vision.colliderect(player.rect):
				#εχθρος σταματαει και κοιταει τον παικτη
				self.update_action(0)#0: idle
				#ριχνει αστερια
				self.shoot()
			else:
				if self.idling == False:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)#1: run
					self.move_counter += 1
					#ανανεωση "ορασης" του εχθρου οσο κινηται
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

					if self.move_counter > TILE_SIZE:
						self.direction *= -1
						self.move_counter *= -1
				else:
					self.idling_counter -= 1
					if self.idling_counter <= 0:
						self.idling = False

		self.rect.x += screen_scroll


	def update_animation(self):
		#ανανεωση animation
		ANIMATION_COOLDOWN = 100
		self.image = self.animation_list[self.action][self.frame_index]
		#αν εχει περασει αρκετος χρονος απο την τελευταια ανανεωση
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index += 1
		#εαν το animation τελειωσε, κανει reset
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0



	def update_action(self, new_action):
		if new_action != self.action:
			self.action = new_action
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()



	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)


	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

#κλαση κοσμου
class World():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])
		#ελεγχει καθε μια τιμη στο csv και τα αποθηκευει
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = x * TILE_SIZE
					img_rect.y = y * TILE_SIZE
					tile_data = (img, img_rect)
					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					# elif tile == 8:#create platform
					# 	platform = Platform( x* TILE_SIZE, y * TILE_SIZE, 0, 1)
					# 	platform_group.add(platform)
					elif tile >= 9 and tile <= 10:
						water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
						water_group.add(water)
					elif tile >= 11 and tile <= 14:
						decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
						decoration_group.add(decoration)
					elif tile == 15:
						player = ninja('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 5, 20, 5)
						health_bar = HealthBar(10, 10, player.health, player.health)
					elif tile == 16:
						enemy = ninja('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, 2, 20, 0)
						enemy_group.add(enemy)
					elif tile == 17:
						item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 18:
						item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 19:
						item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 20:
						exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
						exit_group.add(exit)
					#καθε τιμη εχει και την αντιστοιχια του σε tile, για την δημιουργια πιστας απλα δημιουργουμε ενα csv 
					# οι τιμες ειναι οι παρακατω:
					# -1 = αερας
					# 0-8 = διαφορετικοι τυποι εδαφους
					# 9-10 = νερο
					# 11-14 = διακοσμητικα props (κουτια, πετρες, θαμνοι)
					# 15 = παικτης
					# 16 = εχθροι
					# 17= κουτι με αστερια
					# 18= κουτι με βομβες
					# 19 = hκουτι με ζωη
					# 20= τελος πιστας

		return player, health_bar


	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] += screen_scroll
			screen.blit(tile[0], tile[1])

#κλαση για props
class Decoration(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

# class Platform(pygame.sprite.Sprite):
#     def __init__(self, x, y, move_x, move_y):
#         pygame.sprite.Sprite.__init__(self)
#         img = pygame.image.load('img/platform.png')
#         self.image = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE // 2))
#         self.rect = self.image.get_rect()
#         self.rect.x = x
#         self.rect.y = y
#         self.move_counter = 0
#         self.move_direction = 1
#         self.move_x = move_x
#         self.move_y = move_y


#     def update(self):
#         self.rect.x += self.move_direction * self.move_x
#         self.rect.y += self.move_direction * self.move_y
#         self.move_counter += 1
#         if abs(self.move_counter) > 50:
#             self.move_direction *= -1
#             self.move_counter *= -1


#κλαση νερου
class Water(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

#κλαση τελους πιστας
class Exit(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		self.rect.x += screen_scroll

#κλαση κουτιων ανεφοδιασμου
class ItemBox(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))


	def update(self):
		self.rect.x += screen_scroll
		#ο παικτης ακουμπησε το κουτι;
		if pygame.sprite.collide_rect(self, player):
			#τι κουτι ηταν
			if self.item_type == 'Health':
				player.health += 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Ammo':
				player.ammo += 15
			elif self.item_type == 'Grenade':
				player.grenades += 3
			#σβηνουμε το κουτι
			self.kill()

#κλαση μπαρας ζωης
class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		#ανανεωση με νεα τιμη ζως
		self.health = health
		#υπολογισμος ζωης
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

#κλαση αστεριων
class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		#κινηση αστεριων
		self.rect.x += (self.direction * self.speed) + screen_scroll
		#αστερι εκτος οθονης;
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()
		#αστερι ακουμπησε τοιχο
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#αστερι ακουμπησε παικτη η εχθρο;
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health -= 5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health -= 25
					self.kill()


#κλαση βομβας
class Grenade(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction

	def update(self):
		self.vel_y += GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		#ακουμπησε τον χωρο;
		for tile in world.obstacle_list:
			#ακουμπησε τοιχο;
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction *= -1
				dx = self.direction * self.speed
			#ελεγχος collision στον Υ
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom	


		#ανανεωση τοποθεσιας (βομβας)
		self.rect.x += dx + screen_scroll
		self.rect.y += dy

		#χρονομετρο 
		self.timer -= 1
		if self.timer <= 0:
			self.kill()
			grenade_fx.play()
			explosion = Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			#ζημια σε οποιον ειναι σε εμβελεια
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health -= 50
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
					enemy.health -= 50


#κλαση εκρηξης
class Explosion(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0


	def update(self):
		self.rect.x += screen_scroll

		EXPLOSION_SPEED = 4
		#animation εκρηξης
		self.counter += 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index += 1
			#οταν τελειωσει το animation, διαγραφη
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]





#κουμπια UI
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#γκρουπακια για ολα τα sprites
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
# platform_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#δημιουργια κενης λιστας(για τα tiles)
world_data = []
for row in range(ROWS):
	r = [-1] * COLS
	world_data.append(r)
#φορτωνει το csv, διαβαζει τις τιμες και δημιουργει το επιπεδο
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)



run = True
while run:

	clock.tick(FPS)

	if start_game == False:
		#μενου
		screen.fill(BG)
		#κουμπια στο μενου
		if start_button.draw(screen):
			start_game = True
		if exit_button.draw(screen):
			run = False
	else:
		#ανανεωση background
		draw_bg()
		#δημιουργια κοσμου
		world.draw()
		#εμφανιση ζωης
		health_bar.draw(player.health)
		#εμφανιση ammo που απομενει
		draw_text('ΑΣΤΕΡΙΑ: ', font, WHITE, 10, 35)
		for x in range(player.ammo):
			screen.blit(bullet_img, (118 + (x * 10), 40))
		#εμφανιση grenades που απομενουν
		draw_text('ΒΟΜΒΕΣ: ', font, WHITE, 10, 60)
		for x in range(player.grenades):
			screen.blit(grenade_img, (115 + (x * 15), 60))

		player.update()
		player.draw()

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		#ανανεωση και εμφανιση των γκρουπ
		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		# platform_group.update()
		water_group.update()
		exit_group.update()

		bullet_group.draw(screen)
		grenade_group.draw(screen)
		explosion_group.draw(screen)
		item_box_group.draw(screen)
		decoration_group.draw(screen)
		# platform_group.draw(screen)
		water_group.draw(screen)
		exit_group.draw(screen)




		#ανανεωση πραξεων παικτη
		if player.alive:
			#ριχνει αστερια
			if shoot:
				player.shoot()
			#πεταει βομβες
			elif grenade and grenade_thrown == False and player.grenades > 0:
				grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
				 			player.rect.top, player.direction)
				grenade_group.add(grenade)
				#μειωση βομβες
				player.grenades -= 1
				grenade_thrown = True
			if player.in_air:
				player.update_action(2)#2: πηδαει
			elif moving_left or moving_right:
				player.update_action(1)#1: τρεχει
			else:
				player.update_action(0)#0: ακινητος
			screen_scroll, level_complete = player.move(moving_left, moving_right)
			bg_scroll -= screen_scroll
			#εχει ολοκληρωθει το επιπεδο;
			if level_complete:
				level += 1
				bg_scroll = 0
				world_data = reset_level()
				if level <= MAX_LEVELS:
					#φορτωση δεδομενων και δημιουργια κοσμου
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y] = int(tile)
					world = World()
					player, health_bar = world.process_data(world_data)	
		else:
			screen_scroll = 0
			restart_button.draw(screen)
			bg_scroll = 0
			world_data = reset_level()
			#φορτωση δεδομενων και δημιουργια κοσμου
			with open(f'level{level}_data.csv', newline='') as csvfile:
				reader = csv.reader(csvfile, delimiter=',')
				for x, row in enumerate(reader):
					for y, tile in enumerate(row):
						world_data[x][y] = int(tile)
			world = World()
			player, health_bar = world.process_data(world_data)


	for event in pygame.event.get():
		#εξοδος παιχνιδιου
		if event.type == pygame.QUIT:
			run = False
		#πατηματα πληκτρων
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_SPACE:
				shoot = True
			if event.key == pygame.K_q:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
				jump_fx.play()
			if event.key == pygame.K_ESCAPE:
				run = False


		#αφημα πληκτρων 
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_SPACE:
				shoot = False
			if event.key == pygame.K_q:
				grenade = False
				grenade_thrown = False


	pygame.display.update()

pygame.quit()