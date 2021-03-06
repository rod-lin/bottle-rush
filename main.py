#! /usr/bin/python3

"""

this.camera.position.set(-17, 30, 26);
this.camera.lookAt(new THREE.Vector3(13, 0, -4));

The jumping calculation

var GAME = exports.GAME = {
	BOTTOMBOUND: -55,
	TOPBOUND: 41,
	gravity: 720,
	//gravity: 750,
	touchmoveTolerance: 20,
	LEFTBOUND: -140,
	topTrackZ: -30,
	rightBound: 90,
	HEIGHT: window.innerHeight > window.innerWidth ? window.innerHeight : window.innerWidth,
	WIDTH: window.innerHeight < window.innerWidth ? window.innerHeight : window.innerWidth,
	canShadow: true
};

var BOTTLE = exports.BOTTLE = {
	// bodyWidth: 2.8,
	// bodyDepth: 2.8,
	headRadius: 0.945,
	bodyWidth: 2.34,
	bodyDepth: 2.34,

	bodyHeight: 3.2,

	reduction: 0.005,
	minScale: 0.5,
	velocityYIncrement: 15,
	velocityY: 135,
	velocityZIncrement: 70
};

duration = duration in sec
vel_z = min(150, duration * BOTTLE.velocityZIncrement)
vel_y = min(BOTTLE.velocityY + duration * BOTTLE.velocityYIncrement, 180)

dy = (vel_y - GAME.gravity * flyingTime) * t - GAME.gravity / 2 * t * t

x = duration

v0 = 15x + 135

t = v0 / g * 2
dist = t * (70x)



"""

import numpy as np
from PIL import Image
import math
import time
import adb as pyadb3
import cv2
import os
import io

RESIZE_RATIO = 0.3
SIM_PRESS_X = 600
SIM_PRESS_Y = 600
TIME_DIST_RATIO = 1.52

DELAY_FRAME = 2

CENTER_DELTA_X = 35
CENTER_DELTA_Y = 45

JUMP_RIGHT_ANGLE_TAN = 0.579
JUMP_LEFT_ANGLE_TAN = 0.555

JUMP_RIGHT_ANGLE_SIN = JUMP_RIGHT_ANGLE_TAN / ((1 + JUMP_RIGHT_ANGLE_TAN ** 2) ** 0.5)
JUMP_LEFT_ANGLE_SIN = JUMP_LEFT_ANGLE_TAN / ((1 + JUMP_LEFT_ANGLE_TAN ** 2) ** 0.5)

JUMP_RIGHT_ANGLE_COS = JUMP_RIGHT_ANGLE_SIN / JUMP_RIGHT_ANGLE_TAN
JUMP_LEFT_ANGLE_COS = JUMP_LEFT_ANGLE_SIN / JUMP_LEFT_ANGLE_TAN

JUMP_RIGHT_ANGLE = math.asin(JUMP_RIGHT_ANGLE_SIN)
JUMP_LEFT_ANGLE = math.asin(JUMP_LEFT_ANGLE_SIN)

BOTTLE_IMG_PATH = "bottle.png"
BOTTLE_IMG = None

# 1 = 263.333pt
# 450 ms -> 1
# 620 ms -> 1.5
# 790 ms -> 2
# 980 ms -> 2.5

adb = pyadb3.ADB()

def d2t(dist):
    # return dist * TIME_DIST_RATIO
    # return 2.85 * (dist ** (1 / 1.1))
    # return 4.41 * (dist ** (1 / 1.2))
    return 1.3 * dist + 110
    # this function needs manual adjustment

# return image np array
def screencap(resize = 1.0):
    adb.shell_command("screencap -p")
    raw = adb.get_output()
    img = np.array(Image.open(io.BytesIO(raw)).convert("RGB"))

    if resize != 1.0:
        img = cv2.resize(img, (int(img.shape[1] * resize), int(img.shape[0] * resize)))

    return img

def update(*args):
    img.set_array(screencap())
    return img,

def do_jump(apos, bpos, resize = RESIZE_RATIO):
    dist = ((apos[0] - bpos[0]) ** 2 + (apos[1] - bpos[1]) ** 2) ** 0.5 / resize

    cmd = "input swipe %d %d %d %d %d" % \
          (SIM_PRESS_X, SIM_PRESS_Y, SIM_PRESS_X, SIM_PRESS_Y, d2t(dist))

    print(apos, bpos, dist, cmd)

    adb.shell_command(cmd)

screen = None
bottle_pos = None

def on_mouse(event, x, y, flags, param):
    global click_pos

    if event == cv2.EVENT_LBUTTONUP:
        # bottle_pos = find_bottle()
        print("found bottle at", bottle_pos)
        do_jump(bottle_pos, (x, y))

def find_bottle(screen, resize = RESIZE_RATIO):
    w, h = BOTTLE_IMG.shape[::-1]

    res = cv2.matchTemplate(cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY), BOTTLE_IMG, cv2.TM_CCOEFF_NORMED)

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    pos = (int(max_loc[0] + w / 2), int(max_loc[1] + h * 0.9))

    cv2.rectangle(screen, max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 0, 0), 2)
    # cv2.rectangle(screen, min_loc, (min_loc[0] + w, min_loc[1] + h), (0, 0, 255), 2)
    cv2.circle(screen, pos, 2, (0, 0, 0), -1)
    # cv2.imshow("screen", screen)

    return pos, max_val

    # cv2.rectangle(screen, min_loc, (min_loc[0] + w, min_loc[1] + h), (0, 0, 255), 2)
    # cv2.rectangle(screen, max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 0, 0), 2)
    # cv2.imshow("screen", screen)

prev_dir = 1 # 1 for right, -1 for left

def rough(bottle_pos, resize = RESIZE_RATIO):
    global prev_dir

    h, w = screen.shape[:-1]
    bx, by = bottle_pos

    cv2.circle(screen, (int(w / 2), int(h / 2)), 4, (0, 0, 0), -1)

    h += CENTER_DELTA_X * resize
    w += CENTER_DELTA_Y * resize

    cv2.circle(screen, (int(w / 2), int(h / 2)), 4, (100, 100, 100), -1)

    cx, cy = w / 2, h / 2

    orig = dist = ((cx - bx) ** 2 + (cy - by) ** 2) ** 0.5

    # correction on turn

    if (cx - bx) * prev_dir < 0: # different direction as the previous jump
        if prev_dir == 1: # now turn to the left
            a1 = math.atan(abs(cy - by) / abs(cx - bx)) + JUMP_RIGHT_ANGLE
        else: # now turn to the right
            a1 = math.atan(abs(cy - by) / abs(cx - bx)) + JUMP_LEFT_ANGLE
        
        d1 = dist * math.sin(a1)
        tot = JUMP_LEFT_ANGLE + JUMP_RIGHT_ANGLE

        if tot < math.pi / 2:
            dist = d1 / math.sin(tot)
        else:
            dist = d1 / math.sin(math.pi - tot)

    # print(orig, "->", dist)

    if cx > bx: # jump right
        # dist = math.sin(ang) * dist
        prev_dir = 1
        px = cx + dist * JUMP_RIGHT_ANGLE_COS
        py = cy - dist * JUMP_RIGHT_ANGLE_SIN
    else: # jump left
        prev_dir = -1
        # dist = math.sin(ang) * dist
        px = cx - dist * JUMP_LEFT_ANGLE_COS
        py = cy - dist * JUMP_LEFT_ANGLE_SIN

    # obs_angle = math.acos()

    pos = (int(px), int(py)) # (int(bx + (w / 2 - bx) * 2), int(by + (h / 2 - by) * 2))
    # cv2.circle(screen, pos, 2, (0, 0, 0), -1)

    # print(pos, bottle_pos)

    return pos

def adjust(rough):
    h, w = screen.shape[:-1]
    mask = np.zeros((h + 2, w + 2), np.uint8)

    rx, ry = rough[0], rough[1]

    if rx < 0 or rx >= w or ry < 0 or ry >= h:
        return rough
    
    _, _, _, (x1, y1, x2, y2) = \
        cv2.floodFill(screen, mask, rough, (0, 0, 0), (4, 4, 4), (4, 4, 4), cv2.FLOODFILL_MASK_ONLY)

    return int(x1 + x2 / 2), int(y1 + y2 / 2)

def init_bottle(screen, path = BOTTLE_IMG_PATH, resize = RESIZE_RATIO):
    global BOTTLE_IMG

    bottle = cv2.imread(path, 0)
    w, h = bottle.shape[::-1]
    sh, sw = screen.shape[:-1]

    bottle = cv2.resize(bottle, (int(w * resize), int(h * resize))).astype(np.uint8)

    BOTTLE_IMG = bottle

    maxv = -float("inf")
    maxscale = 0

    # try different scales to get the optimal match
    for scale in np.linspace(0.2, 5, 10)[::-1]:
        scale = float(scale)
        print("trying scale " + str(scale))

        nscreen = cv2.resize(screen, (int(sw * scale), int(sh * scale)))
        _, val = find_bottle(nscreen, resize = 1)

        if val > maxv:
            maxv = val
            maxscale = scale

    print("optimal scale " + str(maxscale))

cv2.namedWindow("screen")
cv2.setMouseCallback("screen", on_mouse)

mode = "coach"
key = 0
delay = 0
init = False

while True:
    screen = screencap(resize = RESIZE_RATIO)

    if not init:
        init = True
        init_bottle(screencap())

    # print(screen.shape)

    bottle_pos, _ = find_bottle(screen)
    next_pos = rough(bottle_pos)
    next_pos = adjust(next_pos)

    cv2.circle(screen, next_pos, 2, (0, 0, 0), -1)

    cv2.imshow("screen", screen)

    key = cv2.waitKey(1) & 0xff

    if key == ord("s"):
        print("stop auto mode")
        mode = "coach"
    elif key == ord("c"):
        print("reinit screen")
        init_bottle(screencap())
        print("continue auto mode")
        mode = "auto"
    
    if mode == "auto" and delay > DELAY_FRAME:
        do_jump(bottle_pos, next_pos)
        delay = 0

    delay += 1
