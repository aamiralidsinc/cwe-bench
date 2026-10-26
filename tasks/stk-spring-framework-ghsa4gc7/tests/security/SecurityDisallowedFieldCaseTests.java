package vtesting;

import org.junit.jupiter.api.Test;

import org.springframework.beans.MutablePropertyValues;
import org.springframework.validation.DataBinder;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Behavioural checks for restrictions on bindable object properties.
 */
class SecurityDisallowedFieldCaseTests {

	private static void bindIgnoringRefusal(DataBinder binder, MutablePropertyValues pvs) {
		try {
			binder.bind(pvs);
		}
		catch (RuntimeException ex) {
			// A refusal raised while screening the field is acceptable: what matters is that the
			// excluded property is not written.
		}
	}

	@Test
	void directPropertyNamedWithInitialCapitalIsNotWritten() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("name");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("Name", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-name", user.getName());
	}

	@Test
	void nestedPropertyNamedWithInitialCapitalIsNotWritten() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("address.city");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("address.City", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-city", user.getAddress().getCity());
	}

	@Test
	void wildcardPatternStillProtectsACapitalisedNestedName() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("address.cit*");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("address.City", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-city", user.getAddress().getCity());
	}

	@Test
	void capitalisedNestedNameUnderADifferentParentIsNotWritten() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("address.city");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("Address.City", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-city", user.getAddress().getCity());
	}
}
