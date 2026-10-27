#include <LiquidCrystal.h>
#include <ezBuzzer.h>
LiquidCrystal lcd(2, 3, 4, 5, 6, 7);

// Variables

unsigned long actionStartTime = 0;
bool actionEnCours = false;

//// LED
int greenLed = 8;
int blueLed = 9;
int redLed = 10;

//// Button
int buttonHitStand = 12;
int buttonDoubleSplit = 13;

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
  pinMode(buttonHitStand, INPUT);
  pinMode(buttonDoubleSplit, INPUT);
  pinMode(greenLed, OUTPUT);
  pinMode(blueLed, OUTPUT);
  pinMode(redLed, OUTPUT);
  lcd.print("Action :");
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


void loop() {
  buzzer.loop();
  int hitStandState = digitalRead(buttonHitStand);
  int doubleSplitState = digitalRead(buttonDoubleSplit);

  // Bouton Hit/Stand
  if (hitStandState == HIGH && hitStandPrev == LOW) {
    hitStandPressTime = millis();  // on vient d'appuyer
  }
  if (hitStandState == LOW && hitStandPrev == HIGH) {
    long duree = millis() - hitStandPressTime;  // on vient de relâcher
    if (duree > dureeLongPress) {
      digitalWrite(redLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Stand");
      Serial.print("Action : Stand | Temps pressé : ");
      Serial.println(duree);
      melodyStand.play();
      actionStartTime = millis();
      actionEnCours = true;
    } else if (duree > dureeShortPress) {
      digitalWrite(greenLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Hit");
      Serial.print("Action : Hit | Temps pressé : ");
      Serial.println(duree);
      melodyHit.play();
      actionStartTime = millis();
      actionEnCours = true;
    }
  }
  hitStandPrev = hitStandState;

  // Bouton Double/Split
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
      Serial.print("Action : Split | Temps pressé : ");
      Serial.println(duree);
      delay(dureeDelay);
      reset();
    } else if (duree > dureeShortPress) {
      digitalWrite(blueLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Double");
      Serial.print("Action : Double | Temps pressé : ");
      Serial.println(duree);
      delay(dureeDelay);
      reset();
    }
  }
  doubleSplitPrev = doubleSplitState;
  if (actionEnCours &&
    millis() - actionStartTime >= dureeDelay) {
  reset();
  actionEnCours = false;
}
}