

[//]: # (Image References)

[imagetrans1]: ./misc/transform1.png
[imagetrans2]: ./misc/transform2.png

### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

So, this is my first Udacity Nanodegree project! So far my solutions works, but I do see points, where I can improve. I will update the repository over time to optimize my code.

Most of the work that I have done actually concerns the perception. I found that the decision file worked surprisingly well out of the box. I tried to change a couple of things and add functionality, but in the end I think that I spent too much time on optimizing perception, so that I did not find enough time to get the driving and picking-up behaviour done properly.

### Notebook Analysis
Most of the functions that were already supplied with the notebook template worked quite well. I just had to fill in some of the coordinate transforms, that were left blank by the instructors.

The parameters I mostly left unchanged. They already worked well during the lessons in the classroom. I noticed that `perspect_transform` was quite sensitive regarding the `source`-parameter. These are two examples, where the corners of the of the parallelogram that the grid forms where moved by just one pixel:

![`[14, 140], [301 ,140],[200, 96], [118, 96]`][imagetrans1] ![`[14, 140], [301 ,140],[200, 97], [118, 97]`][imagetrans2]

Adding thresholding functions to detect the gold nuggets and obstacles was pretty straightforward, since they can both be classified easily by there colors (obstacles very dark in all colors, nuggets no blue).

I experimented a bit with the tracks that the rover leaves, as these are also quite dark and my thresholding seemed to detect some obstacles where there is navigable terrain. But I am not sure about this, it might be that this was just me misjudging the video output.

To detect obstacles, I tried to approaches: Find obstacles directly or declare everything an obstacle that isn't sky, navigable or a gold nugget. In the end, I found that both produce the same map accuracy, so I decided to stick with the simpler first method.

As was suggested in the instructions, I only mapped the terrain, when pitch and roll were low, this gave some improvements in fidelity.

To further improve fidelity, I addressed a function to limit the vision range of the Rover. Due to the warping function, the terrain that was further away came out distorted, so to increase fidelity and map accuracy, I limited the vision range for nav-terrain and obstacles (for the golden pieces I left it higher, because you do not want to miss those.)

I experimented a lot with wall detection. This was part of my endeavor to build a wall-crawler. Unfortunately I failed in that. I tried to things: Use the worldmap of obstacles to detect walls left and right of the Rover and use the Rover-centric map to detect walls in the front left and right. The results were unfortunately very unreliable. And the navigation algorithm that I used to work with those values could not work properly with the supplied data. So I skipped wall detection for the time being.

###### Sample videos:
I did have some issues with the csv file that was produced by the roversim. Due to locale settings, the delimiter in the csv file is `;`, however `pandas` by default expects `,`. I changed this in the notebook, the current version of the notebook should work with all versions of the roversim.

In `own_dataset/` I have the recording my own (manual) drive with the Rover. I used that one only for my analysis.

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result.

Again, pretty straightforward. Most of the required steps were already there. I added lines to fill the worldmap with the detected nuggets and obstacles. I found out that the entries in worldmap should be restricted to 255, otherwise it did not display correctly in the video.

Here I also used my function to restrict the Rover's vision to an area closer to it.

### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

The `perception_step()` was filled with exactly the same functions as in the notebook. Those worked well with the example video and with my own. The transformation of rover-coordinates to polar was also very straightforward.

No changes to `decision_step()` so far.

I increased the max velocity of the rover to 5 to speed things up a little.



#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

Running at resolution of 1024x768 and "good" graphics quality. Framerate is surprisingly low at 20fps. In the folder `autonomous_output` is the output of `drive_rover.py`, where the Rover mapped around 55% of the map with 88% fidelity and found three gold nuggets. 

As described above, I one had crashed a big obstacle-rock, because that was the mean nav-angle. But even with the original settings, the navigation works surprisingly well.

I get fidelity of 80-90%, so no complaints on that. Gold nugget detection works also well, the arbitrary movement of the Rover is enough so that in most cases I find at least four nuggets in a few minutes runtime.

This is an unsorted and incomplete list of things that I would like to change in the future:
- implement more involved decision steps
- advanced obstacle-avoidance: I once had crash, because the rover stood directly in front of an obstacle and `to_polar_coords()` returned angles left and right - the mean was in the center. Possibly try to identify those situations and then prefer one side.
- unstucking routines: I never observed that (not even in the above described crash), but on Slack a lot of fellow students report that their Rovers were stuck in obstacles or even the gold nuggets. This needs to be detected could be solved by arbitrary wild movements
- wall crawling: this bugs me most, because I put a lot of time into wall detection, that in the end did not work. First the Rover has to detect walls and then stick to them (but notice if it just found a single rock). Might have to look for other ways to detect walls.
- gold nugget collection: this was part of the challenge and I never really worked on it. In one version of my code I had it pick up a rock, but this was just for experimenting. For the future I would have the Rover go into a separate mode in case of a detected nugget and then slowly close in on it.
- Returning home: for this I was thinking of storing "waypoints" that carry the information which waypoint is in view and a step closer to home. This way the map could be populated with positions that the Rover can visit one after the other and that each point him to his next stop.
- advanced pitch- and roll-compensation: With some numbercrunching one could make the `perspect_transform` work in arbitrary situations, by taking the Rover-orientation into account. This might further improve fidelity. Since that is already quite high, I don't think that this has priority.
