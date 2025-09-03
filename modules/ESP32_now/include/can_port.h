// CAN port wrapper using mcp_can library
#pragma once

#include <Arduino.h>
#include <mcp_can.h>

class CANPort {
public:
  CANPort();
  ~CANPort();

  // Initialize the MCP2515 on csPin, intPin; osc can be MCP_8MHZ or MCP_16MHZ
  // bitrate use CAN_500KBPS, CAN_250KBPS etc. Returns true on success.
  bool begin(uint8_t csPin, uint8_t intPin = 255, long bitrate = CAN_500KBPS, uint8_t osc = MCP_8MHZ);

  // Check if a frame is available
  bool available();

  // Read a frame into provided buffers. Returns true on success.
  bool read(uint32_t &id, uint8_t &dlc, uint8_t *buf, bool &extended);

  // Send a frame (standard or extended). Returns true on success.
  bool send(uint32_t id, const uint8_t *buf, uint8_t dlc, bool extended = false);

  // Set bitrate/oscillator by reinitializing the controller
  bool setBitrate(long bitrate, uint8_t osc);

private:
  MCP_CAN *m_can;
  uint8_t m_csPin;
  uint8_t m_intPin;
};
