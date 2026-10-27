# Guide Installation Moteur de Distribution

## 📋 Système Complet

Le système comprend :
- **Moteur pas-à-pas 28BYJ-48** : Distribution des cartes
- **Bouton Distribution** : Contrôle du moteur
- **Boutons Hit/Stand & Double/Split** : Actions du jeu (travail des partenaires)
- **LEDs** : Indicateurs visuels (travail des partenaires)
- **Écran LCD** : Affichage (travail des partenaires)

## 🔌 Branchement Moteur 28BYJ-48

### Via le driver ULN2003

**Moteur 28BYJ-48 → ULN2003**
```
Fil Rouge    → +5V
Fil Jaune    → OUT1
Fil Orange   → OUT2
Fil Rose     → OUT3
Fil Bleu     → OUT4
```

**ULN2003 → Arduino**
```
IN1 → A0
IN2 → A1
IN3 → A2
IN4 → A3
+5V → 5V
GND → GND (connecter à l'Arduino)
```

### Bouton Distribution
```
Bouton → Arduino
Pin 1 → A5
Pin 2 → GND
```

### Récapitulatif pins Arduino

| Composant | Pin Arduino | Type |
|-----------|-----------|------|
| LCD RS | 2 | Digital |
| LCD E | 3 | Digital |
| LCD D4-D7 | 4-7 | Digital |
| Green LED | 8 | Digital |
| Blue LED | 9 | Digital |
| Red LED | 10 | Digital |
| Status LED Motor | 11 | Digital |
| Button Hit/Stand | 12 | Digital |
| Button Double/Split | 13 | Digital |
| **Moteur IN1** | **A0** | **Digital** |
| **Moteur IN2** | **A1** | **Digital** |
| **Moteur IN3** | **A2** | **Digital** |
| **Moteur IN4** | **A3** | **Digital** |
| **Bouton Distribution** | **A5** | **Digital** |

## 🔧 Configuration Moteur

Dans le code Arduino, vous pouvez ajuster :

```cpp
const int motorSpeed = 5;  // RPM (tours par minute)
```

Valeurs testées :
- **5 RPM** : Vitesse stable, moteur ne jamme pas ✅
- **10 RPM** : Plus rapide mais peut causer des blocages
- **15+ RPM** : Trop rapide, risque de jamming

## 🧪 Test Moteur

### Via Serial Monitor

1. Ouvrez Arduino IDE
2. Serial Monitor (Ctrl + Shift + M)
3. Envoyez les commandes :

```
CARD1   // Distribue 1 carte (2 tours)
TEST    // Test moteur (1 tour)
```

### Via Bouton Physique

- **Appuyez sur le bouton A5** → Distribue automatiquement 1 carte

## 🎮 Actions Complètes du Système

| Bouton | Action | Résultat |
|--------|--------|----------|
| **Hit/Stand** | Court appui | LED verte + "Hit" |
| **Hit/Stand** | Long appui (500ms) | LED rouge + "Stand" |
| **Double/Split** | Court appui | LED bleue + "Double" |
| **Double/Split** | Long appui (500ms) | LED verte + bleue + "Split" |
| **Distribution** | N'importe quel appui | Moteur distribue 1 carte |

## ⚙️ Nombre de Tours

Le moteur 28BYJ-48 a **2048 steps par tour complet**.

**Configuration actuelle :**
- **1 carte** = 2 tours complets (4096 steps)

Pour modifier, changez dans le code :

```cpp
motor.step(2048 * X);  // Pour X tours
```

## 🐛 Dépannage

### Le moteur ne bouge pas

- Vérifier branchement ULN2003 → Arduino (pins A0-A3)
- Vérifier alimentation 5V et GND
- Tester avec la commande `TEST` via Serial Monitor
- Vérifier que le fil rouge (commun) est connecté à +5V

### Le moteur jamme ou s'arrête

- **Réduire la vitesse** : motorSpeed = 3 ou 4 RPM
- Vérifier qu'aucun câble ne bloque le moteur physiquement
- Vérifier le branchement des 4 fils de contrôle

### Taps non détectés (bouton)

- Vérifier branchement A5 à GND
- Tester avec Serial : le pin doit lire 1 au repos, 0 quand appuyé

### Les LEDs ne s'allument pas (travail des partenaires)

- Vérifier branchement pins 8, 9, 10
- Vérifier polarité LEDs (anode vers Arduino)

## 📝 Notes

- Le moteur pas-à-pas 28BYJ-48 est **idéal** pour projeter les cartes
- Il peut faire des **tours continus illimités** (contrairement au servo 0-180°)
- Plus **stable et puissant** qu'un servomoteur
- La vitesse de **5 RPM** est le sweet spot pour éviter les blocages
- Le moteur peut être **très lent**, c'est normal - il gagne en puissance/stabilité

## 🚀 Améliorations Futures

- Ajouter un **capteur** pour détecter les cartes distribuées
- **Calibration automatique** de la vitesse selon la charge
- **Feedback** visuel/sonore lors de la distribution
- Intégration avec **Raspberry Pi** pour contrôle avancé
