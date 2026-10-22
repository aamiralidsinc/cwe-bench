package benchkit;

/** A user record with a nested value declared by its interface. */
public record RecordEnvelope(Payload payload, String label) {
}
