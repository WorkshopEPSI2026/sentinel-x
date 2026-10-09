# =====================================================================
#  Sentinel-X G1 — génération du boîtier dans Autodesk Fusion (API Python)
#
#  Crée un NOUVEAU document avec 2 composants :
#    - "Boite"     : coque 144 x 104 x 57 mm, murs/fond 2 mm, ouvertures
#                    (PIR, DHT22, USB, aérations, encoche), cadre de breadboard,
#                    glissières du PIR, empreinte de plaque laser à l'arrière
#    - "Couvercle" : plaque 2 mm + jupe d'emboîtement, fenêtre OLED, trous MQ-2
#                    et buzzer, empreinte de plaque laser (logo + n° de série)
#  Chaque opération apparaît dans la timeline (historique) de Fusion.
#
#  Repère : origine au centre du fond, au sol. X = gauche -> droite (USB à droite),
#  Y = avant (PIR, Y négatif) -> arrière, Z = haut. Cotes en mm.
#
#  Utilisation : Utilitaires -> Scripts et compléments (Maj+S) -> + Créer
#  -> Python -> coller ce fichier dans le .py créé -> Exécuter.
# =====================================================================
import math
import traceback

import adsk.core
import adsk.fusion

# ---------------------------- COTES (mm) ----------------------------
L_INT, P_INT, H_INT = 140.0, 100.0, 55.0   # intérieur : longueur, profondeur, hauteur
EP = 2.0                                     # murs et fond
R_COIN = 4.0                                 # rayon des coins extérieurs
JEU = 0.3                                    # jeu du couvercle (0.4 si trop serré)
JUPE_H, JUPE_EP = 5.0, 1.6                   # jupe du couvercle

L_EXT, P_EXT, H_EXT = L_INT + 2 * EP, P_INT + 2 * EP, H_INT + EP   # 144 x 104 x 57

D_PIR, Z_PIR = 23.5, 33.0          # dôme du PIR, centre au-dessus du sol
DHT_W, DHT_H, Z_DHT = 16.0, 26.0, 26.0
USB_W, USB_H, Z_USB = 16.0, 18.0, 19.0
D_MQ2 = 20.5

OLED = (-28.0, 5.0)                # centres sur le couvercle (X ; Y)
MQ2 = (35.0, 12.0)
BUZ = (35.0, -30.0)

BB_L, BB_W = 80.0, 55.0            # breadboard
BB_RIGHT = L_INT / 2 - 2.0         # bord droit de la breadboard (2 mm du mur droit)

app = None
ui = None


def cm(v_mm):
    """L'API Fusion travaille en centimètres."""
    return v_mm / 10.0


def val(v_mm):
    return adsk.core.ValueInput.createByReal(cm(v_mm))


# ------------------------------ OUTILS ------------------------------
def plan_decale(comp, base, decalage_mm, axe, cible_mm):
    """Plan parallèle à 'base', placé à cible_mm sur l'axe donné (le signe est vérifié)."""
    planes = comp.constructionPlanes
    for signe in (1, -1):
        pi = planes.createInput()
        pi.setByOffset(base, val(signe * decalage_mm))
        pl = planes.add(pi)
        o = pl.geometry.origin
        pos = {"x": o.x, "y": o.y, "z": o.z}[axe] * 10.0
        if abs(pos - cible_mm) < 0.01:
            return pl
        pl.deleteMe()
    raise RuntimeError("Impossible de placer le plan à %s = %s mm" % (axe, cible_mm))


class Esquisse:
    """Esquisse dont on donne les points en coordonnées MONDE (mm)."""

    def __init__(self, comp, plan, nom):
        self.sk = comp.sketches.add(plan)
        self.sk.name = nom

    def p(self, x, y, z):
        return self.sk.modelToSketchSpace(adsk.core.Point3D.create(cm(x), cm(y), cm(z)))

    def rect(self, a, b):
        """Rectangle par deux coins opposés (points monde)."""
        self.sk.sketchCurves.sketchLines.addTwoPointRectangle(self.p(*a), self.p(*b))

    def cercle(self, c, rayon):
        self.sk.sketchCurves.sketchCircles.addByCenterRadius(self.p(*c), cm(rayon))

    def rect_arrondi_xy(self, cx, cy, z, w, h, r):
        """Rectangle à coins arrondis dans un plan horizontal (Z = z)."""
        lines = self.sk.sketchCurves.sketchLines
        arcs = self.sk.sketchCurves.sketchArcs
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        bas = lines.addByTwoPoints(self.p(x0 + r, y0, z), self.p(x1 - r, y0, z))
        droite = lines.addByTwoPoints(self.p(x1, y0 + r, z), self.p(x1, y1 - r, z))
        haut = lines.addByTwoPoints(self.p(x1 - r, y1, z), self.p(x0 + r, y1, z))
        gauche = lines.addByTwoPoints(self.p(x0, y1 - r, z), self.p(x0, y0 + r, z))
        k = r * (1 - math.sqrt(0.5))
        arcs.addByThreePoints(bas.endSketchPoint, self.p(x1 - k, y0 + k, z), droite.startSketchPoint)
        arcs.addByThreePoints(droite.endSketchPoint, self.p(x1 - k, y1 - k, z), haut.startSketchPoint)
        arcs.addByThreePoints(haut.endSketchPoint, self.p(x0 + k, y1 - k, z), gauche.startSketchPoint)
        arcs.addByThreePoints(gauche.endSketchPoint, self.p(x0 + k, y0 + k, z), bas.startSketchPoint)

    def profils(self, anneau=False):
        """Tous les profils, ou seulement ceux en anneau (2 boucles) si anneau=True."""
        coll = adsk.core.ObjectCollection.create()
        for pr in self.sk.profiles:
            if not anneau or pr.profileLoops.count == 2:
                coll.add(pr)
        return coll


def extruder(comp, profils, dist_mm, operation, corps=None, sens=1, symetrique=False, nom=""):
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(profils, operation)
    if symetrique:
        inp.setSymmetricExtent(val(dist_mm), True)
    else:
        direction = (adsk.fusion.ExtentDirections.PositiveExtentDirection if sens > 0
                     else adsk.fusion.ExtentDirections.NegativeExtentDirection)
        inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(val(dist_mm)), direction)
    if corps:
        # on relit le corps à chaque fois : la référence reste valide après les fonctions précédentes
        inp.participantBodies = [comp.bRepBodies.item(0)]
    f = ext.add(inp)
    if nom:
        f.name = nom
    return f


JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation


# ------------------------------ LA BOÎTE ------------------------------
def creer_boite(root):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = "Boite"

    # 1. Bloc extérieur à coins arrondis
    e = Esquisse(comp, comp.xYConstructionPlane, "Contour exterieur")
    e.rect_arrondi_xy(0, 0, 0, L_EXT, P_EXT, R_COIN)
    extruder(comp, e.profils(), H_EXT, NEW, nom="Bloc").bodies.item(0).name = "Boite"
    corps = True

    # 2. On vide l'intérieur (fond de 2 mm)
    pl_fond = plan_decale(comp, comp.xYConstructionPlane, EP, "z", EP)
    e = Esquisse(comp, pl_fond, "Interieur")
    e.rect((-L_INT / 2, -P_INT / 2, EP), (L_INT / 2, P_INT / 2, EP))
    extruder(comp, e.profils(), H_INT + 1, CUT, corps, nom="Vider")

    # 3. Mur AVANT (plan au milieu du mur, Y = -51) : PIR + encoche d'ouverture
    y_av = -(P_INT / 2 + EP / 2)
    pl = plan_decale(comp, comp.xZConstructionPlane, abs(y_av), "y", y_av)
    e = Esquisse(comp, pl, "Mur avant - PIR et encoche")
    e.cercle((0, y_av, Z_PIR), D_PIR / 2)
    e.cercle((0, y_av, H_EXT), 7.0)
    extruder(comp, e.profils(), EP + 2, CUT, corps, symetrique=True, nom="PIR + encoche")

    # 4. Mur ARRIÈRE (Y = +51) : 7 fentes d'aération
    y_ar = P_INT / 2 + EP / 2
    pl = plan_decale(comp, comp.xZConstructionPlane, y_ar, "y", y_ar)
    e = Esquisse(comp, pl, "Mur arriere - aeration")
    for i in range(7):
        x = -45 + i * 15
        e.rect((x - 1.5, y_ar, EP + H_INT - 20), (x + 1.5, y_ar, EP + H_INT - 6))
    extruder(comp, e.profils(), EP + 2, CUT, corps, symetrique=True, nom="Aeration arriere")

    # 5. Mur GAUCHE (X = -71) : DHT22 + 4 fentes
    x_g = -(L_INT / 2 + EP / 2)
    pl = plan_decale(comp, comp.yZConstructionPlane, abs(x_g), "x", x_g)
    e = Esquisse(comp, pl, "Mur gauche - DHT22")
    e.rect((x_g, -DHT_W / 2, Z_DHT - DHT_H / 2), (x_g, DHT_W / 2, Z_DHT + DHT_H / 2))
    for y in (-30, -10, 10, 30):
        e.rect((x_g, y - 1.5, EP + H_INT - 15), (x_g, y + 1.5, EP + H_INT - 5))
    extruder(comp, e.profils(), EP + 2, CUT, corps, symetrique=True, nom="DHT22 + aeration gauche")

    # 6. Mur DROIT (X = +71) : passage USB + 4 fentes
    x_d = L_INT / 2 + EP / 2
    pl = plan_decale(comp, comp.yZConstructionPlane, x_d, "x", x_d)
    e = Esquisse(comp, pl, "Mur droit - USB")
    e.rect((x_d, -USB_W / 2, Z_USB - USB_H / 2), (x_d, USB_W / 2, Z_USB + USB_H / 2))
    for y in (-30, -10, 10, 30):
        e.rect((x_d, y - 1.5, EP + H_INT - 15), (x_d, y + 1.5, EP + H_INT - 5))
    extruder(comp, e.profils(), EP + 2, CUT, corps, symetrique=True, nom="USB + aeration droite")

    # 7. Cadre de la breadboard (posé sur le fond, 3 mm de haut)
    e = Esquisse(comp, pl_fond, "Cadre breadboard")
    xi0, xi1 = BB_RIGHT - BB_L - JEU, BB_RIGHT + JEU
    yi = BB_W / 2 + JEU
    e.rect((xi0, -yi, EP), (xi1, yi, EP))
    e.rect((xi0 - 1.2, -yi - 1.2, EP), (xi1 + 1.2, yi + 1.2, EP))
    extruder(comp, e.profils(anneau=True), 3, JOIN, corps, nom="Cadre breadboard")
    e = Esquisse(comp, pl_fond, "Passage USB du cadre")
    e.rect((xi1 - 1.3, -10, EP), (L_INT / 2 - 0.2, 10, EP))
    extruder(comp, e.profils(), 3, CUT, corps, nom="Passage USB")

    # 8. Glissières du PIR (contre le mur avant, à l'intérieur)
    pl = plan_decale(comp, comp.xYConstructionPlane, Z_PIR - 14, "z", Z_PIR - 14)
    e = Esquisse(comp, pl, "Glissieres PIR")
    for s in (-1, 1):
        e.rect((s * 15.8, -P_INT / 2, Z_PIR - 14), (s * 19.8, -P_INT / 2 + 4.5, Z_PIR - 14))
    extruder(comp, e.profils(), 30, JOIN, corps, nom="Glissieres PIR")
    pl = plan_decale(comp, comp.xYConstructionPlane, Z_PIR - 12.2, "z", Z_PIR - 12.2)
    e = Esquisse(comp, pl, "Rainures PIR")
    for s in (-1, 1):
        e.rect((s * 15.3, -P_INT / 2, Z_PIR - 12.2), (s * 17.3, -P_INT / 2 + 2, Z_PIR - 12.2))
    extruder(comp, e.profils(), 40, CUT, corps, nom="Rainures PIR")

    # 9. Empreinte de la plaque « consignes de sécurité » (mur arrière, 1 mm)
    y_ext = P_INT / 2 + EP
    pl = plan_decale(comp, comp.xZConstructionPlane, y_ext, "y", y_ext)
    e = Esquisse(comp, pl, "Empreinte plaque consignes")
    e.rect((-55, y_ext, 8), (55, y_ext, 30))
    extruder(comp, e.profils(), 2, CUT, corps, symetrique=True, nom="Empreinte consignes")
    return comp


# ----------------------------- LE COUVERCLE -----------------------------
def creer_couvercle(root):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = "Couvercle"

    # 1. Plaque (posée sur la boîte, Z de 57 à 59)
    pl = plan_decale(comp, comp.xYConstructionPlane, H_EXT, "z", H_EXT)
    e = Esquisse(comp, pl, "Plaque")
    e.rect_arrondi_xy(0, 0, H_EXT, L_EXT, P_EXT, R_COIN)
    extruder(comp, e.profils(), 2, NEW, nom="Plaque").bodies.item(0).name = "Couvercle"
    corps = True

    # 2. Jupe qui s'emboîte dans la boîte (5 mm vers le bas)
    e = Esquisse(comp, pl, "Jupe")
    xo, yo = L_INT / 2 - JEU, P_INT / 2 - JEU
    e.rect((-xo, -yo, H_EXT), (xo, yo, H_EXT))
    e.rect((-xo + JUPE_EP, -yo + JUPE_EP, H_EXT), (xo - JUPE_EP, yo - JUPE_EP, H_EXT))
    extruder(comp, e.profils(anneau=True), JUPE_H, JOIN, corps, sens=-1, nom="Jupe")

    # 3. Ouvertures : OLED, MQ-2 + couronne, buzzer
    e = Esquisse(comp, pl, "Ouvertures couvercle")
    z = H_EXT
    e.rect((OLED[0] - 12.5, OLED[1] - 7, z), (OLED[0] + 12.5, OLED[1] + 7, z))
    e.cercle((MQ2[0], MQ2[1], z), D_MQ2 / 2)
    for k in range(8):
        a = k * math.pi / 4
        e.cercle((MQ2[0] + 17 * math.cos(a), MQ2[1] + 17 * math.sin(a), z), 1.5)
    for dx, dy in ((0, 0), (5, 0), (-5, 0), (0, 5), (0, -5)):
        e.cercle((BUZ[0] + dx, BUZ[1] + dy, z), 1.25)
    extruder(comp, e.profils(), 3, CUT, corps, nom="OLED + MQ-2 + buzzer")

    # 4. Empreinte de la plaque « logo + n° de série » (1 mm de profondeur)
    pl_haut = plan_decale(comp, comp.xYConstructionPlane, H_EXT + 2, "z", H_EXT + 2)
    e = Esquisse(comp, pl_haut, "Empreinte plaque logo")
    e.rect((-58, 23, H_EXT + 2), (2, 43, H_EXT + 2))
    extruder(comp, e.profils(), 1, CUT, corps, sens=-1, nom="Empreinte logo")
    return comp


def run(context):
    global app, ui
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        root = design.rootComponent

        creer_boite(root)
        creer_couvercle(root)

        app.activeViewport.fit()
        ui.messageBox("Boîtier Sentinel-X généré.\n\n"
                      "Composants : Boite + Couvercle.\n"
                      "Export : clic droit sur un composant -> Enregistrer en tant que maillage (STL).")
    except Exception:
        if ui:
            ui.messageBox("Erreur :\n{}".format(traceback.format_exc()))
