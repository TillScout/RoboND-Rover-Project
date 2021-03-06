import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

# threshing function to detect the gold nuggets
def rock_thresh(img, rgb_thresh=(100,100,50)):
    color_select = np.zeros_like(img[:,:,0])
    # filter out b-channel
    filter_mask = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] < rgb_thresh[2])
    color_select[filter_mask] = 1
    return color_select

# threshing function to detect obstacles
def obs_thresh(img, rgb_thresh=(120, 120, 120)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    below_thresh = (img[:,:,0] < rgb_thresh[0]) \
                & (img[:,:,1] < rgb_thresh[1]) \
                & (img[:,:,2] < rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[below_thresh] = 1
    # Return the binary image
    return color_select

# function to limit the vision of the Rover to only account for the closer and better terrain for navigation purposes
def restrict_vision(xpix, ypix, radius):
    limit = np.sqrt(xpix**2 + ypix**2) < radius
    x_restricted, y_restricted = xpix[limit], ypix[limit]
    return x_restricted, y_restricted


# Define a function to convert to rover-centric coordinates
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = np.absolute(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2).astype(np.float)

    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to apply a rotation to pixel positions
def rotate_pix(xpix, ypix, yaw):
    yaw_rad = yaw*2*np.pi/360
    # Apply a rotation
    xpix_rotated = xpix*np.cos(yaw_rad) - ypix*np.sin(yaw_rad)
    ypix_rotated = xpix*np.sin(yaw_rad) + ypix*np.cos(yaw_rad)
    # Return the result  
    return xpix_rotated, ypix_rotated


# Define a function to perform a translation
def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    x_world = np.int_(xpos + (xpix_rot / scale))
    y_world = np.int_(ypos + (ypix_rot / scale))
    # Return the result  
    return x_world, y_world


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # 1) Define source and destination points for perspective transform
    image = Rover.img
    (xpos, ypos) = Rover.pos
    yaw = Rover.yaw
    roll, pitch = Rover.roll, Rover.pitch
    roll_tol, pitch_tol = 2, 2

    dst_size = 5 
    bottom_offset = 6
    source = np.float32([[14, 140], [301 ,140],[200, 95], [118, 95]])
    destination = np.float32([[image.shape[1]/2 - dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - bottom_offset],
                  [image.shape[1]/2 + dst_size, image.shape[0] - 2*dst_size - bottom_offset], 
                  [image.shape[1]/2 - dst_size, image.shape[0] - 2*dst_size - bottom_offset],
                  ])
    # 2) Apply perspective transform
    warped = perspect_transform(image, source, destination)
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshed_nav = color_thresh(warped)
    threshed_rock = rock_thresh(warped)
    threshed_obs = obs_thresh(warped)
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    Rover.vision_image[:,:,0 ] = threshed_obs*100
    Rover.vision_image[:,:,1 ] = threshed_rock*100
    Rover.vision_image[:,:,2 ] = threshed_nav*100
    
    # 5) Convert map image pixel values to rover-centric coords
    x_rover_nav, y_rover_nav = rover_coords(threshed_nav)
    x_rover_obs, y_rover_obs = rover_coords(threshed_obs)
    x_rover_nugget, y_rover_nugget = rover_coords(threshed_rock)
    # 6) Convert rover-centric pixel values to world coordinates
    #restrict the vision of the Rover to map only the closer terrain:
    x_rover_nav, y_rover_nav = restrict_vision(x_rover_nav, y_rover_nav, 50)
    x_rover_obs, y_rover_obs = restrict_vision(x_rover_obs, y_rover_obs, 50)
    # map them to world coordinates    
    x_world_nav, y_world_nav = pix_to_world(x_rover_nav, y_rover_nav, xpos, ypos, yaw, 200, 10)
    x_world_obs, y_world_obs = pix_to_world(x_rover_obs, y_rover_obs, xpos, ypos, yaw, 200, 10)
    x_world_nugget, y_world_nugget = pix_to_world(x_rover_nugget, y_rover_nugget, xpos, ypos, yaw, 200, 10)
    
    # 7) Update Rover worldmap (to be displayed on right side of screen)
    if (roll > 360 - roll_tol or 0 < roll < roll_tol) and (pitch > 360 - pitch_tol or 0 < pitch < pitch_tol):
        Rover.worldmap[y_world_obs, x_world_obs, 0] += 1
        Rover.worldmap[y_world_nugget, x_world_nugget, 1] += 1
        Rover.worldmap[y_world_nav, x_world_nav, 2] += 1
        Rover.worldmap = np.clip(Rover.worldmap, 0, 255)
    # 8) Convert rover-centric pixel positions to polar coordinates
    dist, phi = to_polar_coords(x_rover_nav, y_rover_nav)
    # Update Rover pixel distances and angles
    Rover.nav_dists = dist
    Rover.nav_angles = phi
 
    
    
    return Rover
