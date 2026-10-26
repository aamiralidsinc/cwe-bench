package com.sun.enterprise.security;
import org.glassfish.hk2.api.ServiceLocator;
public final class SecurityServicesUtil {
    private static final SecurityServicesUtil INSTANCE = new SecurityServicesUtil();
    private SecurityServicesUtil() {}
    public static SecurityServicesUtil getInstance() { return INSTANCE; }
    public ServiceLocator getHabitat() { return null; }
}
