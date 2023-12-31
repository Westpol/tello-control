from djitellopy import Tello
import cv2
import pygame
import numpy as np
import time
from math import sin, cos, radians

# Speed of the drone from 0 to 100
S = 50
# Frames per second of the pygame window display
# A low number also results in input lag, as input information is processed once per frame.
FPS = 120


class FrontEnd(object):
    """ Maintains the Tello display and moves it through the keyboard keys.
        Press escape key to quit.
        The controls are:
            - T: Takeoff
            - L: Land
            - Arrow keys: Forward, backward, left and right.
            - A and D: Counterclockwise and clockwise rotations (yaw)
            - W and S: Up and down.
    """

    def __init__(self, xy_per_second, yaw_degrees_per_second, height_limit, xy_boundary):
        # Init pygame
        pygame.init()

        # Create pygame window
        pygame.display.set_caption("Tello video stream")
        self.screen = pygame.display.set_mode([960, 720])

        # Init Tello object that interacts with the Tello drone
        self.tello = Tello()

        # Drone velocities between -100~100
        self.for_back_velocity = 0
        self.left_right_velocity = 0
        self.up_down_velocity = 0
        self.yaw_velocity = 0
        self.speed = 10

        self.send_rc_control = False

        # create update timer
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000 // FPS)

        # Cage mode variables
        self.x_pos = 0
        self.y_pos = 0
        self.yaw_pos = 0
        self.xy_per_second = xy_per_second * 2
        self.yaw_per_second = yaw_degrees_per_second
        self.height = 0

        self.height_limit = height_limit
        self.groundHeight = 0
        self.xy_boundary = xy_boundary

        self.deltaT = time.time()

    def run(self):

        self.tello.connect()
        self.tello.set_speed(self.speed)

        # In case streaming is on. This happens when we quit this program without the escape key.
        self.tello.streamoff()
        self.tello.streamon()

        frame_read = self.tello.get_frame_read()

        self.groundHeight = self.tello.get_barometer()

        should_stop = False
        while not should_stop:

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.update()
                elif event.type == pygame.QUIT:
                    should_stop = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        should_stop = True
                    else:
                        self.keydown(event.key)
                elif event.type == pygame.KEYUP:
                    self.keyup(event.key)

            if frame_read.stopped:
                break

            self.screen.fill([0, 0, 0])

            frame = frame_read.frame
            # battery percent
            text = "Battery: {}%".format(self.tello.get_battery())
            cv2.putText(frame, text, (5, 720 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)
            frame = np.flipud(frame)

            frame = pygame.surfarray.make_surface(frame)
            self.screen.blit(frame, (0, 0))
            pygame.display.update()

            time.sleep(1 / FPS)

        # Call it always before finishing. To deallocate resources.
        self.tello.end()

    def keydown(self, key):
        """ Update velocities based on key pressed
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP:  # set forward velocity
            self.for_back_velocity = S
        elif key == pygame.K_DOWN:  # set backward velocity
            self.for_back_velocity = -S
        elif key == pygame.K_LEFT:  # set left velocity
            self.left_right_velocity = -S
        elif key == pygame.K_RIGHT:  # set right velocity
            self.left_right_velocity = S
        elif key == pygame.K_w:  # set up velocity
            self.up_down_velocity = S
        elif key == pygame.K_s:  # set down velocity
            self.up_down_velocity = -S
        elif key == pygame.K_a:  # set yaw counterclockwise velocity
            self.yaw_velocity = -S
        elif key == pygame.K_d:  # set yaw clockwise velocity
            self.yaw_velocity = S

    def keyup(self, key):
        """ Update velocities based on key released
        Arguments:
            key: pygame key
        """
        if key == pygame.K_UP or key == pygame.K_DOWN:  # set zero forward/backward velocity
            self.for_back_velocity = 0
        elif key == pygame.K_LEFT or key == pygame.K_RIGHT:  # set zero left/right velocity
            self.left_right_velocity = 0
        elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
            self.up_down_velocity = 0
        elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
            self.yaw_velocity = 0
        elif key == pygame.K_t:  # takeoff
            self.tello.takeoff()
            self.send_rc_control = True
        elif key == pygame.K_l:  # land
            self.tello.land()
            self.send_rc_control = False

    def update(self):
        # Update routine. Send velocities to Tello.
        if self.send_rc_control:

            self.height = self.tello.get_barometer() - self.groundHeight

            if self.height > self.height_limit and self.up_down_velocity > 0:
                self.up_down_velocity = 0

            self.yaw_pos += (self.yaw_per_second * (time.time() - self.deltaT)) * (self.yaw_velocity / S)
            print(self.yaw_pos)
            self.x_pos += cos(radians(self.yaw_pos)) * (self.xy_per_second * (time.time() - self.deltaT)) * (self.for_back_velocity / S)
            self.x_pos += -sin(radians(self.yaw_pos)) * (self.xy_per_second * (time.time() - self.deltaT)) * (self.left_right_velocity / S)
            self.y_pos += -cos(radians(self.yaw_pos)) * (self.xy_per_second * (time.time() - self.deltaT)) * (self.left_right_velocity / S)
            self.y_pos += -sin(radians(self.yaw_pos)) * (self.xy_per_second * (time.time() - self.deltaT)) * (self.for_back_velocity / S)
            print("x:{0}  |  y:{1}".format(self.x_pos, self.y_pos))

            self.deltaT = time.time()

            self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity,
                                       self.up_down_velocity, self.yaw_velocity)


def main():
    frontend = FrontEnd(S, 34.285714286, 200, 500)

    # run frontend

    frontend.run()


if __name__ == '__main__':
    main()
