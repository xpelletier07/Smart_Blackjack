#include <LiquidCrystal.h>
#include <Stepper.h>

LiquidCrystal lcd(2, 3, 4, 5, 6, 7);

// Boutons existants (travail des partenaires)
int buttonHitStand = 12;
int buttonDoubleSplit = 13;
int buttonDistribution = A5;  // Nouveau bouton pour moteur

// LEDs existantes (travail des partenaires)
int greenLed = 8;
int blueLed = 9;
int redLed = 10;
int statusLedMotor = 11;

// Configuration moteur pas-à-pas 28BYJ-48 (moteur distribution)
const int stepsPerRevolution = 2048;
const int motorPin1 = A0;
const int motorPin2 = A1;
const int motorPin3 = A2;
const int motorPin4 = A3;

Stepper motor(stepsPerRevolution, motorPin1, motorPin2, motorPin3, motorPin4);
const int motorSpeed = 5;  // RPM

// Timings
int dureeLongPress = 500;
int dureeShortPress = 50;
int dureeDelay = 2000;

long hitStandPressTime = 0;
long doubleSplitPressTime = 0;

int hitStandPrev = LOW;
int doubleSplitPrev = LOW;
int distributionPrev = LOW;

void setup() {
  Serial.begin(9600);
  lcd.begin(16, 2);

  // Configuration boutons
  pinMode(buttonHitStand, INPUT);
  pinMode(buttonDoubleSplit, INPUT);
  pinMode(buttonDistribution, INPUT_PULLUP);

  // Configuration LEDs
  pinMode(greenLed, OUTPUT);
  pinMode(blueLed, OUTPUT);
  pinMode(redLed, OUTPUT);
  pinMode(statusLedMotor, OUTPUT);

  // Configuration moteur
  motor.setSpeed(motorSpeed);
  digitalWrite(statusLedMotor, LOW);

  lcd.print("Smart Blackjack");
  lcd.setCursor(0, 1);
  lcd.print("Ready!");
  delay(2000);
  lcd.clear();
  lcd.print("Action:");

  Serial.println("System initialized");
}

void reset() {
  digitalWrite(greenLed, LOW);
  digitalWrite(blueLed, LOW);
  digitalWrite(redLed, LOW);
  lcd.setCursor(0, 1);
  lcd.print("                ");
}

void distribute_card() {
  digitalWrite(statusLedMotor, HIGH);

  Serial.println("Distributing card...");
  lcd.setCursor(0, 1);
  lcd.print("Distributing");

  // 2 tours complets pour projeter la carte
  motor.step(2048 * 2);

  digitalWrite(statusLedMotor, LOW);
  Serial.println("Card distributed");
}

void test_motor() {
  Serial.println("Testing motor...");
  lcd.setCursor(0, 1);
  lcd.print("Motor Test");

  digitalWrite(statusLedMotor, HIGH);
  motor.step(2048);
  delay(500);
  digitalWrite(statusLedMotor, LOW);

  Serial.println("Motor test complete");
}

void handle_serial_command() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "CARD1") {
      distribute_card();
    }
    else if (command == "TEST") {
      test_motor();
    }
  }
}

void loop() {
  handle_serial_command();

  // Bouton Hit/Stand (travail des partenaires)
  int hitStandState = digitalRead(buttonHitStand);
  if (hitStandState == HIGH && hitStandPrev == LOW) {
    hitStandPressTime = millis();
  }
  if (hitStandState == LOW && hitStandPrev == HIGH) {
    long duree = millis() - hitStandPressTime;
    if (duree > dureeLongPress) {
      digitalWrite(redLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Stand");
      Serial.print("Action : Stand | Temps : ");
      Serial.println(duree);
      delay(dureeDelay);
      reset();
    } else if (duree > dureeShortPress) {
      digitalWrite(greenLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Hit");
      Serial.print("Action : Hit | Temps : ");
      Serial.println(duree);
      delay(dureeDelay);
      reset();
    }
  }
  hitStandPrev = hitStandState;

  // Bouton Double/Split (travail des partenaires)
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
      Serial.println(duree);
      delay(dureeDelay);
      reset();
    } else if (duree > dureeShortPress) {
      digitalWrite(blueLed, HIGH);
      lcd.setCursor(0, 1);
      lcd.print("Double");
      Serial.print("Action : Double | Temps : ");
      Serial.println(duree);
      delay(dureeDelay);
      reset();
    }
  }
  doubleSplitPrev = doubleSplitState;

  // Bouton Distribution (moteur)
  int distributionState = digitalRead(buttonDistribution);
  if (distributionState == LOW && distributionPrev == HIGH) {
    distribute_card();
    delay(3000);
  }
  distributionPrev = distributionState;
}
