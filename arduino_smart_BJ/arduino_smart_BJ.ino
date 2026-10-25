#include <LiquidCrystal.h>
//Déclaration des pins du LCD
LiquidCrystal lcd(2,3,4,5,6,7);
int buttonHitStand = 12;
int buttonDoubleSplit = 13;
int greenLed = 8;
int blueLed = 9;
int redLed = 10;
long hitStandPressTime;
long doubleSplitPressTime;

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

  if (hitStandState == LOW) {
    hitStandPressTime = millis(); 
  }
  if (millis() - hitStandPressTime > 1000) { 
    digitalWrite(redLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Stand");
    delay(2000);
    reset();

  } else if (millis() - hitStandPressTime > 5) {
    digitalWrite(greenLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Hit");
    delay(2000);
    reset();
  } 

  if (doubleSplitState == LOW) {
    doubleSplitPressTime = millis(); 
  }
  if (millis() - doubleSplitPressTime > 1000) { 
    digitalWrite(greenLed, HIGH);
    digitalWrite(blueLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Split");
    delay(2000);
    reset();

  } else if (millis() - doubleSplitPressTime > 5) {
    digitalWrite(blueLed, HIGH);
    lcd.setCursor(0, 1);
    lcd.print("Double");
    delay(2000);
    reset();
  } 

  Serial.print("millis : ");
  Serial.print(millis());
  Serial.print(" | presstime : ");
  Serial.print(hitStandPressTime);
  Serial.print(" | presstime : ");
  Serial.println(doubleSplitPressTime);



  delay(500);
}