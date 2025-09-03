#include "can_port.h"
#include <SPI.h>

CANPort::CANPort() : m_can(nullptr), m_csPin(0), m_intPin(255) {}

CANPort::~CANPort() {
  if (m_can) delete m_can;
}

bool CANPort::begin(uint8_t csPin, uint8_t intPin, long bitrate, uint8_t osc) {
  m_csPin = csPin;
  m_intPin = intPin;
  SPI.begin();
  if (m_can) delete m_can;
  m_can = new MCP_CAN(m_csPin);

  long rv = m_can->begin(MCP_STDEXT, bitrate, osc);
//  long rv = m_can->begin(MCP_LISTENONLY, bitrate, osc);
  if (rv != CAN_OK) return false;
  m_can->setMode(MCP_NORMAL);
  if (m_intPin != 255) pinMode(m_intPin, INPUT);
  return true;
}

bool CANPort::available() {
  if (!m_can) return false;
  return (m_can->checkReceive() == CAN_MSGAVAIL);
}

bool CANPort::read(uint32_t &id, uint8_t &dlc, uint8_t *buf, bool &extended) {
  if (!m_can) return false;
  unsigned long tmpId;
  uint8_t len = 0;
  byte rv = m_can->readMsgBuf(&tmpId, &len, buf);
  if (rv != CAN_OK) return false;
//   Serial.print("CAN read ID: 0x");
//   Serial.println(tmpId, HEX);
  id = tmpId;
  dlc = len;
  extended = false; // wrapper simplistic
  return true;
}

bool CANPort::send(uint32_t id, const uint8_t *buf, uint8_t dlc, bool extended) {
  if (!m_can) return false;
  byte ext = extended ? 1 : 0;
  byte res = m_can->sendMsgBuf(id, ext, dlc, (uint8_t *)buf);
  return res == CAN_OK;
}

bool CANPort::setBitrate(long bitrate, uint8_t osc) {
  if (!m_can) return false;
  if (m_can) delete m_can;
  m_can = new MCP_CAN(m_csPin);
  long rv = m_can->begin(MCP_STDEXT, bitrate, osc);
  if (rv != CAN_OK) return false;
  m_can->setMode(MCP_NORMAL);
  return true;
}
