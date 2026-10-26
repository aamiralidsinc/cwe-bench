package org.apache.camel.htests;

import java.util.ArrayList;
import java.util.Enumeration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Vector;

import jakarta.jms.Destination;
import jakarta.jms.JMSException;
import jakarta.jms.Message;

/**
 * A messaging-provider message: the properties a broker delivers, exactly as the provider hands them
 * to the consumer. Only the property surface the consumer reads is populated.
 */
public class FakeJmsMessage implements Message {

    private final Map<String, Object> properties = new LinkedHashMap<>();
    private final List<String> acknowledged = new ArrayList<>();
    private boolean redelivered;

    public FakeJmsMessage put(String name, Object value) {
        properties.put(name, value);
        return this;
    }

    public List<String> acknowledged() {
        return acknowledged;
    }

    @Override
    public boolean isBodyAssignableTo(Class c) {
        return true;
    }

    @Override
    public <T> T getBody(Class<T> c) {
        return null;
    }

    @Override
    public void acknowledge() {
        acknowledged.add("ack");
    }

    @Override
    public void clearBody() {
    }

    @Override
    public void clearProperties() {
        properties.clear();
    }

    @Override
    public boolean getBooleanProperty(String name) {
        Object v = properties.get(name);
        return v != null && Boolean.parseBoolean(String.valueOf(v));
    }

    @Override
    public byte getByteProperty(String name) {
        Object v = properties.get(name);
        return v == null ? 0 : Byte.parseByte(String.valueOf(v));
    }

    @Override
    public double getDoubleProperty(String name) {
        Object v = properties.get(name);
        return v == null ? 0d : Double.parseDouble(String.valueOf(v));
    }

    @Override
    public float getFloatProperty(String name) {
        Object v = properties.get(name);
        return v == null ? 0f : Float.parseFloat(String.valueOf(v));
    }

    @Override
    public int getIntProperty(String name) {
        Object v = properties.get(name);
        return v == null ? 0 : Integer.parseInt(String.valueOf(v));
    }

    @Override
    public String getJMSMessageID() {
        return "ID:htests-1";
    }

    @Override
    public void setJMSMessageID(String id) {
    }

    @Override
    public long getJMSTimestamp() {
        return 0L;
    }

    @Override
    public void setJMSTimestamp(long timestamp) {
    }

    @Override
    public byte[] getJMSCorrelationIDAsBytes() {
        return null;
    }

    @Override
    public void setJMSCorrelationIDAsBytes(byte[] correlationID) {
    }

    @Override
    public void setJMSCorrelationID(String correlationID) {
    }

    @Override
    public String getJMSCorrelationID() {
        return null;
    }

    @Override
    public Destination getJMSReplyTo() {
        return null;
    }

    @Override
    public void setJMSReplyTo(Destination replyTo) {
    }

    @Override
    public Destination getJMSDestination() {
        return null;
    }

    @Override
    public void setJMSDestination(Destination destination) {
    }

    @Override
    public int getJMSDeliveryMode() {
        return 1;
    }

    @Override
    public void setJMSDeliveryMode(int deliveryMode) {
    }

    @Override
    public boolean getJMSRedelivered() {
        return redelivered;
    }

    @Override
    public void setJMSRedelivered(boolean redelivered) {
        this.redelivered = redelivered;
    }

    @Override
    public String getJMSType() {
        return null;
    }

    @Override
    public void setJMSType(String type) {
    }

    @Override
    public long getJMSExpiration() {
        return 0L;
    }

    @Override
    public void setJMSExpiration(long expiration) {
    }

    @Override
    public long getJMSDeliveryTime() {
        return 0L;
    }

    @Override
    public void setJMSDeliveryTime(long deliveryTime) {
    }

    @Override
    public int getJMSPriority() {
        return 4;
    }

    @Override
    public void setJMSPriority(int priority) {
    }

    @Override
    public long getLongProperty(String name) {
        Object v = properties.get(name);
        return v == null ? 0L : Long.parseLong(String.valueOf(v));
    }

    @Override
    public Object getObjectProperty(String name) {
        return properties.get(name);
    }

    @Override
    public Enumeration<?> getPropertyNames() {
        return new Vector<>(properties.keySet()).elements();
    }

    @Override
    public short getShortProperty(String name) {
        Object v = properties.get(name);
        return v == null ? 0 : Short.parseShort(String.valueOf(v));
    }

    @Override
    public String getStringProperty(String name) {
        Object v = properties.get(name);
        return v == null ? null : String.valueOf(v);
    }

    @Override
    public boolean propertyExists(String name) {
        return properties.containsKey(name);
    }

    @Override
    public void setBooleanProperty(String name, boolean value) {
        properties.put(name, value);
    }

    @Override
    public void setByteProperty(String name, byte value) {
        properties.put(name, value);
    }

    @Override
    public void setDoubleProperty(String name, double value) {
        properties.put(name, value);
    }

    @Override
    public void setFloatProperty(String name, float value) {
        properties.put(name, value);
    }

    @Override
    public void setIntProperty(String name, int value) {
        properties.put(name, value);
    }

    @Override
    public void setLongProperty(String name, long value) {
        properties.put(name, value);
    }

    @Override
    public void setObjectProperty(String name, Object value) throws JMSException {
        properties.put(name, value);
    }

    @Override
    public void setShortProperty(String name, short value) {
        properties.put(name, value);
    }

    @Override
    public void setStringProperty(String name, String value) {
        properties.put(name, value);
    }
}
