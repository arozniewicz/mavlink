package pl.droidsonroids.drones.model.embedded;

import pl.droidsonroids.drones.model.embedded.message.MAVLinkStats;

public class Parser {

    /**
     * States from the parsing state machine
     */
    enum MavState {
        MAVLINK_PARSE_STATE_UNINIT,
        MAVLINK_PARSE_STATE_IDLE,
        MAVLINK_PARSE_STATE_GOT_STX,
        MAVLINK_PARSE_STATE_GOT_LENGTH,
        MAVLINK_PARSE_STATE_GOT_SEQ,
        MAVLINK_PARSE_STATE_GOT_SYSID,
        MAVLINK_PARSE_STATE_GOT_COMPID,
        MAVLINK_PARSE_STATE_GOT_MSGID,
        MAVLINK_PARSE_STATE_GOT_CRC1,
        MAVLINK_PARSE_STATE_GOT_PAYLOAD
    }

    private static boolean messageReceived;

    private MavState state = MavState.MAVLINK_PARSE_STATE_UNINIT;

    private MAVLinkStats stats = new MAVLinkStats();
    private MAVLinkPacket packet;

    /**
     * This is a convenience function which handles the complete MAVLink
     * parsing. the function will parse one byte at a time and return the
     * complete packet once it could be successfully decoded. Checksum and other
     * failures will be silently ignored.
     *
     * @param c The char to parse
     */
    public MAVLinkPacket parseChar(int c) {
        boolean messageReceived = false;
        
        switch (state) {
            case MAVLINK_PARSE_STATE_UNINIT:
            case MAVLINK_PARSE_STATE_IDLE:
                if (c == MAVLinkPacket.MAVLINK_STX) {
                    state = MavState.MAVLINK_PARSE_STATE_GOT_STX;
                    packet = new MAVLinkPacket();
                }
                break;
            case MAVLINK_PARSE_STATE_GOT_STX:
                if (messageReceived) {
                    messageReceived = false;
                    state = MavState.MAVLINK_PARSE_STATE_IDLE;
                } else {
                    packet.messageLength = c;
                    state = MavState.MAVLINK_PARSE_STATE_GOT_LENGTH;
                }
                break;
            case MAVLINK_PARSE_STATE_GOT_LENGTH:
                packet.messageSequence = c;
                state = MavState.MAVLINK_PARSE_STATE_GOT_SEQ;
                break;
            case MAVLINK_PARSE_STATE_GOT_SEQ:
                packet.systemId = c;
                state = MavState.MAVLINK_PARSE_STATE_GOT_SYSID;
                break;
            case MAVLINK_PARSE_STATE_GOT_SYSID:
                packet.componentId = c;
                state = MavState.MAVLINK_PARSE_STATE_GOT_COMPID;
                break;
            case MAVLINK_PARSE_STATE_GOT_COMPID:
                packet.messageId = c;
                if (packet.messageLength == 0) {
                    state = MavState.MAVLINK_PARSE_STATE_GOT_PAYLOAD;
                } else {
                    state = MavState.MAVLINK_PARSE_STATE_GOT_MSGID;
                }
                break;
            case MAVLINK_PARSE_STATE_GOT_MSGID:
                packet.payload.add((byte) c);
                if (packet.isPayloadFilled()) {
                    state = MavState.MAVLINK_PARSE_STATE_GOT_PAYLOAD;
                }
                break;
            case MAVLINK_PARSE_STATE_GOT_PAYLOAD:
                packet.generateCRC();
                // Check first checksum byte
                if (c != packet.crc.getLSB()) {
                    messageReceived = false;
                    state = MavState.MAVLINK_PARSE_STATE_IDLE;
                    if (c == MAVLinkPacket.MAVLINK_STX) {
                        state = MavState.MAVLINK_PARSE_STATE_GOT_STX;
                        packet.crc.startChecksum();
                    }
                    stats.incrementCrcErrorCount();
                } else {
                    state = MavState.MAVLINK_PARSE_STATE_GOT_CRC1;
                }
                break;
            case MAVLINK_PARSE_STATE_GOT_CRC1:
                // Check second checksum byte
                if (c != packet.crc.getMSB()) {
                    messageReceived = false;
                    state = MavState.MAVLINK_PARSE_STATE_IDLE;
                    if (c == MAVLinkPacket.MAVLINK_STX) {
                        state = MavState.MAVLINK_PARSE_STATE_GOT_STX;
                        packet.crc.startChecksum();
                    }
                    stats.incrementCrcErrorCount();
                } else { // Successfully received the message
                    stats.processNewPacket(packet);
                    messageReceived = true;
                    state = MavState.MAVLINK_PARSE_STATE_IDLE;
                }
                break;
        }

        if (messageReceived) {
            return packet;
        } else {
            return null;
        }
    }

    public MAVLinkStats getStats() {
        return stats;
    }
}
