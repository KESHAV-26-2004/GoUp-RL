import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pygame
import random
import numpy as np
from os import listdir
from os.path import isfile, join

# =============================================================================
# CONSTANTS
# =============================================================================
WIDTH, HEIGHT = 1650, 950
FPS = 60
PLAYER_VEL = 6


# =============================================================================
# ASSET HELPERS
# =============================================================================
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]
    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
    return all_sprites


# =============================================================================
# GAME ENTITIES
# =============================================================================
class Player(pygame.sprite.Sprite):
    GRAVITY = 1
    ANIMATION_DELAY = 2

    def __init__(self, x, y, width, height, sprites):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.SPRITES = sprites
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.update_sprite()

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        if self.rect.x > -190:
            self.x_vel = -vel
            if self.direction != "left":
                self.direction = "left"
                self.animation_count = 0

    def move_right(self, vel):
        if self.rect.x < 1600:
            self.x_vel = vel
            if self.direction != "right":
                self.direction = "right"
                self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
                self.animation_count += 2
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"

        if self.x_vel != 0 and 0 <= self.y_vel < (self.GRAVITY * 2):
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x, offset_y):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y - offset_y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x, offset_y):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))


class Block(Object):
    def __init__(self, x, y, sizex, sizey, x1, y1, terrain_image):
        super().__init__(x, y, sizex, sizey)
        block = self._get_block(sizex, sizey, x1, y1, terrain_image)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)

    @staticmethod
    def _get_block(sizex, sizey, x1, y1, terrain_image):
        surface = pygame.Surface((sizex, sizey), pygame.SRCALPHA, 32)
        rect = pygame.Rect(x1, y1, sizex, sizey)
        surface.blit(terrain_image, (0, 0), rect)
        return pygame.transform.scale2x(surface)


class Fire(Object):
    Animation_Delay = 3

    def __init__(self, x, y, width, height, fire_sprites):
        super().__init__(x, y, width, height, "fire")
        self.fire = fire_sprites
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.Animation_Delay) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.Animation_Delay > len(sprites):
            self.animation_count = 0


class Item(Object):
    def __init__(self, x, y, width, height, start_img, name=None):
        super().__init__(x, y, width, height, name)
        item1 = self._get_item(128, start_img)
        self.image.blit(item1, (0, 0))

    @staticmethod
    def _get_item(size, start_img):
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, size, size)
        surface.blit(start_img, (0, 0), rect)
        return pygame.transform.scale2x(surface)


# =============================================================================
# RL ENVIRONMENT
# =============================================================================
class GoUpEnv:
    """
    Action space (hybrid tuple):
        action = (horizontal, jump)
        horizontal: 0 = no move, 1 = left, 2 = right
        jump:       0 = no jump, 1 = jump trigger

    Set render_mode="human" to watch.
    Set render_mode=None for headless training (fast).
    """

    OBS_SIZE = 33
    _active_envs = 0
    ACTIONS = (
        (0, 0),
        (1, 0),
        (2, 0),
        (0, 1),
        (1, 1),
        (2, 1),
    )

    def __init__(self, render_mode=None):
        self.render_mode = render_mode
        self.obs_size = self.OBS_SIZE
        self.action_size = len(self.ACTIONS)

        # ---------------------------------------------------------------------
        # Pygame init
        # ---------------------------------------------------------------------
        if render_mode != "human":
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        GoUpEnv._active_envs += 1
        self._closed = False
        if render_mode == "human":
            pygame.display.set_caption("GO UP")
            self.window = pygame.display.set_mode((WIDTH, HEIGHT))
            self.clock = pygame.time.Clock()
        else:
            pygame.display.init()
            pygame.display.set_mode((1, 1))
            self.window = pygame.Surface((WIDTH, HEIGHT))
            self.clock = None

        # ---------------------------------------------------------------------
        # Load ALL assets once
        # ---------------------------------------------------------------------
        with open("assets//images//character.txt", "r") as f:
            char_name = f.read().strip()
        self.player_sprites = load_sprite_sheets("MainCharacters", f"{char_name}.chr", 32, 32, True)

        with open("assets//images//Color_c.txt", "r") as f:
            bg_name = f.read().strip()
        self.bg_image = pygame.image.load(join("assets", "Background", f"{bg_name}.png")).convert_alpha()
        _, _, bg_w, bg_h = self.bg_image.get_rect()
        self.bg_tiles = [[i * bg_w, j * bg_h] for i in range(WIDTH // bg_w + 1) for j in range(HEIGHT // bg_h + 1)]

        self.terrain_image = pygame.image.load(join("assets", "Terrain", "Terrain.png")).convert_alpha()
        self.fire_sprites = load_sprite_sheets("Traps", "Fire", 16, 32)

        self.start_img = pygame.image.load("assets//images//Start_b.png").convert_alpha()
        self.start_img = pygame.transform.scale(self.start_img, ((512 // 8), (512 // 8)))
        self.platform_rows = []
        self.platform_lookup = {}
        self.block_platform_lookup = {}
        self.last_reward_breakdown = {}

    # -------------------------------------------------------------------------
    # Level generation
    # -------------------------------------------------------------------------
    def _init_level_params(self):
        self.a_yaxis = []
        self.c_xaxis = []
        self.side1_l = []

        y_axis = 854
        for _ in range(150):
            y_axis -= random.randint(150, 165)
            self.a_yaxis.append(y_axis)

        side1_y = 854
        for _ in range(400):
            side1_y -= 96
            self.side1_l.append(side1_y)

        for _ in range(150):
            b = [
                random.randint(40, 120),
                random.randint(230, 420),
                random.randint(570, 780),
                random.randint(910, 1070),
                random.randint(1220, 1500),
                random.randint(40, 300),
                random.randint(396, 685),
                random.randint(781, 925),
                random.randint(1121, 1532),
                random.randint(40, 500),
                random.randint(596, 960),
                random.randint(1050, 1500),
            ]
            self.c_xaxis.append(b)

    def _generate_objects(self):
        block_size = 96

        floor = [Block(i * block_size, HEIGHT - block_size, block_size, 96, 0, 0, self.terrain_image) for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
        Side1 = [Block(0, self.side1_l[i], 32, 96, 240, 64, self.terrain_image) for i in range(400)]
        Side2 = [Block(1618, self.side1_l[i], 32, 96, 240, 64, self.terrain_image) for i in range(400)]

        for block in floor:
            block.is_action_platform = False
            block.rl_static_role = "floor"

        for block in Side1:
            block.is_action_platform = False
            block.rl_static_role = "wall_left"

        for block in Side2:
            block.is_action_platform = False
            block.rl_static_role = "wall_right"

        item_x1 = Item(100, 758, 128, 97, self.start_img)

        platform_blocks = []

        # ============================================================
        # FIRST CURRICULUM: 3 REACHABLE RANDOM PLATFORMS
        # ============================================================

        PLATFORM_WIDTH = 192       # two 96px blocks
        PLATFORM_HEIGHT = 32

        MIN_X = 180
        MAX_X = 1080

        # Maximum horizontal movement we allow between platforms.
        # Keep this comfortably inside the actual jump capability.
        MAX_HORIZONTAL_GAP = random.randint(180, 260)

        # First platform: completely random.
        current_x = random.randint(MIN_X, MAX_X)

        for i in range(5):

            # --------------------------------------------------------
            # For platforms after the first one:
            # randomly choose LEFT or RIGHT and generate a reachable X
            # --------------------------------------------------------
            if i > 0:

                possible_left = current_x - MAX_HORIZONTAL_GAP
                possible_right = current_x + MAX_HORIZONTAL_GAP

                # Clamp to valid world range
                possible_left = max(MIN_X, possible_left)
                possible_right = min(MAX_X, possible_right)

                # Make sure there is actually room on both sides
                can_go_left = possible_left < current_x
                can_go_right = possible_right > current_x

                if can_go_left and can_go_right:
                    direction = random.choice([-1, 1])

                elif can_go_left:
                    direction = -1

                elif can_go_right:
                    direction = 1

                else:
                    # Should practically never happen
                    direction = 1

                if direction == -1:

                    low = int(possible_left)
                    high = int(current_x - 80)

                else:

                    low = int(current_x + 80)
                    high = int(possible_right)


                # safety check
                if low > high:

                    # fallback opposite side
                    low = int(MIN_X)
                    high = int(MAX_X)


                new_x = random.randint(low, high)

                current_x = new_x

            # --------------------------------------------------------
            # Create the platform
            # --------------------------------------------------------
            for j in range(2):

                x = current_x + j * 96

                block = Block(
                    x,
                    self.a_yaxis[i],
                    96,
                    PLATFORM_HEIGHT,
                    192,
                    64,
                    self.terrain_image
                )

                block.is_action_platform = True
                block.rl_row_hint = i

                platform_blocks.append(block)


        objects = [
            *floor,
            *Side1,
            *Side2,
            *platform_blocks,   # ✅ YOUR NEW BLOCKS
        ]

        return objects, item_x1

    def _build_platform_cache(self):
        actionable_blocks = [
            obj for obj in self.objects
            if isinstance(obj, Block) and getattr(obj, "is_action_platform", False)
        ]

        grouped_rows = {}
        for block in actionable_blocks:
            grouped_rows.setdefault(block.rect.y, []).append(block)

        self.platform_rows = []
        self.platform_lookup = {}
        self.block_platform_lookup = {}

        row_ys = sorted(grouped_rows.keys(), reverse=True)
        for row_order, row_y in enumerate(row_ys):
            blocks = sorted(grouped_rows[row_y], key=lambda block: block.rect.x)
            merged_platforms = []
            current_group = None

            for block in blocks:
                if current_group is None:
                    current_group = {
                        "left": block.rect.left,
                        "right": block.rect.right,
                        "top": block.rect.top,
                        "height": block.rect.height,
                        "blocks": [block],
                    }
                    continue

                if block.rect.left <= current_group["right"] + 2:
                    current_group["right"] = max(current_group["right"], block.rect.right)
                    current_group["height"] = max(current_group["height"], block.rect.height)
                    current_group["blocks"].append(block)
                else:
                    merged_platforms.append(current_group)
                    current_group = {
                        "left": block.rect.left,
                        "right": block.rect.right,
                        "top": block.rect.top,
                        "height": block.rect.height,
                        "blocks": [block],
                    }

            if current_group is not None:
                merged_platforms.append(current_group)

            platforms = []
            for platform_index, platform_group in enumerate(merged_platforms):
                rect = pygame.Rect(
                    platform_group["left"],
                    platform_group["top"],
                    platform_group["right"] - platform_group["left"],
                    platform_group["height"],
                )
                platform_id = f"row{row_order}_platform{platform_index}"
                platform_info = {
                    "id": platform_id,
                    "row_order": row_order,
                    "row_y": row_y,
                    "rect": rect,
                    "centerx": rect.centerx,
                    "width": rect.width,
                }
                self.platform_lookup[platform_id] = platform_info
                platforms.append(platform_info)

                for platform_block in platform_group["blocks"]:
                    platform_block.rl_platform_id = platform_id
                    self.block_platform_lookup[id(platform_block)] = platform_id

            platforms.sort(key=lambda platform: platform["centerx"])
            self.platform_rows.append(
                {
                    "row_order": row_order,
                    "row_y": row_y,
                    "platforms": platforms,
                }
            )

    @staticmethod
    def _clip_norm(value, scale):
        if scale == 0:
            return 0.0
        return float(np.clip(value / scale, -1.0, 1.0))

    def _encode_platform(self, platform, player_centerx, player_bottom):
        dx = self._clip_norm(platform["centerx"] - player_centerx, WIDTH)
        dy = self._clip_norm(platform["rect"].top - player_bottom, HEIGHT)
        width = self._clip_norm(platform["width"], WIDTH)
        return [dx, dy, width]

    def _get_row_above(self, player_bottom, skip_rows=0):
        rows_above = [row for row in self.platform_rows if row["row_y"] < player_bottom - 4]
        if skip_rows >= len(rows_above):
            return None
        return rows_above[skip_rows]

    def _get_row_below(self, player_bottom):
        rows_below = [row for row in self.platform_rows if row["row_y"] >= player_bottom - 4]
        if not rows_below:
            return None
        return min(rows_below, key=lambda row: row["row_y"])

    def _get_support_distance(self):
        player_bottom = self.player.rect.bottom
        below_row = self._get_row_below(player_bottom)
        if below_row is None:
            return 1.0

        gap = max(0, below_row["row_y"] - player_bottom)
        return float(np.clip(gap / HEIGHT, 0.0, 1.0))

    def _get_platform_id(self, obj):
        if obj is None:
            return None
        return self.block_platform_lookup.get(id(obj))

    def _get_episode_metrics(self):
        return {
            "episode_reward": float(self.episode_reward),
            "max_height": float(max(0.0, self.spawn_y - self.best_y)),
            "best_y": float(self.best_y),
            "unique_platforms": len(self.visited_platform_ids),
            "steps_survived": self.steps,
            "stagnation_steps": self.steps_since_progress,
        }

    def get_episode_summary(self):
        metrics = self._get_episode_metrics()
        return (
            f"reward={metrics['episode_reward']:.2f} "
            f"max_height={metrics['max_height']:.1f} "
            f"unique_platforms={metrics['unique_platforms']} "
            f"steps={metrics['steps_survived']}"
        )

    # -------------------------------------------------------------------------
    # Gym-style API
    # -------------------------------------------------------------------------
    def reset(self, seed=None):
        if seed is not None:
            random.seed(seed)
        else:
            random.seed()   # ← THIS IS VERY IMPORTANT

        self._init_level_params()
        self.objects, self.item_x1 = self._generate_objects()
        self._build_platform_cache()

        # Stage 1 win platform = last generated row
        self.final_platform_id = (
            self.platform_rows[-1]["platforms"][0]["id"]
        )

        spawn_x = random.randint(180, WIDTH - 180)
        self.player = Player(spawn_x, 830, 50, 50, self.player_sprites)
        self.offset_x = 0
        self.offset_y = 0
        self.y_out = 900
        self.speed_inc = 1.0
        self.steps = 0
        self._jump_was_pressed = False 
        self.safe_start_steps = 5
        self.current_step = 0

        # Win condition parameters
        self.max_blocks = 40
        self.block_gap = 192
        self.target_height = self.a_yaxis[39]
        self.spawn_y = float(self.player.rect.y)
        self.best_y = float(self.player.rect.y)
        self.episode_reward = 0.0
        self.steps_since_progress = 0
        self.visited_platform_ids = set()
        self.last_landed_platform_id = None
        self.last_reward_breakdown = {}
        self.reward_config = {
            "time_penalty": 0.005,

            # platform progression
            "platform_1_reward": 10.0,
            "platform_2_reward": 20.0,
            "platform_3_reward": 30.0,
            "platform_4_reward": 40.0,
            "platform_5_reward": 50.0,

            # terminal
            "win_reward": 200.0,
            "death_penalty": 50.0,

            # invalid action
            "invalid_jump_penalty": 0.2,
        }

        return self._get_obs()

    def _get_obs(self):
        p = self.player.rect
        player_centerx = p.centerx
        player_centery = p.centery
        player_bottom = p.bottom

        obs = [
            float(np.clip(player_centerx / WIDTH, 0.0, 1.0)),
            float(np.clip(player_centery / HEIGHT, -1.0, 1.0)),
            self._clip_norm(self.player.x_vel, PLAYER_VEL),
            self._clip_norm(self.player.y_vel, 12.0),
            1.0 if self.player.jump_count < 2 else 0.0,
            1.0 if self.player.y_vel > 0 else 0.0,
            float(np.clip(self.player.fall_count / FPS, 0.0, 1.0)),
            self._get_support_distance(),
        ]

        row1 = self._get_row_above(player_bottom, skip_rows=0)
        row2 = self._get_row_above(player_bottom, skip_rows=1)
        below_row = self._get_row_below(player_bottom)

        for row in (row1, row2):
            row_platforms = row["platforms"] if row else []
            for index in range(3):
                if index < len(row_platforms):
                    obs.extend(self._encode_platform(row_platforms[index], player_centerx, player_bottom))
                else:
                    obs.extend([0.0, 0.0, 0.0])

        landing_candidates = []

        if below_row is not None:
            vx = self.player.x_vel

            def score(platform):
                dx = platform["centerx"] - player_centerx

                # alignment with velocity (MAIN factor)
                alignment = abs(dx - vx * 15)

                # slight penalty for distance
                dist_penalty = abs(dx) * 0.1

                return alignment + dist_penalty

            landing_candidates = sorted(
                below_row["platforms"],
                key=score
            )[:2]

        for index in range(2):
            if index < len(landing_candidates):
                obs.extend(self._encode_platform(landing_candidates[index], player_centerx, player_bottom))
            else:
                obs.extend([0.0, 0.0, 0.0])

        jump_state = float(np.clip(self.player.jump_count / 2, 0.0, 1.0))
        obs.append(jump_state)

        obs = np.asarray(obs, dtype=np.float32)

        # SAFETY CHECK (VERY IMPORTANT)
        if len(obs) != self.OBS_SIZE:
            raise ValueError(f"Obs size mismatch: got {len(obs)}, expected {self.OBS_SIZE}")

        return obs

    def _get_nearby_objects(self, margin=300):
        px, py = self.player.rect.centerx, self.player.rect.centery
        return [obj for obj in self.objects if abs(obj.rect.centery - py) < margin and abs(obj.rect.centerx - px) < margin]

    @staticmethod
    def _collide(player, objects, dx):
        player.move(dx, 0)
        player.update()
        collided_object = None
        for obj in objects:
            if pygame.sprite.collide_mask(player, obj):
                collided_object = obj
                break
        player.move(-dx, 0)
        player.update()
        return collided_object

    @staticmethod
    def _handle_vertical_collision(player, objects, dy):
        collided_objects = []
        landed_on = None
        for obj in objects:
            if pygame.sprite.collide_mask(player, obj):
                if dy > 0:
                    player.rect.bottom = obj.rect.top
                    player.landed()
                    if landed_on is None:
                        landed_on = obj
                elif dy < 0:
                    player.rect.top = obj.rect.bottom
                    player.hit_head()
                collided_objects.append(obj)
        return collided_objects, landed_on

    def decode_action(self, action_index):
        return self.ACTIONS[action_index]

    def step(self, action):

        self.steps += 1
        self.current_step += 1

        reward = 0.0
        done = False
        terminal_reason = None

        reward_breakdown = {
            "time_penalty": 0.0,
            "platform": 0.0,
            "terminal": 0.0,
            "invalid_jump": 0.0,
        }


        # ============================================================
        # EVENTS
        # ============================================================

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                terminal_reason = "quit"


        # ============================================================
        # ACTION
        # ============================================================

        nearby = self._get_nearby_objects()


        if self.current_step <= self.safe_start_steps:
            horizontal, jump = 0, 0
        else:
            horizontal, jump = action



        # movement

        self.player.x_vel = 0


        collide_left = self._collide(
            self.player,
            nearby,
            -PLAYER_VEL * 3
        )

        collide_right = self._collide(
            self.player,
            nearby,
            PLAYER_VEL * 3
        )


        if horizontal == 1 and not collide_left:
            self.player.move_left(PLAYER_VEL)

        elif horizontal == 2 and not collide_right:
            self.player.move_right(PLAYER_VEL)



        # jump

        if jump == 1:

            if self.player.jump_count < 2:
                self.player.jump()

            else:
                reward -= self.reward_config["invalid_jump_penalty"]

                reward_breakdown["invalid_jump"] = (
                    -self.reward_config["invalid_jump_penalty"]
                )


        # ============================================================
        # PHYSICS
        # ============================================================

        self.player.loop(FPS)

        # ============================================================
        # CAMERA SCROLLING
        # ============================================================

        # Target: keep player around the lower half of the screen
        # When player goes above mid-screen, scroll camera down

        mid_y = HEIGHT * 0.5

        # Desired screen-top so that player is at mid_y
        desired_screen_top = self.player.rect.y - mid_y

        # Only move camera upward (show lower area) when player goes above mid
        if desired_screen_top < self.offset_y:
            self.offset_y = desired_screen_top



        # ============================================================
        # COLLISION
        # ============================================================

        nearby = self._get_nearby_objects()

        vertical_speed = self.player.y_vel


        _, landed_obj = self._handle_vertical_collision(
            self.player,
            nearby,
            vertical_speed
        )


        landed_platform_id = self._get_platform_id(landed_obj)



        # ============================================================
        # PLATFORM REWARD
        # ============================================================

        if landed_platform_id is not None:


            if landed_platform_id not in self.visited_platform_ids:

                self.visited_platform_ids.add(
                    landed_platform_id
                )


                row_index = getattr(
                    landed_obj,
                    "rl_row_hint",
                    0
                )


                platform_rewards = [
                    self.reward_config["platform_1_reward"],
                    self.reward_config["platform_2_reward"],
                    self.reward_config["platform_3_reward"],
                    self.reward_config["platform_4_reward"],
                    self.reward_config["platform_5_reward"],
                ]

                if row_index < len(platform_rewards):
                    platform_reward = platform_rewards[row_index]
                else:
                    platform_reward = 0.0


                reward += platform_reward
                reward_breakdown["platform"] = platform_reward



        # ============================================================
        # WIN CONDITION
        # ============================================================


        if landed_platform_id == self.final_platform_id:

            done = True
            terminal_reason = "win"

            print("win: reached final platform")

            reward += self.reward_config["win_reward"]

            reward_breakdown["terminal"] = (
                self.reward_config["win_reward"]
            )



        # ============================================================
        # DEATH
        # ============================================================


        # if 300 > self.player.rect.y:

        #     done = True

        #     print("death: fell below y_out")

        #     terminal_reason = "death"


        #     reward -= self.reward_config["death_penalty"]


        #     reward_breakdown["terminal"] = (
        #         -self.reward_config["death_penalty"]
        #     )



        # ============================================================
        # TIME LIMIT
        # ============================================================

        if self.steps >= 450 and not done:

            done = True

            print("death: time limit reached")

            terminal_reason = "timeout"



        # ============================================================
        # SMALL TIME PENALTY
        # ============================================================

        reward -= self.reward_config["time_penalty"]

        reward_breakdown["time_penalty"] = (
            -self.reward_config["time_penalty"]
        )



        # ============================================================
        # SAVE METRICS
        # ============================================================

        self.episode_reward += reward

        self.last_reward_breakdown = reward_breakdown



        info = self._get_episode_metrics()

        info["reward_breakdown"] = reward_breakdown
        info["terminal_reason"] = terminal_reason
        info["last_landed_platform_id"] = landed_platform_id


        if done:
            info["episode_summary"] = self.get_episode_summary()



        # ============================================================
        # RENDER
        # ============================================================

        if self.render_mode == "human":

            self._render()
            self.clock.tick(FPS)



        return self._get_obs(), reward, done, info

    def _render(self):
        for tile in self.bg_tiles:
            self.window.blit(self.bg_image, tile)

        screen_top = self.offset_y
        screen_bottom = self.offset_y + HEIGHT
        margin = 200

        for obj in self.objects:
            if obj.rect.y > screen_bottom + margin or obj.rect.y + obj.rect.height < screen_top - margin:
                continue
            obj.draw(self.window, self.offset_x, self.offset_y)

        self.item_x1.draw(self.window, self.offset_x, self.offset_y)
        self.player.draw(self.window, self.offset_x, self.offset_y)
        pygame.display.update()

    def close(self):
        if self._closed:
            return

        self._closed = True
        GoUpEnv._active_envs = max(0, GoUpEnv._active_envs - 1)
        if GoUpEnv._active_envs == 0:
            pygame.quit()


# =============================================================================
# DEMO
# =============================================================================
# if __name__ == "__main__":
#     env = GoUpEnv(render_mode="human")
#     obs = env.reset()
#     done = False

#     while not done:
#         # Random AI demo — replace with your RL model
#         #action = (random.randint(0, 2), random.randint(0, 1))
#         obs, reward, done, info = env.step(action = None)
#         print(f"obs: {[round(x, 3) for x in obs]} | reward: {reward:.2f} | done: {done}")

#     env.close()

# =============================================================================
# DEMO — HUMAN PLAYABLE
# =============================================================================
if __name__ == "__main__":
    env = GoUpEnv(render_mode="human")
    obs = env.reset()
    done = False

    while not done:
        # --- map keys to hybrid action (horizontal, jump) --------------------
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            horizontal = 1          # left
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            horizontal = 2          # right
        else:
            horizontal = 0          # no move

        # Jump on press, not hold (simple debounce)
        jump = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_w:
                    jump = 1
                if event.key == pygame.K_ESCAPE:
                    done = True

        action = (horizontal, jump)
        obs, reward, done, info = env.step(action)

        # Optional debug print
        # print(f"y:{obs[1]*HEIGHT:.0f}  reward:{reward:.2f}  done:{done}")

    env.close()
