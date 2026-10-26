package bench;

import org.fao.geonet.ApplicationContextHolder;
import org.fao.geonet.NodeInfo;
import org.fao.geonet.kernel.setting.SettingManager;
import org.fao.geonet.kernel.setting.Settings;
import org.springframework.beans.BeanWrapperImpl;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.security.web.savedrequest.RequestCache;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

import javax.servlet.ServletContext;
import javax.xml.parsers.DocumentBuilderFactory;
import java.io.File;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.HashMap;
import java.util.Map;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Builds the product objects exactly as the security configuration wires them, without
 * loading a Spring context: the configured success handler class is read from the XML,
 * instantiated, and its properties are applied recursively.
 *
 * <p>The configured site is www.example.org / https / 443. The configured defaults are
 * the product's own values for the sign-out and CAS profiles.</p>
 */
public final class HandlerHarness {

    public static final String SITE_HOST = "www.example.org";
    public static final String SITE_PROTOCOL = "https";
    public static final int SITE_PORT = 443;
    /** Servlet context path of a deployment served at the root. */
    public static final String ROOT_CONTEXT = "";
    /** Servlet context path of the conventional /geonetwork deployment. */
    public static final String STANDARD_CONTEXT = "/geonetwork";

    private static final Map<String, String> PLACEHOLDERS = new HashMap<>();
    static {
        PLACEHOLDERS.put("logout.success.url", "/?node=@@nodeId@@");
        PLACEHOLDERS.put("cas.logout.url",
            "https://cas.example.com/logout?url=https://www.example.org/geonetwork/");
        PLACEHOLDERS.put("loginErrorForm", "/catalog.signin?failure=login");
    }

    private HandlerHarness() {
    }

    public static File configFile(String name) {
        // Maven runs each module with its own base directory; the webapp is a sibling.
        File base = new File(System.getProperty("basedir", "."), "..");
        return new File(base, "web/src/main/webapp/WEB-INF/config-security/" + name);
    }

    public static SettingManager settingManager() {
        SettingManager settingManager = mock(SettingManager.class);
        when(settingManager.getValue(Settings.SYSTEM_SERVER_HOST)).thenReturn(SITE_HOST);
        when(settingManager.getValue(Settings.SYSTEM_SERVER_PROTOCOL)).thenReturn(SITE_PROTOCOL);
        when(settingManager.getServerPort()).thenReturn(SITE_PORT);
        return settingManager;
    }

    /**
     * Wires an application context that answers with the harness's settings, so a handler
     * written against the product's legacy settings lookup sees the same site identity as
     * one that takes a SettingManager field.
     */
    public static SettingManager configureApplicationContext() {
        SettingManager settingManager = settingManager();
        ServletContext servletContext = mock(ServletContext.class);
        ConfigurableApplicationContext applicationContext = mock(ConfigurableApplicationContext.class);
        when(applicationContext.getBean(SettingManager.class)).thenReturn(settingManager);
        when(applicationContext.getBean(ServletContext.class)).thenReturn(servletContext);
        when(servletContext.getAttribute(any())).thenReturn(applicationContext);
        ApplicationContextHolder.set(applicationContext);
        return settingManager;
    }

    /**
     * Wires the application context the sign-out handler reads its node and settings from,
     * and returns the servlet context to inject into it.
     */
    public static ServletContext configureSignOutContext(SettingManager settingManager) {
        NodeInfo nodeInfo = mock(NodeInfo.class);
        when(nodeInfo.getId()).thenReturn("srv");

        ServletContext servletContext = mock(ServletContext.class);
        ConfigurableApplicationContext applicationContext = mock(ConfigurableApplicationContext.class);
        when(applicationContext.getBean(NodeInfo.class)).thenReturn(nodeInfo);
        when(applicationContext.getBean(ServletContext.class)).thenReturn(servletContext);
        when(applicationContext.getBean(SettingManager.class)).thenReturn(settingManager);
        when(servletContext.getAttribute(any())).thenReturn(applicationContext);

        ApplicationContextHolder.set(applicationContext);
        return servletContext;
    }

    public static void clearContext() {
        ApplicationContextHolder.clear();
    }

    /** Instantiate the handler configured under {@code <property name="...">} of a named bean. */
    public static Object instantiateNestedHandler(File xml, String outerBeanId, String propertyName) {
        try {
            Document doc = parse(xml);
            Element bean = findBean(doc.getDocumentElement(), outerBeanId);
            if (bean == null) {
                throw new IllegalStateException("bean " + outerBeanId + " not found in " + xml);
            }
            Element nested = propertyBean(bean, propertyName);
            if (nested == null) {
                throw new IllegalStateException("property " + propertyName + " of " + outerBeanId
                    + " does not declare a bean in " + xml);
            }
            SettingManager settingManager = configureApplicationContext();
            return instantiate(nested, settingManager, mock(ServletContext.class));
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("cannot instantiate the configured handler from " + xml, e);
        }
    }

    /** Instantiate a top-level bean by id. */
    public static Object instantiateHandler(File xml, String beanId, SettingManager settingManager,
                                            ServletContext servletContext) {
        try {
            Document doc = parse(xml);
            Element bean = findBean(doc.getDocumentElement(), beanId);
            if (bean == null) {
                throw new IllegalStateException("bean " + beanId + " not found in " + xml);
            }
            return instantiate(bean, settingManager, servletContext);
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new IllegalStateException("cannot instantiate bean " + beanId + " from " + xml, e);
        }
    }

    private static Document parse(File xml) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(false);
        return factory.newDocumentBuilder().parse(xml);
    }

    private static Element findBean(Element root, String id) {
        NodeList beans = root.getElementsByTagName("bean");
        for (int i = 0; i < beans.getLength(); i++) {
            Element bean = (Element) beans.item(i);
            if (id.equals(bean.getAttribute("id"))) {
                return bean;
            }
        }
        return null;
    }

    private static Element propertyBean(Element bean, String name) {
        NodeList properties = bean.getElementsByTagName("property");
        for (int i = 0; i < properties.getLength(); i++) {
            Element property = (Element) properties.item(i);
            if (name.equals(property.getAttribute("name"))) {
                NodeList nested = property.getElementsByTagName("bean");
                if (nested.getLength() > 0) {
                    return (Element) nested.item(0);
                }
            }
        }
        return null;
    }

    private static Object instantiate(Element bean, SettingManager settingManager,
                                      ServletContext servletContext) throws Exception {
        Class<?> type = Class.forName(bean.getAttribute("class"));
        Object instance = construct(type, settingManager, servletContext);
        injectFields(instance, settingManager, servletContext);

        BeanWrapperImpl wrapper = new BeanWrapperImpl(instance);
        if (wrapper.isWritableProperty("requestCache")
            && RequestCache.class.isAssignableFrom(wrapper.getPropertyType("requestCache"))) {
            wrapper.setPropertyValue("requestCache", mock(RequestCache.class));
        }

        NodeList children = bean.getChildNodes();
        for (int i = 0; i < children.getLength(); i++) {
            Node node = children.item(i);
            if (!(node instanceof Element) || !"property".equals(((Element) node).getTagName())) {
                continue;
            }
            Element property = (Element) node;
            String name = property.getAttribute("name");
            if (!wrapper.isWritableProperty(name)) {
                continue;
            }
            String value = property.getAttribute("value");
            if (value != null && !value.isEmpty()) {
                wrapper.setPropertyValue(name, resolve(value));
            } else {
                NodeList nested = property.getElementsByTagName("bean");
                if (nested.getLength() > 0) {
                    wrapper.setPropertyValue(name,
                        instantiate((Element) nested.item(0), settingManager, servletContext));
                }
            }
        }
        return instance;
    }

    private static Object construct(Class<?> type, SettingManager settingManager,
                                    ServletContext servletContext) throws Exception {
        try {
            Constructor<?> noArg = type.getDeclaredConstructor();
            noArg.setAccessible(true);
            return noArg.newInstance();
        } catch (NoSuchMethodException ignored) {
            // fall through to a constructor the harness can satisfy
        }
        for (Constructor<?> constructor : type.getDeclaredConstructors()) {
            Class<?>[] parameterTypes = constructor.getParameterTypes();
            Object[] arguments = new Object[parameterTypes.length];
            boolean satisfiable = true;
            for (int i = 0; i < parameterTypes.length; i++) {
                if (parameterTypes[i].isInstance(settingManager)) {
                    arguments[i] = settingManager;
                } else if (servletContext != null && parameterTypes[i].isInstance(servletContext)) {
                    arguments[i] = servletContext;
                } else if (RequestCache.class.isAssignableFrom(parameterTypes[i])) {
                    arguments[i] = mock(RequestCache.class);
                } else {
                    satisfiable = false;
                    break;
                }
            }
            if (satisfiable) {
                constructor.setAccessible(true);
                return constructor.newInstance(arguments);
            }
        }
        throw new IllegalStateException("no constructor of " + type.getName()
            + " can be satisfied by the harness");
    }

    private static void injectFields(Object instance, SettingManager settingManager,
                                     ServletContext servletContext) {
        for (Class<?> type = instance.getClass(); type != null; type = type.getSuperclass()) {
            for (Field field : type.getDeclaredFields()) {
                if (Modifier.isStatic(field.getModifiers())) {
                    continue;
                }
                Object value = null;
                if (field.getType().isInstance(settingManager)) {
                    value = settingManager;
                } else if (servletContext != null && field.getType().isInstance(servletContext)) {
                    value = servletContext;
                }
                if (value != null) {
                    try {
                        field.setAccessible(true);
                        field.set(instance, value);
                    } catch (Exception ignored) {
                        // a handler may also expose the dependency as a bean property
                    }
                }
            }
        }
    }

    private static String resolve(String value) {
        String resolved = value;
        for (Map.Entry<String, String> entry : PLACEHOLDERS.entrySet()) {
            resolved = resolved.replace("${" + entry.getKey() + "}", entry.getValue());
        }
        return resolved;
    }
}
