import math, random
import cv2 as cv
from cmu_112_graphics import *

#All the opencv methods used in this project are referenced from
#the official opencv-python docutation, link:
#https://docs.opencv.org/master/d6/d00/tutorial_py_root.html

def distance(x0, y0, x1, y1):
    return ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5

def circleIntersects(x0, y0, x1, y1, r): 
    #Special version for two equal radii circles
    dist = distance(x0, y0, x1, y1)
    return dist < 2 * r

def xyToPolar(dx, dy):
    #convert cartesian coor to polar coor
    #theta range from 0 to 2pi, no negative angles
    mag = (dx ** 2 + dy ** 2) ** 0.5
    if dx == 0 and dy == 0:
        return (0, 0)
    elif dx == 0 and dy != 0:
        if dy > 0:
            return (mag, math.pi / 2)
        else:
            return (mag, 3 * math.pi / 2)
    elif dx != 0 and dy == 0:
        if dx > 0:
            return (mag, 0)
        else:
            return (mag, math.pi)
    else:
        theta = math.atan(dy / dx)
        if dx < 0:
            theta += math.pi
        elif dx > 0 and dy < 0:
            theta += 2 * math.pi
        return (mag, theta)
    
def getMiddle(bbox):
    #get middle coor of an opencv rectangle
    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    midX = x + w / 2
    midY = y + h / 2
    return (midX, midY)

def drawBox(frame, bbox, color):
    #draw an opencv rectangle using default color red/blue
    if color == 'red':
        fill = (0, 0, 255)
    elif color == 'blue':
        fill = (255, 0, 0)
    x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    cv.rectangle(frame, (x, y), (x + w, y + h), fill, 3, 1)

class Mallet(object):
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.r = 50
        self.maxSpeed = 50
    
    def fixMalletSpeed(self):
        #can't exceed max speed, on both xy directions
        if abs(self.dx) > self.maxSpeed:
            self.dx = (self.maxSpeed * abs(self.dx) / self.dx)
        if abs(self.dy) > self.maxSpeed:
            self.dy = (self.maxSpeed * abs(self.dy) / self.dy)
    
    def fixPosition(self, w1, w2, height):
        #mallet can't go off the screen
        if self.x < w1 + self.r:
            self.x = w1 + self.r
        elif self.x > w2 - self.r:
            self.x = w2 - self.r
        if self.y < self.r:
            self.y = self.r
        elif self.y > height - self.r:
            self.y = height - self.r
    
    def move(self, x, y):
        #move command for mallet
        distX = x - self.x
        distY = y - self.y
        if abs(distX) > self.maxSpeed:
            self.x += self.maxSpeed * distX / abs(distX)
        else:
            self.x += distX
        if abs(distY) > self.maxSpeed:
            self.y += self.maxSpeed * distY / abs(distY)
        else:
            self.y += distY

class Puck(object):
    def __init__(self, x, y, dx, dy):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.r = 50
        self.maxSpeed = 50
    
    def fixPuckSpeed(self):
        #can't exceed max speed
        if abs(self.dx) > self.maxSpeed:
            self.dx = (self.maxSpeed * abs(self.dx) / self.dx)
        if abs(self.dy) > self.maxSpeed:
            self.dy = (self.maxSpeed * abs(self.dy) / self.dy)
    
    def applyFriction(self, friction):
        #apply the impact of friction on the velocity in both xy directions
        if abs(self.dx) <= friction or abs(self.dy) <= friction:
            if abs(self.dy) <= friction:
                self.dy = 0
            else:
                self.dy -= abs(self.dy) / self.dy * friction
            if abs(self.dx) <= friction:
                self.dx = 0
            else:
                self.dx -= abs(self.dx) / self.dx * friction
        else:
            k = friction / (self.dx ** 2 + self.dy ** 2) ** 0.5
            frictionX = k * abs(self.dx)
            frictionY = k * abs(self.dy)
            self.dx -= abs(self.dx) / self.dx * frictionX
            self.dy -= abs(self.dy) / self.dy * frictionY
    
    def puckHitsEdge(self, height):
        #dealing with edge hitting
        yBounced = False
        if self.y < self.r:
            yBounced = True
            self.y = self.r
        if self.y > height - self.r:
            yBounced = True
            self.y = height - self.r 
        if yBounced:
            self.dy = -self.dy
        self.fixPuckSpeed()
    
    #A special thank you to Professor Hael Collins from CMU Department of 
    #Physics for helping me figure out the physics essence of the collision 
    #between two disks, which is the basic idea of this function below
    def puckRebound(self, mallet):
        #this method deals with the collision between mallet and puck
        #lots of physics here
        if circleIntersects(mallet.x, mallet.y, self.x, self.y, self.r):
            bounced = True
            ratio = 2 * self.r / distance(mallet.x, mallet.y, self.x, self.y)
            self.x = (mallet.x + ratio * (self.x - mallet.x))
            self.y = (mallet.y + ratio * (self.y - mallet.y))
            posDx = self.x - mallet.x
            posDy = self.y - mallet.y
            posMag, posTheta = xyToPolar(posDx, posDy)
            puckMag, puckTheta = xyToPolar(self.dx, self.dy)
            malletMag, malletTheta = xyToPolar(mallet.dx, mallet.dy)
            paraMag = (-puckMag * math.cos(posTheta - puckTheta)
                    + 2 * malletMag * math.cos(posTheta - malletTheta))
            if paraMag < 0: return
            perpMag = (puckMag * math.sin(posTheta - puckTheta)
                    + malletMag * math.sin(posTheta - malletTheta))
            self.dx = (paraMag * math.cos(posTheta) + 
                        perpMag * math.cos(posTheta + math.pi / 2))
            self.dy = (paraMag * math.sin(posTheta) + 
                        perpMag * math.sin(posTheta + math.pi / 2))
            self.fixPuckSpeed()
    
    def move(self):
        self.x += self.dx
        self.y += self.dy

class MalletAI(Mallet): #subclass of mallet
    def __init__(self, x, y, dx, dy, difficulty, hand):
        #inherents everything except maxSpeed
        super().__init__(x, y, dx, dy)
        speedDict = { "Mild" : (20, 10),
                      "Medium" : (25, 20),
                      "Nightmare" : (30, 30),
                      "CMU" : (50, 30) }
        #The dict about how difficulties are set up
        self.difficulty = difficulty
        self.maxSpeed = speedDict[difficulty][0]
        self.attackSpeed = speedDict[difficulty][1] 
        #attack speed is the minimum speed before the ai actively attacks
        self.hand = hand #AI is on the opposite side of hand
                         #so if hand = left, the AI should be on the right
    
    def move(self, puck):
        #main method that determines how the AI moves depending on the
        #position and motion of puck
        distY = puck.y - self.y
        if self.puckBehind(puck): return
        if abs(distY) > self.maxSpeed:
            self.dy = self.maxSpeed
            self.y += self.maxSpeed * distY / abs(distY)
        else:
            self.dy = distY 
            self.y += distY
        if abs(puck.dx) < self.attackSpeed:
            if self.hand == 'Left':
                self.dx = -self.maxSpeed
                self.x += self.dx
            else:
                self.dx = self.maxSpeed
                self.x += self.dx
        else:
            if self.hand == 'Left':
                self.x += self.maxSpeed
                self.dx = 0
            else:
                self.x -= self.maxSpeed
                self.dx = 0

    def puckBehind(self, puck):
        #this method helps the AI to recover once it's behind the puck
        #it should technically never reach this method but just in case
        if self.x < puck.x and self.hand == 'Left':
            #move back with maximum speed
            self.dy = -abs(puck.dy) / puck.dy * self.maxSpeed
            self.dx = self.maxSpeed
            self.x += self.dx
            self.y += self.dy
            return True
        elif self.x > puck.x and self.hand == 'Right':
            self.dy = -abs(puck.dy) / puck.dy * self.maxSpeed
            self.dx = -self.maxSpeed
            self.x += self.dx
            self.y += self.dy
            return True

class Rectangle(object):
    def __init__(self, x, hand, height):
        #the rectangles in pratice mode
        self.x = x
        self.hand = hand
        self.length = random.randint(150, height/2)
        self.y = random.randint(0, height-self.length)
        self.width = 28
        self.exist = True

    def puckHits(self, puck):
        #hit only counts when hit from front
        if self.hand == 'Left':
            xHit = puck.x + puck.r >= self.x and puck.dx > 0
        else:
            xHit = puck.x - puck.r <= self.x and puck.dx < 0
        yHit = self.y - 20 < puck.y < self.y + self.length + 20
        if self.exist and xHit and yHit:
            puck.dx = -puck.dx
            self.exist = False #will disappear if hit

class SplashScreenMode(Mode):
#The background image is from the website:
#https://www.walpaperlist.com/2020/01/wallpaper-white-gaming-background.html
    def appStarted(mode):
        mode.background = mode.loadImage('background.jpg')
        mode.onePlayerColor = 'black'
        mode.twoPlayerColor = 'black'
        mode.practiceColor = 'black'
        mode.onePlayerFill = 'white'
        mode.twoPlayerFill = 'white'
        mode.practiceFill = 'white'
    
    def mouseMoved(mode, event):
        fontSize = 36
        if (mode.width/4-80 < event.x < mode.width/4+80
        and mode.height * 2/5-30 < event.y < mode.height * 2/5+30):
            mode.twoPlayerColor = 'white'
            mode.twoPlayerFill = 'gray'
        else: 
            mode.twoPlayerColor = 'black'
            mode.twoPlayerFill = 'white'
        if (mode.width/4+100 < event.x < mode.width/4+260
        and mode.height * 3/5-30 < event.y < mode.height * 3/5+30):
            mode.onePlayerColor = 'white'
            mode.onePlayerFill = 'gray'
        else:
            mode.onePlayerColor = 'black'
            mode.onePlayerFill = 'white'
        if (mode.width/4+280 < event.x < mode.width/4+440
        and mode.height * 4/5-30 < event.y < mode.height * 4/5+30):
            mode.practiceColor = 'white'
            mode.practiceFill = 'gray'
        else:
            mode.practiceColor = 'black'
            mode.practiceFill = 'white'
    
    def mousePressed(mode, event):
        if (mode.width/4-80 < event.x < mode.width/4+80
        and mode.height * 2/5-30 < event.y < mode.height * 2/5+30):
            mode.app.setActiveMode(mode.app.twoPlayerMode)
        elif (mode.width/4+100 < event.x < mode.width/4+260
        and mode.height * 3/5-30 < event.y < mode.height * 3/5+30):
            mode.app.setActiveMode(mode.app.onePlayerMode)
        elif (mode.width/4+280 < event.x < mode.width/4+440
        and mode.height * 4/5-30 < event.y < mode.height * 4/5+30):
            mode.app.setActiveMode(mode.app.practiceMode)    
        
    
    def redrawAll(mode, canvas):
        canvas.create_image(mode.width/2, mode.height/2, 
                            image=ImageTk.PhotoImage(mode.background))
        font = 'Times 36 bold'
        canvas.create_text(mode.width/2, mode.height/5,
        text='Opencv Air Hockey', fill = 'black', font = 'Times 48 bold')
        canvas.create_rectangle(mode.width/4-80, mode.height * 2/5-30,
                                mode.width/4+80, mode.height * 2/5+30,
                            fill=mode.twoPlayerFill, outline='black', width=5)
        canvas.create_text(mode.width/4, mode.height * 2/5, 
        text='2-Player', fill = mode.twoPlayerColor, font = font)
        canvas.create_rectangle(mode.width/4+100, mode.height * 3/5-30,
                                mode.width/4+260, mode.height * 3/5+30,
                            fill=mode.onePlayerFill, outline='black', width=5)
        canvas.create_text(mode.width/4+180, mode.height * 3/5, 
        text='1-Player', fill = mode.onePlayerColor, font = font)
        canvas.create_rectangle(mode.width/4+280, mode.height * 4/5-30,
                                mode.width/4+440, mode.height * 4/5+30,
                            fill=mode.practiceFill, outline='black', width=5)
        canvas.create_text(mode.width/4+360, mode.height * 4/5, 
        text='Practice', fill = mode.practiceColor, font = font)
        canvas.create_text(5, mode.height-5, text='By: Shize Che', 
                           font=font, anchor='sw')

class TwoPlayerMode(Mode):
    def appStarted(mode):
        mode.started = False
        TwoPlayerMode.trackStart(mode)
        mode.leftMallet = Mallet(50, mode.height/2, 0, 0)
        mode.puck = Puck(mode.width/2, mode.height/2, 0, 0)
        mode.rightMallet = Mallet(mode.width-50, mode.height/2, 0, 0)
        mode.friction = 0.5
        mode.leftScore = 0
        mode.rightScore = 0
        mode.menuColor = 'black'
        mode.retrackColor = 'black'
        mode.done = False
        mode.timerDelay = 5  

    def trackStart(mode):
        mode.cap = cv.VideoCapture(0)
        mode.trackers = cv.MultiTracker_create()
        mode.tracked = False
        mode.bbox1 = None
        mode.bbox2 = None
    
    def mouseMoved(mode, event):
        #move onto clickables
        if (event.x >= 40 and event.x <= 140 and 
            event.y >= 0 and event.y <= 36):
            mode.menuColor = 'gray'
        else: mode.menuColor = 'black'
        if (event.x >= mode.width-160 and event.x <= mode.width-40 and 
                event.y >= 0 and event.y <= 36):
                mode.retrackColor = 'gray'
        else:
            mode.retrackColor = 'black'
    
    def mousePressed(mode, event):
        #clicked on clickables
        if (event.x >= 40 and event.x <= 140 and 
            event.y >= 0 and event.y <= 36):
            TwoPlayerMode.appStarted(mode)
            mode.app.setActiveMode(mode.app.splashScreenMode)
        elif (event.x >= mode.width-160 and event.x <= mode.width-40 and 
            event.y >= 0 and event.y <= 36):
            mode.tracked = False
            mode.trackers = cv.MultiTracker_create()

    def keyPressed(mode, event):
        #start a new game
        if mode.done and event.key == 'n':
            TwoPlayerMode.appStarted(mode)

    #lines end with <-- are copied/modified from this youtube video:
    #https://www.youtube.com/watch?v=O1ABXetrMGs
    def setTracking(mode):
        ret, frame = mode.cap.read() #<--
        sizedFrame = cv.resize(frame, (630, 360))
        mirroredFrame = cv.flip(sizedFrame, +1)
        if cv.waitKey(1) == ord('t'):
            mode.bbox1 = cv.selectROI('Tracking', mirroredFrame, False) #<--
            drawBox(mirroredFrame, mode.bbox1, 'red')
            tracker1 = cv.TrackerCSRT_create() #<--
            mode.trackers.add(tracker1, mirroredFrame, mode.bbox1) #<--
            mode.bbox2 = cv.selectROI('Tracking', mirroredFrame, False) #<--
            drawBox(mirroredFrame, mode.bbox2, 'blue')
            tracker2 = cv.TrackerCSRT_create() #<--
            mode.trackers.add(tracker2, mirroredFrame, mode.bbox2) #<--
            mode.tracked = True
            mode.started = True
        cv.imshow('Tracking', mirroredFrame) #<--

    #lines end with <-- are copied/modified from this youtube video:
    #https://www.youtube.com/watch?v=O1ABXetrMGs
    def tracking(mode):
        ret, frame = mode.cap.read() #<--
        sizedFrame = cv.resize(frame, (640, 360))
        mirroredFrame = cv.flip(sizedFrame, +1)
        ret, boxes = mode.trackers.update(mirroredFrame) #<--
        mode.bbox1, mode.bbox2 = boxes[0], boxes[1]
        leftX, leftY = getMiddle(mode.bbox1)
        rightX, rightY = getMiddle(mode.bbox2)
        mode.leftMallet.dx, mode.leftMallet.dy=(leftX*2-mode.leftMallet.x, 
                                                leftY*2-mode.leftMallet.y)
        mode.rightMallet.dx, mode.rightMallet.dy=(rightX*2-mode.rightMallet.x, 
                                                  rightY*2-mode.rightMallet.y)
        mode.leftMallet.fixMalletSpeed()
        mode.rightMallet.fixMalletSpeed()
        if ret: #<--
            drawBox(mirroredFrame, mode.bbox1, 'red') #<--
            drawBox(mirroredFrame, mode.bbox2, 'blue') #<--
        else:
            #it might lose track, so set the track again
            mode.tracked = False
            mode.trackers = cv.MultiTracker_create()
            return
        cv.imshow('Tracking', mirroredFrame) #<--
        mode.leftMallet.move(leftX*2, leftY*2)
        mode.rightMallet.move(rightX*2, rightY*2)
        mode.leftMallet.fixPosition(0, mode.width/2, mode.height)
        mode.rightMallet.fixPosition(mode.width/2, mode.width, mode.height)
    
    def checkEdge(mode):
        #check if any player scores and apply puckHitsEdge method
        if mode.puck.x < 0:
            mode.rightScore += 1
            mode.puck.x, mode.puck.y = mode.width/2, mode.height/2
            mode.puck.dx, mode.puck.dy = 0, 0
        elif mode.puck.x > mode.width:
            mode.leftScore += 1
            mode.puck.x, mode.puck.y = mode.width/2, mode.height/2
            mode.puck.dx, mode.puck.dy = 0, 0
        mode.puck.puckHitsEdge(mode.height)
    
    def checkScore(mode):
        #check if anyone wins
        if mode.leftScore == 6:
            mode.leftWin = True
            mode.done = True
        elif mode.rightScore == 6:
            mode.rightWin = True
            mode.done = True
        
    def timerFired(mode):
        if not mode.done and not mode.tracked:
            TwoPlayerMode.setTracking(mode)
        elif not mode.done and mode.tracked:
            TwoPlayerMode.tracking(mode)
            mode.puck.puckRebound(mode.leftMallet)
            mode.puck.puckRebound(mode.rightMallet)
            mode.puck.applyFriction(mode.friction)
            mode.puck.move()
            TwoPlayerMode.checkEdge(mode)
            TwoPlayerMode.checkScore(mode)
    
    def drawBoard(mode, canvas):
        canvas.create_oval(mode.width/2 - 80, mode.height/2 - 80, 
                           mode.width/2 + 80, mode.height/2 + 80,
                           fill = 'white', outline = 'gray75', width = 5)
        canvas.create_line(mode.width/2, 0, mode.width/2, 25,
                           fill = 'gray75', width = 5)
        canvas.create_line(mode.width/2, 40, mode.width/2, mode.height,
                           fill = 'gray75', width = 5)
        leftCx, rightCx = -mode.height/2, mode.width + mode.height/2
        leftCy, rightCy = mode.height/2, mode.height/2
        r = mode.height / 2 ** 0.5
        canvas.create_oval(leftCx-r, leftCy-r, leftCx+r, leftCy+r,
                           fill = 'white', outline = 'gray75', width = 5 )
        canvas.create_oval(rightCx-r, rightCy-r, rightCx+r, rightCy+r,
                           fill = 'white', outline = 'gray75', width = 5 )
    
    def drawInstruction(mode, canvas):
        if not mode.started:
            instruction = "Go to the camera window,\n\
hold the items you want to\n\
use to control your mallet,\n\
press 't' and select the item"
            canvas.create_rectangle(mode.width/2-220, mode.height/2-100,
                                    mode.width/2+220, mode.height/2+100,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/2, mode.height/2, text=instruction,
                               font="Times 36")
    
    def drawScore(mode, canvas):
        canvas.create_text(mode.width/2, 10,
                           text = f'{mode.leftScore}   vs   {mode.rightScore}',
                           font = "Arial 36", anchor = 'n')
        if mode.done:
            if mode.leftScore == 6:
                leftText, rightText = 'You Won!', 'You Lost!'
            else:
                leftText, rightText = 'You Lost!', 'You Won!'
            canvas.create_rectangle(mode.width/4-100, mode.height/2-30,
                                    mode.width/4+100, mode.height/2+30,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/4, mode.height/2, text = leftText,
                           font = "Arial 36")
            canvas.create_rectangle(mode.width/4*3-100, mode.height/2-30,
                                    mode.width/4*3+100, mode.height/2+30,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/4*3, mode.height/2, text = rightText,
                           font = "Arial 36")
            canvas.create_rectangle(mode.width/2-240, mode.height/4-30,
                                    mode.width/2+240, mode.height/4+30,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/2, mode.height/4, 
            text = "Press 'n' for a new game", font = "Arial 36")
    
    def drawMenuRetrack(mode, canvas):
        canvas.create_text(40, 0, text = 'Menu', fill = mode.menuColor,
                            font = "Times 36", anchor = 'nw')
        canvas.create_text(mode.width-40, 0, text = 'Retrack', 
                    fill = mode.retrackColor, font = "Times 36", anchor = 'ne')
    
    def drawWarning(mode, canvas):
        if not mode.tracked and mode.started:
            canvas.create_rectangle(mode.width/2-540, mode.height/2-40,
                                    mode.width/2+540, mode.height/2+40,
                                    fill='white', outline='red', width=5)
            canvas.create_text(mode.width/2, mode.height/2, 
    text="Lost Item(s), please select the item(s) again in the camera window",
    fill='red', font='Arial 36')
    
    def drawLeftMallet(mode, canvas):
        cx, cy = mode.leftMallet.x, mode.leftMallet.y
        canvas.create_oval(cx - mode.leftMallet.r, cy - mode.leftMallet.r, 
                           cx + mode.leftMallet.r, cy + mode.leftMallet.r, 
                           fill = "orange", outline = 'orange')

    def drawPuck(mode, canvas):
        cx, cy = mode.puck.x, mode.puck.y
        canvas.create_oval(cx - mode.puck.r, cy - mode.puck.r, 
                           cx + mode.puck.r, cy + mode.puck.r, 
                           fill = "black")
    
    def drawRightMallet(mode, canvas):
        cx, cy = mode.rightMallet.x, mode.rightMallet.y
        canvas.create_oval(cx - mode.rightMallet.r, cy - mode.rightMallet.r, 
                           cx + mode.rightMallet.r, cy + mode.rightMallet.r, 
                           fill = "dodger blue", outline = 'dodger blue')

    def redrawAll(mode, canvas):
        TwoPlayerMode.drawBoard(mode, canvas)
        TwoPlayerMode.drawLeftMallet(mode, canvas)
        TwoPlayerMode.drawPuck(mode, canvas)
        TwoPlayerMode.drawRightMallet(mode, canvas)
        TwoPlayerMode.drawScore(mode, canvas)
        TwoPlayerMode.drawMenuRetrack(mode, canvas)
        TwoPlayerMode.drawWarning(mode, canvas)
        TwoPlayerMode.drawInstruction(mode, canvas)
    
class OnePlayerMode(Mode):
#background image is from the website:
#https://sensientpharma.com/white-marble-texture-in-natural-pattern-with-
#high-resolution-for-background-and-design-art-work-white-stone-floor-2/
    def appStarted(mode):
        mode.background = mode.loadImage('marble.jpg')
        mode.started = False
        mode.difficulty = None
        mode.hand = None
        mode.diffColor = {'Mild' : 'black', 'Medium' : 'black',
                          'Nightmare' : 'black', 'CMU' : 'black'}
        mode.handColor = {'Left' : 'black', 'Right' : 'black',
                          'Go' : 'black'}
        mode.selected = False
        OnePlayerMode.trackStart(mode)
        mode.puck = Puck(mode.width/2, mode.height/2, 0, 0)
        mode.friction = 0.5
        mode.leftScore = 0
        mode.rightScore = 0
        mode.menuColor = 'black'
        mode.retrackColor = 'black'
        mode.done = False
        mode.timerDelay = 5  
    
    def selectStart(mode):
        #for the pre-game user interface
        if mode.hand != None and mode.difficulty != None:
            if mode.hand == 'Left':
                mode.leftMallet = Mallet(50, mode.height/2, 0, 0)
                mode.rightMallet = MalletAI(mode.width-50, mode.height/2, 
                                            0, 0, mode.difficulty, mode.hand)
            else:
                mode.rightMallet = Mallet(mode.width-50, mode.height/2, 0, 0)
                mode.leftMallet = MalletAI(50, mode.height/2, 
                                        0, 0, mode.difficulty, mode.hand)
            mode.selected = True
    
    def trackStart(mode):
        mode.cap = cv.VideoCapture(0)
        mode.tracker = cv.TrackerCSRT_create()
        mode.tracked = False
        mode.bbox = None
    
    def keyPressed(mode, event):
        #start a new game
        if (mode.done) and event.key == 'n':
            OnePlayerMode.appStarted(mode)
    
    def mouseMoved(mode, event):
        #mouse move into all clickables
        if not mode.selected:
            if mode.diffColor['Mild'] != 'red':
                if OnePlayerMode.inMild(mode, event.x, event.y):
                    mode.diffColor['Mild'] = 'gray'
                else: mode.diffColor['Mild'] = 'black'
            if mode.diffColor['Medium'] != 'red':
                if OnePlayerMode.inMedium(mode, event.x, event.y):
                    mode.diffColor['Medium'] = 'gray'
                else: mode.diffColor['Medium'] = 'black'
            if mode.diffColor['Nightmare'] != 'red':
                if OnePlayerMode.inNightmare(mode, event.x, event.y):
                    mode.diffColor['Nightmare'] = 'gray'
                else: mode.diffColor['Nightmare'] = 'black'
            if mode.diffColor['CMU'] != 'red':
                if OnePlayerMode.inCMU(mode, event.x, event.y):
                    mode.diffColor['CMU'] = 'gray'
                else: mode.diffColor['CMU'] = 'black'
            if mode.handColor['Left'] != 'red':
                if OnePlayerMode.inLeft(mode, event.x, event.y):
                    mode.handColor['Left'] = 'gray'
                else: mode.handColor['Left'] = 'black'
            if mode.handColor['Right'] != 'red':
                if OnePlayerMode.inRight(mode, event.x, event.y):
                    mode.handColor['Right'] = 'gray'
                else: mode.handColor['Right'] = 'black'
            if OnePlayerMode.inGo(mode, event.x, event.y):
                mode.handColor['Go'] = 'gray'
            else: mode.handColor['Go'] = 'black'
        else:
            if (event.x >= 40 and event.x <= 140 and 
                event.y >= 0 and event.y <= 36):
                mode.menuColor = 'gray'
            else:
                mode.menuColor = 'black'
            if (event.x >= mode.width-160 and event.x <= mode.width-40 and 
                event.y >= 0 and event.y <= 36):
                mode.retrackColor = 'gray'
            else:
                mode.retrackColor = 'black'
    
    def mousePressed(mode, event):
        #clicked on clickables
        if not mode.selected:
            if OnePlayerMode.inMild(mode, event.x, event.y):
                OnePlayerMode.diffBlack(mode)
                mode.diffColor['Mild'] = 'red'
            elif OnePlayerMode.inMedium(mode, event.x, event.y):
                OnePlayerMode.diffBlack(mode)
                mode.diffColor['Medium'] = 'red'
            elif OnePlayerMode.inNightmare(mode, event.x, event.y):
                OnePlayerMode.diffBlack(mode)
                mode.diffColor['Nightmare'] = 'red'
            elif OnePlayerMode.inCMU(mode, event.x, event.y):
                OnePlayerMode.diffBlack(mode)
                mode.diffColor['CMU'] = 'red'
            elif OnePlayerMode.inLeft(mode, event.x, event.y):
                OnePlayerMode.handBlack(mode)
                mode.handColor['Left'] = 'red'
            elif OnePlayerMode.inRight(mode, event.x, event.y):
                OnePlayerMode.handBlack(mode)
                mode.handColor['Right'] = 'red'
            elif OnePlayerMode.inGo(mode, event.x, event.y):
                OnePlayerMode.setDiffHand(mode)
        else:
            if (event.x >= 40 and event.x <= 140 and 
                event.y >= 0 and event.y <= 36):
                OnePlayerMode.appStarted(mode)
                mode.app.setActiveMode(mode.app.splashScreenMode)
            elif (event.x >= mode.width-160 and event.x <= mode.width-40 and 
                event.y >= 0 and event.y <= 36):
                mode.tracked = False
                mode.tracker = cv.TrackerCSRT_create()
    
    def diffBlack(mode):
        #turn all colors into black, since only one color can be red
        for diff in mode.diffColor:
            mode.diffColor[diff] = 'black'
    
    def handBlack(mode):
        #same purpose as diffBlack
        for hand in mode.handColor:
            mode.handColor[hand] = 'black'

    def setDiffHand(mode):
        #set difficulty and hand when clicked on Go
        for diff in mode.diffColor:
            if mode.diffColor[diff] == 'red':
                mode.difficulty = diff
                break
        for hand in mode.handColor:
            if mode.handColor[hand] == 'red':
                mode.hand = hand
                break
    
    def keyPressed(mode, event):
        #start a new game
        if mode.done and event.key == 'n':
            OnePlayerMode.appStarted(mode)

    #lines end with <-- are copied/modified from this youtube video:
    #https://www.youtube.com/watch?v=O1ABXetrMGs
    def setTracking(mode):
        ret, frame = mode.cap.read() #<--
        sizedFrame = cv.resize(frame, (630, 360))
        mirroredFrame = cv.flip(sizedFrame, +1)
        if cv.waitKey(1) == ord('t'):
            mode.bbox = cv.selectROI('Tracking', mirroredFrame, False) #<--
            mode.tracker.init(mirroredFrame, mode.bbox) #<--
            mode.tracked = True
            mode.started = True
        cv.imshow('Tracking', mirroredFrame) #<--
    
    #lines end with <-- are copied/modified from this youtube video:
    #https://www.youtube.com/watch?v=O1ABXetrMGs
    def tracking(mode):
        ret, frame = mode.cap.read() #<--
        sizedFrame = cv.resize(frame, (640, 360))
        mirroredFrame = cv.flip(sizedFrame, +1)
        ret, mode.bbox = mode.tracker.update(mirroredFrame) #<--
        x, y = getMiddle(mode.bbox)
        if mode.hand == 'Left':
            mode.leftMallet.dx = x * 2 - mode.leftMallet.x 
            mode.leftMallet.dy = y * 2 - mode.leftMallet.y
            mode.leftMallet.fixMalletSpeed()
        else:
            mode.rightMallet.dx = x * 2 - mode.rightMallet.x 
            mode.rightMallet.dy = y * 2 - mode.rightMallet.y
            mode.rightMallet.fixMalletSpeed()
        if ret: #<--
            drawBox(mirroredFrame, mode.bbox, 'red') #<--
        else:
            mode.tracked = False
            mode.tracker = cv.TrackerCSRT_create()
            return
        cv.imshow('Tracking', mirroredFrame) #<--
        if mode.hand == 'Left':
            mode.leftMallet.move(x * 2, y * 2)
            mode.leftMallet.fixPosition(0, mode.width/2, mode.height)
        else:
            mode.rightMallet.move(x * 2, y * 2)
            mode.rightMallet.fixPosition(mode.width/2, mode.width, mode.height)
    
    def timerFired(mode):
        if not mode.selected:
            OnePlayerMode.selectStart(mode)
        else:
            if not mode.done and not mode.tracked:
                OnePlayerMode.setTracking(mode)
            elif not mode.done and mode.tracked:
                OnePlayerMode.tracking(mode)
                if mode.hand == 'Left':
                    mode.rightMallet.move(mode.puck)
                    mode.rightMallet.fixPosition(mode.width/2, mode.width, 
                                                 mode.height)
                else:
                    mode.leftMallet.move(mode.puck)
                    mode.leftMallet.fixPosition(0, mode.width/2, mode.height)
                mode.puck.puckRebound(mode.leftMallet)
                mode.puck.puckRebound(mode.rightMallet)
                mode.puck.applyFriction(mode.friction)
                mode.puck.move()
                OnePlayerMode.checkEdge(mode)
                OnePlayerMode.checkScore(mode)
    
    def checkEdge(mode):
        #check if anyone scores and apply puckHitsEdge method
        if mode.puck.x < 0:
            mode.rightScore += 1
            mode.puck.x, mode.puck.y = mode.width/2, mode.height/2
            mode.puck.dx, mode.puck.dy = 0, 0
        elif mode.puck.x > mode.width:
            mode.leftScore += 1
            mode.puck.x, mode.puck.y = mode.width/2, mode.height/2
            mode.puck.dx, mode.puck.dy = 0, 0
        mode.puck.puckHitsEdge(mode.height)
    
    def checkScore(mode):
        #check if anyone wins
        if mode.leftScore == 6:
            mode.leftWin = True
            mode.done = True
        elif mode.rightScore == 6:
            mode.rightWin = True
            mode.done = True
    
    def drawInstruction(mode, canvas):
        if not mode.started:
            instruction = "Go to the camera window,\n\
hold the item you want to\n\
use to control your mallet,\n\
press 't' and select the item"
            canvas.create_rectangle(mode.width/2-220, mode.height/2-100,
                                    mode.width/2+220, mode.height/2+100,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/2, mode.height/2, text=instruction,
                               font="Times 36")
    
    def drawBoard(mode, canvas):
        canvas.create_oval(mode.width/2 - 80, mode.height/2 - 80, 
                           mode.width/2 + 80, mode.height/2 + 80,
                           fill = 'white', outline = 'gray75', width = 5)
        canvas.create_line(mode.width/2, 0, mode.width/2, 25,
                           fill = 'gray75', width = 5)
        canvas.create_line(mode.width/2, 40, mode.width/2, mode.height,
                           fill = 'gray75', width = 5)
        leftCx, rightCx = -mode.height/2, mode.width + mode.height/2
        leftCy, rightCy = mode.height/2, mode.height/2
        r = mode.height / 2 ** 0.5
        canvas.create_oval(leftCx-r, leftCy-r, leftCx+r, leftCy+r,
                           fill = 'white', outline = 'gray75', width = 5 )
        canvas.create_oval(rightCx-r, rightCy-r, rightCx+r, rightCy+r,
                           fill = 'white', outline = 'gray75', width = 5 )
    
    def drawScore(mode, canvas):
        canvas.create_text(mode.width/2, 10,
                           text = f'{mode.leftScore}   vs   {mode.rightScore}',
                           font = "Arial 36", anchor = 'n')
        if mode.done:
            if mode.leftScore == 6 and mode.hand == 'Left':
                leftText, rightText = 'Human Won!', 'AI Lost!'
            elif mode.leftScore == 6 and mode.hand == 'Right':
                leftText, rightText = 'AI Won!', 'Human Lost!'
            elif mode.rightScore == 6 and mode.hand == 'Left':
                leftText, rightText = 'Human Lost!', 'AI Won!'
            else:
                leftText, rightText = 'AI Lost!', 'Human Won!'
            canvas.create_rectangle(mode.width/4-120, mode.height/2-30,
                                    mode.width/4+120, mode.height/2+30,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/4, mode.height/2, text = leftText,
                           font = "Arial 36")
            canvas.create_rectangle(mode.width/4*3-120, mode.height/2-30,
                                    mode.width/4*3+120, mode.height/2+30,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/4*3, mode.height/2, text = rightText,
                           font = "Arial 36")
            canvas.create_rectangle(mode.width/2-240, mode.height/4-30,
                                    mode.width/2+240, mode.height/4+30,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/2, mode.height/4, 
            text = "Press 'n' for a new game", font = "Arial 36")
    
    def drawMenuRetrack(mode, canvas):
        canvas.create_text(40, 0, text = 'Menu', fill = mode.menuColor,
                            font = "Times 36", anchor = 'nw')
        canvas.create_text(mode.width-40, 0, text = 'Retrack', 
                    fill = mode.retrackColor, font = "Times 36", anchor = 'ne')
    
    def drawWarning(mode, canvas):
        if not mode.tracked and mode.started:
            canvas.create_rectangle(mode.width/2-540, mode.height/2-40,
                                    mode.width/2+540, mode.height/2+40,
                                    fill='white', outline='red', width=5)
            canvas.create_text(mode.width/2, mode.height/2, 
    text="Lost Item(s), please select the item(s) again in the camera window",
    fill='red', font='Arial 36')
    
    def drawLeftMallet(mode, canvas):
        cx, cy = mode.leftMallet.x, mode.leftMallet.y
        canvas.create_oval(cx - mode.leftMallet.r, cy - mode.leftMallet.r, 
                           cx + mode.leftMallet.r, cy + mode.leftMallet.r, 
                           fill = "orange", outline = 'orange')

    def drawPuck(mode, canvas):
        cx, cy = mode.puck.x, mode.puck.y
        canvas.create_oval(cx - mode.puck.r, cy - mode.puck.r, 
                           cx + mode.puck.r, cy + mode.puck.r, 
                           fill = "black")
    
    def drawRightMallet(mode, canvas):
        cx, cy = mode.rightMallet.x, mode.rightMallet.y
        canvas.create_oval(cx - mode.rightMallet.r, cy - mode.rightMallet.r, 
                           cx + mode.rightMallet.r, cy + mode.rightMallet.r, 
                           fill = "dodger blue", outline = 'dodger blue')
    
    def drawSelection(mode, canvas):
        font = "Times 36"
        canvas.create_text(mode.width/2, 50, text="Select Difficulty and Hand",
                           font=font)
        canvas.create_text(mode.width/4, mode.height/4, text="Difficulty:",
                           font=font)
        canvas.create_text(mode.width/4, mode.height/4+100, text="Mild",
                        font=font, fill=mode.diffColor['Mild'], anchor='nw')
        canvas.create_text(mode.width/4, mode.height/4+200, text="Medium",
                        font=font, fill=mode.diffColor['Medium'], anchor='nw')
        canvas.create_text(mode.width/4, mode.height/4+300, text="Nightmare",
                    font=font, fill=mode.diffColor['Nightmare'], anchor='nw')
        canvas.create_text(mode.width/4, mode.height/4+400, text="CMU",
                        font=font, fill=mode.diffColor['CMU'], anchor='nw')
        canvas.create_text(mode.width/4 * 3, mode.height/4, text="Hand:",
                           font=font)
        canvas.create_text(mode.width/4 * 3, mode.height/4+100, text="Left",
                        font=font, fill=mode.handColor['Left'], anchor='nw')
        canvas.create_text(mode.width/4 * 3, mode.height/4+200, text="Right",
                        font=font, fill=mode.handColor['Right'], anchor='nw')
        canvas.create_text(mode.width-50, mode.height-50, text='Go', 
                        font=font, fill=mode.handColor['Go'], anchor='se')

    #the followings are position detections for the clickables
    def inMild(mode, x, y):
        xInRange = x >= mode.width/4 and x <= mode.width/4 + 75
        yInRange = y >= mode.height/4+100 and y <= mode.height/4+136
        return xInRange and yInRange

    def inMedium(mode, x, y):
        xInRange = x >= mode.width/4 and x <= mode.width/4 + 125
        yInRange = y >= mode.height/4+200 and y <= mode.height/4+236
        return xInRange and yInRange

    def inNightmare(mode, x, y):
        xInRange = x >= mode.width/4 and x <= mode.width/4 + 160
        yInRange = y >= mode.height/4+300 and y <= mode.height/4+336
        return xInRange and yInRange

    def inCMU(mode, x, y):
        xInRange = x >= mode.width/4 and x <= mode.width/4 + 90
        yInRange = y >= mode.height/4+400 and y <= mode.height/4+436
        return xInRange and yInRange

    def inLeft(mode, x, y):
        xInRange = x >= mode.width/4 * 3 and x <= mode.width/4 * 3 + 75
        yInRange = y >= mode.height/4+100 and y <= mode.height/4+136
        return xInRange and yInRange

    def inRight(mode, x, y):
        xInRange = x >= mode.width/4 * 3 and x <= mode.width/4 * 3 + 90
        yInRange = y >= mode.height/4+200 and y <= mode.height/4+236
        return xInRange and yInRange

    def inGo(mode, x, y):
        xInRange = x >= mode.width-50-2*36 and x <= mode.width-50
        yInRange = y >= mode.height-50-36 and y <= mode.height-50
        return xInRange and yInRange

    def redrawAll(mode, canvas):
        if not mode.selected:
            canvas.create_image(mode.width/2, mode.height/2, 
                                image=ImageTk.PhotoImage(mode.background))
            OnePlayerMode.drawSelection(mode, canvas)
        else:
            OnePlayerMode.drawBoard(mode, canvas)
            OnePlayerMode.drawLeftMallet(mode, canvas)
            OnePlayerMode.drawPuck(mode, canvas)
            OnePlayerMode.drawRightMallet(mode, canvas)
            OnePlayerMode.drawScore(mode, canvas)
            OnePlayerMode.drawMenuRetrack(mode, canvas)
            OnePlayerMode.drawWarning(mode, canvas)
            OnePlayerMode.drawInstruction(mode, canvas)

class PracticeMode(Mode):
#background image is from the website:
#https://sensientpharma.com/white-marble-texture-in-natural-pattern-with-
#high-resolution-for-background-and-design-art-work-white-stone-floor-2/
    def appStarted(mode):
        mode.background = mode.loadImage('marble.jpg')
        mode.started = False
        mode.menuColor = 'black'
        mode.retrackColor = 'black'
        mode.selected = False
        mode.colors = {'Left' : 'black', 'Right' : 'black', 'Go' : 'black'}
        mode.hand = None
        PracticeMode.trackStart(mode)
        mode.friction = 0.5
        mode.lost = False
        mode.won = False
        mode.timerDelay = 5  

    def trackStart(mode):
        mode.cap = cv.VideoCapture(0)
        mode.tracker = cv.TrackerCSRT_create()
        mode.tracked = False
        mode.bbox = None
    
    def selectStart(mode):
        #for pre-game interface
        if mode.hand != None:
            if mode.hand == 'Left':
                mode.mallet = Mallet(50, mode.height/2, 0, 0)
                mode.puck = Puck(mode.width/4, mode.height/2, 0, 0)
                mode.rectangles = ([ Rectangle(mode.width/2 + i*64, 'Left',
                                   mode.height) for i in range(0, 10) ])
            else:
                mode.mallet = Mallet(mode.width-50, mode.height/2, 0, 0)
                mode.puck = Puck(mode.width/4 * 3, mode.height/2, 0, 0)
                mode.rectangles = ([ Rectangle(mode.width/2 - i*64, 'Right',
                                   mode.height) for i in range(0, 10) ])
            mode.selected = True
            #mode.rectangles is a list of 10 rectangle objects
    
    def mouseMoved(mode, event):
        #mouse moved on clickables
        if not mode.selected:
            if mode.colors['Left'] != 'red':
                if PracticeMode.inLeft(mode, event.x, event.y):
                    mode.colors['Left'] = 'gray'
                else:
                    mode.colors['Left'] = 'black'
            if mode.colors['Right'] != 'red':
                if PracticeMode.inRight(mode, event.x, event.y):
                    mode.colors['Right'] = 'gray'
                else:
                    mode.colors['Right'] = 'black'
            if PracticeMode.inGo(mode, event.x, event.y):
                mode.colors['Go'] = 'gray'
            else:
                mode.colors['Go'] = 'black'
        else:
            if mode.hand == 'Left':
                mX1, mY1, mX2, mY2 = 5, 0, 105, 36
                rX1, rY1, rX2, rY2 = 5, mode.height-41, 125, mode.height
            else:
                mX1, mY1, mX2, mY2 = mode.width-105, 0, mode.width-5, 36
                rX1, rY1, rX2, rY2 = (mode.width-125, mode.height-41, 
                                      mode.width-5, mode.height)
            if (event.x >= mX1 and event.x <= mX2 and 
                event.y >= mY1 and event.y <= mY2):
                mode.menuColor = 'gray'
            else:
                mode.menuColor = 'black'
            if (event.x >= rX1 and event.x <= rX2 and 
                event.y >= rY1 and event.y <= rY2):
                mode.retrackColor = 'gray'
            else:
                mode.retrackColor = 'black'
    
    def mousePressed(mode, event):
        #mouse pressed on clickables
        if not mode.selected:
            if PracticeMode.inLeft(mode, event.x, event.y):
                mode.colors['Left'] = 'red'
                mode.colors['Right'] = 'black'
            elif PracticeMode.inRight(mode, event.x, event.y):
                mode.colors['Right'] = 'red'
                mode.colors['Left'] = 'black'
            elif PracticeMode.inGo(mode, event.x, event.y):
                if mode.colors['Left'] == 'red':
                    mode.hand = 'Left'
                elif mode.colors['Right'] == 'red':
                    mode.hand = 'Right' 
        else:
            if mode.hand == 'Left':
                mX1, mY1, mX2, mY2 = 5, 0, 105, 36
                rX1, rY1, rX2, rY2 = 5, mode.height-41, 125, mode.height
            else:
                mX1, mY1, mX2, mY2 = mode.width-105, 0, mode.width-5, 36
                rX1, rY1, rX2, rY2 = (mode.width-125, mode.height-41, 
                                      mode.width-5, mode.height)
            if (event.x >= mX1 and event.x <= mX2 and 
                event.y >= mY1 and event.y <= mY2):
                PracticeMode.appStarted(mode)
                mode.app.setActiveMode(mode.app.splashScreenMode)
            if (event.x >= rX1 and event.x <= rX2 and 
                event.y >= rY1 and event.y <= rY2):
                mode.tracked = False
                mode.tracker = cv.MultiTracker_create()
    
    def keyPressed(mode, event):
        #start a new game
        if (mode.won or mode.lost) and event.key == 'n':
            PracticeMode.appStarted(mode)
    
    #lines end with <-- are copied/modified from this youtube video:
    #https://www.youtube.com/watch?v=O1ABXetrMGs
    def setTracking(mode):
        ret, frame = mode.cap.read() #<--
        sizedFrame = cv.resize(frame, (630, 360))
        mirroredFrame = cv.flip(sizedFrame, +1)
        if cv.waitKey(1) == ord('t'):
            mode.bbox = cv.selectROI('Tracking', mirroredFrame, False) #<--
            mode.tracker.init(mirroredFrame, mode.bbox) #<--
            mode.tracked = True
            mode.started = True
        cv.imshow('Tracking', mirroredFrame) #<--
    
    #lines end with <-- are copied/modified from this youtube video:
    #https://www.youtube.com/watch?v=O1ABXetrMGs
    def tracking(mode):
        ret, frame = mode.cap.read() #<--
        sizedFrame = cv.resize(frame, (640, 360))
        mirroredFrame = cv.flip(sizedFrame, +1)
        ret, mode.bbox = mode.tracker.update(mirroredFrame) #<--
        x, y = getMiddle(mode.bbox)
        mode.mallet.dx = x * 2 - mode.mallet.x 
        mode.mallet.dy = y * 2 - mode.mallet.y
        mode.mallet.fixMalletSpeed()
        if ret: #<--
            drawBox(mirroredFrame, mode.bbox, 'red') #<--
        else:
            mode.tracked = False
            mode.tracker = cv.TrackerCSRT_create()
            return
        cv.imshow('Tracking', mirroredFrame) #<--
        mode.mallet.move(x * 2, y * 2)
        if mode.hand == 'Left':
            mode.mallet.fixPosition(0, mode.width/2, mode.height)
        else:
            mode.mallet.fixPosition(mode.width/2, mode.width, mode.height)
    
    def timerFired(mode):
        if not mode.selected:
            PracticeMode.selectStart(mode)
        else:
            if not (mode.won or mode.lost) and not mode.tracked:
                PracticeMode.setTracking(mode)
            elif not (mode.won or mode.lost) and mode.tracked:
                PracticeMode.tracking(mode)
                mode.puck.puckRebound(mode.mallet)
                for rectangle in mode.rectangles:
                    rectangle.puckHits(mode.puck)
                mode.puck.applyFriction(mode.friction)
                mode.puck.move()
                PracticeMode.checkEdge(mode)
                PracticeMode.checkWon(mode)
    
    def checkEdge(mode):
        #check if puck flies out of the screen or stopped on the other side
        #and apply puckHitsEdge
        puckOut = mode.puck.x < 0 or mode.puck.x > mode.width
        if mode.hand == 'Left': 
            puckStop = mode.puck.x >= mode.width/2 + 50 and mode.puck.dx == 0
        else:
            puckStop = mode.puck.x <= mode.width/2 - 50 and mode.puck.dx == 0
        if puckOut or puckStop:
            mode.lost = True
        mode.puck.puckHitsEdge(mode.height)
    
    def checkWon(mode):
        #won if all rectangles don't exist anymore
        for rectangle in mode.rectangles:
            if rectangle.exist:
                return
        mode.won = True
    
    def drawSelection(mode, canvas):
        font = "Times 36"
        canvas.create_text(mode.width/2, mode.height/4, 
                           text="Select left/right hand", font=font)
        canvas.create_text(mode.width/3, mode.height/2, text='Left', 
                           font=font, fill=mode.colors['Left'], anchor='n')
        canvas.create_text(mode.width/3 * 2, mode.height/2, text='Right', 
                           font=font, fill=mode.colors['Right'], anchor='n')
        canvas.create_text(mode.width-50, mode.height-50, text='Go', 
                        font=font, fill=mode.colors['Go'], anchor='se')
    
    #the followings are position detections for clickables
    def inLeft(mode, x, y):
        xInRange = x >= mode.width/3 - 36*2 and x <= mode.width/3 + 36*2
        yInRange = y >= mode.height/2 and y <= mode.height/2 + 36
        return xInRange and yInRange
    
    def inRight(mode, x, y):
        xInRange = x >= mode.width/3*2 - 36*2 and x <= mode.width/3*2 + 36*2
        yInRange = y >= mode.height/2 and y <= mode.height/2 + 36
        return xInRange and yInRange
    
    def inGo(mode, x, y):
        xInRange = x >= mode.width-50-2*36 and x <= mode.width-50
        yInRange = y >= mode.height-50-36 and y <= mode.height-50
        return xInRange and yInRange
    
    def drawInstruction(mode, canvas):
        if not mode.started:
            instruction = "Go to the camera window,\n\
hold the item you want to\n\
use to control your mallet,\n\
press 't' and select the item"
            canvas.create_rectangle(mode.width/2-220, mode.height/2-100,
                                    mode.width/2+220, mode.height/2+100,
                                    fill='white', outline='black', width=5)
            canvas.create_text(mode.width/2, mode.height/2, text=instruction,
                               font="Times 36")
    
    def drawMenuRetrack(mode, canvas):
        if mode.hand == 'Left':
            menuX, menuY, mAnchor = 5, 0, 'nw'
            retrackX, retrackY, rAnchor = 5, mode.height, 'sw'
        else:
            menuX, menuY, mAnchor = mode.width-5, 0, 'ne'
            retrackX, retrackY, rAnchor = mode.width-5, mode.height, 'se'
        canvas.create_text(menuX, menuY, text = 'Menu', fill = mode.menuColor,
                            font = "Times 36", anchor = mAnchor)
        canvas.create_text(retrackX, retrackY, text = 'Retrack', 
                fill = mode.retrackColor, font = "Times 36", anchor = rAnchor)
    
    def drawRectangles(mode, canvas):
        #only draw rectangles that exist, i.e. rectangle.exist == True
        if mode.hand == 'Left':
            for rectangle in mode.rectangles:
                if rectangle.exist:
                    canvas.create_rectangle(rectangle.x, rectangle.y, 
                                            rectangle.x + rectangle.width, 
                                            rectangle.y + rectangle.length,
                                            fill='black')
        else:
            for rectangle in mode.rectangles:
                if rectangle.exist:
                    canvas.create_rectangle(rectangle.x - rectangle.width, 
                                            rectangle.y, rectangle.x, 
                                            rectangle.y + rectangle.length,
                                            fill='black')
    
    def drawWarning(mode, canvas):
        if not mode.tracked and mode.started:
            canvas.create_rectangle(mode.width/2-540, mode.height/2-40,
                                    mode.width/2+540, mode.height/2+40,
                                    fill='white', outline='red', width=5)
            canvas.create_text(mode.width/2, mode.height/2, 
    text="Lost Item(s), please select the item(s) again in the camera window",
    fill='red', font='Arial 36')
    
    def drawMallet(mode, canvas):
        cx, cy = mode.mallet.x, mode.mallet.y
        canvas.create_oval(cx - mode.mallet.r, cy - mode.mallet.r, 
                           cx + mode.mallet.r, cy + mode.mallet.r, 
                           fill = "orange", outline = 'orange')

    def drawPuck(mode, canvas):
        cx, cy = mode.puck.x, mode.puck.y
        canvas.create_oval(cx - mode.puck.r, cy - mode.puck.r, 
                           cx + mode.puck.r, cy + mode.puck.r, 
                           fill = "black")
    
    def drawDone(mode, canvas):
        font = "Times 36 bold"
        if mode.won:
            canvas.create_rectangle(mode.width/2-90, mode.height/2-30,
                                   mode.width/2+90, mode.height/2+30,
                                   fill='white', outline='black', width=5)
            canvas.create_text(mode.width/2, mode.height/2, 
                                  text='Cleared!', font=font)
        elif mode.lost:
            canvas.create_rectangle(mode.width/2-90, mode.height/2-30,
                                   mode.width/2+90, mode.height/2+30,
                                   fill='white', outline='black', width=5)
            canvas.create_text(mode.width/2, mode.height/2, 
                                  text='Failed!', font=font, fill='black')
    
    def redrawAll(mode, canvas):
        if not mode.selected:
            canvas.create_image(mode.width/2, mode.height/2, 
                                image=ImageTk.PhotoImage(mode.background))
            PracticeMode.drawSelection(mode, canvas)
        else:
            PracticeMode.drawRectangles(mode, canvas)
            PracticeMode.drawMallet(mode, canvas)
            PracticeMode.drawPuck(mode, canvas)
            PracticeMode.drawDone(mode, canvas)
            PracticeMode.drawMenuRetrack(mode, canvas)
            PracticeMode.drawWarning(mode, canvas)
            PracticeMode.drawInstruction(mode, canvas)

class MyModalApp(ModalApp):
    def appStarted(app):
        app.splashScreenMode = SplashScreenMode()
        app.onePlayerMode = OnePlayerMode()
        app.twoPlayerMode = TwoPlayerMode()
        app.practiceMode = PracticeMode()
        app.setActiveMode(app.splashScreenMode)
        app.timerDelay = 5

app = MyModalApp(width=1280, height=720)