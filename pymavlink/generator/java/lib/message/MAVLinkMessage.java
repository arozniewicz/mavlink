package pl.droidsonroids.drones.model.embedded.message;

import java.io.Serializable;

import pl.droidsonroids.drones.model.embedded.MAVLinkPacket;

public abstract class MAVLinkMessage implements Serializable {
	private static final long serialVersionUID = -7754622750478538539L;
	// The MAVLink message classes have been changed to implement Serializable, 
	// this way is possible to pass a mavlink message through the Service-Activity interface
	
	/**
	 *  Simply a common interface for all MAVLink Messages
	 */
	
	protected int systemId;
	protected int componentId;
	protected int messageId;

	public abstract MAVLinkPacket pack();

	public abstract void unpack(MAVLinkPayload payload);
}
	