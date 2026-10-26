package com.sun.enterprise.security.ssl;
import javax.net.ssl.SSLContext;
public interface SSLUtils {
    SSLContext getAdminSSLContext(String alias, String protocol);
}
