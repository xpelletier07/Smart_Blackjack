#include <LiquidCrystal.h>
LiquidCrystal lcd(2,3,4,5,6,7);

int buttonHitStand = 12;
int buttonDoubleSplit = 13;
int greenLed = 8;
int blueLed = 9;
int redLed = 10;

int dureeLongPress = 500;
int dureeShortPress = 50;
int dureeDelay = 2000;

long hitStandPressTime = 0;
long doubleSplitPressTime = 0;
int hitStandPrev = LOW;      // au repos = LOW
int doubleSplitPrev = LOW;

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

void loop() {
  int hitStandState = digitalRead(buttonHitStand);
  int doubleSplitState = digitalRead(buttonDoubleSplit);

  // Bouton Hit/Stand
  if (hitStandState == HIGH && hitStandPrev == LOW) {
    hitStandPressTime = millis();                // on vient d'appuyer
  }
  if (hitStandState == LOW && hitStandPrev == HIGH) {
    long duree = millis() - hitStandPressTime;   // on vient de relâcher
    if (duree > dureeLongPress) {
      digitalWrite(redLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Stand");
      Serial.print("Action : Stand | Temps pressé : ");
      Serial.println(duree);
      delay(dureeDelay);
      reset();
    } else if (duree > dureeShortPress) {
      digitalWrite(greenLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Hit");
      Serial.print("Action : Hit | Temps pressé : ");
      Serial.println(duree);
      delay(dureeDelay);
      reset();
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
}