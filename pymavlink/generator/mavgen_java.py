#!/usr/bin/env python
'''
    parse a MAVLink protocol XML file and generate a Java implementation
    
    Copyright Andrew Tridgell 2011
    Released under GNU GPL version 3 or later
    '''

import sys, textwrap, os, time
from . import mavparse, mavtemplate

t = mavtemplate.MAVTemplate()

def to_camel_case_variable(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0] + "".join(x.title() for x in components[1:])

def to_camel_case_class(snake_str):
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].title() + "".join(x.title() for x in components[1:])

def generate_enums(basename, xml):
    '''generate main header per XML file'''
    directory = os.path.join(basename, '''enums''')
    mavparse.mkdir_p(directory)
    for en in xml.enum:
        en.class_camel_case = to_camel_case_class(en.name.lower())
        f = open(os.path.join(directory, en.class_camel_case+".java"), mode='w')
        t.write(f, '''
/** 
* ${description}
*/
package pl.droidsonroids.drones.model.embedded.enums;

public class ${class_camel_case} {
${{entry:
    public static final int ${name} = ${value}; /* ${description} |${{param:${description}| }} */
}}
}
''', en)
        f.close()



def generate_CRC(directory, xml):
    # and message CRCs array
    xml.message_crcs_array = ''
    for crc in xml.message_crcs:
        xml.message_crcs_array += '%u, ' % crc
    xml.message_crcs_array = xml.message_crcs_array[:-2]
    
    f = open(os.path.join(directory, "CRC.java"), mode='w')
    path=directory.split('/')
    t.write(f,'''
package pl.droidsonroids.drones.model.embedded.%s;

/**
 * X.25 CRC calculation for MAVlink messages. The checksum must be initialized,
 * updated with witch field of the message, and then finished with the message
 * id.
 */
public class CRC {

    private static final int CRC_INIT_VALUE = 0xffff;

    private final int[] MAVLINK_MESSAGE_CRCS = {${message_crcs_array}};
    
    private int crcValue;

    public CRC() {
        startChecksum();
    }

    /**
     * Initialize the buffer for the X.25 CRC
     */
    public void startChecksum() {
        crcValue = CRC_INIT_VALUE;
    }

    /**
     * Finish the CRC calculation of a message, by running the CRC with the
     * Magic Byte. This Magic byte has been defined in MAVlink v1.0.
     *
     * @param messageId The message id number
     */
    public void finishChecksum(int messageId) {
        updateChecksum(MAVLINK_MESSAGE_CRCS[messageId]);
    }

    /**
     * Accumulate the X.25 CRC by adding one char at a time.
     * <p>
     * The checksum function adds the hash of one char at a time to the 16 bit
     * checksum (uint16_t).
     *
     * @param data new char to hash
     */
    public void updateChecksum(int data) {
        int tmp;
        data = data & 0xff;    //cast because we want an unsigned type
        tmp = data ^ (crcValue & 0xff);
        tmp ^= (tmp << 4) & 0xff;
        crcValue = ((crcValue >> 8) & 0xff) ^ (tmp << 8) ^ (tmp << 3) ^ ((tmp >> 4) & 0xf);
    }

    public int getMSB() {
        return ((crcValue >> 8) & 0xff);
    }

    public int getLSB() {
        return (crcValue & 0xff);
    }
}
        ''' % path[len(path)-1], xml)
    
    f.close()


def generate_message_h(directory, m):
    '''generate per-message header for a XML file'''
    m.variable_camel_case = to_camel_case_variable(m.name_lower)
    m.class_camel_case = to_camel_case_class(m.name_lower)
    f = open(os.path.join(directory, '%sMessage.java' % m.class_camel_case), mode='w')

    path=directory.split('/')
    t.write(f, '''
package pl.droidsonroids.drones.model.embedded.%s;

//import android.util.Log;

import pl.droidsonroids.drones.model.embedded.MAVLinkPacket;
import pl.droidsonroids.drones.model.embedded.message.MAVLinkMessage;
import pl.droidsonroids.drones.model.embedded.message.MAVLinkPayload;

/**
* ${description}
*/
public class ${class_camel_case}Message extends MAVLinkMessage {
    
    public static final int MAVLINK_MSG_ID_${name} = ${id};
    public static final int MAVLINK_MSG_LENGTH = ${wire_length};

    private static final long serialVersionUID = MAVLINK_MSG_ID_${name};
    
    ${{ordered_fields:/**
    * ${description}
    */
    private ${type}${array_suffix_2} ${name_variable}${array_generator};
    }}
    /**
    * Generates the payload for a mavlink message for a message of this type
    * @return
    */
    public MAVLinkPacket pack() {
        MAVLinkPacket packet = new MAVLinkPacket();
        packet.messageLength = MAVLINK_MSG_LENGTH;
        packet.systemId = 255;
        packet.componentId = 190;
        packet.messageId = MAVLINK_MSG_ID_${name};
        ${{ordered_fields:${packField}
        }}
        return packet;
    }
    
    /**
    * Decode a ${name_lower} message into this class fields
    *
    * @param payload The message to decode
    */
    public void unpack(MAVLinkPayload payload) {
        payload.resetIndex();
        ${{ordered_fields:${unpackField}
        }}
    }
    
    /**
    * Constructor for a new message, just initializes the messageId
    */
    public ${class_camel_case}Message() {
        messageId = MAVLINK_MSG_ID_${name};
    }
    
    /**
    * Constructor for a new message, initializes the message with the payload
    * from a mavlink packet
    *
    */
    public ${class_camel_case}Message(MAVLinkPacket mavLinkPacket) {
        this.systemId = mavLinkPacket.systemId;
        this.componentId = mavLinkPacket.componentId;
        this.messageId = MAVLINK_MSG_ID_${name};
        unpack(mavLinkPacket.payload);
        //Log.d("MAVLink", "${name}");
        //Log.d("MAVLINK_MSG_ID_${name}", toString());
    }
    ${{ordered_fields: ${getText} }}       
    ${{ordered_fields:
    public void set${name_class}(${type}${array_suffix_2} ${name_variable}) {
        this.${name_variable} = ${name_variable};
    }

    public ${type}${array_suffix_2} get${name_class}() {
        return ${name_variable};
    }
    }}
    /**
    * Returns a string with the MSG name and data
    */
    public String toString() {
        return "MAVLINK_MSG_ID_${name} -"+${{ordered_fields:" ${name_variable}:"+${name_variable}+}}"";
    }
}
        ''' % path[len(path)-1], m)
    f.close()


def generate_MAVLinkMessage(directory, xml_list):
    f = open(os.path.join(directory, "MAVLinkPacket.java"), mode='w')
    f.write('''
package pl.droidsonroids.drones.model.embedded;

import java.io.Serializable;

import pl.droidsonroids.drones.model.embedded.message.MAVLinkMessage;
import pl.droidsonroids.drones.model.embedded.message.MAVLinkPayload;
''')

    for xml in xml_list:
        t.write(f, '''
import pl.droidsonroids.drones.model.embedded.${basename}.*;''',xml)

    f.write('''

/**
 * Common interface for all MAVLink Messages
 * Packet Anatomy
 * This is the anatomy of one packet. It is inspired by the CAN and SAE AS-4 standards.
 * <p>
 * Byte Index  Content              Value       Explanation
 * 0            Packet start sign  v1.0: 0xFE   Indicates the start of a new packet.  (v0.9: 0x55)
 * 1            Payload length      0 - 255     Indicates length of the following payload.
 * 2            Packet sequence     0 - 255     Each component counts up his send sequence. Allows to detect packet loss
 * 3            System ID           1 - 255     ID of the SENDING system. Allows to differentiate different MAVs on the same network.
 * 4            Component ID        0 - 255     ID of the SENDING component. Allows to differentiate different components of the same system, e.g. the IMU and the autopilot.
 * 5            Message ID          0 - 255     ID of the message - the id defines what the payload means and how it should be correctly decoded.
 * 6 to (n+6)   Payload             0 - 255     Data of the message, depends on the message id.
 * (n+7)to(n+8) Checksum (low byte, high byte)  ITU X.25/SAE AS-4 hash, excluding packet start sign, so bytes 1..(n+6) Note: The checksum also includes MAVLINK_CRC_EXTRA (Number computed from message fields. Protects the packet from decoding a different version of the same packet but with different variables).
 * <p>
 * The checksum is the same as used in ITU X.25 and SAE AS-4 standards (CRC-16-CCITT), documented in SAE AS5669A. Please see the MAVLink source code for a documented C-implementation of it. LINK TO CHECKSUM
 * The minimum packet length is 8 bytes for acknowledgement packets without payload
 * The maximum packet length is 263 bytes for full payload
 */
public class MAVLinkPacket implements Serializable {
    private static final long serialVersionUID = 2095947771227815314L;

    public static final int MAVLINK_STX = 254;

    /**
     * Message length. NOT counting STX, LENGTH, SEQ, SYSID, COMPID, MSGID, CRC1 and CRC2
     */
    public int messageLength;
    /**
     * Message sequence
     */
    public int messageSequence;
    /**
     * ID of the SENDING system. Allows to differentiate different MAVs on the
     * same network.
     */
    public int systemId;
    /**
     * ID of the SENDING component. Allows to differentiate different components
     * of the same system, e.g. the IMU and the autopilot.
     */
    public int componentId;
    /**
     * ID of the message - the id defines what the payload means and how it
     * should be correctly decoded.
     */
    public int messageId;
    /**
     * Data of the message, depends on the message id.
     */
    public MAVLinkPayload payload;
    /**
     * ITU X.25/SAE AS-4 hash, excluding packet start sign, so bytes 1..(n+6)
     * Note: The checksum also includes MAVLINK_CRC_EXTRA (Number computed from
     * message fields. Protects the packet from decoding a different version of
     * the same packet but with different variables).
     */
    public CRC crc;

    public MAVLinkPacket() {
        payload = new MAVLinkPayload();
    }

    /**
     * Check if the size of the Payload is equal to the "messageLength" byte
     */
    public boolean isPayloadFilled() {
        return payload.size() >= MAVLinkPayload.MAX_PAYLOAD_SIZE - 1 || (payload.size() == messageLength);
    }

    /**
     * Update CRC for this packet.
     */
    public void generateCRC() {
        crc = new CRC();
        crc.updateChecksum(messageLength);
        crc.updateChecksum(messageSequence);
        crc.updateChecksum(systemId);
        crc.updateChecksum(componentId);
        crc.updateChecksum(messageId);
        payload.resetIndex();
        for (int i = 0; i < payload.size(); ++i) {
            crc.updateChecksum(payload.getByte());
        }
        crc.finishChecksum(messageId);
    }

    /**
     * Encode this packet for transmission.
     *
     * @return Array with bytes to be transmitted
     */
    public byte[] encodePacket() {
        byte[] buffer = new byte[6 + messageLength + 2];
        int i = 0;
        buffer[i++] = (byte) MAVLINK_STX;
        buffer[i++] = (byte) messageLength;
        buffer[i++] = (byte) messageSequence;
        buffer[i++] = (byte) systemId;
        buffer[i++] = (byte) componentId;
        buffer[i++] = (byte) messageId;
        for (int j = 0; j < payload.size(); ++j) {
            buffer[i++] = payload.payload.get(j);
        }
        generateCRC();
        buffer[i++] = (byte) (crc.getLSB());
        buffer[i++] = (byte) (crc.getMSB());
        return buffer;
    }

    /**
     * Unpack the data in this packet and return a MAVLink message
     *
     * @return MAVLink message decoded from this packet
     */
    public MAVLinkMessage unpack() {
        switch (messageId) {
''')

    for xml in xml_list:
        t.write(f, '''${{message:
            case ${class_camel_case}Message.MAVLINK_MSG_ID_${name}:
                return new ${class_camel_case}Message(this);}}''', xml)

    f.write('''
            default:
                return null;
        }
    }
}
''')
    
    f.close()

def copy_fixed_headers(directory, xml):
    '''copy the fixed protocol headers to the target directory'''
    import shutil
    hlist = [ 'Parser.java', 'message/MAVLinkMessage.java', 'message/MAVLinkPayload.java', 'message/MAVLinkStats.java' ]
    basepath = os.path.dirname(os.path.realpath(__file__))
    srcpath = os.path.join(basepath, 'java/lib')
    print("Copying fixed headers")
    for h in hlist:
        src = os.path.realpath(os.path.join(srcpath, h))
        dest = os.path.realpath(os.path.join(directory, h))
        if src == dest:
            continue
        destdir = os.path.realpath(os.path.join(directory, 'message'))
        try:
            os.makedirs(destdir)
        except:
            print("Not re-creating Messages directory")
        shutil.copy(src, dest)

class mav_include(object):
    def __init__(self, base):
        self.base = base


def mavfmt(field):
    '''work out the struct format for a type'''
    map = {
        'float'    : 'float',
        'double'   : 'double',
        'char'     : 'byte',
        'int8_t'   : 'byte',
        'uint8_t'  : 'byte',
        'uint8_t_mavlink_version'  : 'byte',
        'int16_t'  : 'short',
        'uint16_t' : 'short',
        'int32_t'  : 'int',
        'uint32_t' : 'int',
        'int64_t'  : 'long',
        'uint64_t' : 'long',
    }
    
    return map[field.type]

def generate_one(basename, xml):
    '''generate headers for one XML file'''
    
    directory = os.path.join(basename, xml.basename)
    
    print("Generating Java implementation in directory %s" % directory)
    mavparse.mkdir_p(directory)
    
    if xml.little_endian:
        xml.mavlink_endian = "MAVLINK_LITTLE_ENDIAN"
    else:
        xml.mavlink_endian = "MAVLINK_BIG_ENDIAN"
    
    if xml.crc_extra:
        xml.crc_extra_define = "1"
    else:
        xml.crc_extra_define = "0"
    
    if xml.sort_fields:
        xml.aligned_fields_define = "1"
    else:
        xml.aligned_fields_define = "0"
    
    # work out the included headers
    xml.include_list = []
    for i in xml.include:
        base = i[:-4]
        xml.include_list.append(mav_include(base))
    
    # form message lengths array
    xml.message_lengths_array = ''
    for mlen in xml.message_lengths:
        xml.message_lengths_array += '%u, ' % mlen
    xml.message_lengths_array = xml.message_lengths_array[:-2]
    
    
    
    # form message info array
    xml.message_info_array = ''
    for name in xml.message_names:
        if name is not None:
            xml.message_info_array += 'MAVLINK_MESSAGE_INFO_%s, ' % name
        else:
            # Several C compilers don't accept {NULL} for
            # multi-dimensional arrays and structs
            # feed the compiler a "filled" empty message
            xml.message_info_array += '{"EMPTY",0,{{"","",MAVLINK_TYPE_CHAR,0,0,0}}}, '
    xml.message_info_array = xml.message_info_array[:-2]
    
    # add some extra field attributes for convenience with arrays
    for m in xml.message:
        m.msg_name = m.name
        if xml.crc_extra:
            m.crc_extra_arg = ", %s" % m.crc_extra
        else:
            m.crc_extra_arg = ""
        for f in m.fields:
            if f.print_format is None:
                f.c_print_format = 'NULL'
            else:
                f.c_print_format = '"%s"' % f.print_format
            f.getText = ''
            if f.array_length != 0:
                f.array_suffix_2 = '[]'
                f.array_generator = ' = new %s[%u]' % (mavfmt(f),f.array_length)
                f.array_suffix = '[] = new %s[%u]' % (mavfmt(f),f.array_length)
                f.array_prefix = '*'
                f.array_tag = '_array'
                f.array_arg = ', %u' % f.array_length
                f.array_return_arg = '%s, %u, ' % (f.name, f.array_length)
                f.array_const = 'const '
                f.decode_left = ''
                f.decode_right = 'm.%s' % (f.name)
                
                f.unpackField = '''for (int i = 0; i < this.%s.length; ++i) {
            this.%s[i] = payload.get%s();
        }''' % (f.name_variable, f.name_variable, mavfmt(f).title())

                f.packField = '''for (int i = 0; i < %s.length; ++i) {
            packet.payload.put%s(%s[i]);
        }''' % (f.name_variable, mavfmt(f).title(),f.name_variable)

                f.return_type = 'uint16_t'
                f.get_arg = ', %s *%s' % (f.type, f.name)
                if f.type == 'char':
                    f.c_test_value = '"%s"' % f.test_value
                    f.getText = '''
    /**
    * Sets the buffer of this message with a string, adds the necessary padding
    */
    public void set%s(String str) {
        int len = Math.min(str.length(), %d);
        for (int i = 0; i < len; ++i) {
            %s[i] = (byte) str.charAt(i);
        }
        for (int i = len; i < %d; ++i) {			// padding for the rest of the buffer
            %s[i] = 0;
        }
    }

    /**
    * Gets the message, formated as a string
    */
    public String get%sAsString() {
        String result = "";
        for (int i = 0; i < %d; ++i) {
            if (%s[i] != 0) {
                result = result + (char) %s[i];
            } else {
                break;
            }
        }
        return result;
    }''' % (f.name_class,f.array_length,f.name_variable,f.array_length,f.name_variable,f.name_class,f.array_length,f.name_variable,f.name_variable)
                else:
                    test_strings = []
                    for v in f.test_value:
                        test_strings.append(str(v))
                    f.c_test_value = '{ %s }' % ', '.join(test_strings)
            else:
                f.array_suffix_2 = ''
                f.array_generator = ''
                f.array_suffix = ''
                f.array_prefix = ''
                f.array_tag = ''
                f.array_arg = ''
                f.array_return_arg = ''
                f.array_const = ''
                f.decode_left =  '%s' % (f.name)
                f.decode_right = ''
                f.unpackField = 'this.%s = payload.get%s();' % (f.name_variable, mavfmt(f).title())
                f.packField = 'packet.payload.put%s(%s);' % (mavfmt(f).title(),f.name_variable)                   
                
                
                f.get_arg = ''
                f.return_type = f.type
                if f.type == 'char':
                    f.c_test_value = "'%s'" % f.test_value
                elif f.type == 'uint64_t':
                    f.c_test_value = "%sULL" % f.test_value                    
                elif f.type == 'int64_t':
                    f.c_test_value = "%sLL" % f.test_value                    
                else:
                    f.c_test_value = f.test_value
    
    # cope with uint8_t_mavlink_version
    for m in xml.message:
        m.arg_fields = []
        m.array_fields = []
        m.scalar_fields = []
        for f in m.ordered_fields:
            if f.array_length != 0:
                m.array_fields.append(f)
            else:
                m.scalar_fields.append(f)
        for f in m.fields:
            if not f.omit_arg:
                m.arg_fields.append(f)
                f.putname = f.name
            else:
                f.putname = f.const_value
    
    # fix types to java
    for m in xml.message:
        for f in m.ordered_fields:
            f.type = mavfmt(f)
    
    generate_CRC(directory, xml)
    
    for m in xml.message:
        generate_message_h(directory, m)


def generate(basename, xml_list):
    '''generate complete MAVLink Java implemenation'''
    for xml in xml_list:
        generate_one(basename, xml)
        generate_enums(basename, xml)
        generate_MAVLinkMessage(basename, xml_list)
    copy_fixed_headers(basename, xml_list[0])
