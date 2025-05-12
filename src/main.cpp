#include "LoRaWan_APP.h"
#include "Arduino.h"

#define RF_FREQUENCY 865000000 // Hz
#define TX_OUTPUT_POWER 5      // dBm

#define LORA_BANDWIDTH 0
#define LORA_SPREADING_FACTOR 7
#define LORA_CODINGRATE 1
#define LORA_PREAMBLE_LENGTH 8
#define LORA_SYMBOL_TIMEOUT 0
#define LORA_FIX_LENGTH_PAYLOAD_ON false
#define LORA_IQ_INVERSION_ON false

#define RX_TIMEOUT_VALUE 1000
#define BUFFER_SIZE 1001

char txpacket[BUFFER_SIZE];
char rxpacket[BUFFER_SIZE];

static RadioEvents_t RadioEvents;

void OnTxDone(void);
void OnTxTimeout(void);
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr);

typedef enum {
  LOWPOWER,
  STATE_RX,
  STATE_TX
} States_t;

States_t state;
int16_t Rssi, rxSize;
String serialInput = "";
uint8_t retry_count = 0;
const uint8_t max_retries = 3;

void setup() {
  Serial.begin(115200);
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);

  Rssi = 0;
  state = STATE_RX;  // Start in listening mode

  RadioEvents.TxDone = OnTxDone;
  RadioEvents.TxTimeout = OnTxTimeout;
  RadioEvents.RxDone = OnRxDone;

  Radio.Init(&RadioEvents);
  Radio.SetChannel(RF_FREQUENCY);
  Radio.SetTxConfig(MODEM_LORA, TX_OUTPUT_POWER, 0, LORA_BANDWIDTH,
                    LORA_SPREADING_FACTOR, LORA_CODINGRATE,
                    LORA_PREAMBLE_LENGTH, LORA_FIX_LENGTH_PAYLOAD_ON,
                    true, 0, 0, LORA_IQ_INVERSION_ON, 3000);

  Radio.SetRxConfig(MODEM_LORA, LORA_BANDWIDTH, LORA_SPREADING_FACTOR,
                    LORA_CODINGRATE, 0, LORA_PREAMBLE_LENGTH,
                    LORA_SYMBOL_TIMEOUT, LORA_FIX_LENGTH_PAYLOAD_ON,
                    0, true, 0, 0, LORA_IQ_INVERSION_ON, true);
}

void loop() {
  // Always check for serial input
  if (Serial.available()) {
    serialInput = Serial.readStringUntil('\n');
    serialInput.trim();
    strncpy(txpacket, serialInput.c_str(), BUFFER_SIZE);
    txpacket[BUFFER_SIZE - 1] = '\0';
    Serial.printf("Serial input detected, sending: \"%s\"\n", txpacket);
    retry_count = 0;
    state = STATE_TX;
  }

  switch (state) {
    case STATE_TX:
      if (retry_count >= max_retries) {
        Serial.println("Max retries reached. Going back to RX.");
        state = STATE_RX;
        break;
      }

      Serial.printf("Sending packet: \"%s\"\n", txpacket);
      Radio.Send((uint8_t *)txpacket, strlen(txpacket));
      state = LOWPOWER;
      break;

    case STATE_RX:
      Radio.Rx(0);  // Always listening
      state = LOWPOWER;
      break;

    case LOWPOWER:
      Radio.IrqProcess();  // Handle radio events
      break;

    default:
      break;
  }
}

void OnTxDone(void) {
  Serial.println("TX done. Going back to RX.");
  state = STATE_RX;
}

void OnTxTimeout(void) {
  Serial.println("TX timeout occurred.");
  retry_count++;
  Serial.printf("Retry attempt: %d\n", retry_count);
  state = STATE_TX;
}

void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr) {
  size_t copyLength = std::min(static_cast<size_t>(size), static_cast<size_t>(BUFFER_SIZE - 1));
  memcpy(rxpacket, payload, copyLength);
  rxpacket[copyLength] = '\0';


  Radio.Sleep();

  Serial.print("Received: ");
  for (int i = 0; i < size; i += 64) {
    Serial.write((uint8_t *)&rxpacket[i], min(64, size - i));
    delay(1);
  }
  Serial.println();

  Serial.printf("RSSI: %d | SNR: %d\n", rssi, snr);

  state = STATE_RX;
}

