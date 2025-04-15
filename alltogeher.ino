#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP_Mail_Client.h>
#include <ThingSpeak.h>

#define WIFI_SSID "Hii"
#define WIFI_PASSWORD "12345678"

unsigned long channelID = 2848678;  
const char* apiKey = "QD5OMQWKKJA01R4A"; 

WiFiClient client;
ESP8266WebServer server(80);  // Web server on port 80

#define SMTP_HOST "smtp.gmail.com"
#define SMTP_PORT 465  

#define AUTHOR_EMAIL "lohitakshabc12345@gmail.com"
#define AUTHOR_PASSWORD "zkocdkmrsahwdpjw"  

#define RECIPIENT_EMAIL "lohitakshabc12345@gmail.com"

SMTPSession smtp;
ESP_Mail_Session session;
SMTP_Message message;

#define MQ135_PIN A0  

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");

  Serial.print("ESP8266 Web Server running at: http://");
  Serial.println(WiFi.localIP());

  ThingSpeak.begin(client); 

  // API Endpoint: /sensor_data
  server.on("/sensor_data", HTTP_GET, []() {
    int sensorValue = analogRead(MQ135_PIN);
    float voltage = sensorValue * (3.3 / 1023.0);
    
    String jsonResponse = "{ \"air_quality\": " + String(sensorValue) + ", \"voltage\": " + String(voltage, 2) + " }";
    server.send(200, "application/json", jsonResponse);
  });

  server.begin();  // Start the web server
}

void loop() {
  server.handleClient();  // Handle incoming HTTP requests
  
  int sensorValue = analogRead(MQ135_PIN); 
  float voltage = sensorValue * (3.3 / 1023.0); 

  Serial.print("MQ-135 Value: ");
  Serial.print(sensorValue);
  Serial.print(" | Voltage: ");
  Serial.println(voltage);

  // Send data to ThingSpeak
  int status = ThingSpeak.writeField(channelID, 1, sensorValue, apiKey);
  
  if (status == 200) {
    Serial.println("✅ Data sent successfully to ThingSpeak!");
  } else {
    Serial.println("❌ Failed to send data. Check connection.");
  }

  sendEmail(sensorValue, voltage);
  delay(15000);  // Send data every 15 seconds
}

void sendEmail(int airQuality, float voltage) {
  session.server.host_name = SMTP_HOST;
  session.server.port = SMTP_PORT;
  session.login.email = AUTHOR_EMAIL;
  session.login.password = AUTHOR_PASSWORD;
  session.login.user_domain = "gmail.com";

  message.sender.name = "ESP8266 Alert";
  message.sender.email = AUTHOR_EMAIL;
  message.subject = "🚨 Air Quality Update!";

  String alertMessage = "Air Quality Update:\n";
  alertMessage += "Sensor Value: " + String(airQuality) + "\n";
  alertMessage += "Voltage: " + String(voltage, 2) + "V";

  message.text.content = alertMessage.c_str();
  message.addRecipient("Recipient", RECIPIENT_EMAIL);

  smtp.debug(1);

  if (!smtp.connect(&session)) {
    Serial.println("❌ SMTP Connection Failed!");
    return;
  }

  if (MailClient.sendMail(&smtp, &message)) {
    Serial.println("✅ Email Sent Successfully!");
  } else {
    Serial.println("❌ Email Sending Failed!");
  }

  smtp.sendingResult.clear();
}
