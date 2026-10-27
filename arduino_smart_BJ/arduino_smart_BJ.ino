#include <LiquidCrystal.h>
#include <ezBuzzer.h>
#include <Stepper.h>

LiquidCrystal lcd(2, 3, 4, 5, 6, 7);

// Variables

unsigned long actionStartTime = 0;
bool actionEnCours = false;

//// LED

// Boutons existants (travail des partenaires)
int buttonHitStand = 12;
int buttonDoubleSplit = 13;

// LEDs existantes (travail des partenaires)
int greenLed = 8;
int blueLed = 9;
int redLed = 10;

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

  lcd.print("Smart Blackjack");
  lcd.setCursor(0, 1);
  lcd.print("Ready!");
  delay(2000);
  lcd.clear();
  lcd.print("Action:");
}

void reset() {
  digitalWrite(greenLed, LOW);
  digitalWrite(blueLed, LOW);
  digitalWrite(redLed, LOW);
  lcd.setCursor(0, 1);
  lcd.print("                ");
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

void distribute_card(int Xturn) {
  motor.step(2048 * Xturn);
}

void loop() {
  buzzer.loop();
  int hitStandState = digitalRead(buttonHitStand);
  if (hitStandState == HIGH && hitStandPrev == LOW) {
    hitStandPressTime = millis();  // on vient d'appuyer
  }
  if (hitStandState == LOW && hitStandPrev == HIGH) {
    long duree = millis() - hitStandPressTime;  // on vient de relâcher
    if (duree > dureeLongPress) {
      digitalWrite(redLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Stand");
      Serial.print("Action : Stand | Temps : ");
      Serial.print(duree);
      melodyStand.play();
      Serial.println(" | Moteur : OFF");
      actionStartTime = millis();
      actionEnCours = true;
    } else if (duree > dureeShortPress) {
      digitalWrite(greenLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Hit");
      Serial.print("Action : Hit | Temps : ");
      Serial.print(duree);
      melodyHit.play();
      Serial.println(" | Moteur : ON, 1 tours");
      distribute_card(1);
      actionStartTime = millis();
      actionEnCours = true;
    }
  }
  hitStandPrev = hitStandState;

  int doubleSplitState = digitalRead(buttonDoubleSplit);
  if (doubleSplitState == HIGH && doubleSplitPrev == LOW) {
    doubleSplitPressTime = millis();
  }
  if (doubleSplitState == LOW && doubleSplitPrev == HIGH) {
    long duree = millis() - doubleSplitPressTime;
    if (duree > dureeLongPress) {
      digitalWrite(greenLed, HIGH);
      digitalWrite(blueLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Split");
      Serial.print("Action : Split | Temps : ");
      Serial.print(duree);
      melodySplit.play();
      Serial.println(" | Moteur : ON, 2 tours");
      distribute_card(1);
      delay(200);
      distribute_card(1);
      actionStartTime = millis();
      actionEnCours = true;
    } else if (duree > dureeShortPress) {
      digitalWrite(blueLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Double");
      Serial.print("Action : Double | Temps : ");
      Serial.print(duree);
      melodyDouble.play();
      Serial.println(" | Moteur : ON, 2 tours");
      distribute_card(1);
      actionStartTime = millis();
      actionEnCours = true;
    }
  }
  doubleSplitPrev = doubleSplitState;
  if (actionEnCours && millis() - actionStartTime >= dureeDelay) {
    reset();
    actionEnCours = false;
  }
}
