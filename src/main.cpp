/*
#include "LoRaWan_APP.h"
#include "Arduino.h"

#define RF_FREQUENCY 865000000 // Hz
#define TX_OUTPUT_POWER 5      // dBm

#define LORA_BANDWIDTH 0
#define LORA_SPREADING_FACTOR 5
#define LORA_CODINGRATE 1
#define LORA_PREAMBLE_LENGTH 8
#define LORA_SYMBOL_TIMEOUT 0
#define LORA_FIX_LENGTH_PAYLOAD_ON false
#define LORA_IQ_INVERSION_ON false

#define RX_TIMEOUT_VALUE 1000
#define BUFFER_SIZE 1001
#define MAX_CHUNK_SIZE 128

uint8_t txpacket[BUFFER_SIZE];
uint8_t rxpacket[BUFFER_SIZE];

static RadioEvents_t RadioEvents;

void OnTxDone(void);
void OnTxTimeout(void);
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr);

typedef enum
{
typedef enum
{
  LOWPOWER,
  STATE_RX,
  STATE_TX
} States_t;

States_t state;
int16_t Rssi, rxSize;
uint8_t retry_count = 0;
const uint8_t max_retries = 3;

uint8_t fullMessageBytes[BUFFER_SIZE];
int fullMessageLength = 0;
int chunkIndex = 0;
bool sendingInChunks = false;

void SendingtheNextChunktobesent()
{
  if (!sendingInChunks)
    return;
void SendingtheNextChunktobesent()
{
  if (!sendingInChunks)
    return;

  int start = chunkIndex * MAX_CHUNK_SIZE;
  if (start >= fullMessageLength)
  {
  if (start >= fullMessage.length())
  {
    Serial.println("All chunks sent.");
    sendingInChunks = false;
    state = STATE_RX;
    return;
  }

  int len = min(MAX_CHUNK_SIZE, fullMessageLength - start);

  memcpy(txpacket, fullMessageBytes + start, len);

  if (len < BUFFER_SIZE)
  {
    txpacket[len] = '\0';
  }

  Serial.printf("Sending chunk %d (%d bytes)\n", chunkIndex + 1, len);
  // Send the raw byte chunk
  Radio.Send(txpacket, len);
  state = LOWPOWER;
}

void setup()
{
void setup()
{
  Serial.begin(115200);
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);

  Rssi = 0;
  state = STATE_RX; // Start in listening mode
  state = STATE_RX; // Start in listening mode

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

void loop()
{
void loop()
{
  // Check for serial input
  if (Serial.available())
  {
  if (Serial.available())
  {
    serialInput = Serial.readStringUntil('\n');
    serialInput.trim();

    if (serialInput.length() > 0)
    {
    if (serialInput.length() > 0)
    {
      fullMessage = serialInput;
      chunkIndex = 0;
      sendingInChunks = true;
      retry_count = 0;
      SendingtheNextChunktobesent(); // 👈 Send the first chunk
      SendingtheNextChunktobesent(); // 👈 Send the first chunk
    }
  }

  switch (state)
  {
  case STATE_TX:
    // This state is now managed inside sendNextChunk
    break;
  switch (state)
  {
  case STATE_TX:
    // This state is now managed inside sendNextChunk
    break;

  case STATE_RX:
    Radio.Rx(0); // Always listening
    state = LOWPOWER;
    break;
  case STATE_RX:
    Radio.Rx(0); // Always listening
    state = LOWPOWER;
    break;

  case LOWPOWER:
    Radio.IrqProcess(); // Handle radio events
    break;
  case LOWPOWER:
    Radio.IrqProcess(); // Handle radio events
    break;

  default:
    break;
  default:
    break;
  }
}

void OnTxDone(void)
{
void OnTxDone(void)
{
  Serial.println("TX done.");
  chunkIndex++;
  if (sendingInChunks && (chunkIndex * MAX_CHUNK_SIZE < fullMessageLength))
  {
    delay(100); // Short delay between chunks
  if (sendingInChunks && (chunkIndex * MAX_CHUNK_SIZE < fullMessage.length()))
  {
    delay(100); // Short delay between chunks
    SendingtheNextChunktobesent();
  }
  else
  {
  }
  else
  {
    Serial.println("Finished sending all chunks.");
    sendingInChunks = false;
    state = STATE_RX;
  }
}

void OnTxTimeout(void)
{
void OnTxTimeout(void)
{
  Serial.println("TX timeout occurred.");
  retry_count++;
  Serial.printf("Retry attempt: %d\n", retry_count);
  if (retry_count < max_retries)
  {
    SendingtheNextChunktobesent(); // Retry same chunk
  }
  else
  {
  if (retry_count < max_retries)
  {
    SendingtheNextChunktobesent(); // Retry same chunk
  }
  else
  {
    Serial.println("Max retries reached. Going back to RX.");
    sendingInChunks = false;
    state = STATE_RX;
  }
}

void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr)
{
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr)
{
  size_t copyLength = min((size_t)size, (size_t)(BUFFER_SIZE - 1));
  memcpy(rxpacket, payload, copyLength);
  rxpacket[copyLength] = '\0';

  Radio.Sleep();

  Serial.println();
  Serial.printf("Received size: %d bytes\n", size);
  Serial.print("Received: ");
  for (int i = 0; i < size; i += 64)
  {
    // Serial.printf("0x%02X", rxpacket[i]);
  for (int i = 0; i < size; i += 64)
  {
    // Serial.printf("0x%02X", rxpacket[i]);
    Serial.write((uint8_t *)&rxpacket[i], min(64, size - i));
    delay(1);
  }
  Serial.println();
  Serial.printf("RSSI: %d | SNR: %d\n", rssi, snr);
  state = STATE_RX;
}
*/
#include "LoRaWan_APP.h"
#include "Arduino.h"

#define RF_FREQUENCY 865000000 // Hz
#define TX_OUTPUT_POWER 5      // dBm

#define LORA_BANDWIDTH 0
#define LORA_SPREADING_FACTOR 5
#define LORA_CODINGRATE 1
#define LORA_PREAMBLE_LENGTH 8
#define LORA_SYMBOL_TIMEOUT 0
#define LORA_FIX_LENGTH_PAYLOAD_ON false
#define LORA_IQ_INVERSION_ON false

#define RX_TIMEOUT_VALUE 1000
#define BUFFER_SIZE 1001

char txpacket[BUFFER_SIZE];
char rxpacket[BUFFER_SIZE];
size_t bytesSent = 0;

static RadioEvents_t RadioEvents;

void OnTxDone(void);
void OnTxTimeout(void);
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr);

typedef enum
{
  LOWPOWER,
  STATE_RX,
  STATE_TX
} States_t;

States_t state;
int16_t Rssi, rxSize;
String serialInput = "";
bool messagePending = false;

void setup()
{
  Serial.begin(115200);
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);

  Rssi = 0;
  state = STATE_RX;

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

void loop()
{
  // Read full message from serial
  if (Serial.available())
  {
    serialInput = Serial.readStringUntil('\n');
    serialInput.trim();

    if (serialInput.length() > 0 && serialInput.length() < BUFFER_SIZE)
    {
      strncpy(txpacket, serialInput.c_str(), BUFFER_SIZE);
      txpacket[BUFFER_SIZE - 1] = '\0';
      messagePending = true;
      state = STATE_TX;
    }
  }

  switch (state)
  {
  case STATE_TX:
    if (messagePending)
      {
        bytesSent = strlen(txpacket);   // Save length here before sending
        Radio.Send((uint8_t *)txpacket, bytesSent);
        messagePending = false;
        state = LOWPOWER;
      }
    break;

  case STATE_RX:
    Radio.Rx(0); // Listen forever
    state = LOWPOWER;
    break;

  case LOWPOWER:
    Radio.IrqProcess(); // Handle LoRa events
    break;

  default:
    break;
  }
}

void OnTxDone(void)
{
  Serial.println("TX done.");
  Serial.printf("Bytes sent: %d\n", strlen(txpacket));
  state = STATE_RX;
}

void OnTxTimeout(void)
{
  Serial.println("TX timeout occurred.");
  state = STATE_RX;
}

void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr)
{
  size_t copyLength = min((size_t)size, (size_t)(BUFFER_SIZE - 1));
  memcpy(rxpacket, payload, copyLength);
  rxpacket[copyLength] = '\0';

  Radio.Sleep();

  for (int i = 0; i < size; i += 64)
  {
    Serial.write((uint8_t *)&rxpacket[i], min(64, size - i));
    delay(1);
  }

  state = STATE_RX;
}
