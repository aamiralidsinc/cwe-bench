package benchkit;

/** A user record with a nested value declared by a concrete serializable class. */
public record ConcreteRecord(SerializablePayload payload) {
}
