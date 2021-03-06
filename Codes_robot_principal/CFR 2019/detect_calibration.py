
"""
Programme permettant le calibrage des filtres utilisés pour la capture des palets RGB
 et du goldenium sur les images.
"""

# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
from detect_auto_global_opti_max2 import * #nom du fichier dans lequel se trouvent les fonctions pour opencv
import cv2
#from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
import imutils
# module imutils : module avec des classes utiles pour le traitement d'image. Permet notamment 
# d'enregistrer le nombre de FPS pour la capture d'image, mais aussi d'effectuer 
# du multithreading.
# Le multithreading s'effectue via la classe PiVideoSteam (classe redéfinie juste
# en dessous ici).


class PiVideoStream:
    def __init__(self, resolution=(320, 240), framerate=32):
        self.camera = PiCamera()
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        #self.camera.brightness = 60#30
        #self.camera.contrast = 60
        #self.camera.saturation = 60
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,format="bgr", use_video_port=True)
        self.frame = None
        self.stopped = False
    
    def start(self):
        Thread(target=self.update, args=()).start()
        return self
    def update(self):
        for f in self.stream:
            self.frame = f.array
            self.rawCapture.truncate(0)
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return
    def read(self):
        return self.frame
    
    def stop(self):
        self.stopped = True


print("[INFO] sampling THREADED frames from `picamera` module...")
# Initialisation de l'objet PiVideoStream
#On laisse 3 secondes pour permettre à la caméra de s'initialiser
vs = PiVideoStream().start()
time.sleep(3.0)


# lecture de l'image et remise à une échelle plus petite, pour accélérer le traitement.
frame = vs.read()
img_C = imutils.resize(frame, width=400)

# Affichage image via opencv --> affichage format BGR

cv2.namedWindow("mon image BGR", cv2.WINDOW_NORMAL) 
cv2.imshow("mon image BGR", img_C)


def Egalisation_HSL(img_BGR):
    """
    Permet de réhausser les contrastes, via l'égalisation des histogrammes
    des composantes de l'image, pour la détection de palets RGB.
    A noter : pour du HSL, l'égalisation n'a généralement lieu que sur la
    composante L (luminance), parfois sur la composante S, jamais sur la H 
    (forte dégradation des couleurs de l'image sinon).
    """
    img_HSL = cv2.cvtColor(img_BGR,cv2.COLOR_BGR2HLS) # Image BGR --> HSV
    h,l,s   = cv2.split(img_HSL)                      # Extraction des 3 plans HSV notamment value v
    h_egal = cv2.equalizeHist(h)
    s_egal  = cv2.equalizeHist(s)                     # Egalisation histogramme sur s
    l_egal  = cv2.equalizeHist(l)                     # Egalisation histogramme sur v
    
    img_egal= img_HSL.copy()               # Copie de l'image HSL
    #img_egal[:,:,0] = h_egal             # Modification du plan h
    #img_egal[:,:,2] = s_egal             # Modification du plan s
    #img_egal[:,:,1] = l_egal              # Modification du plan l (parfois utile pour détection du blanc)
    
    return img_result

# 1. Mise en oeuvre egalisation HSL
img_egalisation = Egalisation_HSL(img_C)

cv2.namedWindow("Ega", cv2.WINDOW_NORMAL) 
cv2.imshow("Ega", img_egalisation)

imgHSL = img_egalisation.copy()
# Etapes 2 et 3 : application filtres des composants, filtres ouverture et fermeture

def binarizeHSL(p                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       os):
    """
    Permet de filtrer l'image selon les valeurs maximales / minimales des
    composantes HSL choisies via les barres.
    Effectue ensuite les opérations de fermeture puis d'ouverture sur l'image.
    Pour cela, utilise un élément structurant de forme éliptique, dont la taille
    est fixée via les barres.
    """
    
    # Fixe les valeurs des composantes HSL
    Hmin = cv2.getTrackbarPos('Hmin','Mon masque')
    Hmax = cv2.getTrackbarPos('Hmax','Mon masque')
    Smin = cv2.getTrackbarPos('Smin','Mon masque')
    Smax = cv2.getTrackbarPos('Smax','Mon masque')
    Lmin = cv2.getTrackbarPos('Lmin','Mon masque')
    Lmax = cv2.getTrackbarPos('Lmax','Mon masque')
    # Fixe la taille des éléments structurants
    k1 = cv2.getTrackbarPos('Taille k1','Mon masque')
    k2 = cv2.getTrackbarPos('Taille k2','Mon masque')


    lower = np.array([Hmin,Lmin,Smin])
    upper = np.array([Hmax,Lmax,Smax])

    # Applique les filtres de couleurs sur l'image
    img_bin = cv2.inRange(imgHSL,lower,upper)
    img_calc = cv2.bitwise_and(imgHSL,imgHSL,mask = img_bin)
    cv2.imshow('Mon masque',img_bin)
    
    # La tailles des éléments structurants doit être impaire.
    kf = 2*k1 + 1 
    ko = 2*k2 + 1 
    
    # Crée les filtres ouverture/fermeture
    kernelf = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kf, kf))
    kernelo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ko, ko))
   
    # Applique ces filtres sur l'image
    et1 = cv2.morphologyEx(img_bin, cv2.MORPH_CLOSE, kernelf)
    et2 = cv2.morphologyEx(et1, cv2.MORPH_OPEN, kernelo)

    # Renvoie l'image sous forme binarisée, puis en couleur.
    cv2.imshow('Ap fermeture / ouverture ',et2)
    img3 = cv2.bitwise_and(img_calc,img_calc,mask=et2)

    cv2.imshow("image finale",img3)
    



# Creation des barres de défilement pour régler les filtres

cv2.namedWindow('Mon masque',cv2.WINDOW_NORMAL)
cv2.createTrackbar('Hmin','Mon masque',0,255,binarizeHSL)
cv2.createTrackbar('Hmax','Mon masque',cv2.getTrackbarPos('Hmin','Mon masque'),255,binarizeHSL)
cv2.createTrackbar('Smin','Mon masque',0,255,binarizeHSL)
cv2.createTrackbar('Smax','Mon masque',cv2.getTrackbarPos('Smin','Mon masque'),255,binarizeHSL)
cv2.createTrackbar('Lmin','Mon masque',0,255,binarizeHSL)
cv2.createTrackbar('Lmax','Mon masque',cv2.getTrackbarPos('Lmin','Mon masque'),255,binarizeHSL)
cv2.createTrackbar('Taille k1','Mon masque',0,18,binarizeHSL)
cv2.createTrackbar('Taille k2','Mon masque',0,18,binarizeHSL)
# Test
binarizeHSL(0)



##### FIN
cv2.waitKey(0)                     
cv2.destroyAllWindows()
vs.stop()

