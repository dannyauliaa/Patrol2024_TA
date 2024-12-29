#include <Wire.h> 
#include <LiquidCrystal_I2C.h> 
#include <MPU6050.h>

MPU6050 mpu; 
LiquidCrystal_I2C lcd(0x27, 16, 2); 
int16_t prev_ax = 0, prev_ay = 0, prev_az = 0; 

int led1 = 2; 
int led2 = 3; 
int led3 = 4; 

const int16_t threshold1 = 3000; 
const int16_t threshold2 = 6000; 

void setup() { 

    Serial.begin(9600); 
    
    pinMode(led1, OUTPUT); 
    pinMode(led2, OUTPUT); 
    pinMode(led3, OUTPUT);  
    
    lcd.init(); 
    lcd.backlight(); 
    lcd.setCursor(0, 0);  
    lcd.print("Hello guys"); 
    lcd.setCursor(0, 1);  
    lcd.print("obstac map"); 

    Wire.begin(); 
    mpu.initialize(); 

    Serial.println("Kalibrasi accelerometer"); 
    mpu.CalibrateGyro(); 
    Serial.println("Kalibrasi selesai."); 
    Serial.print("Offset kalibrasi X: "); 
    Serial.println(mpu.getXGyroOffset()); 
    Serial.print("Offset kalibrasi Y: "); 
    Serial.println(mpu.getYGyroOffset()); 
    Serial.print("Offset kalibrasi Z: "); 
    Serial.println(mpu.getZGyroOffset()); 
} 

void loop() { 
    lcd.clear(); 
    int16_t ax, ay, az; 
    mpu.getAcceleration(&ax, &ay, &az); 

    int16_t delta_ax = ax - prev_ax; 
    int16_t delta_ay = ay - prev_ay; 
    int16_t delta_az = az - prev_az; 
    prev_ax = ax; 
    prev_ay = ay; 
    prev_az = az; 

    if ((abs(delta_ax) > threshold1 && abs(delta_ax) < threshold2) || 
    (abs(delta_ay) > threshold1 && abs(delta_ay) < threshold2) || 
    (abs(delta_az) > threshold1 && abs(delta_az) < threshold2)) { 

    digitalWrite(led3, HIGH);  
    digitalWrite(led1, LOW); 
    digitalWrite(led2, LOW);  

    lcd.setCursor(0, 0);  
    lcd.print("KERUSAKAN KECIL"); 
    lcd.setCursor(0, 1);  
    lcd.print("Hati-hati"); 

    Serial.print("Kerusakan Kecil;"); 
    Serial.print("sumbu X: "); Serial.print(ax); 
    Serial.print(",sumbu Y: "); Serial.print(ay); 
    Serial.print(",sumbu Z: "); Serial.println(az); 
    delay(500); 

    } else if (abs(delta_ax) > threshold2 || abs(delta_ay) > threshold2 || abs(delta_az) > threshold2) { 
    digitalWrite(led2, HIGH);  
    digitalWrite(led1, LOW); 
    digitalWrite(led3, LOW);  

    lcd.setCursor(0, 0);  
    lcd.print("Kerusakan Besar"); 
    lcd.setCursor(0, 1);  
    lcd.print("Cari Bantuan"); 

    Serial.print("Kerusakan Besar;"); 
    Serial.print("sumbu X: "); Serial.print(ax); 
    Serial.print(",sumbu Y: "); Serial.print(ay);| 
    Serial.print(",sumbu Z: "); Serial.println(az); 
    delay(500); 
    
    } else { 
    lcd.setCursor(0, 0); 
    lcd.print("Jalan Baik"); 
    lcd.setCursor(0, 1); 
    lcd.print("Have a Good Day"); 

    digitalWrite(led1, HIGH);  
    digitalWrite(led2, LOW); 
    digitalWrite(led3, LOW);  
    Serial.print("Kondisi Null;"); 

    Serial.print("sumbu X: "); Serial.print(ax); 
    Serial.print(",sumbu Y: "); Serial.print(ay); 
    Serial.print(",sumbu Z: "); Serial.println(az); 
    delay(500); 
    } 
    delay(1000); } 