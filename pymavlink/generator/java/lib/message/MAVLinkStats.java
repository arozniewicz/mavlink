package pl.droidsonroids.drones.model.embedded.message;

import pl.droidsonroids.drones.model.embedded.MAVLinkPacket;

/**
 * Storage for MAVLink Packet and Error statistics
 */
public class MAVLinkStats /* implements Serializable */{

	private int receivedPacketCount;
	private int crcErrorCount;
	private int lostPacketCount;
	private int lastPacketSequence;

	/**
	 * Check the new received packet to see if has lost someone between this and
	 * the last packet
	 * 
	 * @param packet	Packet that should be checked
	 */
	public void processNewPacket(MAVLinkPacket packet) {
		advanceLastPacketSequence();
		if (hasLostPackets(packet)) {
			updateLostPacketCount(packet);
		}
		lastPacketSequence = packet.messageSequence;
		++receivedPacketCount;
	}

	private void updateLostPacketCount(MAVLinkPacket packet) {
		int lostPackets;
		if (packet.messageSequence - lastPacketSequence < 0) {
			lostPackets = (packet.messageSequence - lastPacketSequence) + 255;
		} else {
			lostPackets = (packet.messageSequence - lastPacketSequence);
		}
		lostPacketCount += lostPackets;
	}

	private boolean hasLostPackets(MAVLinkPacket packet) {
		return lastPacketSequence > 0 && packet.messageSequence != lastPacketSequence;
	}

	private void advanceLastPacketSequence() {
		// wrap from 255 to 0 if necessary
		lastPacketSequence = (lastPacketSequence + 1) & 0xFF;
	}

	/**
	 * Called when a CRC error happens on the parser
	 */
	public void incrementCrcErrorCount() {
		++crcErrorCount;
	}

	/**
	 * Resets statistics for this MAVLink.
	 */
	public void resetStats() {
		lastPacketSequence = -1;
		lostPacketCount = 0;
		crcErrorCount = 0;
		receivedPacketCount = 0;
	}

	public int getReceivedPacketCount() {
		return receivedPacketCount;
	}

	public int getCrcErrorCount() {
		return crcErrorCount;
	}

	public int getLostPacketCount() {
		return lostPacketCount;
	}

	public int getLastPacketSequence() {
		return lastPacketSequence;
	}
}