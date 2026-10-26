package vtesting;

import org.junit.jupiter.api.Test;

import org.springframework.beans.MutablePropertyValues;
import org.springframework.validation.DataBinder;

import static org.junit.jupiter.api.Assertions.assertEquals;

/**
 * Behavioural checks for the reported route: a direct property named with an initial capital.
 */
class SecurityDirectFieldCaseTests {

	private static void bindIgnoringRefusal(DataBinder binder, MutablePropertyValues pvs) {
		try {
			binder.bind(pvs);
		}
		catch (RuntimeException ex) {
			// A refusal raised while screening the field is acceptable.
		}
	}

	@Test
	void nameNamedWithInitialCapitalIsNotWritten() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("name");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("Name", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-name", user.getName());
	}

	@Test
	void roleNamedWithInitialCapitalIsNotWritten() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("role");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("Role", "admin");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("user", user.getRole());
	}

	@Test
	void cityNamedWithInitialCapitalIsNotWritten() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("city");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("City", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-city", user.getCity());
	}

	@Test
	void idNamedWithInitialCapitalIsNotWritten() {
		VBeans.User user = new VBeans.User();
		DataBinder binder = new DataBinder(user);
		binder.setDisallowedFields("id");

		MutablePropertyValues pvs = new MutablePropertyValues();
		pvs.add("Id", "hijacked");
		bindIgnoringRefusal(binder, pvs);

		assertEquals("original-id", user.getId());
	}
}
