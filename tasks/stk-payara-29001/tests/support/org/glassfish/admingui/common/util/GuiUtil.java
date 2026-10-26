package org.glassfish.admingui.common.util;
import java.text.MessageFormat;
import java.util.Locale;
import java.util.Map;
import java.util.logging.Logger;
import com.sun.jsftemplating.layout.descriptors.handler.HandlerContext;
public final class GuiUtil {
    public static final Locale guiLocale = Locale.ENGLISH;
    private static final Logger LOG = Logger.getLogger("org.glassfish.admingui.common.util.GuiUtil");
    private GuiUtil() {}
    public static Logger getLogger() { return LOG; }
    public static String getCommonMessage(String key) { return key; }
    public static String getCommonMessage(String key, Object[] args) {
        return args == null || args.length == 0 ? key : new MessageFormat(key, guiLocale).format(args);
    }
    public static void prepareAlert(String type, String summary, String detail) { }
    public static void handleException(HandlerContext ctx, Throwable ex) { }
    public static void handleError(HandlerContext ctx, String detail) { }
    public static Object getMapValue(Map<String, ?> map, String mapKeys) {
        if (map == null || mapKeys == null) return null;
        Object cur = map;
        for (String k : mapKeys.split(",")) {
            if (!(cur instanceof Map)) return null;
            cur = ((Map<?, ?>) cur).get(k);
        }
        return cur;
    }
}
