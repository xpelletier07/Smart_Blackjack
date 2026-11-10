#include <LiquidCrystal.h>
#include <ezBuzzer.h>
#include <Stepper.h>
#include <TM1637Display.h>

LiquidCrystal lcd(2, 3, 4, 5, 6, 7);

#define CLK A4
#define DIO A5

TM1637Display display(CLK, DIO);

// Variables

unsigned long actionStartTime = 0;
bool actionEnCours = false;

//// LED

// Boutons existants (travail des partenaires)
int buttonHitStand = 12;
int buttonDoubleSplit = 13;

// LEDs existantes (travail des partenaires)
int greenLed = 9;
int blueLed = 10;
int redLed = 8;

// Configuration moteur pas-à-pas 28BYJ-48 (moteur distribution)
const int stepsPerRevolution = 2048;
const int motorPin1 = A0;
const int motorPin2 = A1;
const int motorPin3 = A2;
const int motorPin4 = A3;

Stepper motor(stepsPerRevolution, motorPin1, motorPin3, motorPin2, motorPin4);
const int motorSpeed = 15;  // RPM9


// Timings
int dureeLongPress = 500;
int dureeShortPress = 50;
int dureeDelay = 2000;

long hitStandPressTime = 0;
long doubleSplitPressTime = 0;
int hitStandPrev = LOW;  // au repos = LOW
int doubleSplitPrev = LOW;

//// Buzzer
int buzzer_pin = 11;
ezBuzzer buzzer(buzzer_pin, BUZZER_TYPE_PASSIVE, HIGH);


void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);

  // Configuration boutons
  pinMode(buttonHitStand, INPUT);
  pinMode(buttonDoubleSplit, INPUT);

  // Configuration LEDs
  pinMode(greenLed, OUTPUT);
  pinMode(blueLed, OUTPUT);
  pinMode(redLed, OUTPUT);

  // Configuration moteur
  motor.setSpeed(motorSpeed);

  // Configuration digit display
  display.setBrightness(0x0f);

  starting_distribution();
}

void starting_distribution() {
  display.clear();

  lcd.print("Smart Blackjack");
  lcd.setCursor(0, 1);
  lcd.print("Distributing...");
  affichage("Distribution", true, 4, false, false, false, false, "");

  distribute_card(1);
  delay(400);
  distribute_card(1);
  delay(400);
  distribute_card(1);
  delay(400);
  distribute_card(1);

  lcd.clear();
  lcd.print("Action:");
}

void reset() {
  digitalWrite(greenLed, LOW);
  digitalWrite(blueLed, LOW);
  digitalWrite(redLed, LOW);
  lcd.setCursor(0, 1);
  lcd.print("                ");
  affichage("Reset", false, 0, false, false, false, false, "");
}


// Melodie for Buzzer
// Hit : mélodie ascendante
const int melodyHitNotes[] = {
  523, 659, 784
};

const int melodyHitDurations[] = {
  8, 8, 4
};

// Stand : mélodie descendante
const int melodyStandNotes[] = {
  784, 523
};

const int melodyStandDurations[] = {
  4, 2
};

// Double 
const int melodyDoubleNotes[] = {
  523, 659, 784
};

const int melodyDoubleDurations[] = {
  8, 8, 4
};
// Split
const int melodySplitNotes[] = {
  784, 523
};

const int melodySplitDurations[] = {
  4, 2
};

class Melody {
private:
  const int* notes;
  const int* durations;
  int len;

public:
  Melody(const int melodyNotes[],
         const int melodyDurations[],
         int melodyLength) {
    notes = melodyNotes;
    durations = melodyDurations;
    len = melodyLength;
  }

  void play() {
    buzzer.playMelody(
      (int*)notes,
      (int*)durations,
      len);
  }
};

Melody melodyStand(
  melodyStandNotes,
  melodyStandDurations,
  sizeof(melodyStandNotes) / sizeof(melodyStandNotes[0]));

Melody melodyHit(
  melodyHitNotes,
  melodyHitDurations,
  sizeof(melodyHitNotes) / sizeof(melodyHitNotes[0]));

Melody melodyDouble(
  melodyDoubleNotes,
  melodyDoubleDurations,
  sizeof(melodyDoubleNotes) / sizeof(melodyDoubleNotes[0]));

Melody melodySplit(
  melodySplitNotes,
  melodySplitDurations,
  sizeof(melodySplitNotes) / sizeof(melodySplitNotes[0]));

// Fonction pour distribuer une carte ou plusieurs cartes en fonction du nombre de tours spécifié
void distribute_card(int Xturn) {
  motor.step(2048 * Xturn);
}

// Fonction pour afficher les informations sur le port série
void affichage(String action, bool moteur, int nombre_tours, bool buzzer, bool greenLed, bool blueLed, bool redLed, String digit_display) {
  Serial.print(action);
  Serial.print(":");
  Serial.print(moteur);
  Serial.print(":");
  Serial.print(nombre_tours);
  Serial.print(":");
  Serial.print(buzzer);
  Serial.print(":");
  Serial.print(greenLed);
  Serial.print(":");
  Serial.print(blueLed);
  Serial.print(":");
  Serial.print(redLed);
  Serial.print(":");
  Serial.println(digit_display);
}

// Fonction pour effectuer une action spécifique
void faireAction(String action) {
  if (action == "Hit") {
    digitalWrite(greenLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Hit");

    // 4 Digit display
    uint8_t seg_hit[] = { 0x00, 0x76, 0x06, 0x78 }; // [Vide], H, I, t
    display.setSegments(seg_hit);


    melodyHit.play();
    affichage("Hit", true, 1, true, true, false, false, "H1t");
    distribute_card(1);
    actionStartTime = millis();
    actionEnCours = true;
  } else if (action == "Stand") {
    digitalWrite(redLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Stand");

    // 4 Digit display
    uint8_t seg_stnd[] = { 0x6D, 0x78, 0x54, 0x5E }; // 5, t, n, d
    display.setSegments(seg_stnd);

    melodyStand.play();
    affichage("Stand", false, 0, true, false, false, true, "5tnd");
    actionStartTime = millis();
    actionEnCours = true;
  } else if (action == "Double") {
    digitalWrite(blueLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Double");

    // 4 Digit display
    uint8_t seg_dbl[] = { 0x00, 0x5E, 0x7C, 0x38 }; // [Vide], d, b, L
    display.setSegments(seg_dbl);

    melodyDouble.play();
    affichage("Double", true, 1, true, false, true, false, "dbL");
    distribute_card(1);
    actionStartTime = millis();
    actionEnCours = true;
  } else if (action == "Split") {
    digitalWrite(greenLed, HIGH);
    digitalWrite(blueLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Split");

    // 4 Digit display
    uint8_t seg_splt[] = { 0x6D, 0x73, 0x38, 0x78 }; // 5, P, L, t
    display.setSegments(seg_splt);

    melodySplit.play();
    affichage("Split", true, 2, true, true, true, false, "5PLt");
    distribute_card(1);
    delay(200);
    distribute_card(1);
    actionStartTime = millis();
    actionEnCours = true;
  }
}

// Fonction principale de la boucle
void loop() {
  buzzer.loop();

  // Lecture de l'état des boutons et gestion des actions en fonction de la durée d'appui
  int hitStandState = digitalRead(buttonHitStand);
  if (hitStandState == HIGH && hitStandPrev == LOW) {
    hitStandPressTime = millis();  // on vient d'appuyer
  }
  if (hitStandState == LOW && hitStandPrev == HIGH) {
    long duree = millis() - hitStandPressTime;  // on vient de relâcher
    if (duree > dureeLongPress) {
      faireAction("Stand");
    } else if (duree > dureeShortPress) {
      faireAction("Hit");
    }
  }
  hitStandPrev = hitStandState;

  // Lecture de l'état du bouton Double/Split et gestion des actions en fonction de la durée d'appui
  int doubleSplitState = digitalRead(buttonDoubleSplit);
  if (doubleSplitState == HIGH && doubleSplitPrev == LOW) {
    doubleSplitPressTime = millis();
  }
  if (doubleSplitState == LOW && doubleSplitPrev == HIGH) {
    long duree = millis() - doubleSplitPressTime;
    if (duree > dureeLongPress) {
      faireAction("Split");
    } else if (duree > dureeShortPress) {
      faireAction("Double");
    }
  }
  doubleSplitPrev = doubleSplitState;
  if (actionEnCours && millis() - actionStartTime >= dureeDelay) {
    reset();
    actionEnCours = false;
  }

  // Lecture des commandes série envoyées par blackjack_utils.py (format "COMMANDE" ou "COMMANDE:valeur")
  if (Serial.available() > 0) {
    String ligne = Serial.readStringUntil('\n');
    ligne.trim();

    // Séparation de la commande et de la valeur
    String command = ligne;
    String valeur = "";
    int sep = ligne.indexOf(':');
    if (sep != -1) {
      command = ligne.substring(0, sep);
      valeur = ligne.substring(sep + 1);
    }

    if (command == "GREEN_LED_ON") {
      digitalWrite(greenLed, HIGH);
    } else if (command == "GREEN_LED_OFF") {
      digitalWrite(greenLed, LOW);
    } else if (command == "BLUE_LED_ON") {
      digitalWrite(blueLed, HIGH);
    } else if (command == "BLUE_LED_OFF") {
      digitalWrite(blueLed, LOW);
    } else if (command == "RED_LED_ON") {
      digitalWrite(redLed, HIGH);
    } else if (command == "RED_LED_OFF") {
      digitalWrite(redLed, LOW);
    } else if (command == "BUZZER_ON") {
      tone(buzzer_pin, 1000, 500);
    } else if (command == "BUZZER_OFF") {
      buzzer.stop();
    } else if (command == "LCD") {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print(valeur);
    } else if (command == "ACTION") {
      faireAction(valeur);
    } else if (command == "SCORE") {
      display.showNumberDec(valeur.toInt());
    }
  }
  
}
