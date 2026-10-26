package vtesting;

import java.util.Locale;

import org.junit.jupiter.api.Test;

import org.springframework.beans.MutablePropertyValues;
import org.springframework.validation.DataBinder;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Behavioural checks for restrictions on bindable object properties while the process runs under a
 * regional setting whose letter-case rules differ from the default one.
 */
class SecurityDisallowedFieldLocaleTests {

	private static void bindIgnoringRefusal(DataBinder binder, MutablePropertyValues pvs) {
		try {
			binder.bind(pvs);
		}
		catch (RuntimeException ex) {
			// A refusal raised while screening the field is acceptable.
		}
	}

	private static void withLocale(Locale locale, Runnable action) {
		Locale previous = Locale.getDefault();
		try {
			Locale.setDefault(locale);
			action.run();
		}
		finally {
			Locale.setDefault(previous);
		}
	}

	@Test
	void restrictionHoldsWhenTheProcessUsesATurkishLocale() {
		withLocale(new Locale("tr", "TR"), () -> {
			VBeans.User user = new VBeans.User();
			DataBinder binder = new DataBinder(user);
			binder.setDisallowedFields("id");

			MutablePropertyValues pvs = new MutablePropertyValues();
			pvs.add("Id", "hijacked");
			bindIgnoringRefusal(binder, pvs);

			assertEquals("original-id", user.getId());
		});
	}

	@Test
	void restrictionNamedWithACapitalHoldsUnderATurkishLocale() {
		withLocale(new Locale("tr", "TR"), () -> {
			VBeans.User user = new VBeans.User();
			DataBinder binder = new DataBinder(user);
			binder.setDisallowedFields("Id");

			MutablePropertyValues pvs = new MutablePropertyValues();
			pvs.add("id", "hijacked");
			bindIgnoringRefusal(binder, pvs);

			assertEquals("original-id", user.getId());
		});
	}
}
